"""Logging utilities for the application."""

import logging
import os
from pathlib import Path
from logging.handlers import RotatingFileHandler

# Constants
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
DEFAULT_LOG_LEVEL = logging.INFO

class LoggerConfig:
    """Configuration for logger setup."""
    
    def __init__(self, log_dir, log_level=DEFAULT_LOG_LEVEL, max_size_mb=10, 
                 backup_count=3, console_output=True):
        """Initialize logger configuration.
        
        Args:
            log_dir (Path): Directory for log files
            log_level (int): Logging level (default: INFO)
            max_size_mb (int): Maximum size of log file in MB
            backup_count (int): Number of backup files to keep
            console_output (bool): Whether to output to console
        """
        self.log_dir = Path(log_dir)
        self.log_level = log_level
        self.max_size_mb = max_size_mb
        self.backup_count = backup_count
        self.console_output = console_output

def setup_logger(name, log_dir, log_level=DEFAULT_LOG_LEVEL, console_output=True):
    """Set up a logger with file and optional console output.
    
    Args:
        name (str): Logger name
        log_dir (Path): Directory for log files
        log_level (int): Logging level
        console_output (bool): Whether to output to console
        
    Returns:
        logging.Logger: Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    
    # Create log directory if it doesn't exist
    log_dir = Path(log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Create file handler
    log_file = log_dir / f"{name}.log"
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=3,
        encoding='utf-8'
    )
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
    logger.addHandler(file_handler)
    
    # Add console handler if requested
    if console_output:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(LOG_FORMAT))
        logger.addHandler(console_handler)
    
    return logger

def get_logger(name):
    """Get or create a logger by name.
    
    Args:
        name (str): Logger name
        
    Returns:
        logging.Logger: Logger instance
    """
    return logging.getLogger(name)

def rotate_logs(log_file, max_backups=3):
    """Rotate log files, keeping only the specified number of backups.
    
    Args:
        log_file (Path): Path to log file
        max_backups (int): Maximum number of backup files to keep
    """
    log_file = Path(log_file)
    if not log_file.exists():
        return
    
    # Get list of backup files
    backup_files = sorted([
        f for f in log_file.parent.glob(f"{log_file.stem}.*{log_file.suffix}")
    ])
    
    # Remove excess backup files
    while len(backup_files) > max_backups:
        backup_files[0].unlink()
        backup_files = backup_files[1:]
