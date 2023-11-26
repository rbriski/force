# project/server/models.py


# import datetime

# from flask import current_app

import uuid

from project.server import db
from decimal import Decimal


class Base(db.Model):
    __abstract__ = True

    id = db.Column(db.CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(
        db.DateTime,
        default=db.func.current_timestamp(),
        onupdate=db.func.current_timestamp(),
    )


class PlayerParent(Base):
    __tablename__ = "m_player_parent"

    player_id = db.Column("player_id", db.ForeignKey("people.id"), primary_key=True)
    parent_id = db.Column("parent_id", db.ForeignKey("people.id"), primary_key=True)


class PlayerTransactions(Base):
    __tablename__ = "m_people_transactions"

    person_id = db.Column("person_id", db.ForeignKey("people.id"), primary_key=True)
    transaction_id = db.Column(
        "transaction_id", db.ForeignKey("transactions.id"), primary_key=True
    )


class Person(Base):
    __tablename__ = "people"

    at_id = db.Column(db.VARCHAR)
    name = db.Column(db.VARCHAR)
    description = db.Column(db.VARCHAR)
    email = db.Column(db.VARCHAR)
    phone = db.Column(db.VARCHAR)

    parents = db.relationship(
        "Person",
        secondary="m_player_parent",
        primaryjoin="Person.id == m_player_parent.c.player_id",
        secondaryjoin="Person.id == m_player_parent.c.parent_id",
        backref="players",
    )

    transactions = db.relationship(
        "Transaction",
        secondary="m_people_transactions",
        primaryjoin="Person.id == m_people_transactions.c.person_id",
        secondaryjoin="Transaction.id == m_people_transactions.c.transaction_id",
        back_populates="people",
        order_by="Transaction.created_at",
    )

    expenses = db.relationship(
        "Transaction",
        secondary="m_people_transactions",
        primaryjoin="Person.id == m_people_transactions.c.person_id",
        secondaryjoin="and_(Transaction.id == m_people_transactions.c.transaction_id, Transaction.debit==1)",  # noqa: E501
        back_populates="people",
        order_by="Transaction.created_at",
        viewonly=True,
    )

    payments = db.relationship(
        "Transaction",
        secondary="m_people_transactions",
        primaryjoin="Person.id == m_people_transactions.c.person_id",
        secondaryjoin="and_(Transaction.id == m_people_transactions.c.transaction_id, Transaction.debit==0)",  # noqa: E501
        back_populates="people",
        order_by="Transaction.created_at",
        viewonly=True,
    )

    def ledger(self):
        total = 0
        ordered_transactions = []
        for t in self.transactions:
            total += t.per_person()
            ot = OrderedTransaction(total=total, transaction=t)
            ordered_transactions.append(ot)

        return ordered_transactions

    def balance(self):
        total = 0
        for t in self.transactions:
            total += t.per_person()

        value = Decimal(total)
        return round(value, 2)


class Transaction(Base):
    __tablename__ = "transactions"

    at_id = db.Column(db.VARCHAR)
    event_id = db.Column(db.VARCHAR)
    amount = db.Column(db.FLOAT)
    description = db.Column(db.VARCHAR)
    debit = db.Column(db.BOOLEAN)

    event_id = db.Column("event_id", db.ForeignKey("events.id"))
    event = db.relationship("Event")

    people = db.relationship(
        "Person",
        secondary="m_people_transactions",
        primaryjoin="Transaction.id == m_people_transactions.c.transaction_id",
        secondaryjoin="Person.id == m_people_transactions.c.person_id",
        back_populates="transactions",
    )

    def per_person(self):
        return self.amount / len(self.people)


class Event(Base):
    __tablename__ = "events"

    at_id = db.Column(db.VARCHAR)
    name = db.Column(db.VARCHAR)
    date = db.Column(db.DATE)
    description = db.Column(db.VARCHAR)

    transaction = db.relationship("Transaction", back_populates="event")


class OrderedTransaction:
    def __init__(self, total: float, transaction: Transaction):
        self.total = total
        self.transaction = transaction


class TSTeam(Base):
    __tablename__ = "ts_teams"

    team_id = db.Column(db.NUMERIC)
    roster_id = db.Column(db.NUMERIC)
    name = db.Column(db.VARCHAR)
    link = db.Column(db.VARCHAR)
    role = db.Column(db.VARCHAR)
    additional_info = db.Column(db.VARCHAR)


class TSPlayer(Base):
    __tablename__ = "ts_players"

    name = db.Column(db.VARCHAR)
    link = db.Column(db.VARCHAR)
    image = db.Column(db.VARCHAR)
    number = db.Column(db.VARCHAR)
    position = db.Column(db.VARCHAR)

    team_id = db.Column("team_id", db.ForeignKey("ts_players.id"))
    # team = db.relationship("TSTeam")

    # events = db.relationship(
    #     "PlayerEvents",
    #     secondary="m_ts_player_events",
    #     primaryjoin="TSPlayer.id == m_ts_player_events.c.player_id",
    #     secondaryjoin="TSEvent.id == m_ts_player_events.c.event_id",
    #     back_populates="players",
    #     order_by="TSEvent.created_at",
    # )


class TSContact(Base):
    __tablename__ = "ts_contacts"

    name = db.Column(db.VARCHAR)
    email = db.Column(db.VARCHAR)
    relationship = db.Column(db.VARCHAR)

    player_id = db.Column("player_id", db.ForeignKey("ts_players.id"))
    player = db.relationship("TSPlayer")


class TSEvent(Base):
    __tablename__ = "ts_events"

    event_id = db.Column(db.NUMERIC)
    name = db.Column(db.VARCHAR)
    link = db.Column(db.VARCHAR)
    address = db.Column(db.VARCHAR)
    date_time = db.Column(db.VARCHAR)
    arrival_time = db.Column(db.VARCHAR)
    location = db.Column(db.VARCHAR)
    location_details = db.Column(db.VARCHAR)
    notes = db.Column(db.VARCHAR)


class PlayerEvents(Base):
    __tablename__ = "m_ts_player_events"

    event_id = db.Column("event_id", db.ForeignKey("ts_events.id"), primary_key=True)
    player_id = db.Column("player_id", db.ForeignKey("ts_players.id"), primary_key=True)
