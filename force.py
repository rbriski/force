from flask import Flask
from flask import render_template, abort, request, redirect, url_for, session
from flask_session import Session
import arrow
import at_db as db
import functools
import locale
import math
import os
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
import urllib.parse
import requests
from requests.auth import HTTPBasicAuth
from pprint import pprint

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

# Set up sessions
SESSION_TYPE = "redis"
app.config.from_object(__name__)
Session(app)


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


@app.route("/")
def index():
    scopes = "openid email"
    client_id = os.environ["PAYPAL_CLIENT_ID"]
    return_url = os.environ["AUTH_RETURN_URL"]
    url = "https://www.sandbox.paypal.com/connect"
    params = {
        "flowEntry": "static",
        "scope": scopes,
        "client_id": client_id,
        "redirect_uri": return_url,
        "response_type": "code",
        "fullPage": "true",
    }
    login_url = "?".join([url, urllib.parse.urlencode(params)])
    return render_template("index.html", login_url=login_url)


@app.route("/auth", methods=["GET"])
def auth():
    args = request.args
    code = args.get("code", default=None, type=str)

    if code is None:
        return redirect(url_for("index"), code=302)

    client_id = os.environ["PAYPAL_CLIENT_ID"]
    secret = os.environ["PAYPAL_SECRET"]
    r = requests.post(
        os.path.join(os.environ["PAYPAL_API_BASE"], "v1/oauth2/token"),
        data={"grant_type": "authorization_code", "code": code},
        auth=HTTPBasicAuth(client_id, secret),
    )

    auth_package = r.json()
    session["access_token"] = auth_package["access_token"]
    session["refresh_token"] = auth_package["refresh_token"]

    r = requests.get(
        os.path.join(os.environ["PAYPAL_API_BASE"], "v1/identity/oauth2/userinfo"),
        params={"schema": "paypalv1.1"},
        headers={
            "Authorization": f"Bearer {session['access_token']}",
            "Content-Type": "application/json",
        },
    )

    user_info = r.json()
    emails = [e["value"] for e in user_info["emails"]]
    session["emails"] = emails

    return redirect(url_for("player_ledger"), code=302)


@app.route("/ledger")
def player_ledger():
    emails = session["emails"]
    if emails is None:
        return redirect(url_for("index"), code=302)

    emails = [e.casefold() for e in emails]

    player = db.get_roster_record(emails)

    # No matching player is a 404
    if not player:
        abort(404)

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
