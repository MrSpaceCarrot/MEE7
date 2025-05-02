# Module Import
import logging
import datetime
from typing import List
from sqlalchemy import desc
from database.models import SessionLocal, Server, ServerCategory, User, Currency, UserCurrency, UserJob, Job, Cooldown
from sqlalchemy.orm import joinedload
from sqlalchemy.sql.expression import func

# Logging
database_logger: logging.Logger = logging.getLogger("database")

# Server Operations
# Get the list of server categories
def get_server_categories() -> list:
    with SessionLocal() as session:
        server_categories = session.query(ServerCategory).all()
        server_categories_list = []
        for category in server_categories:
            server_categories_list.append(category.name)
        database_logger.debug(f"Got server categories: {server_categories_list}") 
        return server_categories_list
    
# Get all server information for one server
def get_server_information(server_name: str) -> Server:
    with SessionLocal() as session:
        server_information = session.query(Server).filter(Server.name == server_name).first()
        database_logger.debug(f"Got server information for server: {server_information.name}")
        return server_information
    
# Get one specific property of one specific server
def get_server_property(server_name: str, property: str):
    with SessionLocal() as session:
        server_information = session.query(Server).filter(Server.name == server_name).first()
        property_value = getattr(server_information, property) if server_information else None
        database_logger.debug(f"Got server property for {server_name}: {property}, {property_value}")
        return property_value
    
# Get names of all servers in a specific category
def get_server_names(category: str) -> list:
    with SessionLocal() as session:
        if category == "All":
            servers = session.query(Server).all()
        else:
            servers = session.query(Server).filter(Server.category == category).all()
        server_names_list = []
        for server in servers:
            server_names_list.append(server.name)
        database_logger.debug(f"Got server names for servers with category '{category}': {server_names_list}")
        return server_names_list

# Economy Operations
# Populate user currencies
def populate_user_currencies(user_id: int) -> None:
    with SessionLocal() as session:
        # Get user from db, create new if user does not exist
        user = session.query(User).filter(User.user_id == user_id).first()
        if not user:
            user = User(user_id=user_id)
            session.add(user)
            session.commit()
            database_logger.debug(f"Creating user: {user_id}")
        else:
            database_logger.debug(f"User {user_id} already exists")

        # If a user does not have an entry for a currency, create it
        currencies = session.query(Currency).all()
        commit_needed = False
        for currency in currencies:
            user_currency = session.query(UserCurrency).filter(UserCurrency.user_id == user_id, UserCurrency.currency_id == currency.currency_id).first()
            if not user_currency:
                created_user_currency = UserCurrency(user_id=user_id, currency_id=currency.currency_id, balance=currency.starting_value)
                session.add(created_user_currency)
                database_logger.debug(f"Populating currency '{currency.currency_id}' for user {user_id}'")
                commit_needed = True
            else:
                database_logger.debug(f"Currency '{currency.currency_id} already exists for user {user_id}")
        if commit_needed == True:
            session.commit()

# Get user balance for a specific currency
def get_user_balance(user_id: int, currency_id: str) -> UserCurrency:
    with SessionLocal() as session:
        populate_user_currencies(user_id)
        # Return user currency, eagerly load currency information
        user_currency = session.query(UserCurrency).options(joinedload(UserCurrency.currency)).filter(UserCurrency.user_id == user_id, UserCurrency.currency_id == currency_id).first()
        database_logger.debug(f"Got balance for user {user_id} for currency {user_currency.currency_id}")
        return user_currency

# Get user balance for all currencies
def get_user_balances(user_id: int):
    with SessionLocal() as session:
        populate_user_currencies(user_id)
        # Return user, eagerly load user currency and balance information
        user = session.query(User).options(joinedload(User.balances).joinedload(UserCurrency.currency)).filter(User.user_id == user_id).first()
        database_logger.debug(f"Got balances for user {user_id}")
        return user.balances

# Set user balance
def set_user_balance(user_id: int, currency_id: str, amount: float) -> None:
    with SessionLocal() as session:
        populate_user_currencies(user_id)
        user_currency = session.query(UserCurrency).filter(UserCurrency.user_id == user_id, UserCurrency.currency_id == currency_id).first()
        user_currency.balance = amount
        database_logger.debug(f"Set balance for user {user_id} for currency {user_currency.currency_id} to {amount}")
        session.commit()

# Get balance for all users for a specific currency
def get_all_balances(currency_id: str) -> List[UserCurrency]:
    with SessionLocal() as session:
        database_logger.debug(f"Got all balances for {currency_id}")
        return session.query(UserCurrency).options(joinedload(UserCurrency.currency)).filter(UserCurrency.currency_id == currency_id).order_by(desc(UserCurrency.balance)).all()
        
# Get currency information
def get_currency(currency_id: str) -> Currency:
    with SessionLocal() as session:
        database_logger.debug(f"Got currency {currency_id}")
        return session.query(Currency).filter(Currency.currency_id == currency_id).first()

# Get all currencies
def get_currencies() -> List[Currency]:
    with SessionLocal() as session:
        database_logger.debug(f"Got all currencies")
        return session.query(Currency).all()

# Set exchange rate
def set_exchange_rate(currency_id: str, exchange_rate: float) -> None:
    with SessionLocal() as session:
        currency = session.query(Currency).filter(Currency.currency_id == currency_id).first()
        currency.exchange_rate = exchange_rate
        database_logger.debug(f"Updating exchange rate for {currency.currency_id} to {exchange_rate}")
        session.commit()

# Get user job
def get_user_job(user_id: int) -> UserJob:
    with SessionLocal() as session:
        populate_user_currencies(user_id)
        user_job = session.query(UserJob).options(joinedload(UserJob.job), joinedload(UserJob.currency)).filter(UserJob.user_id == user_id).first()
        database_logger.debug(f"Got job for user {user_id}")
        return user_job
    
# Give user job
def give_user_random_job(user_id: int) -> None:
    with SessionLocal() as session:
        # Remove existing job and generate new one
        populate_user_currencies(user_id)
        remove_user_job(user_id)
        random_job = session.query(Job).order_by(func.rand()).limit(1).first()

        # If job specifies a currency to be paid in, use that
        if random_job.currency_override:
            user_job = UserJob(user_id=user_id, job_id=random_job.job_id, currency_id=random_job.overridden_currency.id)
        else:
            random_currency = session.query(Currency).filter(Currency.can_work_for == True).order_by(func.rand()).limit(1).first()
            user_job = UserJob(user_id=user_id, job_id=random_job.job_id, currency_id=random_currency.currency_id)

        # Commit changes
        session.add(user_job)
        database_logger.debug(f"Gave user {user_id} job: {random_job.job_id}")
        session.commit()

# Remove user job
def remove_user_job(user_id: int) -> None:
    with SessionLocal() as session:
        populate_user_currencies(user_id)
        user_job = session.query(UserJob).filter(UserJob.user_id == user_id).first()
        if user_job:
            session.delete(user_job)
            database_logger.debug(f"Removed job from user {user_id}")
            session.commit()

# Create cooldown
def create_cooldown(user_id: int, duration: int, cooldown_type: str) -> Cooldown:
    with SessionLocal() as session:
        # Remove existing cooldown
        existing_cooldown = session.query(Cooldown).filter(Cooldown.user_id == user_id, Cooldown.cooldown_type == cooldown_type).first()
        if existing_cooldown:
            session.delete(existing_cooldown)
            database_logger.debug(f"Removing cooldown for user {user_id} of type {cooldown_type}")
            session.commit()

        # Create new cooldown
        timestamp = datetime.datetime.now() + datetime.timedelta(seconds=duration)
        new_cooldown = Cooldown(user_id=user_id, expiry_timestamp=timestamp, cooldown_type=cooldown_type)
        session.add(new_cooldown)
        database_logger.debug(f"Created cooldown for user {user_id} for type {cooldown_type}")
        session.commit()
        session.refresh(new_cooldown)
        return new_cooldown

# Check cooldown
def check_cooldown(user_id: int, cooldown_type: str) -> Cooldown:
    with SessionLocal() as session:
        cooldown = session.query(Cooldown).filter(Cooldown.user_id == user_id, Cooldown.cooldown_type == cooldown_type).first()
        database_logger.debug(f"Getting cooldown for user {user_id} for type {cooldown_type}")
        if cooldown:
            # Check if cooldown is expired
            if datetime.datetime.now() > cooldown.expiry_timestamp:
                session.delete(cooldown)
                session.commit()
                return None
            else:
                return cooldown
        else: 
            return None
        
# Remove cooldown
def remove_cooldown(user_id: int, cooldown_type: str) -> None:
    with SessionLocal() as session:
        cooldown = session.query(Cooldown).filter(Cooldown.user_id == user_id, Cooldown.cooldown_type == cooldown_type).first()
        if cooldown:
            session.delete(cooldown)
            database_logger.debug(f"Removing cooldown for user {user_id} of type {cooldown_type}")
            session.commit()