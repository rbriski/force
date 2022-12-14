# manage.py
import subprocess
import sys
import unittest
from pprint import pprint

from dotenv import load_dotenv
from flask.cli import FlaskGroup
from pyairtable import Table

from project.server import at, create_app, db
from project.server.models import Person

load_dotenv()
app = create_app()
cli = FlaskGroup(create_app=create_app)


@cli.command()
def create_db():
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
def expenses():
    expenses = Table(at.api_key, at.base_id, at.tables["parents"])
    for e in expenses.all():
        f = e["fields"]
        p = Person(
            at_id=e["id"], name=f["Name"], email=f.get("Email"), phone=f.get("Phone")
        )
        db.session.add(p)
        pprint(e)
    db.session.commit()


if __name__ == "__main__":
    cli()
