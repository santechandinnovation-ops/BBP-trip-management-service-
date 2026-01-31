import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def setup_database():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL not set in environment variables")
        return

    try:
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        with open('database/init_trips_tables.sql', 'r') as f:
            sql_script = f.read()
        cursor.execute(sql_script)
        conn.commit()
        print("Trip Management tables created successfully!")
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error setting up database: {e}")
        raise

if __name__ == "__main__":
    setup_database()
