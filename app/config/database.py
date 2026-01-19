import psycopg2
from psycopg2 import pool
from app.config.settings import settings
import logging

logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.connection_pool = None

    def initialize(self):
        try:
            self.connection_pool = psycopg2.pool.SimpleConnectionPool(
                1, 20, dsn=settings.DATABASE_URL
            )
            logger.info("Database connection pool created successfully")
        except Exception as e:
            logger.error(f"Error creating connection pool: {e}")
            raise

    def get_connection(self):
        if self.connection_pool:
            return self.connection_pool.getconn()
        raise Exception("Connection pool not initialized")

    def return_connection(self, connection):
        if self.connection_pool:
            self.connection_pool.putconn(connection)

    def close_all_connections(self):
        if self.connection_pool:
            self.connection_pool.closeall()

db = Database()
