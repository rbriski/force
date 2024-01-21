import datetime
from typing import ClassVar
from decimal import Decimal
from uuid import uuid4, UUID

from pydantic import BaseModel, Field
from abc import ABC
import svcs
from psycopg import Connection


class AirtableMixin(ABC):
    @classmethod
    def exists_airtable(cls, cursor, at_id: str) -> bool:
        cursor.execute(
            f"""
            SELECT EXISTS (
                SELECT 1
                FROM {cls.table_name}
                WHERE at_id = %s
            )
            """,
            (at_id,),
        )
        return bool(cursor.fetchone()["exists"])

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


class Base(BaseModel):
    id: UUID = Field(default_factory=lambda: uuid4().hex)
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)
    updated_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)


class PlayerParent(Base):
    table_name: ClassVar[str] = "m_player_parent"

    player_id: UUID
    parent_id: UUID


class PlayerTransactions(Base):
    table_name: ClassVar[str] = "m_people_transactions"

    person_id: UUID
    transaction_id: UUID


class Transaction(Base, AirtableMixin):
    table_name: ClassVar[str] = "transactions"

    at_id: str
    event_id: UUID | None
    amount: float
    description: str | None
    debit: bool

    def per_person(self):
        cursor = svcs.flask.get(Connection).cursor()
        people_count = cursor.execute(
            f"SELECT COUNT(*) FROM {PlayerTransactions.table_name} where transaction_id=%s",
            [self.id],
        ).fetchone()["count"]
        return self.amount / people_count

    def insert(self, cursor):
        cursor.execute(
            f"""INSERT INTO {self.table_name} (id, at_id, created_at, updated_at, event_id, amount, description, debit) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
            (
                self.id,
                self.at_id,
                self.created_at,
                self.updated_at,
                self.event_id,
                self.amount,
                self.description,
                self.debit,
            ),
        )


class Person(Base, AirtableMixin):
    table_name: ClassVar[str] = "people"

    at_id: str
    name: str
    description: str | None
    email: str | None
    phone: str | None

    def insert(self, cursor):
        cursor.execute(
            f"""INSERT INTO {self.table_name} (id, at_id, created_at, updated_at, description, name, email, phone) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
            (
                self.id,
                self.at_id,
                self.created_at,
                self.updated_at,
                self.description,
                self.name,
                self.email,
                self.phone,
            ),
        )

    def transactions(self, cursor):
        cursor.execute(
            f"""
            SELECT t.*
            FROM {Transaction.table_name} t join {PlayerTransactions.table_name} pt on t.id = pt.transaction_id
            WHERE pt.person_id = %s
            """,
            (self.id,),
        )
        vals = cursor.fetchall()

        for v in vals:
            yield Transaction(**v)

    def ledger(self, cursor):
        total = 0
        ordered_transactions = []
        for t in self.transactions(cursor):
            total += t.per_person()
            ot = OrderedTransaction(total=total, transaction=t)
            ordered_transactions.append(ot)

        return ordered_transactions

    def balance(self, cursor):
        total = 0
        for t in self.transactions(cursor):
            total += t.per_person()

        value = Decimal(total)
        return round(value, 2)


class Event(Base, AirtableMixin):
    table_name: ClassVar[str] = "events"

    at_id: str
    name: str
    date: datetime.date | None
    description: str | None

    def insert(self, cursor):
        cursor.execute(
            f"""INSERT INTO {self.table_name} (id, at_id, created_at, updated_at, name, date, description) VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (
                self.id,
                self.at_id,
                self.created_at,
                self.updated_at,
                self.name,
                self.date,
                self.description,
            ),
        )


class OrderedTransaction:
    def __init__(self, total: float, transaction: Transaction):
        self.total = total
        self.transaction = transaction
