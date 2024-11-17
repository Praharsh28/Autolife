"""
Disk management utilities for monitoring and managing disk space.
"""

import os
import shutil
import psutil
from typing import Dict, Optional, Tuple
from pathlib import Path
from .utilities import setup_logger
from .constants import (
    MIN_FREE_SPACE_BYTES, TEMP_DIR_CLEANUP_THRESHOLD,
    TEMP_FILE_MAX_AGE, DISK_CHECK_INTERVAL
)

logger = setup_logger('disk_utils')

def get_disk_usage(path: str) -> Tuple[int, int, float]:
    """
    Get disk usage statistics for the given path.
    
    Args:
        path: Path to check disk usage for
        
    Returns:
        Tuple containing:
        - Total space in bytes
        - Free space in bytes
        - Usage percentage
        
    Raises:
        OSError: If disk information cannot be retrieved
    """
    try:
        usage = shutil.disk_usage(path)
        percent_used = (usage.used / usage.total) * 100
        return usage.total, usage.free, percent_used
    except Exception as e:
        logger.error(f"Failed to get disk usage for {path}: {str(e)}")
        raise OSError(f"Could not get disk usage: {str(e)}")

def check_disk_space(path: str, required_bytes: Optional[int] = None) -> bool:
    """
    Check if there's enough free disk space at the given path.
    
    Args:
        path: Path to check disk space for
        required_bytes: Optional number of bytes required (defaults to MIN_FREE_SPACE_BYTES)
        
    Returns:
        bool: True if there's enough space, False otherwise
    """
    try:
        _, free_bytes, usage_percent = get_disk_usage(path)
        required = required_bytes if required_bytes is not None else MIN_FREE_SPACE_BYTES
        
        if free_bytes < required:
            logger.warning(
                f"Low disk space at {path}: {free_bytes/1024/1024:.1f}MB free, "
                f"need {required/1024/1024:.1f}MB"
            )
            return False
            
        if usage_percent > TEMP_DIR_CLEANUP_THRESHOLD:
            logger.warning(
                f"High disk usage at {path}: {usage_percent:.1f}% used"
            )
            cleanup_temp_files(path)
            
        return True
        
    except Exception as e:
        logger.error(f"Error checking disk space at {path}: {str(e)}")
        return False

def estimate_space_needed(audio_file: str, include_temp: bool = True) -> int:
    """
    Estimate space needed for processing an audio file.
    
    Args:
        audio_file: Path to the audio file
        include_temp: Whether to include temporary file space in estimate
        
    Returns:
        int: Estimated space needed in bytes
    """
    try:
        file_size = os.path.getsize(audio_file)
        # WAV files are typically 10x larger than compressed audio
        wav_size = file_size * 10 if include_temp else 0
        # Subtitle files are typically very small
        subtitle_size = 100 * 1024  # 100KB estimate
        
        total_size = wav_size + subtitle_size
        # Add 10% buffer
        return int(total_size * 1.1)
        
    except Exception as e:
        logger.error(f"Error estimating space needed for {audio_file}: {str(e)}")
        # Return a conservative estimate
        return 500 * 1024 * 1024  # 500MB

def cleanup_temp_files(temp_dir: str) -> None:
    """
    Clean up old temporary files to free up disk space.
    
    Args:
        temp_dir: Directory containing temporary files
    """
    try:
        temp_path = Path(temp_dir)
        if not temp_path.exists():
            return
            
        current_time = time.time()
        deleted_size = 0
        
        for file_path in temp_path.glob("*.wav"):
            try:
                stats = file_path.stat()
                age = current_time - stats.st_mtime
                
                if age > TEMP_FILE_MAX_AGE:
                    size = stats.st_size
                    file_path.unlink()
                    deleted_size += size
                    logger.info(
                        f"Deleted old temp file {file_path.name} "
                        f"({size/1024/1024:.1f}MB, {age/3600:.1f} hours old)"
                    )
                    
            except Exception as e:
                logger.warning(f"Failed to process temp file {file_path}: {str(e)}")
                
        if deleted_size > 0:
            logger.info(f"Cleaned up {deleted_size/1024/1024:.1f}MB of temporary files")
            
    except Exception as e:
        logger.error(f"Error during temp file cleanup: {str(e)}")

def get_temp_dir_size(temp_dir: str) -> int:
    """
    Get the total size of files in a temporary directory.
    
    Args:
        temp_dir: Directory to check
        
    Returns:
        int: Total size in bytes
    """
    try:
        total_size = 0
        temp_path = Path(temp_dir)
        
        if temp_path.exists():
            for file_path in temp_path.glob("*"):
                try:
                    total_size += file_path.stat().st_size
                except Exception:
                    continue
                    
        return total_size
        
    except Exception as e:
        logger.error(f"Error getting temp directory size: {str(e)}")
        return 0

def monitor_disk_space(path: str, callback=None) -> None:
    """
    Continuously monitor disk space and trigger cleanup when needed.
    
    Args:
        path: Path to monitor
        callback: Optional callback function when disk space is low
    """
    while True:
        try:
            _, free_bytes, usage_percent = get_disk_usage(path)
            
            if usage_percent > TEMP_DIR_CLEANUP_THRESHOLD:
                cleanup_temp_files(path)
                
            if free_bytes < MIN_FREE_SPACE_BYTES and callback:
                callback(free_bytes, usage_percent)
                
        except Exception as e:
            logger.error(f"Error monitoring disk space: {str(e)}")
            
        time.sleep(DISK_CHECK_INTERVAL)
