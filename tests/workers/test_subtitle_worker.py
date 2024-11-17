"""Tests for the SubtitleWorker class."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os
from pathlib import Path
import torch
from PyQt5.QtCore import QThread

from modules.workers.subtitle_worker import SubtitleWorker
from modules.workers.worker_signals import WorkerSignals
from modules.network_utils import RetryableError, NonRetryableError
from modules.streaming_utils import StreamingError
from modules.language_utils import LanguageError

@pytest.fixture
def mock_api_session():
    """Mock API session for testing."""
    with patch('modules.workers.subtitle_worker.APISession') as mock:
        session = Mock()
        mock.return_value = session
        yield session

@pytest.fixture
def mock_audio_streamer():
    """Mock audio streamer for testing."""
    with patch('modules.workers.subtitle_worker.AudioStreamer') as mock:
        streamer = Mock()
        mock.return_value = streamer
        yield streamer

@pytest.fixture
def mock_translation_manager():
    """Mock translation manager for testing."""
    with patch('modules.workers.subtitle_worker.TranslationManager') as mock:
        manager = Mock()
        mock.return_value = manager
        yield manager

@pytest.fixture
def mock_cache():
    """Mock cache for testing."""
    with patch('modules.workers.subtitle_worker.Cache') as mock:
        cache = Mock()
        mock.return_value = cache
        yield cache

@pytest.fixture
def worker(tmp_path):
    """Create a SubtitleWorker instance for testing."""
    test_files = [str(tmp_path / f"test_audio_{i}.wav") for i in range(3)]
    for file in test_files:
        Path(file).touch()
    worker = SubtitleWorker(test_files)
    yield worker
    worker.wait()
    worker.deleteLater()

class TestSubtitleWorker:
    """Test cases for SubtitleWorker class."""

    @pytest.mark.worker
    def test_worker_initialization(self, worker):
        """Test worker initialization."""
        assert isinstance(worker, QThread)
        assert isinstance(worker.signals, WorkerSignals)
        assert worker.batch_size == 3
        assert worker._active_tasks == 0

    @pytest.mark.worker
    def test_memory_management(self, worker):
        """Test memory management functions."""
        # Test memory check
        assert worker._check_memory_usage() is True
        
        # Test resource allocation
        with worker._task_semaphore:
            assert worker._active_tasks == 0
            worker._active_tasks += 1
            assert worker._active_tasks == 1

    @pytest.mark.worker
    def test_signal_emission(self, worker, qtbot):
        """Test signal emissions."""
        # Setup signal tracking
        progress_signal = Mock()
        error_signal = Mock()
        finished_signal = Mock()
        
        worker.signals.progress.connect(progress_signal)
        worker.signals.error.connect(error_signal)
        worker.signals.finished.connect(finished_signal)
        
        # Simulate progress
        worker.signals.progress.emit(50)
        assert progress_signal.called
        assert progress_signal.call_args[0][0] == 50

    @pytest.mark.worker
    @pytest.mark.asyncio
    async def test_subtitle_generation(self, worker, mock_api_session, mock_audio_streamer, qtbot):
        """Test subtitle generation process."""
        # Mock successful API response
        mock_api_session.process_audio.return_value = {
            'text': 'Test subtitle text',
            'segments': [
                {'start': 0, 'end': 2, 'text': 'Test'},
                {'start': 2, 'end': 4, 'text': 'subtitle'},
                {'start': 4, 'end': 6, 'text': 'text'}
            ]
        }
        
        # Start worker
        with qtbot.waitSignal(worker.signals.finished, timeout=1000):
            worker.start()

        # Verify API calls
        assert mock_api_session.process_audio.called
        assert mock_audio_streamer.stream.called

    @pytest.mark.worker
    def test_error_handling(self, worker, mock_api_session, qtbot):
        """Test error handling scenarios."""
        # Test network error
        mock_api_session.process_audio.side_effect = RetryableError("Network error")
        
        error_signal = Mock()
        worker.signals.error.connect(error_signal)
        
        with qtbot.waitSignal(worker.signals.error, timeout=1000):
            worker.start()
        
        assert error_signal.called
        assert "Network error" in str(error_signal.call_args[0][0])

    @pytest.mark.worker
    @pytest.mark.gpu
    def test_gpu_processing(self, worker):
        """Test GPU-specific processing."""
        if not torch.cuda.is_available():
            pytest.skip("GPU not available")
            
        # Test GPU memory management
        assert worker._check_gpu_memory() is True
        
        # Test GPU resource allocation
        with worker._gpu_lock:
            assert worker._gpu_in_use is False
            worker._gpu_in_use = True
            assert worker._gpu_in_use is True

    @pytest.mark.worker
    def test_batch_processing(self, worker, mock_api_session, mock_audio_streamer, qtbot):
        """Test batch processing functionality."""
        # Setup mock responses for batch processing
        mock_api_session.process_audio.side_effect = [
            {'text': f'Test {i}', 'segments': []} for i in range(3)
        ]
        
        progress_signal = Mock()
        worker.signals.progress.connect(progress_signal)
        
        with qtbot.waitSignal(worker.signals.finished, timeout=1000):
            worker.start()
        
        # Verify batch processing
        assert mock_api_session.process_audio.call_count == 3
        assert progress_signal.call_count > 0

    @pytest.mark.worker
    def test_resource_cleanup(self, worker, mock_audio_streamer, qtbot):
        """Test resource cleanup on worker completion."""
        cleanup_signal = Mock()
        worker.signals.cleanup.connect(cleanup_signal)
        
        with qtbot.waitSignal(worker.signals.cleanup, timeout=1000):
            worker.start()
            worker.wait()
        
        assert cleanup_signal.called
        assert worker._active_tasks == 0
        assert not worker._gpu_in_use

    @pytest.mark.worker
    def test_cancellation(self, worker, mock_api_session, qtbot):
        """Test worker cancellation."""
        cancel_signal = Mock()
        worker.signals.cancelled.connect(cancel_signal)
        
        # Start and immediately cancel
        worker.start()
        worker.cancel()
        
        with qtbot.waitSignal(worker.signals.cancelled, timeout=1000):
            worker.wait()
        
        assert cancel_signal.called
        assert worker._active_tasks == 0
