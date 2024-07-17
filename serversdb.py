# Module Imports
import mysql.connector

from constants import Constants


# Load constants and database information
CONSTANTS = Constants()


# Connect to database
def database_connection(use_dictionary):
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
    return output


#Return all server names of a certain category
def get_server_names(category) -> list:
    # Define db and cursor
    db, cursor = database_connection(False)

    # Get servers from db
    output = []
    categories = get_categories()

    if category in categories:
        cursor.execute(f"SELECT name FROM serverinformation WHERE category = '{category}' ORDER BY serverID Asc")
    elif category == "All":
        cursor.execute("SELECT name FROM serverinformation ORDER BY serverID Asc")
    
    # Add retrieved servers to list
    for i in cursor:
        output.append(i[0])

    # Return results and close connection
    db.close()
    return output


#Return all server info of one specific server
def get_server_information(server) -> str:
    # Define cursor and db
    db, cursor = database_connection(True)

    # Get server info from db
    cursor.execute("SELECT * FROM serverinformation WHERE name = " + "'" + server + "'")
    
    # Return results and close connection
    result = cursor.fetchone()
    db.close()
    return result