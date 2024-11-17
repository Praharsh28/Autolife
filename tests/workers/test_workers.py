"""
Tests for worker thread functionality and resource management.
"""

import os
import pytest
from unittest.mock import patch, MagicMock, call
from PyQt5.QtCore import QThread

# Subtitle Worker Tests
def test_subtitle_worker_initialization():
    """Test subtitle worker initialization."""
    from modules.workers.subtitle_worker import SubtitleWorker
    
    files = ['test1.mp4', 'test2.mp4']
    worker = SubtitleWorker(files, batch_size=2)
    
    assert worker.files == files
    assert worker.batch_size == 2
    assert isinstance(worker, QThread)
    assert hasattr(worker, 'signals')

def test_subtitle_worker_signals():
    """Test subtitle worker signal emission."""
    from modules.workers.subtitle_worker import SubtitleWorker
    
    worker = SubtitleWorker(['test.mp4'])
    
    # Test progress signal
    with patch.object(worker.signals.progress, 'emit') as mock_progress:
        worker.update_progress(50)
        mock_progress.assert_called_once_with(50)
    
    # Test error signal
    with patch.object(worker.signals.error, 'emit') as mock_error:
        worker.handle_error("Test error")
        mock_error.assert_called_once_with("Test error")
    
    # Test completion signal
    with patch.object(worker.signals.finished, 'emit') as mock_finished:
        worker.process_completed()
        mock_finished.assert_called_once()

def test_subtitle_worker_batch_processing():
    """Test batch processing functionality."""
    from modules.workers.subtitle_worker import SubtitleWorker
    
    files = ['test1.mp4', 'test2.mp4', 'test3.mp4']
    worker = SubtitleWorker(files, batch_size=2)
    
    with patch.object(worker, 'process_file') as mock_process:
        worker.run()
        assert mock_process.call_count == 3
        mock_process.assert_has_calls([
            call('test1.mp4'),
            call('test2.mp4'),
            call('test3.mp4')
        ])

# SRT to ASS Worker Tests
def test_srt_to_ass_worker_initialization():
    """Test SRT to ASS worker initialization."""
    from modules.workers.srt_to_ass_worker import SrtToAssWorker
    
    files = ['test1.srt', 'test2.srt']
    worker = SrtToAssWorker(files, template_file='template.ass')
    
    assert worker.files == files
    assert worker.template_file == 'template.ass'
    assert isinstance(worker, QThread)
    assert hasattr(worker, 'signals')

def test_srt_to_ass_worker_signals():
    """Test SRT to ASS worker signal emission."""
    from modules.workers.srt_to_ass_worker import SrtToAssWorker
    
    worker = SrtToAssWorker(['test.srt'])
    
    # Test progress signal
    with patch.object(worker.signals.progress, 'emit') as mock_progress:
        worker.update_progress(50)
        mock_progress.assert_called_once_with(50)
    
    # Test error signal
    with patch.object(worker.signals.error, 'emit') as mock_error:
        worker.handle_error("Test error")
        mock_error.assert_called_once_with("Test error")
    
    # Test completion signal
    with patch.object(worker.signals.finished, 'emit') as mock_finished:
        worker.process_completed()
        mock_finished.assert_called_once()

def test_srt_to_ass_style_application():
    """Test style application in SRT to ASS conversion."""
    from modules.workers.srt_to_ass_worker import SrtToAssWorker
    
    worker = SrtToAssWorker(['test.srt'], style_name="TestStyle")
    with patch('builtins.open', create=True) as mock_open:
        mock_open.return_value.__enter__.return_value.read.return_value = "Test content"
        worker.apply_style('test.srt', 'test.ass')
        mock_open.assert_called()

# Resource Management Tests
def test_worker_resource_allocation():
    """Test worker resource allocation and limits."""
    from modules.workers.subtitle_worker import SubtitleWorker
    from modules.constants import MAX_MEMORY_PERCENT
    
    worker = SubtitleWorker(['test.mp4'])
    
    with patch('psutil.Process') as mock_process:
        # Test within limits
        mock_process.return_value.memory_percent.return_value = MAX_MEMORY_PERCENT - 10
        assert worker.check_memory_usage() is True
        
        # Test exceeding limits
        mock_process.return_value.memory_percent.return_value = MAX_MEMORY_PERCENT + 10
        with pytest.raises(MemoryError):
            worker.check_memory_usage()

def test_worker_resource_cleanup():
    """Test worker resource cleanup."""
    from modules.workers.subtitle_worker import SubtitleWorker
    
    worker = SubtitleWorker(['test.mp4'])
    
    with patch('os.remove') as mock_remove:
        with patch('os.path.exists', return_value=True):
            worker.cleanup_resources()
            mock_remove.assert_called()

def test_worker_concurrent_processing():
    """Test concurrent processing limits."""
    from modules.workers.subtitle_worker import SubtitleWorker
    from modules.constants import MAX_CONCURRENT_TASKS
    
    files = [f'test{i}.mp4' for i in range(MAX_CONCURRENT_TASKS + 2)]
    worker = SubtitleWorker(files)
    
    with patch('threading.active_count') as mock_count:
        mock_count.return_value = MAX_CONCURRENT_TASKS - 1
        assert worker.can_start_new_task() is True
        
        mock_count.return_value = MAX_CONCURRENT_TASKS + 1
        assert worker.can_start_new_task() is False

# Progress Tracking Tests
def test_worker_progress_tracking():
    """Test worker progress tracking."""
    from modules.workers.subtitle_worker import SubtitleWorker
    
    worker = SubtitleWorker(['test1.mp4', 'test2.mp4'])
    
    with patch.object(worker.signals.progress, 'emit') as mock_progress:
        worker.update_progress(0)  # Start
        worker.update_progress(50)  # Middle
        worker.update_progress(100)  # Complete
        
        assert mock_progress.call_count == 3
        mock_progress.assert_has_calls([
            call(0),
            call(50),
            call(100)
        ])

def test_worker_file_progress():
    """Test individual file progress tracking."""
    from modules.workers.subtitle_worker import SubtitleWorker
    
    worker = SubtitleWorker(['test1.mp4', 'test2.mp4'])
    
    with patch.object(worker.signals.file_completed, 'emit') as mock_file_completed:
        worker.file_completed('test1.mp4')
        mock_file_completed.assert_called_once_with('test1.mp4')

# State Management Tests
def test_worker_state_management():
    """Test worker state management."""
    from modules.workers.subtitle_worker import SubtitleWorker
    
    worker = SubtitleWorker(['test1.mp4', 'test2.mp4'])
    
    # Test state saving
    with patch('json.dump') as mock_dump:
        worker.save_state()
        mock_dump.assert_called_once()
    
    # Test state loading
    with patch('json.load') as mock_load:
        mock_load.return_value = {'files': ['test1.mp4'], 'current_index': 0}
        worker.load_state()
        mock_load.assert_called_once()

def test_worker_error_state():
    """Test worker error state handling."""
    from modules.workers.subtitle_worker import SubtitleWorker
    
    worker = SubtitleWorker(['test.mp4'])
    
    with patch.object(worker, 'save_state') as mock_save:
        with patch.object(worker, 'cleanup_resources') as mock_cleanup:
            worker.handle_error("Test error")
            mock_save.assert_called_once()
            mock_cleanup.assert_called_once()
