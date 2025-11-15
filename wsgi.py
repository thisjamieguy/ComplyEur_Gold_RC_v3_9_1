"""WSGI entry point for ComplyEur application."""
import os
import logging

# Configure logging before app creation
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

logger.info("=" * 60)
logger.info("ComplyEur WSGI Startup")
logger.info("=" * 60)
logger.info(f"Environment: {os.getenv('FLASK_ENV', 'unknown')}")
logger.info(f"Render: {os.getenv('RENDER', 'false')}")
logger.info(f"Database path: {os.getenv('DATABASE_PATH', 'not set')}")
logger.info(f"SQLAlchemy URI: {os.getenv('SQLALCHEMY_DATABASE_URI', 'not set')}")
logger.info(f"Persistent dir: {os.getenv('PERSISTENT_DIR', 'not set')}")
logger.info("=" * 60)

try:
    from app import create_app
    logger.info("Successfully imported create_app")
    
    app = create_app()
    logger.info("Application created successfully")
    logger.info("=" * 60)
except Exception as e:
    logger.error(f"Failed to create application: {e}")
    import traceback
    logger.error(traceback.format_exc())
    logger.error("=" * 60)
    raise
