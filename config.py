import logging

# Configure the logging system
logging.basicConfig(
    level=logging.INFO, # Only show INFO level and higher
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        # logging.FileHandler("app.log"), # Log to a file
        logging.StreamHandler()         # Also log to console
    ]
)

logger = logging.getLogger(__name__)