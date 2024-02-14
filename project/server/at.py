import os
from dotenv import load_dotenv
from pyairtable import Table, Api


load_dotenv()

api = Api(os.environ["AT_API_KEY"])

base_id = os.environ["AT_BASE_ID"]
tables = {
    "roster": os.environ["AT_ROSTER"],
    "expenses": os.environ["AT_EXPENSES"],
    "payments": os.environ["AT_PAYMENTS"],
    "parents": os.environ["AT_PARENTS"],
    "events": os.environ["AT_EVENTS"],
}


def get_roster_record(name):
    roster_record: Table = api.table(base_id, tables["roster"])
    for rec in roster_record.all():
        if rec["id"] == name:
            return rec


def get_expenses(rec_id):
    expenses = api.table(base_id, tables["expenses"])
    return [e for e in expenses.all() if rec_id in e["fields"]["Attendees"]]


def get_payments(rec_id):
    payments = api.table(base_id, tables["payments"])
    return [e for e in payments.all() if rec_id in e["fields"]["Attendees"]]


def get_ledger(expenses, payments):
    ledger = []
    for e in expenses:
        evt = e["fields"].get("Event (from Event)")
        evt_name = evt and ", ".join(e["fields"].get("Event (from Event)")) or None
        it = {
            "amount": e["fields"]["Cost Per Person"] * -1,
            "description": e["fields"]["Description"],
            "event": evt_name,
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

    ledger = sorted(ledger, key=lambda i: i["created_at"])
    balance = 0
    for it in ledger:
        balance += it["amount"]
        it["balance"] = balance

    return ledger


if __name__ == "__main__":
    roster = api.table(base_id, tables["roster"])
    for r in roster.all():
        print(f"{r['fields']['Name']} : https://deanzaforce.club/{r['id']}")
