# manage.py
import logging
import subprocess
import sys
import unittest
from datetime import datetime
from pprint import pprint

from dotenv import load_dotenv
from flask.cli import FlaskGroup
from pyairtable import Table

from project.server import at, create_app, db
from project.server.models import Event, Person, Transaction

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
def output():
    for e in Expense.query.all():
        for p in e.players:
            print(f"{p.name} -- {e.per_person()} of {e.amount}")


if __name__ == "__main__":
    cli()
