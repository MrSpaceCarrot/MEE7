# Module Imports
import logging
from decimal import Decimal

import mysql.connector

from constants import Constants


# Load constants and database information, logging
CONSTANTS = Constants()
database_logger: logging.Logger = logging.getLogger("database")


# Connect to database
def database_connection(use_dictionary: bool, database: str):
    # Create mysql connection and return database and cursor objects
    db = mysql.connector.connect(host=CONSTANTS.DBHOST, user=CONSTANTS.DBUSERNAME, passwd=CONSTANTS.DBPASSWORD, database=database)
    if use_dictionary:
        cursor = db.cursor(dictionary=True)
    else:
        cursor = db.cursor()
    return db, cursor


# Server Information
# Get list of valid categories
def get_categories() -> list:
    # Define db and cursor
    db, cursor = database_connection(False, CONSTANTS.DBDATABASE)

    # Get categories from db
    output = []
    cursor.execute("SELECT name FROM servercategories ORDER BY category_id Asc")

    # Add retrieved categories to list
    for i in cursor:
        output.append(i[0])

    # Return results and close connection
    db.close()
    database_logger.debug(f"Got server categories: {output}")
    return output


# Return all server info of one specific server
def get_server_information(server: str) -> dict:
    # Define cursor and db
    db, cursor = database_connection(True, CONSTANTS.DBSERVERSDATABASE)

    # Get server info from db
    cursor.execute("SELECT * FROM serverinformation WHERE name = " + "'" + server + "'")
    
    # Return results and close connection
    result = cursor.fetchone()
    db.close()
    database_logger.debug(f"Got server information: {result}")
    return result


# Return one specific property of one specific server
def get_server_property(server: str, property: str):
    # Define cursor and db
    db, cursor = database_connection(True, CONSTANTS.DBSERVERSDATABASE)

    # Get server info from db
    cursor.execute("SELECT " + property + " FROM serverinformation WHERE name = " + "'" + server + "'")
    
    # Return results and close connection
    result = cursor.fetchone()
    value = result[property]
    db.close()
    database_logger.debug(f"Got server property for {server}: {property}, {value}")
    return value


# Return one specific property of all servers of a certain category
def get_server_properties(category: str, property: str) -> list:
    # Define db and cursor
    db, cursor = database_connection(False, CONSTANTS.DBSERVERSDATABASE)

    # Get servers from db
    output = []
    
    # Get all servers if "All" is provided, else only grab a specific category
    if category == "All":
        cursor.execute("SELECT " + property + " FROM serverinformation ORDER BY serverID Asc")
    else:
        cursor.execute("SELECT " + property + " FROM serverinformation WHERE category = '" + category + "' ORDER BY serverID Asc")
    
    # Add retrieved servers to list
    for i in cursor:
        output.append(i[0])

    # Return results and close connection
    db.close()
    database_logger.debug(f"Got server property {property} for {category}: {output}")
    return output

# Economy
# Create entry in db for new users
def create_user_data(user_id: int) -> None:
    db, cursor = database_connection(True, CONSTANTS.DBMEE7DATABASE)
    query = "INSERT INTO economy (user_id) VALUES (" + "'" + str(user_id) + "'" + ")"
    cursor.execute(query)
    db.commit()
    database_logger.debug(f"Created data for user {user_id}")
    db.close()

# Get all balances for all users
def get_all_balances() -> dict:
    # Define cursor and db
    db, cursor = database_connection(True, CONSTANTS.DBMEE7DATABASE)

    # Get balance from db
    cursor.execute("SELECT * FROM economy")
    output = cursor.fetchall()
    
    # Return results and close connection
    db.close()
    database_logger.debug(f"Got all balances")
    return output

# Get a user's balance
def get_user_balance(user_id: int) -> dict:
    # Define cursor and db
    db, cursor = database_connection(True, CONSTANTS.DBMEE7DATABASE)

    # Get balance from db
    cursor.execute("SELECT * FROM economy WHERE user_id = " + "'" + str(user_id) + "'")
    result = cursor.fetchone()
    
    # Return results and close connection
    db.close()
    database_logger.debug(f"Got balance for user {user_id}")
    try:
        return result
    except Exception as e:
        create_user_data(user_id)
        return result
    
# Set currency value for a user
def set_user_balance(user_id: int, currency: str, amount: Decimal) -> None:
    # Define cursor and db
    db, cursor = database_connection(True, CONSTANTS.DBMEE7DATABASE)

    # Update balance
    query = "UPDATE economy SET " + currency + " = " + str(amount) + " WHERE user_id = " + str(user_id) + ""
    cursor.execute(query)
    db.commit()
    db.close()
    database_logger.debug(f"Set {currency} value for user {user_id} to {amount}")

# Get all exchange rates for all currencies
def get_all_exchange_rates() -> dict:
    # Define cursor and db
    db, cursor = database_connection(True, CONSTANTS.DBMEE7DATABASE)

    # Get balance from db
    cursor.execute("SELECT * FROM currencies")
    output = cursor.fetchall()
    
    # Return results and close connection
    db.close()
    database_logger.debug(f"Got all exchange rates")
    return output

# Update exchange rates of currencies
def update_exchange_rate(currency: str, value: float) -> None:
    # Define cursor and db
    db, cursor = database_connection(True, CONSTANTS.DBMEE7DATABASE)

    # Update exchange rate
    query = "UPDATE currencies SET exchange_rate = " + str(value) + " WHERE name = '" + str(currency) + "'"
    cursor.execute(query)
    db.commit()
    db.close()
    database_logger.debug(f"Set exchange rate for {currency} to {value}")