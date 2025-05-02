# Module Imports
import logging
from urllib.parse import quote_plus

from sqlalchemy import create_engine, Column, Integer, String, BigInteger, Boolean, text, ForeignKey, Float, Date, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker, relationship, Mapped
from typing import List
import datetime

from constants import Constants

# Load constants and database information, logging
CONSTANTS = Constants()
database_logger: logging.Logger = logging.getLogger("database")

# Connect to DB
DATABASE_URL = f"mysql+mysqlconnector://{CONSTANTS.DBUSERNAME}:{quote_plus(CONSTANTS.DBPASSWORD)}@{CONSTANTS.DBHOST}:{CONSTANTS.DBPORT}/{CONSTANTS.DBDATABASE}"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

# Models
class Server(Base):
    __tablename__ = "serverinformation"
    server_id = Column(Integer, primary_key=True)
    name = Column(String(25), default=None, server_default=None)
    description = Column(String(150), default=None, server_default=None)
    category = Column(String(25), default=None, server_default=None)
    version = Column(String(25), default=None, server_default=None)
    modloader = Column(String(20), default=None, server_default=None)
    modlist = Column(String(300), default=None, server_default=None)
    moddownload = Column(String(150), default=None, server_default=None)
    active = Column(Boolean, default=None, server_default=None)
    compatible = Column(Boolean, default=None, server_default=None)
    modconditions = Column(String(150), default=None, server_default=None)
    icon = Column(String(45), default=None, server_default=None)
    color = Column(String(25), default=None, server_default=None)
    port = Column(Integer, default=None, server_default=None)
    emoji = Column(String(45), default=None, server_default=None)
    uuid = Column(String(30), default=None, server_default=None)
    domain = Column(String(60), default=None, server_default=None)

class ServerCategory(Base):
    __tablename__ = "servercategories"
    category_id = Column(Integer, primary_key=True)
    name = Column(String(25), default=None, server_default=None)
    icon = Column(String(45), default=None, server_default=None)
    color = Column(String(25), default=None, server_default=None)
    minecraft = Column(Boolean, default=None, server_default=None)

class User(Base):
    __tablename__ = "users"
    user_id = Column(BigInteger, primary_key=True)
    balances: Mapped[List["UserCurrency"]] = relationship("UserCurrency", back_populates="user", cascade="all, delete-orphan")
    job: Mapped["UserCurrency"] = relationship("UserJob", back_populates="user", cascade="all, delete-orphan")
    cooldowns: Mapped[List["Cooldown"]] = relationship("Cooldown", back_populates="user", cascade="all, delete-orphan")

class Currency(Base):
    __tablename__ = "currencies"
    currency_id = Column(String(25), primary_key=True)
    display_name = Column(String(25), default=None, server_default=None)
    prefix = Column(String(1), default=None, server_default=None)
    can_gamble = Column(Boolean, default=None, server_default=None)
    can_exchange = Column(Boolean, default=None, server_default=None)
    can_work_for = Column(Boolean, default=None, server_default=None)
    exchange_rate = Column(Float, default=None, server_default=None)
    decimal_places = Column(Integer, default=None, server_default=None)
    value_multiplier = Column(Float, default=None, server_default=None)
    starting_value = Column(Float, default=None, server_default=None)

class UserCurrency(Base):
    __tablename__ = "user_currencies"
    user_id: Mapped[int] = Column(BigInteger, ForeignKey('users.user_id'), primary_key=True)
    currency_id: Mapped[str] = Column(String(25), ForeignKey('currencies.currency_id'), primary_key=True)
    balance: Mapped[float] = Column(Float(precision=53), default=0, server_default=text("0"))

    user: Mapped["User"] = relationship("User", back_populates="balances")
    currency: Mapped["Currency"] = relationship("Currency")

class Job(Base):
    __tablename__ = "jobs"
    job_id = Column(String(25), primary_key=True)
    display_name = Column(String(25), default=None, server_default=None)
    min_pay = Column(Float, default=None, server_default=None)
    max_pay = Column(Float, default=None, server_default=None)
    cooldown = Column(Integer, default=None, server_default=None)
    currency_override: Mapped[str] = Column(String(25), ForeignKey('currencies.currency_id'), nullable=True)

    overridden_currency = relationship("Currency", foreign_keys=[currency_override])

class UserJob(Base):
    __tablename__ = "user_jobs"
    user_id: Mapped[int] = Column(BigInteger, ForeignKey('users.user_id'), primary_key=True)
    job_id: Mapped[int] = Column(String(25), ForeignKey('jobs.job_id'), primary_key=True)
    currency_id: Mapped[str] = Column(String(25), ForeignKey('currencies.currency_id'), primary_key=True)

    user: Mapped["User"] = relationship("User", back_populates="job")
    currency: Mapped["Currency"] = relationship("Currency")
    job: Mapped["Job"] = relationship("Job")

class Cooldown(Base):
    __tablename__ = "cooldowns"
    user_id: Mapped[int] = Column(BigInteger, ForeignKey('users.user_id'), primary_key=True)
    expiry_timestamp: Mapped[DateTime] = Column(DateTime, default=None, server_default=None)
    cooldown_type = Column(String(25), default=None, server_default=None)

    user: Mapped["User"] = relationship("User", back_populates="cooldowns")
    

# Setup
def init_db():
    Base.metadata.create_all(bind=engine)