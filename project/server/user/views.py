# project/server/user/views.py
import functools

from flask import Blueprint, abort, render_template

from project.server import at as db
from project.server.models import Event, Person, Transaction

user_blueprint = Blueprint("user", __name__)


@user_blueprint.route("/rec<rec_id>", methods=["GET"])
def ledger(rec_id=None):
    # Home page is a 404
    if rec_id is None:
        abort(404)

    rec_id = "rec" + rec_id
    player = Person.query.filter_by(at_id=rec_id)

    # No matching player is a 404
    if not player:
        abort(404)

    expenses = db.get_expenses(player["id"])
    payments = db.get_payments(player["id"])
    ledger = db.get_ledger(expenses, payments)

    total = functools.reduce(lambda a, b: a + b["amount"], ledger, 0)

    return render_template(
        "user/ledger.html",
        player=player["fields"]["Name"],
        total=total,
        ledger=sorted(ledger, key=lambda i: i["created_at"], reverse=True),
    )
