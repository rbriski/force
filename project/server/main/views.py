# project/server/main/views.py
from flask import Blueprint, render_template, request, redirect, Response
import urllib

from project.server.models import Bracket

main_blueprint = Blueprint("main", __name__)


@main_blueprint.route("/")
def home():
    return render_template("main/home.html")


@main_blueprint.route("/about/")
def about():
    return render_template("main/about.html")


@main_blueprint.route("/verify/", methods=["POST"])
def inbound():
    """
    Inbound POST from Slack to test token
    """
    # When Slack sends a POST to your app, it will send a JSON payload:
    payload = request.get_json()

    # This response will only be used for the initial URL validation:
    if payload:
        return Response(payload["challenge"]), 200


@main_blueprint.route("/bracket/")
def bracket():
    return render_template("main/bracket.html")


@main_blueprint.route("/bracket/submit", methods=["POST"])
def submit_bracket():
    # Extract form data
    name = request.form.get("name")
    email = request.form.get("email")
    bracket_ids = request.form.getlist(
        "bracketID[]"
    )  # Extracts all bracket IDs as a list

    # Determine the total number of brackets
    total_brackets = len(bracket_ids)

    # Calculate payment amount based on the number of brackets
    # $50 for 1 bracket, $100 for 2 or 3 brackets, $150 for 4 or 5 brackets, etc.
    if total_brackets <= 3:
        amount = 100 if total_brackets > 1 else 50
    else:
        # Calculate the extra sets beyond the initial 3 brackets
        extra_sets = (total_brackets - 3) // 2
        extra_single_bracket = (total_brackets - 3) % 2
        amount = 100 + (extra_sets * 100) + (extra_single_bracket * 50)

    description = f"March Madness - {email} - {','.join(bracket_ids)} - {amount}"
    description_encoded = urllib.parse.quote(description)

    paypal_url = f"https://www.paypal.com/paypalme/Force2010G/{amount}?description={description_encoded}"

    # Example: Print received data to console
    print(f"Name: {name}, Email: {email}, Bracket IDs: {bracket_ids}")

    b = Bracket(
        email=email,
        name=name,
        bracket_ids=",".join(bracket_ids),
    )
    b.insert()

    # Redirect or respond after processing
    return redirect(paypal_url)


@main_blueprint.route("/healthz/")
def healthz():
    return "OK", 200
