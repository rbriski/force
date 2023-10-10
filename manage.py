# manage.py
import json
import os
import subprocess
import sys
import unittest
from datetime import datetime
from pprint import pprint

import requests
from dotenv import load_dotenv
from flask.cli import FlaskGroup
from pyairtable import Table

from project.server import at, create_app, db
from project.server.models import Event, Person, Transaction
from project.teamsnap import Teamsnap

# logging.basicConfig()
# logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)


load_dotenv()
app = create_app()
cli = FlaskGroup(create_app=create_app)


@cli.command()
def createdb():
    db.drop_all()
    db.create_all()
    db.session.commit()


@cli.command()
def test():
    """Runs the unit tests without test coverage."""
    tests = unittest.TestLoader().discover("project/tests", pattern="test*.py")
    result = unittest.TextTestRunner(verbosity=2).run(tests)
    if result.wasSuccessful():
        sys.exit(0)
    else:
        sys.exit(1)


@cli.command()
def flake():
    """Runs flake8 on the project."""
    subprocess.run(["flake8", "project"])


@cli.command()
def invoice():
    """Send invoices to parents"""
    """python manage.py invoice"""
    for p in Person.query.all():
        bal = p.balance()
        if bal < -500:
            if p.name != "Ayla Briski":
                continue
            print(p.name)
            print(p.balance())
            print("\n--\n")

            for rent in p.parents:
                print(rent.name)

                # continue
                requests.post(
                    "https://api.mailgun.net/v3/m.deanzaforce.club/messages",
                    auth=("api", os.environ["MAILGUN_API_KEY"]),
                    data={
                        "from": "DeAnza 2010G - Bob Briski <postmaster@m.deanzaforce.club>",
                        "to": rent.name + " <" + rent.email + ">",
                        "h:Reply-To": "Bob Briski <rbriski+force@gmail.com>",
                        "subject": "2010G Force : 2023 ECNL Showcase Fees",
                        "template": "force-payment-request",
                        "h:X-Mailgun-Variables": json.dumps(
                            {
                                "player_name": p.name,
                                "parent_name": rent.name,
                                "amount": str(p.balance() * -1),
                                "ledger_link": "https://deanzaforce.club/" + p.at_id,
                            }
                        ),
                    },
                )


@cli.command()
def people():
    parents = Table(at.api_key, at.base_id, at.tables["parents"])
    for p in parents.all():
        f = p["fields"]
        existing = Person.query.filter_by(at_id=p["id"]).first()
        if existing:
            continue
        person = Person(
            at_id=p["id"],
            name=f["Name"],
            email=f.get("Email"),
            phone=f.get("Phone"),
        )
        db.session.add(person)
    db.session.commit()

    players = Table(at.api_key, at.base_id, at.tables["roster"])
    for p in players.all():
        f = p["fields"]
        existing = Person.query.filter_by(at_id=p["id"]).first()
        if existing:
            continue
        person = Person(
            at_id=p["id"],
            name=f["Name"],
            email=f.get("Email"),
            phone=f.get("Phone"),
        )
        db.session.add(person)
    db.session.commit()


@cli.command()
def ppeople():
    roster = Table(at.api_key, at.base_id, at.tables["roster"])
    for r in roster.all():
        if "Parents" in r["fields"]:
            player = Person.query.filter_by(at_id=r["id"]).first()
            pprint(player.name)
            parents = Person.query.where(Person.at_id.in_(r["fields"]["Parents"])).all()
            for parent in parents:
                player.parents.append(parent)
                print("--" + parent.name)
    db.session.commit()


@cli.command()
def events():
    events = Table(at.api_key, at.base_id, at.tables["events"])
    for p in events.all():
        f = p["fields"]
        f_dt = f.get("Date")
        dt = None
        if f_dt:
            dt = datetime.strptime(f.get("Date"), "%Y-%m-%d")
        existing = Event.query.filter_by(at_id=p["id"]).first()
        if existing:
            continue
        evt = Event(at_id=p["id"], name=f.get("Event"), date=dt)
        db.session.add(evt)
    db.session.commit()


@cli.command()
def expenses():
    expenses = Table(at.api_key, at.base_id, at.tables["expenses"])
    for p in expenses.all():
        f = p["fields"]
        event = None
        if "Event" in f:
            evt_id = f["Event"][0]
            event = Event.query.filter_by(at_id=evt_id).one()
        dt = datetime.strptime(p["createdTime"], "%Y-%m-%dT%H:%M:%S.000Z")
        existing = Transaction.query.filter_by(at_id=p["id"]).first()
        if existing:
            continue
        expense = Transaction(
            at_id=p["id"],
            created_at=dt,
            amount=f["Amount"] * -1,
            description=f["Description"],
            debit=True,
        )
        expense.event = event
        db.session.add(expense)

    db.session.commit()


@cli.command()
def payments():
    payments = Table(at.api_key, at.base_id, at.tables["payments"])
    for p in payments.all():
        f = p["fields"]
        dt = datetime.strptime(p["createdTime"], "%Y-%m-%dT%H:%M:%S.000Z")
        existing = Transaction.query.filter_by(at_id=p["id"]).first()
        if existing:
            continue
        payment = Transaction(
            at_id=p["id"],
            created_at=dt,
            amount=f["Amount"],
            description=f["Description"],
            debit=False,
        )
        db.session.add(payment)

    db.session.commit()


@cli.command()
def ppayments():
    roster = Table(at.api_key, at.base_id, at.tables["roster"])
    for r in roster.all():
        if "Payments" in r["fields"]:
            player = Person.query.filter_by(at_id=r["id"]).one()
            pprint(player.name)
            payments = Transaction.query.where(
                Transaction.at_id.in_(r["fields"]["Payments"])
            ).all()
            for payment in payments:
                player.transactions.append(payment)
                print("--" + payment.description)

    db.session.commit()


@cli.command()
def pexpenses():
    roster = Table(at.api_key, at.base_id, at.tables["roster"])
    for r in roster.all():
        if "Expenses" in r["fields"]:
            player = Person.query.filter_by(at_id=r["id"]).one()
            pprint(player.name)
            expenses = Transaction.query.where(
                Transaction.at_id.in_(r["fields"]["Expenses"])
            ).all()
            for expense in expenses:
                player.transactions.append(expense)
                print("--" + expense.description)

    db.session.commit()


@cli.command()
def teams():
    ts = Teamsnap(
        username=os.environ["TEAMSNAP_LOGIN"],
        password=os.environ["TEAMSNAP_PASSWORD"],
    )
    teams = ts.teams()
    print(teams)


@cli.command()
def roster():
    ts = Teamsnap(
        username=os.environ["TEAMSNAP_LOGIN"],
        password=os.environ["TEAMSNAP_PASSWORD"],
    )
    roster = ts.roster(8063393)
    print(roster)


@cli.command()
def schedule():
    ts = Teamsnap(
        username=os.environ["TEAMSNAP_LOGIN"],
        password=os.environ["TEAMSNAP_PASSWORD"],
    )
    events = ts.schedule(8063393)
    print(events)


@cli.command()
def event():
    ts = Teamsnap(
        username=os.environ["TEAMSNAP_LOGIN"],
        password=os.environ["TEAMSNAP_PASSWORD"],
    )
    ts.event("8063393/schedule/view_event/296356109")


@cli.command()
def parentemails():
    for p in Person.query.all():
        if not p.parents:
            continue
        emails = [parent.email for parent in p.parents]
        print(f"{p.name}\t{ ','.join(emails) }\thttps://deanzaforce.club/{ p.at_id }")


if __name__ == "__main__":
    cli()
