# app/models/transaction.py

from sqlalchemy import Column, Integer, String, Date, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.session import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, nullable=False)
    total_amount = Column(Integer, nullable=False)
    used_date = Column(Date, nullable=False)
    name = Column(String, nullable=False)
    memo = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    splits = relationship("TransactionSplit", back_populates="transaction")


class TransactionSplit(Base):
    __tablename__ = "transaction_splits"

    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(Integer, ForeignKey("transactions.id"))
    user_id = Column(Integer, nullable=False)
    amount = Column(Integer, nullable=False)

    transaction = relationship("Transaction", back_populates="splits")
