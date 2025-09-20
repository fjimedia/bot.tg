from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    username = Column(String(50))
    full_name = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)

class Ad(Base):
    __tablename__ = 'ads'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    channel = Column(String(100), nullable=False)
    text = Column(String(4000))
    price = Column(Integer)
    duration = Column(String(50))
    status = Column(String(20), default='pending')
    created_at = Column(DateTime, default=datetime.utcnow)