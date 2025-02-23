from typing import Dict, Any, Optional
import logging
import logging.handlers
from pathlib import Path
import json
from datetime import datetime
import sys

class LoggingManager:
    """Manages system-wide logging configuration."""
    
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Configure logging formats
        self.log_formats = {
            "default": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "detailed": "%(asctime)s - %(name)s - %(levelname)s - %(pathname)s:%(lineno)d - %(message)s",
            "json": '{"timestamp": "%(asctime)s", "logger": "%(name)s", "level": "%(levelname)s", "message": "%(message)s"}'
        }
        
        # Initialize loggers
        self._setup_logging()
    
    def _setup_logging(self):
        """Setup logging configuration."""
        # System logger
        system_logger = logging.getLogger("movie_generator")
        system_logger.setLevel(logging.INFO)
        
        # File handlers
        system_handler = logging.handlers.RotatingFileHandler(
            self.log_dir / "system.log",
            maxBytes=10_000_000,  # 10MB
            backupCount=5
        )
        system_handler.setFormatter(logging.Formatter(self.log_formats["detailed"]))
        system_logger.addHandler(system_handler)
        
        # Error logger
        error_logger = logging.getLogger("movie_generator.error")
        error_logger.setLevel(logging.ERROR)
        
        error_handler = logging.handlers.RotatingFileHandler(
            self.log_dir / "error.log",
            maxBytes=10_000_000,
            backupCount=5
        )
        error_handler.setFormatter(logging.Formatter(self.log_formats["detailed"]))
        error_logger.addHandler(error_handler)
        
        # Performance logger
        perf_logger = logging.getLogger("movie_generator.performance")
        perf_handler = logging.handlers.RotatingFileHandler(
            self.log_dir / "performance.log",
            maxBytes=10_000_000,
            backupCount=5
        )
        perf_handler.setFormatter(logging.Formatter(self.log_formats["json"]))
        perf_logger.addHandler(perf_handler)
        
        # Console handler for development
        if "dev" in sys.argv:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(logging.Formatter(self.log_formats["default"]))
            system_logger.addHandler(console_handler)
    
    def get_logger(self, name: str) -> logging.Logger:
        """Get a logger by name."""
        return logging.getLogger(f"movie_generator.{name}")
    
    def log_performance_metric(self, metric_name: str, value: Any, context: Dict[str, Any]):
        """Log a performance metric."""
        logger = logging.getLogger("movie_generator.performance")
        metric_data = {
            "metric": metric_name,
            "value": value,
            "timestamp": datetime.now().isoformat(),
            "context": context
        }
        logger.info(json.dumps(metric_data)) 