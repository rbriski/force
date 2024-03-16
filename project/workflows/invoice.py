import asyncio
import datetime
import json
import os
from dataclasses import dataclass

from temporalio import activity, workflow

with workflow.unsafe.imports_passed_through():
    from datetime import timedelta
    from typing import ClassVar
    from uuid import UUID, uuid4

    import requests
    import svcs
    from psycopg import Connection
    from pydantic import BaseModel, Field

    from project.server.models import (
        Person,
    )

# Invoice each parent
#
# 1. Is it time to invoice?
# 2. If so, do they owe money
# 3. Collect all information for each parent
# 4. Get invoice data
# 5. Send email to each parent


class Base(BaseModel):
    id: UUID = Field(default_factory=lambda: uuid4().hex)
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)
    updated_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)

    class Config:
        arbitrary_types_allowed = True


invoice_queue_name = "invoices"


@dataclass
class WorkflowOptions:
    id: str


@dataclass
class PlayerInfo:
    id: str = ""
    active: bool = False
    count: int = 0


async def email_api_request(player):
    for rent in player.parents():
        if rent.name != "Bob Briski":
            continue
        print(rent.name)
        print(rent.email)
        amount_due = str(player.balance() * -1)
        requests.post(
            "https://api.mailgun.net/v3/m.deanzaforce.club/messages",
            auth=("api", os.environ["MAILGUN_API_KEY"]),
            data={
                "from": "DeAnza 2010G - Bob Briski <postmaster@m.deanzaforce.club>",
                "to": rent.name + " <" + rent.email + ">",
                "h:Reply-To": "Bob Briski <rbriski+force@gmail.com>",
                "subject": f"2010G Force : Monthly Invoice : ${amount_due}",
                "template": "force-payment-request",
                "h:X-Mailgun-Variables": json.dumps(
                    {
                        "player_name": player.name,
                        "parent_name": rent.name,
                        "amount": amount_due,
                        "ledger_link": "https://deanzaforce.club/" + player.at_id,
                    }
                ),
            },
        )


@activity.defn
async def send_invoice(info: PlayerInfo) -> str:
    conn = svcs.flask.get(Connection)
    cursor = conn.cursor()

    p = Person.find_by_at_id(cursor, info.id)

    balance = p.balance()
    if balance > -50:
        print(f"No invoice needed for {p.name} (balance is {balance})")
        return "success"

    print(
        f"Sending email to {p.name} at {p.email} with a balance of {balance}, count: {info.count}"
    )
    await email_api_request(p)
    return "success"


@workflow.defn
class SendInvoiceWorkflow:
    def __init__(self) -> None:
        self.player_info = PlayerInfo()

    @workflow.run
    async def run(self, data: WorkflowOptions) -> None:
        duration = 12
        self.player_info.id = data.id
        self.player_info.active = True
        self.player_info.count = 0

        while self.player_info.active:
            self.player_info.count += 1
            try:
                await workflow.execute_activity(
                    send_invoice,
                    self.player_info,
                    start_to_close_timeout=timedelta(seconds=10),
                )
                await asyncio.sleep(duration)

            except asyncio.CancelledError as err:
                # Cancelled by the user. Send them a goodbye message.
                self.email_details.active = False
                # await workflow.execute_activity(
                #     send_email,
                #     self.email_details,
                #     start_to_close_timeout=timedelta(seconds=10),
                # )
                # raise error so workflow shows as cancelled.
                raise err
