import datetime
from abc import ABC
from decimal import Decimal
from typing import ClassVar
from uuid import UUID, uuid4

import svcs
from jinja2 import Environment
from psycopg import Connection
from pydantic import BaseModel, Field


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


class TransactionDB(Base, AirtableMixin):
    table_name: ClassVar[str] = "transactions"

    at_id: str
    event_id: UUID | None
    amount: float
    description: str | None
    debit: bool

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


class Transaction(TransactionDB):
    num_attendees: int | None
    amount_per_person: float | None
    event: Event | None

    @classmethod
    def _assign_values(cls, vals: dict) -> "Transaction":
        t = cls(
            id=vals["t_id"],
            created_at=vals["t_created_at"],
            updated_at=vals["t_updated_at"],
            at_id=vals["t_at_id"],
            event_id=vals["t_event_id"],
            amount=vals["t_amount"],
            description=vals["t_description"],
            debit=vals["t_debit"],
            num_attendees=vals["t_attendees"],
            amount_per_person=vals["t_per_person"],
            event=None,
        )
        if t.event_id:
            t.event = Event(
                id=vals["e_id"],
                created_at=vals["e_created_at"],
                updated_at=vals["e_updated_at"],
                at_id=vals["e_at_id"],
                name=vals["e_name"],
                date=vals["e_date"],
                description=vals["e_description"],
            )
        return t

    @classmethod
    def collect_all(cls) -> list["Transaction"]:
        conn, env = svcs.flask.get(Connection, Environment)
        cursor = conn.cursor()

        qry = env.get_template("transactions.sql").render()
        cursor.execute(qry)
        for vals in cursor:
            t = cls._assign_values(vals)
            yield t

    @classmethod
    def collect_by_user_id(cls, person_id: str) -> list["Transaction"]:
        conn, env = svcs.flask.get(Connection, Environment)
        cursor = conn.cursor()

        qry = env.get_template("transactions.sql").render(
            person_id=person_id,
        )
        print(qry)
        cursor.execute(qry)
        for vals in cursor:
            t = cls._assign_values(vals)
            yield t

    def players(self) -> list["Person"]:
        yield from Person.collect_players_by_transaction_id(self.id)


class Person(Base, AirtableMixin):
    table_name: ClassVar[str] = "people"

    at_id: str
    name: str
    description: str | None
    email: str | None
    phone: str | None

    @classmethod
    def collect_players(cls) -> list["Person"]:
        conn, env = svcs.flask.get(Connection, Environment)
        cursor = conn.cursor()

        qry = env.get_template("players.sql").render()
        cursor.execute(qry)
        for vals in cursor:
            p = cls(**vals)
            yield p

    @classmethod
    def collect_players_by_transaction_id(cls, transaction_id) -> list["Person"]:
        conn, env = svcs.flask.get(Connection, Environment)
        cursor = conn.cursor()

        qry = env.get_template("players.sql").render(transaction_id=transaction_id)
        # print(qry)
        cursor.execute(qry)
        for vals in cursor:
            p = cls(**vals)
            yield p

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

    def transactions(self):
        yield from Transaction.collect_by_user_id(person_id=self.id)

    def ledger(self, cursor):
        total = 0
        ordered_transactions = []
        for t in self.transactions():
            print(t)
            total += t.amount_per_person
            ot = OrderedTransaction(total=total, transaction=t)
            ordered_transactions.append(ot)

        return ordered_transactions

    def balance(self, cursor):
        total = 0
        for t in self.transactions():
            total += t.amount_per_person

        value = Decimal(total)
        return round(value, 2)


class OrderedTransaction:
    def __init__(self, total: float, transaction: TransactionDB):
        self.total = total
        self.transaction = transaction
