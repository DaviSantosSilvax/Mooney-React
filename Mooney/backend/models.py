from datetime import datetime
from decimal import Decimal
import uuid
from sqlalchemy import (
    Column, Integer, String, Numeric, DateTime, Date, Boolean, Text,
    ForeignKey, UniqueConstraint, CheckConstraint, Index, SmallInteger
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, ENUM
from sqlalchemy.orm import relationship
from database import Base

# Enums PostgreSQL
account_type_enum = ENUM(
    'checking', 'savings', 'credit_card', 'investment', 'cash', 'other',
    name='account_type', create_type=False
)
transaction_type_enum = ENUM(
    'income', 'expense', 'transfer',
    name='transaction_type', create_type=False
)
import_status_enum = ENUM(
    'pending', 'processing', 'done', 'failed', 'reverted',
    name='import_status', create_type=False
)
investment_type_enum = ENUM(
    'savings', 'cdb', 'lci_lca', 'treasury', 'fund', 'stock', 'fii', 'etf', 'crypto', 'pension', 'other',
    name='investment_type', create_type=False
)
rate_type_enum = ENUM(
    'prefixed', 'cdi_percent', 'selic', 'ipca_plus', 'savings', 'variable',
    name='rate_type', create_type=False
)
tax_regime_enum = ENUM(
    'ir_regressive', 'exempt', 'none',
    name='tax_regime', create_type=False
)
investment_tx_type_enum = ENUM(
    'deposit', 'withdrawal', 'yield', 'dividend', 'fee', 'tax',
    name='investment_tx_type', create_type=False
)
contribution_frequency_enum = ENUM(
    'once', 'daily', 'weekly', 'monthly', 'yearly',
    name='contribution_frequency', create_type=False
)


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(120), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(Text, nullable=False)
    currency = Column(String(3), default="BRL", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    accounts = relationship("Account", back_populates="user", cascade="all, delete-orphan")
    investments = relationship("Investment", back_populates="user", cascade="all, delete-orphan")
    simulations = relationship("Simulation", back_populates="user", cascade="all, delete-orphan")


class Institution(Base):
    __tablename__ = "institutions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(30), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    bank_code = Column(String(10), nullable=True)
    parser_key = Column(String(50), nullable=True)
    logo_url = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)


class Account(Base):
    __tablename__ = "accounts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    institution_id = Column(Integer, ForeignKey("institutions.id"), nullable=True)
    name = Column(String(100), nullable=False)
    type = Column(account_type_enum, default="checking", nullable=False)
    initial_balance = Column(Numeric(14, 2), default=Decimal("0.00"), nullable=False)
    credit_limit = Column(Numeric(14, 2), nullable=True)
    include_in_total = Column(Boolean, default=True, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    metadata_ = Column("metadata", JSONB, default=dict, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="accounts")
    transactions = relationship("Transaction", back_populates="account", cascade="all, delete-orphan")


class Category(Base):
    __tablename__ = "categories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("categories.id", ondelete="SET NULL"), nullable=True)
    name = Column(String(80), nullable=False)
    type = Column(transaction_type_enum, default="expense", nullable=False)
    color = Column(String(9), nullable=True)
    icon = Column(String(50), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id", ondelete="SET NULL"), nullable=True, index=True)
    import_id = Column(UUID(as_uuid=True), nullable=True)
    invoice_id = Column(UUID(as_uuid=True), nullable=True)
    type = Column(transaction_type_enum, nullable=False)
    amount = Column(Numeric(14, 2), nullable=False)
    description = Column(String(255), nullable=False)
    raw_description = Column(Text, nullable=True)
    occurred_on = Column(Date, nullable=False)
    external_id = Column(String(100), nullable=True)
    dedupe_hash = Column(String(64), nullable=False)
    transfer_group_id = Column(UUID(as_uuid=True), nullable=True)
    installment_number = Column(SmallInteger, nullable=True)
    installment_total = Column(SmallInteger, nullable=True)
    notes = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSONB, default=dict, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    account = relationship("Account", back_populates="transactions")


class Investment(Base):
    __tablename__ = "investments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="SET NULL"), nullable=True)
    name = Column(String(120), nullable=False)
    type = Column(investment_type_enum, nullable=False)
    ticker = Column(String(20), nullable=True)
    rate_type = Column(rate_type_enum, default="prefixed", nullable=False)
    rate_value = Column(Numeric(8, 4), nullable=True)
    tax_regime = Column(tax_regime_enum, default="ir_regressive", nullable=False)
    started_on = Column(Date, nullable=False)
    matures_on = Column(Date, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    metadata_ = Column("metadata", JSONB, default=dict, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="investments")
    transactions = relationship("InvestmentTransaction", back_populates="investment", cascade="all, delete-orphan")


class InvestmentTransaction(Base):
    __tablename__ = "investment_transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    investment_id = Column(UUID(as_uuid=True), ForeignKey("investments.id", ondelete="CASCADE"), nullable=False, index=True)
    type = Column(investment_tx_type_enum, nullable=False)
    amount = Column(Numeric(14, 2), nullable=False)
    occurred_on = Column(Date, nullable=False)
    quantity = Column(Numeric(18, 8), nullable=True)
    unit_price = Column(Numeric(14, 4), nullable=True)
    transaction_id = Column(UUID(as_uuid=True), ForeignKey("transactions.id", ondelete="SET NULL"), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    investment = relationship("Investment", back_populates="transactions")


class Simulation(Base):
    __tablename__ = "simulations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    investment_id = Column(UUID(as_uuid=True), ForeignKey("investments.id", ondelete="CASCADE"), nullable=True)
    name = Column(String(120), nullable=False)
    target_date = Column(Date, nullable=False)
    annual_rate = Column(Numeric(8, 4), nullable=True)
    initial_amount = Column(Numeric(14, 2), nullable=True)
    tax_regime = Column(tax_regime_enum, default="ir_regressive", nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="simulations")
    contributions = relationship("SimulationContribution", back_populates="simulation", cascade="all, delete-orphan")


class SimulationContribution(Base):
    __tablename__ = "simulation_contributions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    simulation_id = Column(UUID(as_uuid=True), ForeignKey("simulations.id", ondelete="CASCADE"), nullable=False)
    amount = Column(Numeric(14, 2), nullable=False)
    frequency = Column(contribution_frequency_enum, nullable=False)
    starts_on = Column(Date, nullable=False)
    ends_on = Column(Date, nullable=True)

    simulation = relationship("Simulation", back_populates="contributions")
