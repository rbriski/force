# project/server/user/views.py

from flask import Blueprint, render_template

from project.server.models import Transaction

transaction_blueprint = Blueprint("transaction", __name__)


@transaction_blueprint.route("/expenses", methods=["GET"])
def expenses():
    expenses = []

    for t in Transaction.expenses().order_by(Transaction.created_at.desc()).all():
        obj = {
            "description": t.description,
            "player_names": [p.name for p in t.players()],
            "amount": t.amount,
        }
        expenses.append(obj)

    return render_template(
        "transaction/expenses.html", player="Expenses", expenses=expenses
    )
