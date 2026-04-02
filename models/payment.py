# ORM models for payment tables: Card_Types, Cards, and Coach_Payment_History.
# Stores saved client payment cards and the transaction history between clients and coaches.

from datetime import datetime, timezone
from sqlalchemy import Boolean, CHAR, Column, DateTime, ForeignKey, Integer, Numeric, SmallInteger, String
from sqlalchemy.orm import relationship
from core.database import Base


def _now():
    return datetime.now(timezone.utc)


class CardType(Base):
    __tablename__ = 'card_types'

    card_type_id   = Column(Integer, primary_key=True, autoincrement=True)
    card_type_name = Column(String(50), nullable=False, unique=True)


class Card(Base):
    __tablename__ = 'cards'

    card_id      = Column(Integer, primary_key=True, autoincrement=True)
    user_id      = Column(Integer, ForeignKey('users.user_id',          ondelete='CASCADE'), nullable=False)
    card_type_id = Column(Integer, ForeignKey('card_types.card_type_id'), nullable=False)
    card_number  = Column(CHAR(16), nullable=False)
    expiry_month = Column(SmallInteger, nullable=False)     # MM
    expiry_year  = Column(SmallInteger, nullable=False)     # YYYY
    zip_code     = Column(CHAR(10))
    is_default   = Column(Boolean, nullable=False, default=False)
    created_at   = Column(DateTime(timezone=True), nullable=False, default=_now)
    last_updated = Column(DateTime(timezone=True), nullable=False, default=_now, onupdate=_now)

    card_type = relationship('CardType')


class CoachPaymentHistory(Base):
    __tablename__ = 'coach_payment_history'

    payment_id   = Column(Integer, primary_key=True, autoincrement=True)
    client_id    = Column(Integer, ForeignKey('clients.client_id', ondelete='CASCADE'), nullable=False)
    coach_id     = Column(Integer, ForeignKey('coaches.coach_id',  ondelete='CASCADE'), nullable=False)
    amount       = Column(Numeric(10, 2), nullable=False)
    payment_date = Column(DateTime(timezone=True), nullable=False, default=_now)
    created_at   = Column(DateTime(timezone=True), nullable=False, default=_now)
    last_updated = Column(DateTime(timezone=True), nullable=False, default=_now)

    client = relationship('Client')
    coach  = relationship('Coach')
