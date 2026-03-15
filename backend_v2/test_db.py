import sys
from dotenv import load_dotenv
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_db():
    load_dotenv()
    try:
        from src.database.db import init_db
        logger.info("Testing database connection and table creation...")
        init_db()
        logger.info("Successfully connected to MySQL and created tables!")
    except Exception as e:
        logger.error(f"Failed to connect to DB: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_db()
