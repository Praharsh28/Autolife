"""Tests for the logger module."""

import pytest
import logging
import os
from pathlib import Path
from unittest.mock import patch, MagicMock, call
import tempfile
import json

from modules.utils.logger import (
    setup_logger,
    get_logger,
    LoggerConfig,
    rotate_logs,
    LOG_FORMAT,
    DEFAULT_LOG_LEVEL
)

@pytest.fixture
def temp_log_dir():
    """Create a temporary directory for log files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)

@pytest.fixture
def mock_logger():
    """Mock logger instance."""
    with patch('logging.getLogger') as mock:
        mock_logger = MagicMock()
        mock.return_value = mock_logger
        yield mock_logger

@pytest.fixture
def logger_config(temp_log_dir):
    """Create a test logger configuration."""
    return LoggerConfig(
        log_dir=temp_log_dir,
        log_level=logging.INFO,
        max_size_mb=10,
        backup_count=3,
        console_output=True
    )

class TestLogger:
    """Test cases for logger module."""

    @pytest.mark.logger
    def test_logger_initialization(self, temp_log_dir, mock_logger):
        """Test logger initialization."""
        logger = setup_logger(
            name="test_logger",
            log_dir=temp_log_dir,
            log_level=logging.INFO
        )
        
        assert logger is not None
        assert logger.level == logging.INFO
        assert len(logger.handlers) > 0

    @pytest.mark.logger
    def test_logger_config(self, logger_config):
        """Test logger configuration."""
        assert logger_config.log_dir is not None
        assert logger_config.log_level == logging.INFO
        assert logger_config.max_size_mb == 10
        assert logger_config.backup_count == 3
        assert logger_config.console_output is True

    @pytest.mark.logger
    def test_get_logger(self, mock_logger):
        """Test get_logger function."""
        logger1 = get_logger("test_logger")
        logger2 = get_logger("test_logger")
        
        # Should return same logger instance
        assert logger1 is logger2
        assert mock_logger.setLevel.called

    @pytest.mark.logger
    def test_log_rotation(self, temp_log_dir):
        """Test log file rotation."""
        log_file = temp_log_dir / "test.log"
        
        # Create some log files
        for i in range(5):
            backup = log_file.with_suffix(f".log.{i}")
            backup.touch()
        
        rotate_logs(log_file, max_backups=3)
        
        # Check only 3 backup files remain
        backups = list(temp_log_dir.glob("*.log.*"))
        assert len(backups) == 3

    @pytest.mark.logger
    def test_log_levels(self, temp_log_dir, mock_logger):
        """Test different log levels."""
        logger = setup_logger(
            name="test_levels",
            log_dir=temp_log_dir,
            log_level=logging.DEBUG
        )
        
        # Test all log levels
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")
        logger.critical("Critical message")
        
        assert mock_logger.debug.called
        assert mock_logger.info.called
        assert mock_logger.warning.called
        assert mock_logger.error.called
        assert mock_logger.critical.called

    @pytest.mark.logger
    def test_file_handler(self, temp_log_dir):
        """Test file handler configuration."""
        logger = setup_logger(
            name="test_file",
            log_dir=temp_log_dir,
            log_level=logging.INFO
        )
        
        # Find file handler
        file_handler = next(
            (h for h in logger.handlers if isinstance(h, logging.FileHandler)),
            None
        )
        
        assert file_handler is not None
        assert file_handler.baseFilename.endswith(".log")
        assert os.path.exists(file_handler.baseFilename)

    @pytest.mark.logger
    def test_console_handler(self, temp_log_dir):
        """Test console handler configuration."""
        logger = setup_logger(
            name="test_console",
            log_dir=temp_log_dir,
            log_level=logging.INFO,
            console_output=True
        )
        
        # Find console handler
        console_handler = next(
            (h for h in logger.handlers if isinstance(h, logging.StreamHandler)),
            None
        )
        
        assert console_handler is not None
        assert isinstance(console_handler.formatter, logging.Formatter)

    @pytest.mark.logger
    def test_log_format(self, temp_log_dir, mock_logger):
        """Test log message formatting."""
        logger = setup_logger(
            name="test_format",
            log_dir=temp_log_dir,
            log_level=logging.INFO
        )
        
        # Test log format
        test_message = "Test log message"
        logger.info(test_message)
        
        # Verify format matches LOG_FORMAT
        mock_logger.info.assert_called_with(test_message)

    @pytest.mark.logger
    def test_error_handling(self, temp_log_dir):
        """Test error handling in logger setup."""
        # Test invalid log directory
        with pytest.raises(Exception):
            setup_logger(
                name="test_error",
                log_dir=Path("/nonexistent/dir"),
                log_level=logging.INFO
            )
        
        # Test invalid log level
        with pytest.raises(ValueError):
            setup_logger(
                name="test_error",
                log_dir=temp_log_dir,
                log_level=999  # Invalid level
            )

    @pytest.mark.logger
    def test_logger_persistence(self, temp_log_dir):
        """Test logger persistence across multiple calls."""
        # Create logger
        logger1 = setup_logger(
            name="test_persist",
            log_dir=temp_log_dir,
            log_level=logging.INFO
        )
        
        # Write some logs
        test_message = "Test persistence"
        logger1.info(test_message)
        
        # Get same logger
        logger2 = get_logger("test_persist")
        
        # Verify it's the same logger
        assert logger1 is logger2
        
        # Verify log file exists and contains message
        log_file = next(temp_log_dir.glob("*.log"))
        assert log_file.exists()
        with open(log_file, 'r') as f:
            assert test_message in f.read()

    @pytest.mark.logger
    def test_concurrent_logging(self, temp_log_dir):
        """Test concurrent logging from multiple sources."""
        logger = setup_logger(
            name="test_concurrent",
            log_dir=temp_log_dir,
            log_level=logging.INFO
        )
        
        # Simulate concurrent logging
        messages = [f"Message {i}" for i in range(100)]
        for msg in messages:
            logger.info(msg)
        
        # Verify all messages were logged
        log_file = next(temp_log_dir.glob("*.log"))
        with open(log_file, 'r') as f:
            content = f.read()
            for msg in messages:
                assert msg in content
