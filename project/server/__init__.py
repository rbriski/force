# project/server/__init__.py
import locale
import math
import os

import arrow
from flask import Flask, render_template
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_moment import Moment

db = SQLAlchemy()
migrate = Migrate()
moment = Moment()


def create_app(script_info=None):
    # instantiate the app
    app = Flask(
        __name__,
        template_folder="../client/templates",
        static_folder="../client/static",
    )

    locale.setlocale(locale.LC_ALL, "en_US.UTF-8")

    # set config
    app_settings = os.getenv("APP_SETTINGS", "project.server.config.ProductionConfig")
    app.config.from_object(app_settings)

    db.init_app(app)
    migrate.init_app(app, db)
    moment.init_app(app)

    # register blueprints
    from project.server.main.views import main_blueprint
    from project.server.user.views import user_blueprint

    app.register_blueprint(user_blueprint)
    app.register_blueprint(main_blueprint)

    # flask login
    # from project.server.models import User

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
        return {"app": app, "db": db}

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
