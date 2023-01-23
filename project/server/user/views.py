# project/server/user/views.py
from pprint import pprint

from flask import Blueprint, abort, render_template

from project.server.models import Person

user_blueprint = Blueprint("user", __name__)


@user_blueprint.route("/rec<rec_id>", methods=["GET"])
def ledger(rec_id=None):
    # Home page is a 404
    if rec_id is None:
        abort(404)

    rec_id = "rec" + rec_id
    player = Person.query.filter_by(at_id=rec_id).first()

    # No matching player is a 404
    if not player:
        abort(404)

    ledger = player.ledger()
    ledger.reverse()
    balance = player.balance()

    return render_template(
        "user/ledger.html",
        player=player.name,
        balance=balance,
        ledger=ledger,
    )
