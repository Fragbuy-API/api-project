from sqlalchemy import create_engine, text
from sqlalchemy.pool import QueuePool
import time
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database connection with pooling and reconnection settings
DATABASE_URL = "mysql+pymysql://Qboid:JY8xM2ch5#Q[@155.138.159.75/products"
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800,  # Recycle connections after 30 minutes
    pool_pre_ping=True  # Enable automatic reconnection
)

def execute_with_retry(query, params, max_retries=3):
    """Execute a database query with retry logic"""
    for attempt in range(max_retries):
        try:
            logger.info(f"Executing query (attempt {attempt+1}/{max_retries})")
            with engine.connect() as connection:
                result = connection.execute(query, params)
                connection.commit()
                logger.info("Query executed successfully")
                return result
        except Exception as e:
            logger.error(f"Database error on attempt {attempt+1}: {str(e)}")
            if attempt == max_retries - 1:  # Last attempt
                logger.error("Maximum retry attempts reached, raising exception")
                raise  # Re-raise the last error
            time.sleep(1 * (attempt + 1))  # Exponential backoff
            logger.info(f"Retrying in {1 * (attempt + 1)} seconds")