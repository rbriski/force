# project/server/models.py


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

    @classmethod
    def all_players(klass):
        ps = []
        for p in klass.query.all():
            if p.parents:
                ps.append(p)

        return ps

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

        return total


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

    @classmethod
    def expenses(klass):
        return klass.query.filter_by(debit=True)

    @classmethod
    def payments(klass):
        return klass.query.filter_by(debit=False)

    def per_person(self):
        return self.amount / len(self.people)

    def players(self):
        return [p for p in self.people if p.parents is not None]


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
