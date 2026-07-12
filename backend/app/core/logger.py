import os
import sys
import logging
import time
from logging.handlers import RotatingFileHandler
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

# Configure logs directory relative to the backend root
LOGS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 
    "logs"
)
os.makedirs(LOGS_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOGS_DIR, "app.log")

# Setup enterprise-grade formatter
# Example: 2026-07-01 10:00:00 INFO Server Started
class EnterpriseFormatter(logging.Formatter):
    converter = time.localtime
    
    def formatTime(self, record, datefmt=None):
        ct = self.converter(record.created)
        if datefmt:
            s = time.strftime(datefmt, ct)
        else:
            # Match YYYY-MM-DD HH:MM:SS format requested
            s = time.strftime("%Y-%m-%d %H:%M:%S", ct)
        return s

formatter = EnterpriseFormatter('%(asctime)s %(levelname)s %(message)s')

def setup_logging(log_level: str = "INFO"):
    """
    Sets up application logging with file rotation and console stdout handlers.
    """
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # Remove existing handlers to prevent duplicate logs
    if root_logger.handlers:
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
            
    # Console Stream Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(numeric_level)
    root_logger.addHandler(console_handler)
    
    # Rotating File Handler (10 MB size limits, keep up to 5 logs)
    file_handler = RotatingFileHandler(
        LOG_FILE, maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(numeric_level)
    root_logger.addHandler(file_handler)
    
    # Silence or capture noisy logs from dependencies
    logging.getLogger("uvicorn.access").handlers = []
    logging.getLogger("uvicorn.access").propagate = True
    logging.getLogger("uvicorn").handlers = []
    logging.getLogger("uvicorn").propagate = True

logger = logging.getLogger("app")

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log details of incoming HTTP requests and response durations.
    """
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Log request receipt
        logger.info(f"Incoming request: {request.method} {request.url.path}")
        
        try:
            response = await call_next(request)
            process_time = (time.time() - start_time) * 1000
            logger.info(
                f"Completed request: {request.method} {request.url.path} "
                f"Status: {response.status_code} "
                f"Duration: {process_time:.2f}ms"
            )
            return response
        except Exception as e:
            process_time = (time.time() - start_time) * 1000
            logger.error(
                f"Failed request: {request.method} {request.url.path} "
                f"Error: {str(e)} "
                f"Duration: {process_time:.2f}ms",
                exc_info=True
            )
            raise e
