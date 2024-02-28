# project/server/user/views.py

from flask import Blueprint, abort, render_template, jsonify, make_response, current_app

from project.server.models import Person
import svcs
from psycopg import Connection
from temporalio.client import Client

from project.workflows.invoice import (
    SendInvoiceWorkflow,
    WorkflowOptions,
    invoice_queue_name,
)

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


# @user_blueprint.route("/subscribe/rec<rec_id>", methods=["GET"])
# async def start_subscription(rec_id=None):
#     client = current_app.temporal_client

#     conn = svcs.flask.get(Connection)
#     cursor = conn.cursor()

#     # Home page is a 404
#     if rec_id is None:
#         abort(404)

#     rec_id = "rec" + rec_id
#     player = Person.find_by_at_id(cursor, rec_id)

#     email: str = str(player.email)
#     data: WorkflowOptions = WorkflowOptions(email=email)
#     await client.start_workflow(
#         SendEmailWorkflow.run,
#         data,
#         id=data.email,
#         task_queue=task_queue_name,
#     )

#     message = jsonify({"message": "Resource created successfully"})
#     response = make_response(message, 201)
#     return response


@user_blueprint.route("/subscribe/rec<rec_id>", methods=["GET"])
async def start_invoicing(rec_id=None):
    client = current_app.temporal_client

    conn = svcs.flask.get(Connection)
    cursor = conn.cursor()

    # Home page is a 404
    if rec_id is None:
        abort(404)

    rec_id = "rec" + rec_id

    data: WorkflowOptions = WorkflowOptions(id=rec_id)
    await client.start_workflow(
        SendInvoiceWorkflow.run,
        data,
        id=data.id,
        task_queue=invoice_queue_name,
    )

    message = jsonify({"message": "Resource created successfully"})
    response = make_response(message, 201)
    return response
