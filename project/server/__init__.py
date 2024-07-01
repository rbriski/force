# project/server/__init__.py
import locale
import math
import os

import arrow
from flask import Flask, render_template, request, Response
import psycopg
from psycopg.rows import dict_row
from psycopg import Connection

from pprint import pprint

from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler

import svcs


def create_app(script_info=None):
    # instantiate the app
    app = Flask(
        __name__,
        template_folder="../client/templates",
        static_folder="../client/static",
    )
    app = svcs.flask.init_app(app)

    locale.setlocale(locale.LC_ALL, "en_US.UTF-8")

    # set config
    app_settings = "project.server.config.Config"
    app.config.from_object(app_settings)

    def connection_factory():
        DATABASE_URL = f"postgresql://{os.environ['POSTGRES_USER']}:{os.environ['POSTGRES_PASSWORD']}@{os.environ['DB_HOST']}:5432/postgres?sslmode=disable"
        with psycopg.connect(DATABASE_URL, row_factory=dict_row) as conn:
            yield conn

    svcs.flask.register_factory(
        # The app argument makes it good for custom init_app() functions.
        app,
        Connection,
        connection_factory,
        ping=lambda conn: conn.cursor().execute("SELECT 1"),
        on_registry_close=lambda conn: conn.close(),
    )

    # Register slack middleware
    slack = App(
        token=os.environ.get("SLACK_BOT_TOKEN"),
        signing_secret=os.environ.get("SLACK_SIGNING_SECRET"),
    )

    @slack.middleware  # or app.use(log_request)
    def log_request(logger, body, next):
        logger.debug(body)
        return next()

    @slack.event("app_mention")
    def event_test(body, say, logger):
        logger.info(body)
        say("Hey there! I'm totally inconsequential.  No one should worry about me.")

    @slack.event("message")
    def handle_message(body, say, logger):
        say("_Nothing to see here_")

    handler = SlackRequestHandler(slack)

    # register blueprints
    from project.server.main.views import main_blueprint
    from project.server.user.views import user_blueprint

    app.register_blueprint(user_blueprint)
    app.register_blueprint(main_blueprint)

    # flask login
    # from project.server.models import User

    @app.route("/slack/events", methods=["POST"])
    def slack_events():
        return handler.handle(request)

    # error handlers
    @app.errorhandler(401)
    def unauthorized_page(error):
        return render_template("errors/401.html"), 401

    @app.errorhandler(403)
    def forbidden_page(error):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def page_not_found(error):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error_page(error):
        return render_template("errors/500.html"), 500

    # shell context for flask cli
    @app.shell_context_processor
    def ctx():
        return {"app": app, "db": svcs.flask.get(Connection)}

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

    @app.template_filter()
    def format_dt(date):
        """Sane currency formatting."""
        dt = arrow.get(date)
        return dt.format("MMM D, YYYY")

    @app.template_filter()
    def round_currency_up(number: float, decimals: int = 2):
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

    return app
