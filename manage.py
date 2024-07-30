# manage.py
import locale
from datetime import datetime
from pprint import pprint

import click
import svcs
from dotenv import load_dotenv
from flask.cli import FlaskGroup
from psycopg import Connection

from project.server import at, create_app
from project.models.db import (
    Event,
    Person,
    PlayerParent,
    PlayerTransactions,
    TransactionDB,
)

locale.setlocale(locale.LC_ALL, "en_US.UTF-8")

# logging.basicConfig()
# logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)


load_dotenv()
app = create_app()
cli = FlaskGroup(create_app=create_app)


# @cli.command()
# def test():
#     """Runs the unit tests without test coverage."""
#     tests = unittest.TestLoader().discover("project/tests", pattern="test*.py")
#     result = unittest.TextTestRunner(verbosity=2).run(tests)
#     if result.wasSuccessful():
#         sys.exit(0)
#     else:
#         sys.exit(1)


# @cli.command()
# def flake():
#     """Runs flake8 on the project."""
#     subprocess.run(["flake8", "project"])


# @cli.command()
# def invoice():
#     """Send invoices to parents"""
#     """python manage.py invoice"""
#     for p in Person.query.all():
#         bal = p.balance()
#         if bal < -500:
#             if p.name != "Ayla Briski":
#                 continue
#             print(p.name)
#             print(p.balance())
#             print("\n--\n")

#             for rent in p.parents:
#                 print(rent.name)


#                 # continue
#                 requests.post(
#                     "https://api.mailgun.net/v3/m.deanzaforce.club/messages",
#                     auth=("api", os.environ["MAILGUN_API_KEY"]),
#                     data={
#                         "from": "DeAnza 2010G - Bob Briski <postmaster@m.deanzaforce.club>",
#                         "to": rent.name + " <" + rent.email + ">",
#                         "h:Reply-To": "Bob Briski <rbriski+force@gmail.com>",
#                         "subject": "2010G Force : 2023 ECNL Showcase Fees",
#                         "template": "force-payment-request",
#                         "h:X-Mailgun-Variables": json.dumps(
#                             {
#                                 "player_name": p.name,
#                                 "parent_name": rent.name,
#                                 "amount": str(p.balance() * -1),
#                                 "ledger_link": "https://deanzaforce.club/" + p.at_id,
#                             }
#                         ),
#                     },
#                 )
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
