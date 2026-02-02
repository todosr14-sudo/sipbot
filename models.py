from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class SIP(Base):
    __tablename__ = "sips"
    id = Column(Integer, primary_key=True)
    number = Column(String, unique=True)
    password = Column(String)
    host = Column(String)
    provider = Column(String)
    status = Column(String, default="free")  # free / used
    assigned_to = Column(String, nullable=True)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    telegram_id = Column(String, unique=True)
    username = Column(String)
    sip_assigned = Column(String, nullable=True)
