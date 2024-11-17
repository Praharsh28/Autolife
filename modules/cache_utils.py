"""
Cache utilities for efficient file and data caching.
"""

import os
import time
import json
import hashlib
import threading
from typing import Optional, Dict, Any, List, Tuple
from pathlib import Path
from datetime import datetime, timedelta
from .utilities import setup_logger
from .disk_utils import check_disk_space, estimate_space_needed
from .constants import (
    CACHE_DIR,
    CACHE_MAX_SIZE,
    CACHE_MAX_AGE,
    CACHE_CLEANUP_INTERVAL,
    CACHE_MIN_FREE_SPACE
)

logger = setup_logger('cache_utils')

class CacheError(Exception):
    """Base exception for cache-related errors."""
    pass

class Cache:
    """Thread-safe LRU cache implementation with disk persistence."""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """Ensure singleton instance."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize cache."""
        if not hasattr(self, 'initialized'):
            self.cache_dir = Path(CACHE_DIR)
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            self.metadata_file = self.cache_dir / 'metadata.json'
            self.metadata: Dict[str, Dict] = {}
            self.cleanup_thread = None
            self._load_metadata()
            self._start_cleanup_thread()
            self.initialized = True
    
    def _load_metadata(self):
        """Load cache metadata from disk."""
        try:
            if self.metadata_file.exists():
                with open(self.metadata_file, 'r') as f:
                    self.metadata = json.load(f)
        except Exception as e:
            logger.error(f"Error loading cache metadata: {str(e)}")
            self.metadata = {}
    
    def _save_metadata(self):
        """Save cache metadata to disk."""
        try:
            with open(self.metadata_file, 'w') as f:
                json.dump(self.metadata, f)
        except Exception as e:
            logger.error(f"Error saving cache metadata: {str(e)}")
    
    def _get_cache_key(self, file_path: str, params: Optional[Dict] = None) -> str:
        """
        Generate cache key from file path and optional parameters.
        
        Args:
            file_path: Path to file
            params: Optional parameters affecting processing
            
        Returns:
            str: Cache key
        """
        key_parts = [file_path]
        if params:
            key_parts.extend(f"{k}={v}" for k, v in sorted(params.items()))
        key_string = '|'.join(key_parts)
        return hashlib.sha256(key_string.encode()).hexdigest()
    
    def _get_cache_path(self, cache_key: str) -> Path:
        """Get path for cached file."""
        return self.cache_dir / cache_key
    
    def _update_metadata(self, cache_key: str, original_path: str, params: Optional[Dict] = None):
        """Update metadata for cached item."""
        self.metadata[cache_key] = {
            'original_path': original_path,
            'params': params or {},
            'last_access': datetime.now().isoformat(),
            'size': os.path.getsize(self._get_cache_path(cache_key))
        }
        self._save_metadata()
    
    def _cleanup_old_entries(self):
        """Clean up old cache entries."""
        try:
            current_time = datetime.now()
            total_size = 0
            entries_to_remove = []
            
            # Calculate total size and find old entries
            for key, data in self.metadata.items():
                cache_path = self._get_cache_path(key)
                if not cache_path.exists():
                    entries_to_remove.append(key)
                    continue
                
                last_access = datetime.fromisoformat(data['last_access'])
                age = current_time - last_access
                
                if age > timedelta(seconds=CACHE_MAX_AGE):
                    entries_to_remove.append(key)
                else:
                    total_size += data['size']
            
            # Remove old entries
            for key in entries_to_remove:
                self._remove_cache_entry(key)
            
            # Check total size
            while total_size > CACHE_MAX_SIZE:
                oldest_key = min(
                    self.metadata.keys(),
                    key=lambda k: datetime.fromisoformat(self.metadata[k]['last_access'])
                )
                self._remove_cache_entry(oldest_key)
                total_size = sum(data['size'] for data in self.metadata.values())
                
        except Exception as e:
            logger.error(f"Error during cache cleanup: {str(e)}")
    
    def _remove_cache_entry(self, cache_key: str):
        """Remove cache entry and its metadata."""
        try:
            cache_path = self._get_cache_path(cache_key)
            if cache_path.exists():
                cache_path.unlink()
            self.metadata.pop(cache_key, None)
            self._save_metadata()
        except Exception as e:
            logger.error(f"Error removing cache entry: {str(e)}")
    
    def _cleanup_loop(self):
        """Background cleanup loop."""
        while True:
            try:
                time.sleep(CACHE_CLEANUP_INTERVAL)
                self._cleanup_old_entries()
            except Exception as e:
                logger.error(f"Error in cleanup loop: {str(e)}")
    
    def _start_cleanup_thread(self):
        """Start background cleanup thread."""
        if not self.cleanup_thread or not self.cleanup_thread.is_alive():
            self.cleanup_thread = threading.Thread(
                target=self._cleanup_loop,
                daemon=True
            )
            self.cleanup_thread.start()
    
    def get(self, file_path: str, params: Optional[Dict] = None) -> Optional[str]:
        """
        Get cached file if available.
        
        Args:
            file_path: Original file path
            params: Optional parameters affecting processing
            
        Returns:
            Optional[str]: Path to cached file if available, None otherwise
        """
        try:
            cache_key = self._get_cache_key(file_path, params)
            cache_path = self._get_cache_path(cache_key)
            
            if cache_key in self.metadata and cache_path.exists():
                # Update last access time
                self._update_metadata(cache_key, file_path, params)
                return str(cache_path)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting cached file: {str(e)}")
            return None
    
    def put(
        self,
        file_path: str,
        data_path: str,
        params: Optional[Dict] = None
    ) -> Optional[str]:
        """
        Cache a file.
        
        Args:
            file_path: Original file path
            data_path: Path to data to cache
            params: Optional parameters affecting processing
            
        Returns:
            Optional[str]: Path to cached file if successful, None otherwise
        """
        try:
            # Check disk space
            if not check_disk_space(required_bytes=CACHE_MIN_FREE_SPACE):
                logger.warning("Insufficient disk space for caching")
                return None
            
            cache_key = self._get_cache_key(file_path, params)
            cache_path = self._get_cache_path(cache_key)
            
            # Copy file to cache
            with open(data_path, 'rb') as src, open(cache_path, 'wb') as dst:
                dst.write(src.read())
            
            # Update metadata
            self._update_metadata(cache_key, file_path, params)
            
            return str(cache_path)
            
        except Exception as e:
            logger.error(f"Error caching file: {str(e)}")
            return None
    
    def invalidate(self, file_path: str, params: Optional[Dict] = None):
        """
        Invalidate cached file.
        
        Args:
            file_path: Original file path
            params: Optional parameters affecting processing
        """
        try:
            cache_key = self._get_cache_key(file_path, params)
            self._remove_cache_entry(cache_key)
        except Exception as e:
            logger.error(f"Error invalidating cache entry: {str(e)}")
    
    def clear(self):
        """Clear entire cache."""
        try:
            for cache_key in list(self.metadata.keys()):
                self._remove_cache_entry(cache_key)
        except Exception as e:
            logger.error(f"Error clearing cache: {str(e)}")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dict[str, Any]: Cache statistics
        """
        try:
            total_size = sum(data['size'] for data in self.metadata.values())
            return {
                'entry_count': len(self.metadata),
                'total_size': total_size,
                'max_size': CACHE_MAX_SIZE,
                'cache_dir': str(self.cache_dir)
            }
        except Exception as e:
            logger.error(f"Error getting cache stats: {str(e)}")
            return {}
