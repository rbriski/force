import asyncio
from datetime import timedelta
from dataclasses import dataclass
from temporalio import workflow, activity

task_queue_name = "email_subscription"


@dataclass
class WorkflowOptions:
    email: str


@dataclass
class EmailDetails:
    email: str = ""
    message: str = ""
    count: int = 0
    subscribed: bool = False


@activity.defn
async def send_email(details: EmailDetails) -> str:
    print(
        f"Sending email to {details.email} with message: {details.message}, count: {details.count}"
    )
    return "success"


@workflow.defn
class SendEmailWorkflow:
    def __init__(self) -> None:
        self.email_details = EmailDetails()

    @workflow.run
    async def run(self, data: WorkflowOptions) -> None:
        duration = 12
        self.email_details.email = data.email
        self.email_details.message = "Welcome to our Subscription Workflow!"
        self.email_details.subscribed = True
        self.email_details.count = 0

        while self.email_details.subscribed:
            self.email_details.count += 1
            if self.email_details.count > 1:
                self.email_details.message = "Thank you for staying subscribed!"

            try:
                await workflow.execute_activity(
                    send_email,
                    self.email_details,
                    start_to_close_timeout=timedelta(seconds=10),
                )
                await asyncio.sleep(duration)

            except asyncio.CancelledError as err:
                # Cancelled by the user. Send them a goodbye message.
                self.email_details.subscribed = False
                self.email_details.message = "Sorry to see you go"
                await workflow.execute_activity(
                    send_email,
                    self.email_details,
                    start_to_close_timeout=timedelta(seconds=10),
                )
                # raise error so workflow shows as cancelled.
                raise err

    @workflow.query
    def details(self) -> EmailDetails:
        return self.email_details
