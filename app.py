from flask import Flask
from flask import render_template
import arrow
import at_db as db
import functools
import locale
import os

locale.setlocale(locale.LC_ALL, "en_US.UTF-8")
app = Flask(__name__)


@app.template_filter()
def paypal_me(amount):
    """Paypal link."""
    tr_amount = format(abs(amount), ".2f")
    return os.path.join(os.environ["PAYPAL_LINK"], tr_amount)


@app.template_filter()
def currency(amount):
    """Sane currency formatting."""
    return locale.currency(amount, grouping=True)


@app.template_filter()
def humanize(date):
    """Sane currency formatting."""
    dt = arrow.get(date)
    return dt.humanize()


@app.route("/<rec_id>")
def player_ledger(rec_id=None):
    player = db.get_roster_record(rec_id)
    expenses = db.get_expenses(player["id"])
    payments = db.get_payments(player["id"])
    ledger = db.get_ledger(expenses, payments)

    total = functools.reduce(lambda a, b: a + b["amount"], ledger, 0)

    return render_template(
        "ledger.html",
        player=player["fields"]["Name"],
        total=total,
        ledger=sorted(ledger, key=lambda i: i["created_at"]),
    )
