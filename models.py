from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class SIP(Base):
    __tablename__ = "sips"
    id = Column(Integer, primary_key=True)
    number = Column(String(255), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    host = Column(String(255), nullable=False)
    provider = Column(String(255), nullable=False)
    status = Column(String(20), default="free", nullable=False)  # free / used
    assigned_to = Column(String(255), nullable=True)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    telegram_id = Column(String(255), unique=True, nullable=False)
    username = Column(String(255), nullable=True)
    sip_assigned = Column(String(255), nullable=True)
