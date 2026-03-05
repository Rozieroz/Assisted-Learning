"""
- initializes the PostgreSQL database by executing SQL scripts in order...
- creates the necessary schema and tables, and then runs the additional SQL scripts to set up the database structure. 
- includes a test connection using SQLAlchemy to verify that the database is accessible and properly configured. 
- logging is implemented for better visibility of the process. 
"""

import os
import logging
import psycopg2
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

DB_HOST = os.getenv("host")
DB_PORT = os.getenv("port")
DB_NAME = os.getenv("database")
DB_USER = os.getenv("user")
DB_PASSWORD = os.getenv("password")
DB_SCHEMA = os.getenv("schema", "public")

# List of SQL scripts to execute (in order)
SQL_SCRIPTS = [
    "01_create_tables.sql",
    "02_practice_fullname.sql"
]

def execute_sql_files():
    """Connect to PostgreSQL and execute all SQL scripts."""
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        conn.autocommit = True
        cursor = conn.cursor()

        # Create schema if not exists
        cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {DB_SCHEMA};")
        logger.info(f"Schema '{DB_SCHEMA}' confirmed.")

        # Set search path to the schema
        cursor.execute(f"SET search_path TO {DB_SCHEMA};")

        # Execute each SQL file
        for script_path in SQL_SCRIPTS:
            if not os.path.exists(script_path):
                logger.warning(f"Script not found: {script_path}, skipping.")
                continue
            with open(script_path, 'r') as f:
                sql = f.read()
                cursor.execute(sql)
                logger.info(f"Executed {script_path} successfully.")

        cursor.close()
        conn.close()
        logger.info("All SQL scripts executed.")

    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise

def test_connection_sqlalchemy():
    """Test connection using SQLAlchemy engine."""
    try:
        db_url = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        engine = create_engine(db_url)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            logger.info(f"SQLAlchemy connection successful: {result.fetchone()}")
    except Exception as e:
        logger.error(f"SQLAlchemy connection failed: {e}")
        raise

if __name__ == "__main__":
    execute_sql_files()
    test_connection_sqlalchemy()