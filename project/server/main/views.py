# project/server/main/views.py
from flask import Blueprint, render_template

main_blueprint = Blueprint("main", __name__)


@main_blueprint.route("/")
def home():
    return render_template("main/home.html")


@main_blueprint.route("/about/")
def about():
    return render_template("main/about.html")


@main_blueprint.route("/healthz/")
def healthz():
    return "OK", 200
