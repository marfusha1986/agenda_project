import os
import oracledb


#Oracle bağlantı bilgileri

DB_USER = "C##AGENDA"
DB_PASSWORD = "agenda123"
DB_DSN = "localhost:1521/FREE"

def get_db_connection():
    try:
        connection = oracledb.connect(
            user=DB_USER,
            password=DB_PASSWORD,
            dsn=DB_DSN
        )
        return connection

    except Exception as e:
        print(f"Veritabanı bağlantı hastası: {e}")
        raise e

