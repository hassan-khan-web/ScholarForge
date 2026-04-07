"""
Structured Logging Configuration for ScholarForge
Provides JSON-formatted logging for Docker, CloudWatch, and Datadog integration
"""
import logging
import json
import sys
from datetime import datetime


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_obj = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_obj)


def setup_logging(name: str = "scholarforge") -> logging.Logger:
    """
    Configure structured logging with JSON formatter
    
    Args:
        name: Logger name (default: "scholarforge")
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    # Remove existing handlers to avoid duplicates
    logger.handlers = []
    
    # Console handler with JSON formatter
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(JSONFormatter())
    
    logger.addHandler(console_handler)
    
    return logger


# Create a module-level logger for convenience
logger = setup_logging()
