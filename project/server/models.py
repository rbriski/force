# project/server/models.py


# import datetime

# from flask import current_app

import uuid

from project.server import db


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


#     email = db.Column(db.String(255), unique=True, nullable=False)
#     password = db.Column(db.String(255), nullable=False)
#     registered_on = db.Column(db.DateTime, nullable=False)
#     admin = db.Column(db.Boolean, nullable=False, default=False)

#     def __init__(self, email, password, admin=False):
#         self.email = email
#         self.password = bcrypt.generate_password_hash(
#             password, current_app.config.get("BCRYPT_LOG_ROUNDS")
#         ).decode("utf-8")
#         self.registered_on = datetime.datetime.now()
#         self.admin = admin

#     def is_authenticated(self):
#         return True

#     def is_active(self):
#         return True

#     def is_anonymous(self):
#         return False

#     def get_id(self):
#         return self.id

#     def __repr__(self):
#         return "<User {0}>".format(self.email)
