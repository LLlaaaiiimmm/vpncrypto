import os
import secrets
import sys
import logging

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# ===== Environment Configuration =====
ENV = os.getenv("ENV", "development")
DEBUG = os.getenv("DEBUG", "true" if ENV == "development" else "false").lower() == "true"
LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG" if DEBUG else "INFO")

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ===== SECRET_KEY Validation =====
SECRET_KEY = os.getenv("SECRET_KEY", "")
if not SECRET_KEY:
    # Development mode: auto-generate
    if ENV == "production":
        logger.error("SECRET_KEY must be set in production environment!")
        sys.exit(1)
    SECRET_KEY = secrets.token_hex(32)
    logger.warning("Using auto-generated SECRET_KEY. Set SECRET_KEY in .env for production!")
elif len(SECRET_KEY) < 32:
    logger.error(f"SECRET_KEY must be at least 32 characters long (current: {len(SECRET_KEY)})")
    sys.exit(1)

# ===== JWT Configuration =====
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "480"))  # 8 hours

# ===== Database Configuration =====
DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "budtender.db")
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "uploads")

# ===== OpenAI Configuration =====
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_TIMEOUT = int(os.getenv("OPENAI_TIMEOUT", "30"))

# ===== Rate Limiting Configuration =====
RATE_LIMIT_MAX = int(os.getenv("RATE_LIMIT_MAX", "10"))  # max submissions per IP per 24h
RATE_LIMIT_WINDOW_HOURS = int(os.getenv("RATE_LIMIT_WINDOW_HOURS", "24"))

# ===== File Upload Configuration =====
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", str(5 * 1024 * 1024)))  # 5MB default
ALLOWED_EXTENSIONS = os.getenv("ALLOWED_EXTENSIONS", "jpg,jpeg,png").split(",")

# ===== Application Configuration =====
APP_NAME = os.getenv("APP_NAME", "Budtender Feedback System")
APP_VERSION = os.getenv("APP_VERSION", "1.0.0")
ALLOWED_TAGS = [
    "Salary", "Store", "Product", "Conflict", "Legal",
    "Management", "Schedule", "Safety", "Training", "Equipment",
    "Customer", "Policy", "Communication", "Hygiene", "Other"
]

# ===== Security Configuration =====
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")
TRUSTED_HOSTS = os.getenv("TRUSTED_HOSTS", "*").split(",")

# Log configuration on startup
if ENV == "production":
    logger.info(f"Starting {APP_NAME} v{APP_VERSION} in PRODUCTION mode")
    logger.info(f"Debug mode: {DEBUG}")
    logger.info(f"Log level: {LOG_LEVEL}")
    logger.info(f"Rate limit: {RATE_LIMIT_MAX} per {RATE_LIMIT_WINDOW_HOURS}h")
    logger.info(f"OpenAI enabled: {bool(OPENAI_API_KEY)}")
else:
    logger.debug(f"Starting {APP_NAME} v{APP_VERSION} in DEVELOPMENT mode")
