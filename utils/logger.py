import logging
import os
import sys
from logging.handlers import RotatingFileHandler
import appdirs

class Logger:
    def __init__(self, app_name="WhatsAppClone"):
        self.app_name = app_name
        self.log_dir = os.path.join(appdirs.user_log_dir(app_name))
        os.makedirs(self.log_dir, exist_ok=True)
        
        # Set up logging
        self.logger = logging.getLogger(app_name)
        self.logger.setLevel(logging.DEBUG)
        
        # Create formatters
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_formatter = logging.Formatter(
            '%(levelname)s: %(message)s'
        )
        
        # File handler
        log_file = os.path.join(self.log_dir, f"{app_name.lower()}.log")
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=5*1024*1024,  # 5MB
            backupCount=3
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(file_formatter)
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(console_formatter)
        
        # Add handlers
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
    def debug(self, message):
        """Log debug message"""
        self.logger.debug(message)
        
    def info(self, message):
        """Log info message"""
        self.logger.info(message)
        
    def warning(self, message):
        """Log warning message"""
        self.logger.warning(message)
        
    def error(self, message):
        """Log error message"""
        self.logger.error(message)
        
    def critical(self, message):
        """Log critical message"""
        self.logger.critical(message)
        
    def exception(self, message):
        """Log exception message with traceback"""
        self.logger.exception(message)
        
    def log_function_entry_exit(self, func):
        """Decorator to log function entry and exit"""
        def wrapper(*args, **kwargs):
            self.debug(f"Entering {func.__name__}")
            try:
                result = func(*args, **kwargs)
                self.debug(f"Exiting {func.__name__}")
                return result
            except Exception as e:
                self.exception(f"Exception in {func.__name__}: {str(e)}")
                raise
        return wrapper
        
    def get_logger(self):
        """Get the logger instance"""
        return self.logger
        
    def set_level(self, level):
        """Set logging level"""
        self.logger.setLevel(level)