"""
Utility functions used throughout the media processing application.
"""

import os
import logging
from datetime import datetime
from .constants import (
    RESOURCES_DIR, TEMPLATES_DIR,
    TEST_FILES_DIR, LOGS_DIR
)

def ensure_app_directories():
    """Ensure all required application directories exist."""
    directories = [
        RESOURCES_DIR,
        TEMPLATES_DIR,
        TEST_FILES_DIR,
        LOGS_DIR
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)

def setup_logger(name, log_dir=None):
    """
    Set up a logger with file handler for a given module.
    
    Args:
        name (str): Name of the logger
        log_dir (str): Directory to store log files
        
    Returns:
        logging.Logger: Configured logger instance
    """
    # Get the absolute path to the resources/logs directory
    if log_dir is None:
        ensure_app_directories()
        log_dir = LOGS_DIR
    
    # Create logger
    logger = logging.getLogger(name)
    
    # Only add handlers if they don't exist
    if not logger.handlers:
        logger.setLevel(logging.DEBUG)
        
        # Create file handler
        log_file = os.path.join(log_dir, f'{name}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
        fh = logging.FileHandler(log_file, encoding='utf-8')
        fh.setLevel(logging.DEBUG)
        
        # Create console handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        
        # Add handlers to logger
        logger.addHandler(fh)
        logger.addHandler(ch)
    
    return logger

def segment_text(text, max_chars):
    """
    Segment text into lines according to maximum character limit.
    
    Args:
        text (str): Text to segment
        max_chars (int): Maximum characters per line
        
    Returns:
        list: List of segmented lines
    """
    words = text.split()
    if not words:
        return []

    lines = []
    current_line = words[0]
    
    for word in words[1:]:
        # Try adding the next word
        if len(current_line) + 1 + len(word) <= max_chars:
            current_line += ' ' + word
        else:
            # Line is full, start a new one
            lines.append(current_line)
            current_line = word
    
    # Add the last line
    if current_line:
        lines.append(current_line)
    
    return lines

# File Management Functions
def validate_file_format(filename):
    """
    Validate if the file format is supported.
    
    Args:
        filename (str): Name of the file to validate
        
    Returns:
        bool: True if format is supported, False otherwise
    """
    valid_formats = {'.mp4', '.srt', '.ass'}
    ext = get_file_extension(filename)
    return ext.lower() in valid_formats

def get_file_extension(filename):
    """
    Get the extension of a file.
    
    Args:
        filename (str): Name of the file
        
    Returns:
        str: File extension including the dot
    """
    return os.path.splitext(filename)[1]

def change_extension(filename, new_ext):
    """
    Change the extension of a filename.
    
    Args:
        filename (str): Original filename
        new_ext (str): New extension (including dot)
        
    Returns:
        str: Filename with new extension
    """
    base = os.path.splitext(filename)[0]
    return base + new_ext

def ensure_directory(directory):
    """
    Ensure a directory exists, create it if it doesn't.
    
    Args:
        directory (str): Path to directory
    """
    os.makedirs(directory, exist_ok=True)

def remove_file(filepath):
    """
    Safely remove a file if it exists.
    
    Args:
        filepath (str): Path to file to remove
    """
    try:
        os.remove(filepath)
    except OSError:
        pass

def copy_file(source, destination):
    """
    Copy a file from source to destination.
    
    Args:
        source (str): Source file path
        destination (str): Destination file path
    """
    import shutil
    shutil.copy2(source, destination)

def create_temp_file(temp_dir, extension):
    """
    Create a temporary file with given extension.
    
    Args:
        temp_dir (str): Directory for temporary file
        extension (str): File extension
        
    Returns:
        str: Path to created temporary file
    """
    import tempfile
    fd, temp_path = tempfile.mkstemp(suffix=extension, dir=temp_dir)
    os.close(fd)
    return temp_path

def cleanup_temp_files(temp_dir):
    """
    Clean up all files in temporary directory.
    
    Args:
        temp_dir (str): Directory to clean
    """
    for filename in os.listdir(temp_dir):
        filepath = os.path.join(temp_dir, filename)
        try:
            if os.path.isfile(filepath):
                os.remove(filepath)
        except OSError:
            pass

def is_file_expired(filepath, max_age):
    """
    Check if a file is older than max_age.
    
    Args:
        filepath (str): Path to file
        max_age (int): Maximum age in seconds
        
    Returns:
        bool: True if file is expired
    """
    if not os.path.exists(filepath):
        return True
    
    file_time = os.path.getmtime(filepath)
    current_time = datetime.now().timestamp()
    return (current_time - file_time) > max_age

def cleanup_old_files(directory, max_age):
    """
    Remove files older than max_age.
    
    Args:
        directory (str): Directory to clean
        max_age (int): Maximum age in seconds
    """
    for filename in os.listdir(directory):
        filepath = os.path.join(directory, filename)
        if os.path.isfile(filepath) and is_file_expired(filepath, max_age):
            remove_file(filepath)

def cache_file(source_file, cache_dir):
    """
    Cache a file and return cache key.
    
    Args:
        source_file (str): File to cache
        cache_dir (str): Cache directory
        
    Returns:
        str: Cache key
    """
    import hashlib
    
    # Generate cache key from file content
    with open(source_file, 'rb') as f:
        file_hash = hashlib.md5(f.read()).hexdigest()
    
    # Copy file to cache
    cache_path = os.path.join(cache_dir, file_hash + get_file_extension(source_file))
    copy_file(source_file, cache_path)
    
    return file_hash

def get_cached_file(cache_key, cache_dir):
    """
    Get cached file path from cache key.
    
    Args:
        cache_key (str): Cache key
        cache_dir (str): Cache directory
        
    Returns:
        str: Path to cached file or None if not found
    """
    for filename in os.listdir(cache_dir):
        if filename.startswith(cache_key):
            return os.path.join(cache_dir, filename)
    return None

def clear_cache(cache_dir):
    """
    Clear all files from cache directory.
    
    Args:
        cache_dir (str): Cache directory to clear
    """
    cleanup_temp_files(cache_dir)

def check_cache_size(cache_dir):
    """
    Get total size of cache directory in bytes.
    
    Args:
        cache_dir (str): Cache directory
        
    Returns:
        int: Total size in bytes
    """
    total_size = 0
    for filename in os.listdir(cache_dir):
        filepath = os.path.join(cache_dir, filename)
        if os.path.isfile(filepath):
            total_size += os.path.getsize(filepath)
    return total_size

def cleanup_cache(cache_dir, max_size):
    """
    Clean up cache directory if it exceeds max size.
    
    Args:
        cache_dir (str): Cache directory
        max_size (int): Maximum size in bytes
    """
    while check_cache_size(cache_dir) > max_size:
        # Remove oldest file
        oldest_file = None
        oldest_time = float('inf')
        
        for filename in os.listdir(cache_dir):
            filepath = os.path.join(cache_dir, filename)
            if os.path.isfile(filepath):
                file_time = os.path.getmtime(filepath)
                if file_time < oldest_time:
                    oldest_time = file_time
                    oldest_file = filepath
        
        if oldest_file:
            remove_file(oldest_file)
        else:
            break  # No more files to remove
