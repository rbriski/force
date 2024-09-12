# manage.py
import locale
import os
from datetime import datetime

import boto3
import click
import svcs
from dotenv import load_dotenv
from flask.cli import FlaskGroup
from psycopg import Connection
from rich import print
from slack_bolt import App

from project.models.db import (
    Event,
    Person,
    PlayerParent,
    PlayerTransactions,
    TransactionDB,
    VendorPayment,
)
from project.models.email import Email
from project.server import at, create_app

locale.setlocale(locale.LC_ALL, "en_US.UTF-8")

# logging.basicConfig()
# logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)


load_dotenv()
app = create_app()
cli = FlaskGroup(create_app=create_app)

slack = App(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET"),
)


@cli.command()
def cleardb():
    conn = svcs.flask.get(Connection)
    cursor = conn.cursor()

    cursor.execute("TRUNCATE TABLE people CASCADE")
    cursor.execute("TRUNCATE TABLE m_people_transactions CASCADE")
    cursor.execute("TRUNCATE TABLE m_player_parent CASCADE")
    cursor.execute("TRUNCATE TABLE events CASCADE")
    cursor.execute("TRUNCATE TABLE transactions CASCADE")
    conn.commit()


def send_message(cursor, player):
    at_id = player.at_id
    b = player.balance(cursor)

    for parent in player.parents(cursor):
        slack_id = parent.slack_id
        if not slack_id:
            continue
        print(f"Sending message to {player.name} parent: ({parent.name}) for ${b*-1}")

        conv = slack.client.conversations_open(users=slack_id)

        msg = f"Hello, {parent.name}!  You owe *${b*-1}*.  Details at the Ledger :  https://deanzaforce.club/{at_id}  Pay at : https://www.paypal.com/paypalme/Force2010G/{b*-1}."
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"Hello, {parent.name}!  You owe *${b*-1}*.",
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"Details at the Ledger :  https://deanzaforce.club/{at_id}",
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"Pay at : https://www.paypal.com/paypalme/Force2010G/{b*-1}.",
                },
            },
        ]
        slack.client.chat_postMessage(
            channel=conv["channel"]["id"],
            text=msg,
            blocks=blocks,
        )


@cli.command()
def getemail():
    conn = svcs.flask.get(Connection)
    conn.set_autocommit(True)
    cursor = conn.cursor()
    s3 = boto3.client(
        "s3",
        aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
        region_name="us-east-1",
    )
    emls = Email.all(bucket="bob.briski", prefix="", s3_client=s3)
    for e in emls:
        try:
            msg = e.get_content()
            res = e.parse(msg)
            vp = VendorPayment(
                vendor_name="paypal",
                amount=res["amount"],
                transaction_date=res["transaction_date"],
                vendor_txn_id=res["transaction_id"],
                sender=res["sender"],
            )
            vp.insert(cursor)
            print(res)
        except Exception as e:
            print("Could not parse email")
            print(e)


@cli.command()
def getplayer():
    conn = svcs.flask.get(Connection)
    cursor = conn.cursor()

    p = Person.find_by_paypal_name(cursor, "Marco Marini")
    player = p.player(cursor)
    for pt in player.payments(cursor):
        print(pt)


@cli.command()
def invoice():
    conn = svcs.flask.get(Connection)
    cursor = conn.cursor()

    for p in Person.all_players(cursor):
        b = p.balance(cursor)
        if b < 0:
            send_message(cursor, p)


@cli.command()
def people():
    conn = svcs.flask.get(Connection)
    cursor = conn.cursor()

    parents = at.api.table(at.base_id, at.tables["parents"])
    for p in parents.all():
        f = p["fields"]
        if Person.exists_airtable(cursor, at_id=p["id"]):
            continue
        person = Person(
            at_id=p["id"],
            created_at=p["createdTime"],
            updated_at=p["createdTime"],
            description=None,
            name=f["Name"],
            email=f.get("Email"),
            phone=f.get("Phone"),
            slack_id=f.get("Slack"),
            paypal_name=f.get("Paypal"),
            venmo_name=f.get("Venmo"),
        )
        person.insert(cursor)
    conn.commit()

    players = at.api.table(at.base_id, at.tables["roster"])
    for p in players.all():
        f = p["fields"]
        if Person.exists_airtable(cursor, at_id=p["id"]):
            continue
        person = Person(
            at_id=p["id"],
            created_at=p["createdTime"],
            updated_at=p["createdTime"],
            description=None,
            name=f["Name"],
            email=f.get("Email"),
            phone=f.get("Phone"),
            slack_id=None,
            paypal_name=f.get("Paypal"),
            venmo_name=f.get("Venmo"),
        )
        person.insert(cursor)
    conn.commit()

    for p in players.all():
        f = p["fields"]
        if "Parents" in f:
            player = Person.find_by_at_id(cursor, at_id=p["id"])
            for parent_at_id in f["Parents"]:
                p = Person.find_by_at_id(cursor, at_id=parent_at_id)
                cxn = PlayerParent(player_id=player.id, parent_id=p.id)
                cursor.execute(
                    f"""INSERT INTO {PlayerParent.table_name} (id, player_id, parent_id) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING""",
                    (cxn.id, cxn.player_id, cxn.parent_id),
                )
    conn.commit()


@cli.command()
def events():
    conn = svcs.flask.get(Connection)
    cursor = conn.cursor()

    events = at.api.table(at.base_id, at.tables["events"])
    for p in events.all():
        f = p["fields"]
        if Event.exists_airtable(cursor, at_id=p["id"]):
            continue
        f_dt = f.get("Date")
        dt = None
        if f_dt:
            dt = datetime.strptime(f.get("Date"), "%Y-%m-%d")
        event = Event(
            at_id=p["id"],
            created_at=p["createdTime"],
            updated_at=p["createdTime"],
            name=f.get("Event"),
            date=dt,
            description=f.get("Description"),
        )
        event.insert(cursor)
    conn.commit()


@cli.command()
@click.option("--truncate", "-t", help="Truncate transaction tables", is_flag=True)
def transactions(truncate):
    conn = svcs.flask.get(Connection)
    cursor = conn.cursor()

    if truncate:
        cursor.execute(f"TRUNCATE TABLE {PlayerTransactions.table_name} CASCADE")
        cursor.execute(f"TRUNCATE TABLE {TransactionDB.table_name} CASCADE")

    expenses = at.api.table(at.base_id, at.tables["expenses"])
    for p in expenses.all():
        f = p["fields"]
        if TransactionDB.exists_airtable(cursor, at_id=p["id"]):
            continue

        event_id = None
        if "Event" in f:
            evt_id = f["Event"][0]
            event_id = Event.find_by_at_id(cursor, at_id=evt_id).id
        expense = TransactionDB(
            at_id=p["id"],
            created_at=p["createdTime"],
            updated_at=p["createdTime"],
            amount=f["Amount"] * -1,
            description=f["Description"],
            debit=True,
            event_id=event_id,
        )
        expense.insert(cursor)
    conn.commit()

    payments = at.api.table(at.base_id, at.tables["payments"])
    for p in payments.all():
        f = p["fields"]
        if TransactionDB.exists_airtable(cursor, at_id=p["id"]):
            continue

        event_id = None
        if "Event" in f:
            evt_id = f["Event"][0]
            event_id = Event.find_by_at_id(cursor, at_id=evt_id).id
        payment = TransactionDB(
            at_id=p["id"],
            created_at=p["createdTime"],
            updated_at=p["createdTime"],
            amount=f["Amount"],
            description=f["Description"],
            debit=False,
            event_id=event_id,
        )
        payment.insert(cursor)
    conn.commit()

    roster = at.api.table(at.base_id, at.tables["roster"])
    for r in roster.all():
        player = Person.find_by_at_id(cursor, at_id=r["id"])
        if "Payments" in r["fields"]:
            for payment_at_id in r["fields"]["Payments"]:
                t = TransactionDB.find_by_at_id(cursor, at_id=payment_at_id)
                cxn = PlayerTransactions(person_id=player.id, transaction_id=t.id)
                cursor.execute(
                    f"""INSERT INTO {PlayerTransactions.table_name} (id, person_id, transaction_id) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING""",
                    (cxn.id, cxn.person_id, cxn.transaction_id),
                )

        if "Expenses" in r["fields"]:
            for expense_at_id in r["fields"]["Expenses"]:
                t = TransactionDB.find_by_at_id(cursor, at_id=expense_at_id)
                cxn = PlayerTransactions(person_id=player.id, transaction_id=t.id)
                cursor.execute(
                    f"""INSERT INTO {PlayerTransactions.table_name} (id, person_id, transaction_id) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING""",
                    (cxn.id, cxn.person_id, cxn.transaction_id),
                )
    conn.commit()


@cli.command()
def tr():
    conn = svcs.flask.get(Connection)
    cursor = conn.cursor()

    p = Person.find_by_at_id(cursor, "reckwBcC6q1wijgoB")
    for t in p.transactions():
        print(t)


# def parentemails():
#     for p in Person.query.all():
#         if not p.parents:
#             continue
#         emails = [parent.email for parent in p.parents]
#         print(f"{p.name}\t{ ','.join(emails) }\thttps://deanzaforce.club/{ p.at_id }")


if __name__ == "__main__":
    cli()
