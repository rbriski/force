import os
from pprint import pprint
from flask import Blueprint, request
import svcs
from psycopg import Connection
from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler

from project.models.db import Person
from project.models.slack import Event, Message

slack_blueprint = Blueprint("slack", __name__)

# Register slack middleware
slack = App(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET"),
)
handler = SlackRequestHandler(slack)


@slack.middleware  # or app.use(log_request)
def log_request(logger, body, next):
    logger.debug(body)
    return next()


@slack.event("app_mention")
def event_test(body, say, logger):
    am = Message(**body)
    pprint(am)
    say("Hey there! I'm totally inconsequential.  No one should worry about me.")


@slack.event("message")
def handle_message(body, say, logger):
    msg = Message(**body)
    pprint(msg)
    say("Nothing to see here")


@slack.event("app_home_opened")
def app_home(client, event, context):
    conn = context["connection"]
    cursor = conn.cursor()

    evt = Event(**event)
    parent = Person.find_by_slack_id(cursor, evt.user)
    player = parent.player(cursor)

    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": ":dollar:  Welcome to the ledger! :dollar:",
            },
        },
        {"type": "divider"},
    ]

    if player:
        balance = player.balance(cursor)

        if balance < 0:
            blocks.extend(
                [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"Hello, {parent.name}!  You owe *${balance*-1}*.",
                        },
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"Details at the Ledger :  https://deanzaforce.club/{player.at_id}",
                        },
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"Pay at : https://www.paypal.com/paypalme/Force2010G/{balance*-1}.",
                        },
                    },
                ]
            )
        else:
            blocks.extend(
                [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"Hello, {parent.name}!  You're carrying a credit of *${balance * -1}*.",
                        },
                    },
                ]
            )
    else:
        blocks.extend(
            [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "Hello, thanks for checking out the Ledger!  It looks like you don't have your slack ID associated with a player.  Please contact <@U073Q1ALBL1> to get that set up.",
                    },
                },
            ]
        )

    blocks.extend(
        [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "If you have questions, message <@U073Q1ALBL1>",
                },
            },
        ]
    )

    # Call views.publish with the built-in client
    client.views_publish(
        # Use the user ID associated with the event
        user_id=event["user"],
        # Home tabs must be enabled in your app configuration
        view={"type": "home", "blocks": blocks},
    )


@slack_blueprint.route("/slack/events", methods=["POST"])
def slack_events():
    return handler.handle(request)
