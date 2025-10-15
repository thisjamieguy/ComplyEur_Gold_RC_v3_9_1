# Production entry point for Render deployment
import logging
import traceback

try:
    from app import create_app
    app = create_app()
except Exception as e:
    # Log the error to a file if possible
    try:
        import os
        logs_dir = 'logs'
        os.makedirs(logs_dir, exist_ok=True)

        log_handlers = [logging.StreamHandler()]
        try:
            log_handlers.append(logging.FileHandler(os.path.join(logs_dir, 'startup_error.log')))
        except Exception:
            pass

        logging.basicConfig(
            level=logging.ERROR,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=log_handlers
        )
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to create app: {e}")
        logger.error(traceback.format_exc())
    except:
        print(f"CRITICAL: Failed to create app: {e}")
        print(traceback.format_exc())
    raise

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
