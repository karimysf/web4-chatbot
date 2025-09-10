import mysql.connector
from  config import DB_HOST,DB_NAME,DB_PASSWORD,DB_PORT,DB_USERNAME
def get_db_connection():
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USERNAME,
        port=DB_PORT,
        password=DB_PASSWORD,
        database=DB_NAME
    )
   
