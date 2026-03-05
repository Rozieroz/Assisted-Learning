"""
Database connection and session management.
Uses async SQLAlchemy with PostgreSQL 
==> sets up the async SQLAlchemy engine, session factory, and base class for models
"""

import os
import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logger
logger = logging.getLogger(__name__)

# Database connection parameters
DB_USER = os.getenv("user")
DB_PASSWORD = os.getenv("password")
DB_HOST = os.getenv("host")
DB_PORT = os.getenv("port")
DB_NAME = os.getenv("database")
DB_SCHEMA = os.getenv("schema", "public")

# Build async connection URL (postgresql+asyncpg://...)- for SQLAlchemy async engine
ASYNC_DB_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Create async engine
engine = create_async_engine(
    ASYNC_DB_URL,               # Async connection URL
    echo=True,                  # Set to False in production
    future=True,                # Use SQLAlchemy 2.0 style behavior
    pool_size=5,                # Connection pool size- to handle multiple concurrent requests (5 database connections)
    max_overflow=10         # Allow up to 10 additional connections beyond the pool size (total 15) to handle spikes in traffic
)

# Create async session factory-for creating async sessions to interact with the database
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False          # Prevents automatic expiration of objects after commit, allowing them to be accessed without re-querying the database
)

# Base (parent) class for ORM models- to be imported in models.py
Base = declarative_base()

# Function to get DB session (for dependency injection)- database session to API routes.
async def get_db() -> AsyncSession:
    """
    Dependency that provides an async database session.
    Yields a session and ensures it is closed after request.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()



"""
Async SQLAlchemy setup for PostgreSQL database connection and session management.
- Loads database connection parameters from environment variables.
- Configures an async SQLAlchemy engine with connection pooling.
- Defines a session factory for creating async sessions to interact with the database.
- Provides a dependency function to get a database session for API routes, ensuring proper cleanup after use.
- Sets up a base class for ORM models to be defined in models.py.

async allows for non-blocking database operations, improving performance and scalability of the app when handling multiple concurrent requests.
"""