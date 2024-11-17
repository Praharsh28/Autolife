"""
Network utilities for handling API requests and retries.
"""

import time
import random
import requests
from functools import wraps
from typing import Any, Callable, Dict, Optional, Union, Type
from requests.exceptions import (
    ConnectionError, Timeout, TooManyRedirects,
    ChunkedEncodingError, ReadTimeout, ConnectTimeout,
    RequestException
)
from .utilities import setup_logger
from .constants import (
    MAX_RETRIES, BASE_RETRY_DELAY, MAX_RETRY_DELAY,
    JITTER_RANGE, RETRY_STATUS_CODES, REQUEST_TIMEOUT
)

logger = setup_logger('network_utils')

class RetryableError(Exception):
    """Exception class for errors that should trigger a retry."""
    pass

class NonRetryableError(Exception):
    """Exception class for errors that should not be retried."""
    pass

def is_retryable_error(error: Exception) -> bool:
    """
    Determine if an error should trigger a retry.
    
    Args:
        error: The exception to check
        
    Returns:
        bool: True if the error should trigger a retry
    """
    if isinstance(error, RetryableError):
        return True
        
    if isinstance(error, requests.exceptions.RequestException):
        # Retry on connection and timeout errors
        if isinstance(error, (ConnectionError, Timeout, TooManyRedirects,
                            ChunkedEncodingError, ReadTimeout, ConnectTimeout)):
            return True
            
        # Retry on certain status codes
        if hasattr(error.response, 'status_code'):
            return error.response.status_code in RETRY_STATUS_CODES
            
    return False

def calculate_retry_delay(attempt: int, base_delay: float = BASE_RETRY_DELAY) -> float:
    """
    Calculate the delay before the next retry attempt with exponential backoff and jitter.
    
    Args:
        attempt: The current retry attempt number (0-based)
        base_delay: The base delay in seconds
        
    Returns:
        float: The calculated delay in seconds
    """
    # Calculate exponential backoff
    delay = min(base_delay * (2 ** attempt), MAX_RETRY_DELAY)
    
    # Add jitter (±10%)
    jitter = delay * JITTER_RANGE
    delay = delay + random.uniform(-jitter, jitter)
    
    return max(0, delay)  # Ensure non-negative delay

class APISession:
    """
    Manages API requests with automatic retries and connection pooling.
    """
    
    def __init__(self):
        """Initialize the API session with a connection pool."""
        self.session = requests.Session()
        self.logger = setup_logger('APISession')
        
    def __enter__(self):
        """Context manager entry."""
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with proper cleanup."""
        self.session.close()
        
    def request(
        self,
        method: str,
        url: str,
        retry_count: int = MAX_RETRIES,
        **kwargs
    ) -> requests.Response:
        """
        Make an HTTP request with automatic retries.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            url: Target URL
            retry_count: Maximum number of retries
            **kwargs: Additional arguments for requests
            
        Returns:
            Response object from the request
            
        Raises:
            NonRetryableError: For errors that shouldn't be retried
            Exception: For other errors after all retries are exhausted
        """
        # Ensure timeout is set
        kwargs.setdefault('timeout', REQUEST_TIMEOUT)
        
        attempt = 0
        last_error = None
        
        while attempt <= retry_count:
            try:
                self.logger.debug(
                    f"Attempt {attempt + 1}/{retry_count + 1} for {method} {url}"
                )
                
                response = self.session.request(method, url, **kwargs)
                
                # Check for error status codes
                if response.status_code >= 400:
                    error_msg = f"HTTP {response.status_code}: {response.text}"
                    
                    if response.status_code in RETRY_STATUS_CODES:
                        raise RetryableError(error_msg)
                    else:
                        raise NonRetryableError(error_msg)
                        
                return response
                
            except Exception as e:
                last_error = e
                
                if not is_retryable_error(e) or attempt >= retry_count:
                    if isinstance(e, (RetryableError, NonRetryableError)):
                        raise
                    raise NonRetryableError(str(e))
                    
                delay = calculate_retry_delay(attempt)
                self.logger.warning(
                    f"Request failed (attempt {attempt + 1}/{retry_count + 1}): {str(e)}"
                    f"\nRetrying in {delay:.2f} seconds..."
                )
                
                time.sleep(delay)
                attempt += 1
                
        # If we get here, we've exhausted all retries
        raise NonRetryableError(f"All retry attempts failed: {str(last_error)}")

def with_retry(
    retry_count: int = MAX_RETRIES,
    base_delay: float = BASE_RETRY_DELAY
) -> Callable:
    """
    Decorator for adding retry behavior to functions.
    
    Args:
        retry_count: Maximum number of retries
        base_delay: Base delay between retries in seconds
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            attempt = 0
            last_error = None
            
            while attempt <= retry_count:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    
                    if not is_retryable_error(e) or attempt >= retry_count:
                        if isinstance(e, (RetryableError, NonRetryableError)):
                            raise
                        raise NonRetryableError(str(e))
                        
                    delay = calculate_retry_delay(attempt, base_delay)
                    logger.warning(
                        f"Function {func.__name__} failed (attempt {attempt + 1}/{retry_count + 1}): {str(e)}"
                        f"\nRetrying in {delay:.2f} seconds..."
                    )
                    
                    time.sleep(delay)
                    attempt += 1
                    
            raise NonRetryableError(f"All retry attempts failed: {str(last_error)}")
            
        return wrapper
    return decorator
