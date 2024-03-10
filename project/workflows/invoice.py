import asyncio
from dataclasses import dataclass
import datetime

from temporalio import activity, workflow

with workflow.unsafe.imports_passed_through():
    from pydantic import BaseModel, Field
    import svcs
    from psycopg import Connection

    from datetime import timedelta
    from typing import ClassVar
    from uuid import UUID, uuid4

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


class Person(Base):
    table_name: ClassVar[str] = "people"

    at_id: str
    name: str
    description: str | None
    email: str | None
    phone: str | None

    @classmethod
    def find_by_at_id(cls, cursor, at_id: str) -> "Person":
        cursor.execute(
            f"""
            SELECT *
            FROM {cls.table_name}
            WHERE at_id = %s
            """,
            (at_id,),
        )
        vals = cursor.fetchone()
        return cls(**vals)


invoice_queue_name = "invoices"


@dataclass
class WorkflowOptions:
    id: str


@dataclass
class PlayerInfo:
    id: str = ""
    active: bool = False
    count: int = 0


@activity.defn
async def send_invoice(info: PlayerInfo) -> str:
    conn = svcs.flask.get(Connection)
    cursor = conn.cursor()

    p = Person.find_by_at_id(cursor, info.id)

    print(f"Sending email to {p.name} at {p.email}, count: {info.count}")
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
