"""
Tests for error handling across different components.
"""

import os
import pytest
from unittest.mock import patch, MagicMock
from requests.exceptions import (
    ConnectionError, Timeout, TooManyRedirects,
    ChunkedEncodingError, ReadTimeout, ConnectTimeout
)

# Network Error Tests
def test_network_retry_mechanism():
    """Test network retry mechanism for failed requests."""
    from modules.network_utils import retry_on_failure
    
    mock_function = MagicMock(side_effect=[ConnectionError, ConnectionError, True])
    decorated_function = retry_on_failure()(mock_function)
    
    result = decorated_function()
    assert result is True
    assert mock_function.call_count == 3

def test_network_timeout_handling():
    """Test handling of network timeouts."""
    from modules.network_utils import retry_on_failure
    
    mock_function = MagicMock(side_effect=[Timeout, True])
    decorated_function = retry_on_failure()(mock_function)
    
    result = decorated_function()
    assert result is True
    assert mock_function.call_count == 2

def test_max_retries_exceeded():
    """Test behavior when maximum retries are exceeded."""
    from modules.network_utils import retry_on_failure
    from modules.constants import MAX_RETRIES
    
    mock_function = MagicMock(side_effect=ConnectionError)
    decorated_function = retry_on_failure()(mock_function)
    
    with pytest.raises(ConnectionError):
        decorated_function()
    assert mock_function.call_count == MAX_RETRIES + 1

# File System Error Tests
def test_invalid_file_format():
    """Test handling of invalid file formats."""
    from modules.workers.subtitle_worker import SubtitleWorker
    
    worker = SubtitleWorker(['test.txt'])
    with pytest.raises(ValueError, match="Unsupported file format"):
        worker.validate_file('test.txt')

def test_missing_file():
    """Test handling of missing files."""
    from modules.workers.subtitle_worker import SubtitleWorker
    
    worker = SubtitleWorker(['nonexistent.mp4'])
    with pytest.raises(FileNotFoundError):
        worker.validate_file('nonexistent.mp4')

def test_insufficient_disk_space():
    """Test handling of insufficient disk space."""
    from modules.disk_utils import check_disk_space
    
    with patch('psutil.disk_usage') as mock_disk_usage:
        mock_disk_usage.return_value = MagicMock(
            free=1024,  # 1KB free space
            total=1024 * 1024  # 1MB total space
        )
        with pytest.raises(OSError, match="Insufficient disk space"):
            check_disk_space('/', required_space=1024 * 1024)  # Require 1MB

# Memory Error Tests
def test_memory_limit_exceeded():
    """Test handling of memory limit exceeded."""
    from modules.workers.subtitle_worker import SubtitleWorker
    
    with patch('psutil.Process') as mock_process:
        mock_process.return_value.memory_percent.return_value = 90.0
        worker = SubtitleWorker(['test.mp4'])
        with pytest.raises(MemoryError):
            worker.check_memory_usage()

def test_resource_cleanup():
    """Test resource cleanup after errors."""
    from modules.workers.subtitle_worker import SubtitleWorker
    
    worker = SubtitleWorker(['test.mp4'])
    with patch.object(worker, 'cleanup_resources') as mock_cleanup:
        try:
            raise MemoryError("Test error")
        except MemoryError:
            worker.handle_error()
        mock_cleanup.assert_called_once()

# API Error Tests
def test_api_error_handling():
    """Test handling of API errors."""
    from modules.network_utils import retry_on_failure
    
    mock_function = MagicMock(side_effect=ValueError("API Error"))
    decorated_function = retry_on_failure()(mock_function)
    
    with pytest.raises(ValueError, match="API Error"):
        decorated_function()

def test_api_rate_limit():
    """Test handling of API rate limiting."""
    from modules.network_utils import retry_on_failure
    
    mock_function = MagicMock(side_effect=[
        ConnectionError("Rate limited"),
        True
    ])
    decorated_function = retry_on_failure()(mock_function)
    
    result = decorated_function()
    assert result is True
    assert mock_function.call_count == 2

# Timeout Error Tests
def test_process_timeout():
    """Test handling of process timeouts."""
    from modules.workers.subtitle_worker import SubtitleWorker
    
    worker = SubtitleWorker(['test.mp4'])
    with patch('subprocess.run') as mock_run:
        mock_run.side_effect = TimeoutError("Process timed out")
        with pytest.raises(TimeoutError):
            worker.process_file('test.mp4')

def test_worker_timeout():
    """Test handling of worker timeouts."""
    from modules.workers.subtitle_worker import SubtitleWorker
    
    worker = SubtitleWorker(['test.mp4'])
    with patch.object(worker, 'process_file') as mock_process:
        mock_process.side_effect = TimeoutError("Worker timed out")
        with pytest.raises(TimeoutError):
            worker.run()

# Batch Processing Error Tests
def test_batch_error_handling():
    """Test error handling in batch processing."""
    from modules.workers.subtitle_worker import SubtitleWorker
    
    worker = SubtitleWorker(['test1.mp4', 'test2.mp4'])
    with patch.object(worker, 'process_file') as mock_process:
        mock_process.side_effect = [ValueError("Error in file 1"), True]
        worker.run()  # Should continue processing despite error in first file
        assert mock_process.call_count == 2

def test_batch_cancellation():
    """Test batch processing cancellation."""
    from modules.workers.subtitle_worker import SubtitleWorker
    
    worker = SubtitleWorker(['test1.mp4', 'test2.mp4'])
    with patch.object(worker, 'process_file') as mock_process:
        mock_process.side_effect = KeyboardInterrupt
        with pytest.raises(KeyboardInterrupt):
            worker.run()
        assert mock_process.call_count == 1

# Recovery Tests
def test_error_recovery():
    """Test system recovery after errors."""
    from modules.workers.subtitle_worker import SubtitleWorker
    
    worker = SubtitleWorker(['test.mp4'])
    with patch.object(worker, 'process_file') as mock_process:
        mock_process.side_effect = [ValueError, True]
        worker.run()  # Should recover and retry
        assert mock_process.call_count == 2

def test_state_recovery():
    """Test state recovery after system errors."""
    from modules.workers.subtitle_worker import SubtitleWorker
    
    worker = SubtitleWorker(['test.mp4'])
    with patch.object(worker, 'save_state') as mock_save:
        with patch.object(worker, 'load_state') as mock_load:
            worker.handle_error()
            mock_save.assert_called_once()
            mock_load.assert_called_once()
