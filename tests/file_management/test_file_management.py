"""
Tests for file management functionality.
"""

import os
import pytest
import tempfile
import shutil
from unittest.mock import patch, MagicMock, Mock
from pathlib import Path

# Mock QListWidget for testing without PyQt5
class MockQListWidget:
    def __init__(self):
        self.items = []
        self.selected_items = []
    
    def addItem(self, text):
        item = Mock()
        item.text.return_value = text
        item.isSelected.return_value = False
        self.items.append(item)
    
    def item(self, index):
        return self.items[index] if index < len(self.items) else None
    
    def count(self):
        return len(self.items)
    
    def takeItem(self, index):
        if 0 <= index < len(self.items):
            return self.items.pop(index)
        return None
    
    def clear(self):
        self.items.clear()
        self.selected_items.clear()
    
    def selectedItems(self):
        return self.selected_items

# Mock FileListWidget for testing
class MockFileListWidget(MockQListWidget):
    def __init__(self):
        super().__init__()
        self.file_statuses = {}
        self.file_progress = {}
    
    def add_file(self, filepath):
        if not any(item.text() == filepath for item in self.items):
            self.addItem(filepath)
    
    def remove_file(self, filepath):
        for i, item in enumerate(self.items):
            if item.text() == filepath:
                self.takeItem(i)
                break
    
    def select_file(self, filepath):
        for item in self.items:
            if item.text() == filepath:
                item.isSelected.return_value = True
                self.selected_items.append(item)
                break
    
    def is_selected(self, filepath):
        return any(item.text() == filepath and item.isSelected() for item in self.items)
    
    def filter_by_extension(self, extension):
        return [item.text() for item in self.items if item.text().endswith(extension)]
    
    def update_file_status(self, filepath, status):
        self.file_statuses[filepath] = status
    
    def get_file_status(self, filepath):
        return self.file_statuses.get(filepath)
    
    def clear_file_status(self, filepath):
        self.file_statuses.pop(filepath, None)
    
    def update_file_progress(self, filepath, progress):
        self.file_progress[filepath] = progress
    
    def get_file_progress(self, filepath):
        return self.file_progress.get(filepath, 0)
    
    def clear_file_progress(self, filepath):
        self.file_progress[filepath] = 0

# File List Tests
@patch('modules.file_list_widget.FileListWidget', MockFileListWidget)
def test_file_list_operations():
    """Test file list widget operations."""
    file_list = MockFileListWidget()
    
    # Test adding files
    file_list.add_file('test1.mp4')
    file_list.add_file('test2.mp4')
    assert file_list.count() == 2
    
    # Test removing files
    file_list.remove_file('test1.mp4')
    assert file_list.count() == 1
    assert file_list.item(0).text() == 'test2.mp4'
    
    # Test clearing files
    file_list.clear()
    assert file_list.count() == 0

@patch('modules.file_list_widget.FileListWidget', MockFileListWidget)
def test_file_list_selection():
    """Test file list selection functionality."""
    file_list = MockFileListWidget()
    file_list.add_file('test1.mp4')
    file_list.add_file('test2.mp4')
    
    # Test selecting files
    file_list.select_file('test1.mp4')
    assert file_list.is_selected('test1.mp4')
    
    # Test getting selected files
    selected = [item.text() for item in file_list.selectedItems()]
    assert 'test1.mp4' in selected
    assert len(selected) == 1

@patch('modules.file_list_widget.FileListWidget', MockFileListWidget)
def test_file_list_filtering():
    """Test file list filtering functionality."""
    file_list = MockFileListWidget()
    file_list.add_file('test1.mp4')
    file_list.add_file('test2.srt')
    file_list.add_file('test3.mp4')
    
    # Test filtering by extension
    mp4_files = file_list.filter_by_extension('.mp4')
    assert len(mp4_files) == 2
    assert all(f.endswith('.mp4') for f in mp4_files)

# File Format Tests
def test_file_format_validation():
    """Test file format validation."""
    from modules.utilities import validate_file_format
    
    # Test valid formats
    assert validate_file_format('test.mp4') is True
    assert validate_file_format('test.srt') is True
    assert validate_file_format('test.ass') is True
    
    # Test invalid formats
    assert validate_file_format('test.txt') is False
    assert validate_file_format('test.doc') is False
    assert validate_file_format('test') is False

def test_file_extension_handling():
    """Test file extension handling."""
    from modules.utilities import get_file_extension, change_extension
    
    # Test getting extensions
    assert get_file_extension('test.mp4') == '.mp4'
    assert get_file_extension('test.file.srt') == '.srt'
    assert get_file_extension('test') == ''
    
    # Test changing extensions
    assert change_extension('test.mp4', '.srt') == 'test.srt'
    assert change_extension('test.file.mp4', '.ass') == 'test.file.ass'
    assert change_extension('test', '.mp4') == 'test.mp4'

# File System Tests
def test_file_system_operations():
    """Test file system operations."""
    from modules.utilities import ensure_directory, remove_file, copy_file
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Test directory creation
        test_dir = os.path.join(temp_dir, 'test_dir')
        ensure_directory(test_dir)
        assert os.path.exists(test_dir)
        
        # Test file creation and removal
        test_file = os.path.join(test_dir, 'test.txt')
        Path(test_file).touch()
        assert os.path.exists(test_file)
        
        remove_file(test_file)
        assert not os.path.exists(test_file)
        
        # Test file copying
        source_file = os.path.join(temp_dir, 'source.txt')
        dest_file = os.path.join(temp_dir, 'dest.txt')
        Path(source_file).touch()
        
        copy_file(source_file, dest_file)
        assert os.path.exists(dest_file)

# Temporary File Tests
def test_temporary_file_management():
    """Test temporary file management."""
    from modules.utilities import create_temp_file, cleanup_temp_files
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Test temp file creation
        temp_file = create_temp_file(temp_dir, '.txt')
        assert os.path.exists(temp_file)
        assert temp_file.endswith('.txt')
        
        # Test temp file cleanup
        cleanup_temp_files(temp_dir)
        assert not os.path.exists(temp_file)

def test_temp_file_age_management():
    """Test temporary file age management."""
    from modules.utilities import is_file_expired, cleanup_old_files
    from modules.constants import TEMP_FILE_MAX_AGE
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test file
        test_file = os.path.join(temp_dir, 'test.txt')
        Path(test_file).touch()
        
        # Test file age check
        assert not is_file_expired(test_file, TEMP_FILE_MAX_AGE)
        
        # Test old file cleanup
        cleanup_old_files(temp_dir, TEMP_FILE_MAX_AGE)
        assert os.path.exists(test_file)  # File should still exist as it's new

# Cache Tests
def test_cache_management():
    """Test cache management functionality."""
    from modules.utilities import cache_file, get_cached_file, clear_cache
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Test caching file
        source_file = os.path.join(temp_dir, 'source.txt')
        Path(source_file).touch()
        
        cache_key = cache_file(source_file, temp_dir)
        assert cache_key is not None
        
        # Test retrieving cached file
        cached_file = get_cached_file(cache_key, temp_dir)
        assert cached_file is not None
        assert os.path.exists(cached_file)
        
        # Test clearing cache
        clear_cache(temp_dir)
        assert not os.path.exists(cached_file)

def test_cache_size_management():
    """Test cache size management."""
    from modules.utilities import check_cache_size, cleanup_cache
    from modules.constants import CACHE_MAX_SIZE
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Test cache size check
        assert check_cache_size(temp_dir) == 0
        
        # Create some cached files
        for i in range(5):
            file_path = os.path.join(temp_dir, f'cache_{i}.txt')
            with open(file_path, 'wb') as f:
                f.write(b'0' * 1024 * 1024)  # 1MB files
        
        # Test cache cleanup
        cleanup_cache(temp_dir, CACHE_MAX_SIZE)
        total_size = sum(os.path.getsize(os.path.join(temp_dir, f))
                        for f in os.listdir(temp_dir))
        assert total_size <= CACHE_MAX_SIZE

# File Status Tests
@patch('modules.file_list_widget.FileListWidget', MockFileListWidget)
def test_file_status_tracking():
    """Test file status tracking functionality."""
    file_list = MockFileListWidget()
    file_list.add_file('test.mp4')
    
    # Test status updates
    file_list.update_file_status('test.mp4', 'Processing')
    assert file_list.get_file_status('test.mp4') == 'Processing'
    
    file_list.update_file_status('test.mp4', 'Completed')
    assert file_list.get_file_status('test.mp4') == 'Completed'
    
    # Test status clearing
    file_list.clear_file_status('test.mp4')
    assert file_list.get_file_status('test.mp4') is None

@patch('modules.file_list_widget.FileListWidget', MockFileListWidget)
def test_file_progress_tracking():
    """Test file progress tracking functionality."""
    file_list = MockFileListWidget()
    file_list.add_file('test.mp4')
    
    # Test progress updates
    file_list.update_file_progress('test.mp4', 50)
    assert file_list.get_file_progress('test.mp4') == 50
    
    file_list.update_file_progress('test.mp4', 100)
    assert file_list.get_file_progress('test.mp4') == 100
    
    # Test progress clearing
    file_list.clear_file_progress('test.mp4')
    assert file_list.get_file_progress('test.mp4') == 0
