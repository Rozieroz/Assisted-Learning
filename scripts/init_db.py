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

# Import ORM Base and models so that metadata is populated
from app.database import Base
from app import models  # ensures all models are registered

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

"""
# ============for python script================
DB_HOST = os.getenv("host")
DB_PORT = os.getenv("port")
DB_NAME = os.getenv("database")
DB_USER = os.getenv("user")
DB_PASSWORD = os.getenv("password")
"""

# Read schema from environment, default to 'public' if not set
DB_SCHEMA = os.getenv("SCHEMA", "public")
logger.info(f"Using schema: {DB_SCHEMA}")

# ================FOR DOCKER PURPOSES==================================
# Use DATABASE_URL from .env (replace +asyncpg for psycopg2)
DB_URL = os.getenv("DATABASE_URL_SYNC")         # uses
if not DB_URL:
    raise RuntimeError("DATABASE_URL_SYNC is not set in your .env file")
DB_URL_PSYCOG = DB_URL.replace("postgresql+asyncpg", "postgresql")


# List of SQL scripts to execute (in order) – only the practice script now,
# because core tables are created by ORM.
SQL_SCRIPTS = [
    # "scripts/01_create_tables.sql",  # replaced by ORM creation
    "scripts/02_practice_fullname.sql"
]

def create_tables_orm():
    """Create all tables using SQLAlchemy ORM (ensures foreign keys)."""
    try:
        # Create a sync engine (using the same URL)
        engine = create_engine(DB_URL_PSYCOG)

        # Create schema if not exists and set search path
        with engine.connect() as conn:
            # Explicitly create schema (use the value from env)
            conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {DB_SCHEMA}"))
            conn.execute(text(f"SET search_path TO {DB_SCHEMA}"))
            conn.commit()
            logger.info(f"Schema '{DB_SCHEMA}' ensured and search path set.")

        # Create all tables (they will be placed in the schema specified
        # by each model's __table_args__, or metadata.schema if not set)
        logger.info(f"Tables to create: {Base.metadata.tables.keys()}")
        Base.metadata.create_all(engine)
        logger.info(f"Core tables created/verified using ORM (expected schema: {DB_SCHEMA}).")

    except Exception as e:
        logger.error(f"ORM table creation failed: {e}")
        raise

def execute_sql_files():
    """Connect to PostgreSQL and execute all SQL scripts."""
    try:
        """
        #  ============for python script================
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        conn.autocommit = True
        cursor = conn.cursor()
        """
        # ================FOR DOCKER PURPOSES==================================
        conn = psycopg2.connect(DB_URL_PSYCOG)
        conn.autocommit = True
        cursor = conn.cursor()

        # Set search path to the schema (in case it's not the default)
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
        db_url = DB_URL_PSYCOG
        engine = create_engine(db_url)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            logger.info(f"SQLAlchemy connection successful: {result.fetchone()}")
    except Exception as e:
        logger.error(f"SQLAlchemy connection failed: {e}")
        raise

if __name__ == "__main__":
    # Step 1: Create core tables using ORM (this creates foreign keys correctly)
    create_tables_orm()

    # Step 2: Run any additional SQL scripts (e.g., practice exercise)
    execute_sql_files()

    # Step 3: Test connection
    test_connection_sqlalchemy()