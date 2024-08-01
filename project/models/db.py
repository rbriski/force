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
        if not vals:
            return None
        return cls(**vals)

    @classmethod
    def find_by_slack_id(cls, cursor, slack_id: str) -> "Person":
        cursor.execute(
            f"""
            SELECT *
            FROM {cls.table_name}
            WHERE slack_id = %s
            """,
            (slack_id,),
        )
        vals = cursor.fetchone()
        if not vals:
            return None
        return cls(**vals)


class Base(BaseModel):
    id: UUID = Field(default_factory=lambda: uuid4().hex)
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)
    updated_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)


class Bracket(Base):
    table_name: ClassVar[str] = "brackets"

    name: str
    email: str | None
    bracket_ids: str | None

    def insert(self):
        conn = svcs.flask.get(Connection)
        cursor = conn.cursor()
        cursor.execute(
            f"""INSERT INTO {self.table_name} (id, created_at, updated_at, name, email, bracket_ids) VALUES (%s, %s, %s, %s, %s, %s)""",
            (
                self.id,
                self.created_at,
                self.updated_at,
                self.name,
                self.email,
                self.bracket_ids,
            ),
        )


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
    def collect_by_user_at_id(cls, cursor, person_at_id: str) -> list["Transaction"]:
        cursor.execute(
            f"""with user_transactions as (
            select *
            from {PlayerTransactions.table_name} mpt
                    join {Person.table_name} p on mpt.person_id = p.id
            where p.at_id = %s
        ),
            people_per as (
                select mpt.transaction_id, count(*) as attendees
                from {PlayerTransactions.table_name} mpt
                        join {Person.table_name} p on mpt.person_id = p.id
                        join {cls.table_name} t on mpt.transaction_id = t.id
                group by 1
            )
        select t.id as t_id,
            t.created_at as t_created_at,
            t.updated_at as t_updated_at,
            t.at_id as t_at_id,
            t.event_id as t_event_id,
            t.amount as t_amount,
            t.description as t_description,
            t.debit as t_debit,
            attendees as t_attendees,
            t.amount / attendees as t_per_person,
            e.id as e_id,
            e.created_at as e_created_at,
            e.updated_at as e_updated_at,
            e.at_id as e_at_id,
            e.name as e_name,
            e.date as e_date,
            e.description as e_description
        from people_per pp
                join user_transactions ut on pp.transaction_id = ut.transaction_id
                join {cls.table_name} t on pp.transaction_id = t.id
                left join {Event.table_name} e on t.event_id=e.id
        order by t.created_at;
                    """,
            (person_at_id,),
        )
        for vals in cursor:
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
            yield t


class Person(Base, AirtableMixin):
    table_name: ClassVar[str] = "people"

    at_id: str
    name: str
    description: str | None
    email: str | None
    phone: str | None
    slack_id: str | None

    @classmethod
    def all_players(cls, cursor):
        cursor.execute(
            f"""select * from {cls.table_name} where id in (select player_id from {PlayerParent.table_name} group by 1)"""
        )
        players = []
        for player in cursor.fetchall():
            players.append(Person(**player))

        return players

    def insert(self, cursor):
        cursor.execute(
            f"""INSERT INTO {self.table_name} (id, at_id, created_at, updated_at, description, name, email, phone, slack_id) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (
                self.id,
                self.at_id,
                self.created_at,
                self.updated_at,
                self.description,
                self.name,
                self.email,
                self.phone,
                self.slack_id,
            ),
        )

    def player(self, cursor):
        cursor.execute(
            f"""select * from {self.table_name} p join {PlayerParent.table_name} mpp on p.id=mpp.player_id  where mpp.parent_id=%s""",
            (self.id,),
        )

        player = cursor.fetchone()
        if not player:
            return None

        return Person(**player)

    def parents(self, cursor):
        cursor.execute(
            f"""select * from {self.table_name} p join {PlayerParent.table_name} mpp on p.id=mpp.parent_id where mpp.player_id=%s""",
            (self.id,),
        )

        parents = []
        for parent in cursor.fetchall():
            parents.append(Person(**parent))

        return parents

    def transactions(self, cursor):
        yield from Transaction.collect_by_user_at_id(cursor, person_at_id=self.at_id)

    def ledger(self, cursor):
        total = 0
        ordered_transactions = []
        for t in self.transactions(cursor=cursor):
            total += t.amount_per_person
            ot = OrderedTransaction(total=total, transaction=t)
            ordered_transactions.append(ot)

        return ordered_transactions

    def balance(self, cursor):
        total = 0
        for t in self.transactions(cursor=cursor):
            total += t.amount_per_person

        value = Decimal(total)
        return round(value, 2)


class OrderedTransaction:
    def __init__(self, total: float, transaction: TransactionDB):
        self.total = total
        self.transaction = transaction
