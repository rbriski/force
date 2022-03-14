import os
from pyairtable import Table
from pprint import pprint

api_key = os.environ["AT_API_KEY"]

base_id = os.environ["AT_BASE_ID"]
tables = {
    "roster": os.environ["AT_ROSTER"],
    "expenses": os.environ["AT_EXPENSES"],
    "payments": os.environ["AT_PAYMENTS"],
}


def get_roster_record(name):
    roster = Table(api_key, base_id, tables["roster"])
    for r in roster.all():
        if r["id"] == name:
            return r


def get_expenses(rec_id):
    expenses = Table(api_key, base_id, tables["expenses"])
    return [e for e in expenses.all() if rec_id in e["fields"]["Attendees"]]


def get_payments(rec_id):
    payments = Table(api_key, base_id, tables["payments"])
    return [e for e in payments.all() if rec_id in e["fields"]["Attendees"]]


def get_ledger(expenses, payments):
    ledger = []
    for e in expenses:
        it = {
            "amount": e["fields"]["Cost Per Person"] * -1,
            "description": e["fields"]["Description"],
            "event": ", ".join(e["fields"]["Event (from Event)"]),
            "created_at": e["createdTime"],
        }
        ledger.append(it)
    for p in payments:
        it = {
            "amount": p["fields"]["Cost Per Person"],
            "description": p["fields"]["Description"],
            "created_at": p["createdTime"],
        }
        ledger.append(it)
    return ledger


if __name__ == "__main__":
    roster = Table(api_key, base_id, tables["roster"])
    for r in roster.all():
        print(f"{r['fields']['Name']} : https://deanzaforce.club/{r['id']}")
