import psycopg2
from psycopg2 import pool, OperationalError
from app.config.settings import settings
import logging

logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.connection_pool = None

    def _get_connection_kwargs(self):
        """Get connection parameters with keepalive settings."""
        return {
            'dsn': settings.DATABASE_URL,
            # TCP keepalive settings to detect dead connections
            'keepalives': 1,
            'keepalives_idle': 30,      # Start keepalive after 30s idle
            'keepalives_interval': 10,  # Send keepalive every 10s
            'keepalives_count': 5,      # Close after 5 failed keepalives
            'connect_timeout': 10,      # Connection timeout
        }

    def initialize(self):
        try:
            kwargs = self._get_connection_kwargs()
            self.connection_pool = psycopg2.pool.SimpleConnectionPool(
                1, 20, **kwargs
            )
            logger.info("Database connection pool created successfully")
        except Exception as e:
            logger.error(f"Error creating connection pool: {e}")
            raise

    def _test_connection(self, conn):
        """Test if connection is still alive."""
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
            return True
        except (OperationalError, psycopg2.InterfaceError):
            return False

    def get_connection(self):
        """Get a connection from pool, with health check."""
        if not self.connection_pool:
            raise Exception("Connection pool not initialized")
        
        conn = self.connection_pool.getconn()
        
        # Test if connection is still valid
        if not self._test_connection(conn):
            logger.warning("Stale connection detected, reconnecting...")
            try:
                conn.close()
            except Exception:
                pass
            # Put back the dead connection and get a fresh one
            self.connection_pool.putconn(conn, close=True)
            conn = self.connection_pool.getconn()
            
            # Verify the new connection works
            if not self._test_connection(conn):
                raise Exception("Failed to establish database connection")
        
        return conn

    def return_connection(self, connection):
        """Return connection to pool, closing if broken."""
        if self.connection_pool and connection:
            try:
                # Check if connection is still usable before returning to pool
                if connection.closed:
                    self.connection_pool.putconn(connection, close=True)
                else:
                    self.connection_pool.putconn(connection)
            except Exception as e:
                logger.warning(f"Error returning connection to pool: {e}")
                try:
                    self.connection_pool.putconn(connection, close=True)
                except Exception:
                    pass

    def close_all_connections(self):
        if self.connection_pool:
            self.connection_pool.closeall()

db = Database()
