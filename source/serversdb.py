# Module Imports
import mysql.connector

from constants import Constants


# Load constants and database information
CONSTANTS = Constants()


# Connect to database
def DatabaseConnection():
    # Create mysql connection and return database and cursor objects
    db = mysql.connector.connect(host=CONSTANTS.DBHOST, user=CONSTANTS.DBUSERNAME, passwd=CONSTANTS.DBPASSWORD, database=CONSTANTS.DBDATABASE)
    cursor = db.cursor()
    return db, cursor


#Return all server names of a certain category
def GetServerNames(category) -> list:
    # Define db and cursor
    db, cursor = DatabaseConnection()

    # Get servers from db
    output = []

    if category in ["General", "SMP", "Origins", "Pokemon", "Misc", "Non-MC"]:
        cursor.execute(f"SELECT name FROM serverinformation WHERE category = {'General'} ORDER BY serverID Asc")
    elif category == "All":
        cursor.execute("SELECT name FROM serverinformation ORDER BY serverID Asc")
    
    # Add retrieved servers to list
    for i in cursor:
        output.append(i[0])

    # Return results and close connection
    db.close()
    return output


#Return all server info of one specific server
def GetServerInformation(server) -> str:
    # Define cursor and db
    db, cursor = DatabaseConnection()

    # Get server info from db
    cursor.execute("SELECT * FROM serverinformation WHERE name = " + "'" + server + "'")
    
    # Return results and close connection
    result = cursor.fetchone()
    db.close()
    return result