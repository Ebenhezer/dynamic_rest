import os
import logging
from logging.handlers import RotatingFileHandler
from apscheduler.schedulers.background import BackgroundScheduler

# Logging Configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),  # Log to terminal
        RotatingFileHandler("/app/app.log", maxBytes=10485760, backupCount=3)  # 10MB max, keep 3 backups
    ]
)
logger = logging.getLogger(__name__)

# APScheduler Configuration
scheduler = BackgroundScheduler()

APP_DIR = os.path.abspath(os.path.dirname(__file__))
