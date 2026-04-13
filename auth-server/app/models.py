from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)

class License(Base):
    __tablename__ = "licenses"
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, index=True)
    owner_id = Column(String)  # Telegram ID of the owner
    bot_token_prefix = Column(String, index=True) # Bound bot token prefix
    api_id_encrypted = Column(String, nullable=True)
    api_hash_encrypted = Column(String, nullable=True)
    bot_token_encrypted = Column(String, nullable=True)
    expiry_date = Column(DateTime)
    is_active = Column(Boolean, default=True)
    is_locked = Column(Boolean, default=False)
    failed_attempts = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
