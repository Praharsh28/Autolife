"""Test configuration and fixtures for the media subtitle processing application."""

import os
import platform
import pytest
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
import sys
import tempfile
from pathlib import Path
import shutil
import wave
import struct
import torch
import threading

# Ensure Qt runs in offscreen mode for CI
os.environ["QT_QPA_PLATFORM"] = "offscreen"

# Global fixtures
@pytest.fixture(scope="session")
def qapp():
    """Create a Qt application instance for the test session."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
        # Enable high DPI scaling
        app.setAttribute(Qt.AA_EnableHighDpiScaling)
        app.setAttribute(Qt.AA_UseHighDpiPixmaps)
    return app

# Global test configurations
pytest.GPU_AVAILABLE = torch.cuda.is_available()

@pytest.fixture(scope="session", autouse=True)
def setup_test_env():
    """Set up test environment variables."""
    os.environ["TESTING"] = "1"
    os.environ["HUGGINGFACE_API_TOKEN"] = "dummy_token"
    yield
    os.environ.pop("TESTING", None)
    os.environ.pop("HUGGINGFACE_API_TOKEN", None)

@pytest.fixture(scope="session")
def test_dir():
    """Create and return a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)

@pytest.fixture(autouse=True)
def cleanup_threads():
    """Clean up any threads created during tests."""
    yield
    for thread in threading.enumerate():
        if isinstance(thread, threading.Thread):
            thread.join()

# Helper fixtures for media and subtitle testing
@pytest.fixture
def media_helper(test_dir):
    """Helper fixture for creating test media files."""
    class MediaHelper:
        def create_dummy_video(self, duration=5, fps=30, size=(640, 480)):
            """Create a dummy video file for testing."""
            video_path = test_dir / f"test_video_{duration}s.mp4"
            # Create a minimal valid MP4 file
            with open(video_path, 'wb') as f:
                f.write(b'\x00' * 1024)  # Minimal valid MP4 header
            return str(video_path)

        def create_dummy_audio(self, duration=5, sample_rate=44100, channels=1):
            """Create a dummy WAV file for testing."""
            audio_path = test_dir / f"test_audio_{duration}s.wav"
            
            # Create a WAV file with sine wave
            with wave.open(str(audio_path), 'w') as wav_file:
                wav_file.setnchannels(channels)
                wav_file.setsampwidth(2)  # 2 bytes per sample
                wav_file.setframerate(sample_rate)
                
                # Generate simple sine wave
                for i in range(duration * sample_rate):
                    value = int(32767.0 * 0.5)  # Constant value for simplicity
                    data = struct.pack('<h', value)
                    wav_file.writeframes(data * channels)
            
            return str(audio_path)
    
    return MediaHelper()

@pytest.fixture
def subtitle_helper(test_dir):
    """Helper fixture for subtitle testing."""
    class SubtitleHelper:
        def create_subtitle(self, start_time=0, duration=1, text="Test subtitle"):
            """Create a test subtitle entry."""
            return {
                'start_time': start_time,
                'end_time': start_time + duration,
                'text': text
            }
        
        def create_srt_file(self, subtitles=None):
            """Create a test SRT file."""
            if subtitles is None:
                subtitles = [self.create_subtitle()]
            
            srt_path = test_dir / "test.srt"
            with open(srt_path, 'w', encoding='utf-8') as f:
                for i, sub in enumerate(subtitles, 1):
                    f.write(f"{i}\n")
                    f.write(f"{self._format_time(sub['start_time'])} --> {self._format_time(sub['end_time'])}\n")
                    f.write(f"{sub['text']}\n\n")
            return str(srt_path)
        
        def _format_time(self, seconds):
            """Format time in SRT format."""
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            seconds = seconds % 60
            msec = int((seconds % 1) * 1000)
            return f"{hours:02d}:{minutes:02d}:{int(seconds):02d},{msec:03d}"
    
    return SubtitleHelper()

@pytest.fixture
def ui_helper(qapp, qtbot):
    """Helper fixture for UI testing."""
    class UIHelper:
        def wait_for(self, widget, timeout=1000):
            """Wait for widget to process events."""
            qtbot.wait(timeout)
        
        def click_button(self, button):
            """Simulate button click."""
            qtbot.mouseClick(button, Qt.LeftButton)
        
        def enter_text(self, widget, text):
            """Enter text into widget."""
            widget.setFocus()
            qtbot.keyClicks(widget, text)
        
        def select_item(self, widget, index):
            """Select item at index in list/combo widget."""
            widget.setCurrentIndex(index)
        
        def drag_and_drop(self, source, target, data):
            """Simulate drag and drop operation."""
            mime_data = source.mimeData()
            mime_data.setText(data)
            target.dropEvent(mime_data)
    
    return UIHelper()

@pytest.fixture
def batch_helper(test_dir, media_helper):
    """Helper for batch processing tests."""
    class BatchHelper:
        def create_batch_files(self, num_files=3, file_type='video', duration=5):
            """Create multiple media files for batch testing."""
            files = []
            for i in range(num_files):
                if file_type == 'video':
                    file_path = media_helper.create_dummy_video(duration=duration)
                else:
                    file_path = media_helper.create_dummy_audio(duration=duration)
                files.append(file_path)
            return files
        
        def cleanup_batch_files(self, files):
            """Clean up temporary batch files."""
            for file_path in files:
                try:
                    os.remove(file_path)
                except OSError:
                    pass
    
    return BatchHelper()

def pytest_configure(config):
    """Configure custom markers."""
    config.addinivalue_line("markers", "slow: marks tests as slow")
    config.addinivalue_line("markers", "gpu: marks tests that require GPU")
    config.addinivalue_line("markers", "benchmark: marks performance benchmark tests")
    config.addinivalue_line("markers", "integration: marks integration tests")
    config.addinivalue_line("markers", "ui: marks UI tests")
    config.addinivalue_line("markers", "network: marks tests that require network access")
    config.addinivalue_line("markers", "translation: marks translation-related tests")
    config.addinivalue_line("markers", "media: marks media processing tests")
    config.addinivalue_line("markers", "batch: marks batch processing tests")
    config.addinivalue_line("markers", "worker: marks worker thread tests")
    config.addinivalue_line("markers", "subtitle: marks subtitle-related tests")

def pytest_runtest_setup(item):
    """Skip tests based on environment conditions."""
    for marker in item.iter_markers():
        if marker.name == 'gpu' and not pytest.GPU_AVAILABLE:
            pytest.skip("Test requires GPU")
        elif marker.name == 'network' and _is_offline():
            pytest.skip("Test requires network access")

def _has_gpu():
    """Check if GPU is available."""
    return torch.cuda.is_available()

def _is_offline():
    """Check if network is available."""
    import socket
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=1)
        return False
    except OSError:
        return True
