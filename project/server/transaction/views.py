# project/server/user/views.py

from flask import Blueprint, redirect, render_template
from flask_wtf import FlaskForm
from wtforms import BooleanField, DecimalField, HiddenField, StringField

from project.server.models import Person, Transaction

transaction_blueprint = Blueprint("transaction", __name__)


class TransactionForm(FlaskForm):
    amount = DecimalField("Amount")
    description = StringField("Description")
    event_id = HiddenField()
    participants = HiddenField()
    debit = BooleanField("Expense?")


@transaction_blueprint.route("/expenses", methods=["GET"])
def expenses():
    expenses = []

    for t in Transaction.collect_all():
        if not t.debit:
            continue
        obj = {
            "description": t.description,
            "player_names": [p.name for p in t.players()],
            "amount": t.amount,
        }
        expenses.append(obj)

    return render_template(
        "transaction/expenses.html", player="Expenses", expenses=expenses
    )


@transaction_blueprint.route("/expenses/add", methods=["GET"])
def add_expense():
    f = TransactionForm()
    if f.validate_on_submit():
        return redirect("/expenses")

    players = Person.all_players()
    return render_template("transaction/expense_form.html", f=f, players=players)
