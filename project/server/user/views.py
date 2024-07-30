# project/server/user/views.py

from flask import Blueprint, abort, render_template

from project.models.db import Person
import svcs
from psycopg import Connection

user_blueprint = Blueprint("user", __name__)


@user_blueprint.route("/rec<rec_id>", methods=["GET"])
def ledger(rec_id=None):
    conn = svcs.flask.get(Connection)
    cursor = conn.cursor()

    # Home page is a 404
    if rec_id is None:
        abort(404)

    rec_id = "rec" + rec_id
    player = Person.find_by_at_id(cursor, rec_id)

    # No matching player is a 404
    if not player:
        abort(404)

    ledger = player.ledger(cursor)
    ledger.reverse()
    balance = player.balance(cursor)

    return render_template(
        "user/ledger.html",
        player=player.name,
        balance=balance,
        ledger=ledger,
    )
