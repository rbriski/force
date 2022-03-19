from flask import Flask
from flask import render_template
import arrow
import at_db as db
import functools
import locale
import math
import os
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

# Returns None on no value, which is what I want
sentry_dsn = os.environ.get("SENTRY_DSN")
sentry_sdk.init(
    dsn=sentry_dsn,
    integrations=[FlaskIntegration()],
    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for performance monitoring.
    # We recommend adjusting this value in production.
    traces_sample_rate=1.0,
)

locale.setlocale(locale.LC_ALL, "en_US.UTF-8")
app = Flask(__name__)


def round_decimals_up(number: float, decimals: int = 2):
    """
    Returns a value rounded up to a specific number of decimal places.
    """
    if not isinstance(decimals, int):
        raise TypeError("decimal places must be an integer")
    elif decimals < 0:
        raise ValueError("decimal places has to be 0 or more")
    elif decimals == 0:
        return math.ceil(number)

    factor = 10**decimals
    return math.ceil(number * factor) / factor


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
    total = round_decimals_up(total)

    return render_template(
        "ledger.html",
        player=player["fields"]["Name"],
        total=total,
        ledger=sorted(ledger, key=lambda i: i["created_at"], reverse=True),
    )


@app.route("/debug-sentry")
def trigger_error():
    division_by_zero = 1 / 0
