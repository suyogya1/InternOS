from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, JSON, Float, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from .db import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    handle = Column(String, unique=True, index=True, nullable=False)
    attempts = relationship("Attempt", back_populates="user")

class TicketBase(Base):
    __tablename__ = "tickets"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    ticket_id = Column(Integer, ForeignKey("tickets.id"))
    started_at = Column(DateTime, default=datetime.utcnow)
    finished_at = Column(DateTime, nullable=True)
    status = Column(String, default="in_progress") 
    repo_path = Column(String, nullable=True) # local clone path

    user = relationship("User", back_populates="attempts")
    ticket = relationship("Ticket", back_populates="attemps")
    metrics = relationship("Metric", back_populates="attempt")
    artifacts = relationship("Artifact", back_populates="attempt")

class Metric(Base):
    __tablename__ = "Metrics"
    id = Column(Integer, ForeignKey("attempts.id"))
    attempt_id = Column(Integer, ForeignKey("attemps.id"))
    key = Column(String, index=True)
    value = Column(Float)
    extra = Column(JSON, nullable=True)
    attempt = relationship("Attempt", back_populates="metrics")

class Artifact(Base):
    __tablename__ = "artifacts"
    id = Column(Integer, primary_key=True)
    attempt_id = Column(Integer, ForeignKey("attemps.id"))
    kind = Column(String)
    url = Column(String)
    note = Column(Text, nullable=True)
    attempt = relationship("Attempt", back_populates="artifacts")

class SignalSnapshot(Base):
    __tablename__ = "signals"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    snapshot_json = Column(JSON, nullable=False)

    