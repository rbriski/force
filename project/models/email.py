import json
import os
from email import policy
from email.parser import BytesParser

import boto3
from openai import OpenAI
from pydantic import BaseModel, Field
from rich import print

openai = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))


class PayPalEmail(BaseModel):
    sender: str = Field(..., description="The name of the sender of the email.")
    amount: str = Field(
        ...,
        description="The amount of money mentioned in the email, including the currency.",
    )
    transaction_date: str = Field(
        ..., description="The date of the transaction in a readable format."
    )
    transaction_id: str = Field(
        ..., description="The unique identifier for the transaction."
    )


class Email:
    """
    Provides a class for managing emails stored in an S3 bucket.

    The `Email` class provides a way to list all emails stored in an S3 bucket, given a bucket name and an optional prefix. It also provides a way to create an `Email` object for a specific email key.

    The `all()` class method returns a list of `Email` objects for all emails in the specified bucket and prefix. The `__init__()` method creates an `Email` object for the specified key.
    """

    download_folder = "email_downloads"  # Class-level attribute for download folder

    @classmethod
    def all(cls, bucket, prefix, s3_client=None):
        """
        Retrieves a list of `Email` objects for all emails in the specified S3 bucket and prefix.

        Args:
            bucket (str): The name of the S3 bucket to retrieve emails from.
            prefix (str): The optional prefix to filter the emails by.
            s3_client (boto3.client, optional): An existing S3 client to use. If not provided, a new client will be created.

        Returns:
            list[Email]: A list of `Email` objects for all emails in the specified bucket and prefix.
        """
        if s3_client is None:
            s3 = boto3.client(
                "s3",
                region_name="us-east-1",
            )
        else:
            s3 = s3_client

        emails = []
        continuation_token = None

        while True:
            list_params = {"Bucket": bucket, "Delimiter": "/" if not prefix else None}
            if prefix:
                list_params["Prefix"] = prefix
            if continuation_token:
                list_params["ContinuationToken"] = continuation_token

            response = s3.list_objects_v2(**list_params)

            if "Contents" in response:
                for obj in response["Contents"]:
                    if (
                        not prefix or obj["Key"] != prefix
                    ):  # Exclude the prefix itself if it's a directory
                        emails.append(cls(s3_client, obj["Key"], bucket))

            if response.get("IsTruncated"):  # Check if there are more files to list
                continuation_token = response.get("NextContinuationToken")
            else:
                break

        return emails

    @classmethod
    def set_download_folder(cls, folder):
        cls.download_folder = folder

    def __init__(self, s3_client, key, bucket):
        self.s3 = s3_client
        self.key = key
        self.bucket = bucket
        self.local_path = os.path.join(self.download_folder, self.key.replace("/", "_"))

    def __repr__(self):
        return f"Email(key={self.key})"

    def download(self, force=False):
        if not os.path.exists(self.download_folder):
            os.makedirs(self.download_folder)

        if force or not os.path.exists(self.local_path):
            self.s3.download_file(self.bucket, self.key, self.local_path)

        return self.local_path

    def get_content(self, force=False):
        local_file = self.download(force=force)
        with open(local_file, "rb") as f:
            return BytesParser(policy=policy.default).parse(f)

    def get_body(self, msg):
        """
        Extract the body of the email (handling both plain text and HTML).

        :param msg: The email message object
        :return: The email body as a string
        """
        if msg.is_multipart():
            for part in msg.iter_parts():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))

                if (
                    content_type == "text/plain"
                    and "attachment" not in content_disposition
                ):
                    return part.get_payload(decode=True).decode(
                        part.get_content_charset()
                    )
                elif (
                    content_type == "text/html"
                    and "attachment" not in content_disposition
                ):
                    return part.get_payload(decode=True).decode(
                        part.get_content_charset()
                    )
        else:
            return msg.get_payload(decode=True).decode(msg.get_content_charset())

    def parse(self, msg):
        print("Subject:", msg["subject"])
        print("From:", msg["from"])

        try:
            html = self.get_body(msg)
        except Exception as e:
            print("Error parsing email:", e)
            print("Skipping this email...")
            return None

        messages = [
            {
                "role": "system",
                "content": "You are an AI that helps parse PayPal email notifications. The email is in HTML format.",
            },
            {
                "role": "user",
                "content": "Please extract the following details from the email and return them in JSON format:\n"
                "1. The sender of the email.\n"
                "2. The amount of money mentioned in the email.\n"
                "3. The transaction date.\n"
                "4. The transaction ID.\n\n"
                "Email HTML content:\n"
                f"{html}",
            },
        ]
        # Make a request to the OpenAI API
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=300,
            temperature=0.2,
            response_format={"type": "json_object"},
        )

        # Extract the result from the API response
        result = response.choices[0].message.content

        # Try to parse the result as JSON
        try:
            parsed_result = json.loads(result)
        except json.JSONDecodeError:
            # Handle the case where the result is not valid JSON
            parsed_result = {
                "error": "Failed to parse the result as JSON.",
                "raw_result": result,
            }

        return parsed_result

    # def save_to_airtable(self, result, msg) -> None:

    def process(self, force=False) -> None:
        msg = self.get_content(force)
        result = self.parse(msg)
        # self.save_to_airtable(result, msg)
