# Module Imports
import logging

import mysql.connector

from constants import Constants


# Load constants and database information, logging
CONSTANTS = Constants()
database_logger: logging.Logger = logging.getLogger("database")


# Connect to database
def database_connection(use_dictionary: bool):
    # Create mysql connection and return database and cursor objects
    db = mysql.connector.connect(host=CONSTANTS.DBHOST, user=CONSTANTS.DBUSERNAME, passwd=CONSTANTS.DBPASSWORD, database=CONSTANTS.DBDATABASE)
    if use_dictionary:
        cursor = db.cursor(dictionary=True)
    else:
        cursor = db.cursor()
    return db, cursor


# Get list of valid categories
def get_categories() -> list:
    # Define db and cursor
    db, cursor = database_connection(False)

    # Get categories from db
    output = []
    cursor.execute("SELECT name FROM servercategories ORDER BY categoryID Asc")

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
    db, cursor = database_connection(True)

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
    db, cursor = database_connection(True)

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
    db, cursor = database_connection(False)

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
