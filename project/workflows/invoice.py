import asyncio
from datetime import timedelta
from dataclasses import dataclass
from temporalio import workflow, activity

# from project.server.models import Person

# Invoice each parent
#
# 1. Is it time to invoice?
# 2. If so, do they owe money
# 3. Collect all information for each parent
# 4. Get invoice data
# 5. Send email to each parent

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
    print(f"Sending email to {info.id}, count: {info.count}")
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
