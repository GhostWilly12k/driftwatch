from sqlalchemy import Column, String, Numeric, Integer, Boolean, ForeignKey, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import declarative_base
import uuid

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False)
    name = Column(String)
    plan = Column(String, default="starter")
    avatar_url = Column(String)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())


class UserSettings(Base):
    __tablename__ = "user_settings"
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    account_size = Column(Numeric, default=10000)
    risk_per_trade = Column(Numeric, default=1.0)
    daily_max_loss = Column(Numeric, default=200)
    weekly_max_loss = Column(Numeric, default=600)
    theme = Column(String, default="dark")
    agent_config = Column(JSONB, default={})
    notif_config = Column(JSONB, default={})


class Trade(Base):
    __tablename__ = "trades"

    id = Column(UUID(as_uuid=True), default=uuid.uuid4, primary_key=True, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    symbol = Column(String, nullable=False)
    direction = Column(String, nullable=False)
    strategy = Column(String)
    entry_price = Column(Numeric)
    exit_price = Column(Numeric)
    stop_loss = Column(Numeric)
    profit_target = Column(Numeric)
    planned_entry = Column(Numeric)
    planned_stop = Column(Numeric)
    quantity = Column(Numeric)
    r_result = Column(Numeric)
    mae = Column(Numeric)
    mfe = Column(Numeric)
    mindset = Column(String)
    emotion_pre = Column(JSONB)
    confidence = Column(Integer)
    rationale = Column(String)
    post_notes = Column(String)
    chart_url = Column(String)
    psychology_tags = Column(JSONB)
    rule_breaks = Column(JSONB)
    entered_at = Column(TIMESTAMP(timezone=True), primary_key=True, nullable=False)
    exited_at = Column(TIMESTAMP(timezone=True))
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    __table_args__ = (
        {"postgresql_partition_by": "RANGE (entered_at)"},
    )