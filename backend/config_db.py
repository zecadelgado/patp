import mysql.connector 

def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="M@nu2425",
        database="patrimonio_ideau"
    )

