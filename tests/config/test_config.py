"""
Tests for configuration handling and validation.
"""

import os
import pytest
from unittest.mock import patch, MagicMock
from modules.constants import (
    API_URL, API_TOKEN, MAX_RETRIES, BASE_RETRY_DELAY,
    MAX_RETRY_DELAY, REQUEST_TIMEOUT, RETRY_STATUS_CODES
)

def test_api_token_validation():
    """Test API token validation."""
    with patch.dict('os.environ', {'HUGGINGFACE_API_TOKEN': ''}):
        with pytest.raises(ValueError, match="HUGGINGFACE_API_TOKEN not found"):
            from modules.constants import API_TOKEN

def test_path_configurations():
    """Test path configuration validation."""
    from modules.constants import BASE_DIR, RESOURCES_DIR, TEMPLATES_DIR
    
    assert os.path.exists(BASE_DIR), "Base directory does not exist"
    assert os.path.exists(RESOURCES_DIR), "Resources directory does not exist"
    assert os.path.exists(TEMPLATES_DIR), "Templates directory does not exist"

def test_network_configurations():
    """Test network configuration values."""
    assert isinstance(MAX_RETRIES, int), "MAX_RETRIES should be an integer"
    assert MAX_RETRIES > 0, "MAX_RETRIES should be positive"
    
    assert isinstance(BASE_RETRY_DELAY, float), "BASE_RETRY_DELAY should be a float"
    assert BASE_RETRY_DELAY > 0, "BASE_RETRY_DELAY should be positive"
    
    assert isinstance(MAX_RETRY_DELAY, float), "MAX_RETRY_DELAY should be a float"
    assert MAX_RETRY_DELAY > BASE_RETRY_DELAY, "MAX_RETRY_DELAY should be greater than BASE_RETRY_DELAY"
    
    assert isinstance(REQUEST_TIMEOUT, int), "REQUEST_TIMEOUT should be an integer"
    assert REQUEST_TIMEOUT > 0, "REQUEST_TIMEOUT should be positive"
    
    assert isinstance(RETRY_STATUS_CODES, set), "RETRY_STATUS_CODES should be a set"
    assert all(isinstance(code, int) for code in RETRY_STATUS_CODES), "All status codes should be integers"

def test_language_configurations():
    """Test language configuration validation."""
    from modules.constants import (
        SUPPORTED_LANGUAGES, DEFAULT_LANGUAGE,
        LANGUAGE_CODES, LANGUAGE_DIRECTIONS, LANGUAGE_MODELS
    )
    
    assert isinstance(SUPPORTED_LANGUAGES, set), "SUPPORTED_LANGUAGES should be a set"
    assert DEFAULT_LANGUAGE in SUPPORTED_LANGUAGES, "DEFAULT_LANGUAGE should be in SUPPORTED_LANGUAGES"
    
    assert isinstance(LANGUAGE_CODES, dict), "LANGUAGE_CODES should be a dictionary"
    assert all(isinstance(k, str) and isinstance(v, str) for k, v in LANGUAGE_CODES.items()), \
        "LANGUAGE_CODES should contain string key-value pairs"
    
    assert isinstance(LANGUAGE_DIRECTIONS, dict), "LANGUAGE_DIRECTIONS should be a dictionary"
    assert all(v in ['rtl', 'ltr'] for v in LANGUAGE_DIRECTIONS.values()), \
        "LANGUAGE_DIRECTIONS should only contain 'rtl' or 'ltr' values"
    
    assert isinstance(LANGUAGE_MODELS, dict), "LANGUAGE_MODELS should be a dictionary"
    assert 'default' in LANGUAGE_MODELS, "LANGUAGE_MODELS should have a default model"

def test_subtitle_configurations():
    """Test subtitle configuration validation."""
    from modules.constants import (
        MAX_CHARS_PER_LINE, MIN_CHARS_PER_LINE,
        MIN_DURATION, MAX_DURATION, CHARS_PER_SECOND,
        MIN_WORDS_PER_LINE, MAX_LINES_PER_SUBTITLE
    )
    
    assert isinstance(MAX_CHARS_PER_LINE, int), "MAX_CHARS_PER_LINE should be an integer"
    assert MAX_CHARS_PER_LINE > MIN_CHARS_PER_LINE, \
        "MAX_CHARS_PER_LINE should be greater than MIN_CHARS_PER_LINE"
    
    assert isinstance(MIN_DURATION, float), "MIN_DURATION should be a float"
    assert isinstance(MAX_DURATION, float), "MAX_DURATION should be a float"
    assert MAX_DURATION > MIN_DURATION, "MAX_DURATION should be greater than MIN_DURATION"
    
    assert isinstance(CHARS_PER_SECOND, int), "CHARS_PER_SECOND should be an integer"
    assert CHARS_PER_SECOND > 0, "CHARS_PER_SECOND should be positive"
    
    assert isinstance(MIN_WORDS_PER_LINE, int), "MIN_WORDS_PER_LINE should be an integer"
    assert MIN_WORDS_PER_LINE > 0, "MIN_WORDS_PER_LINE should be positive"
    
    assert isinstance(MAX_LINES_PER_SUBTITLE, int), "MAX_LINES_PER_SUBTITLE should be an integer"
    assert MAX_LINES_PER_SUBTITLE > 0, "MAX_LINES_PER_SUBTITLE should be positive"

def test_resource_configurations():
    """Test resource management configuration validation."""
    from modules.constants import (
        MAX_MEMORY_PERCENT, MAX_CONCURRENT_TASKS,
        MEMORY_CHECK_INTERVAL, CLEANUP_DELAY,
        MIN_FREE_SPACE_BYTES
    )
    
    assert isinstance(MAX_MEMORY_PERCENT, float), "MAX_MEMORY_PERCENT should be a float"
    assert 0 < MAX_MEMORY_PERCENT <= 100, "MAX_MEMORY_PERCENT should be between 0 and 100"
    
    assert isinstance(MAX_CONCURRENT_TASKS, int), "MAX_CONCURRENT_TASKS should be an integer"
    assert MAX_CONCURRENT_TASKS > 0, "MAX_CONCURRENT_TASKS should be positive"
    
    assert isinstance(MEMORY_CHECK_INTERVAL, float), "MEMORY_CHECK_INTERVAL should be a float"
    assert MEMORY_CHECK_INTERVAL > 0, "MEMORY_CHECK_INTERVAL should be positive"
    
    assert isinstance(CLEANUP_DELAY, float), "CLEANUP_DELAY should be a float"
    assert CLEANUP_DELAY > 0, "CLEANUP_DELAY should be positive"
    
    assert isinstance(MIN_FREE_SPACE_BYTES, int), "MIN_FREE_SPACE_BYTES should be an integer"
    assert MIN_FREE_SPACE_BYTES > 0, "MIN_FREE_SPACE_BYTES should be positive"

def test_streaming_configurations():
    """Test streaming configuration validation."""
    from modules.constants import (
        CHUNK_SIZE, MAX_CHUNK_DURATION, MIN_CHUNK_SIZE,
        CHUNK_OVERLAP, MAX_CHUNKS_IN_MEMORY, STREAM_BUFFER_SIZE
    )
    
    assert isinstance(CHUNK_SIZE, int), "CHUNK_SIZE should be an integer"
    assert CHUNK_SIZE >= MIN_CHUNK_SIZE, "CHUNK_SIZE should be greater than or equal to MIN_CHUNK_SIZE"
    
    assert isinstance(MAX_CHUNK_DURATION, int), "MAX_CHUNK_DURATION should be an integer"
    assert MAX_CHUNK_DURATION > 0, "MAX_CHUNK_DURATION should be positive"
    
    assert isinstance(CHUNK_OVERLAP, float), "CHUNK_OVERLAP should be a float"
    assert CHUNK_OVERLAP >= 0, "CHUNK_OVERLAP should be non-negative"
    
    assert isinstance(MAX_CHUNKS_IN_MEMORY, int), "MAX_CHUNKS_IN_MEMORY should be an integer"
    assert MAX_CHUNKS_IN_MEMORY > 0, "MAX_CHUNKS_IN_MEMORY should be positive"
    
    assert isinstance(STREAM_BUFFER_SIZE, int), "STREAM_BUFFER_SIZE should be an integer"
    assert STREAM_BUFFER_SIZE > 0, "STREAM_BUFFER_SIZE should be positive"
