from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, JSON, Float, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from .db import Base


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    handle = Column(String, unique=True, index=True, nullable=False)
    attempts = relationship("Attempt", back_populates="user")


class Ticket(Base):
    __tablename__ = "tickets"
    id = Column(Integer, primary_key=True)
    kind = Column(String, nullable=False)
    repo_url = Column(String, nullable=False)
    rubric_json = Column(JSON, nullable=False)
    time_limit = Column(Integer, nullable=True)
    attempts = relationship("Attempt", back_populates="ticket")


class Attempt(Base):
    __tablename__ = "attempts"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    ticket_id = Column(Integer, ForeignKey("tickets.id"))
    started_at = Column(DateTime, default=datetime.utcnow)
    finished_at = Column(DateTime, nullable=True)
    status = Column(String, default="in_progress")
    repo_path = Column(String, nullable=True)

    user = relationship("User", back_populates="attempts")
    ticket = relationship("Ticket", back_populates="attempts")
    metrics = relationship("Metric", back_populates="attempt", cascade="all, delete-orphan")
    artifacts = relationship("Artifact", back_populates="attempt", cascade="all, delete-orphan")


class Metric(Base):
    __tablename__ = "metrics"
    id = Column(Integer, primary_key=True)
    attempt_id = Column(Integer, ForeignKey("attempts.id"))
    key = Column(String, index=True)
    value = Column(Float)
    extra = Column(JSON, nullable=True)
    attempt = relationship("Attempt", back_populates="metrics")


class Artifact(Base):
    __tablename__ = "artifacts"
    id = Column(Integer, primary_key=True)
    attempt_id = Column(Integer, ForeignKey("attempts.id"))
    kind = Column(String)
    url = Column(String)
    note = Column(Text, nullable=True)
    attempt = relationship("Attempt", back_populates="artifacts")


class SignalSnapshot(Base):
    __tablename__ = "signals"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    snapshot_json = Column(JSON, nullable=False)
