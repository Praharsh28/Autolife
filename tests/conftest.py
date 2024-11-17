"""Test configuration and fixtures for the media subtitle processing application."""

import os
import platform
import pytest
from PyQt5.QtWidgets import QApplication
import sys
import tempfile
from pathlib import Path
import shutil
import wave
import struct
import torch

# Global fixtures
@pytest.fixture(scope="session")
def qapp():
    """Create a Qt application instance for the test session."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app

# Global test configurations
pytest.GPU_AVAILABLE = torch.cuda.is_available()

@pytest.fixture(scope="session")
def test_dir():
    """Create and return a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)

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
                num_samples = int(duration * sample_rate)
                for i in range(num_samples):
                    value = int(32767.0 * 0.5)  # Constant value for simplicity
                    data = struct.pack('<h', value)
                    wav_file.writeframes(data * channels)
            
            return str(audio_path)
            
        def cleanup(self):
            """Clean up test media files."""
            pass
    
    helper = MediaHelper()
    yield helper
    helper.cleanup()

@pytest.fixture
def subtitle_helper(test_dir):
    """Helper fixture for creating test subtitle files."""
    class SubtitleHelper:
        def create_subtitle(self, start_time, duration, text):
            """Create a subtitle entry."""
            return {
                'start_time': start_time,
                'duration': duration,
                'text': text
            }
            
        def create_subtitle_file(self, subtitles, format='srt'):
            """Create a subtitle file with given entries."""
            subtitle_path = test_dir / f"test_subtitles.{format}"
            with open(subtitle_path, 'w', encoding='utf-8') as f:
                for i, sub in enumerate(subtitles, 1):
                    f.write(f"{i}\n")
                    start = self._format_time(sub['start_time'])
                    end = self._format_time(sub['start_time'] + sub['duration'])
                    f.write(f"{start} --> {end}\n")
                    f.write(f"{sub['text']}\n\n")
            return str(subtitle_path)
            
        def _format_time(self, seconds):
            """Format time in SRT format (HH:MM:SS,mmm)."""
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            seconds = seconds % 60
            return f"{hours:02d}:{minutes:02d}:{seconds:06.3f}".replace('.', ',')
            
        def cleanup(self):
            """Clean up test subtitle files."""
            pass
    
    helper = SubtitleHelper()
    yield helper
    helper.cleanup()

@pytest.fixture
def ui_helper(qapp, qtbot):
    """Helper fixture for UI testing."""
    class UIHelper:
        def wait_for_signal(self, signal, timeout=1000):
            """Wait for a Qt signal to be emitted."""
            from PyQt5.QtTest import QSignalSpy
            spy = QSignalSpy(signal)
            return spy.wait(timeout)
            
        def simulate_click(self, widget):
            """Simulate a mouse click on a widget."""
            from PyQt5.QtCore import Qt
            from PyQt5.QtTest import QTest
            QTest.mouseClick(widget, Qt.LeftButton)
            
        def wait_for(self, widget, timeout=1000):
            """Wait for widget to be ready."""
            qtbot.waitForWindowShown(widget)
            qtbot.wait(timeout)
            
        def click_button(self, button):
            """Simulate button click."""
            qtbot.mouseClick(button, Qt.LeftButton)
            
        def enter_text(self, widget, text):
            """Enter text into widget."""
            qtbot.keyClicks(widget, text)
    
    return UIHelper()

@pytest.fixture
def batch_helper(test_dir, media_helper):
    """Helper for batch processing tests."""
    class BatchHelper:
        def create_batch_files(self, count, type='video', **kwargs):
            """Create multiple test files for batch processing."""
            files = []
            for i in range(count):
                if type == 'video':
                    files.append(media_helper.create_dummy_video(**kwargs))
                elif type == 'audio':
                    files.append(media_helper.create_dummy_audio(**kwargs))
            return files
            
        def cleanup_batch_files(self, files):
            """Clean up batch test files."""
            for file in files:
                try:
                    Path(file).unlink()
                except:
                    pass
                    
    return BatchHelper()

# Platform-specific markers
def pytest_collection_modifyitems(items):
    """Add platform-specific markers to tests."""
    for item in items:
        # Add platform markers
        if platform.system() == "Windows":
            item.add_marker(pytest.mark.windows)
        elif platform.system() == "Linux":
            item.add_marker(pytest.mark.linux)
            
        # Add slow marker to tests that historically take longer
        if "batch" in item.keywords or "ffmpeg" in item.keywords:
            item.add_marker(pytest.mark.slow)
            
        # Add serial marker to tests that can't run in parallel
        if "gpu" in item.keywords or "ffmpeg" in item.keywords:
            item.add_marker(pytest.mark.serial)

# Skip markers based on environment
def pytest_runtest_setup(item):
    """Skip tests based on environment conditions."""
    # Skip GPU tests if no GPU available
    if "gpu" in item.keywords and not pytest.GPU_AVAILABLE:
        pytest.skip("Test requires GPU")
        
    # Skip network tests if offline mode
    if "network" in item.keywords and _is_offline():
        pytest.skip("Test requires network connectivity")
        
    # Skip platform-specific tests
    if "windows" in item.keywords and platform.system() != "Windows":
        pytest.skip("Test requires Windows")
    if "linux" in item.keywords and platform.system() != "Linux":
        pytest.skip("Test requires Linux")

# Test categories for better organization
def pytest_configure(config):
    """Configure custom markers."""
    config.addinivalue_line("markers", "subtitle: Tests for subtitle processing")
    config.addinivalue_line("markers", "translation: Tests for translation features")
    config.addinivalue_line("markers", "media: Tests for media file operations")
    config.addinivalue_line("markers", "batch: Tests for batch processing")
    config.addinivalue_line("markers", "preview: Tests for subtitle preview")
    config.addinivalue_line("markers", "gpu: Tests requiring GPU")
    config.addinivalue_line("markers", "network: Tests requiring network")
    config.addinivalue_line("markers", "ffmpeg: Tests using FFmpeg")
    config.addinivalue_line("markers", "torch: Tests using PyTorch")
    config.addinivalue_line("markers", "qt: Tests using PyQt")
    config.addinivalue_line("markers", "visual: Tests for visual appearance")
    config.addinivalue_line("markers", "error: Tests for error conditions")
    config.addinivalue_line("markers", "boundary: Tests for boundary conditions")
    config.addinivalue_line("markers", "state: Tests for state management")
    config.addinivalue_line("markers", "config: Tests for configuration")
    config.addinivalue_line("markers", "cache: Tests for caching")
    config.addinivalue_line("markers", "windows: Windows-specific tests")
    config.addinivalue_line("markers", "linux: Linux-specific tests")
    config.addinivalue_line("markers", "cross_platform: Cross-platform tests")

# Helper functions
def _has_gpu():
    """Check if GPU is available."""
    try:
        import torch
        return torch.cuda.is_available()
    except ImportError:
        return False

def _is_offline():
    """Check if network is available."""
    import socket
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=1)
        return False
    except OSError:
        return True

# Common test data
@pytest.fixture
def sample_subtitle_data():
    """Provide sample subtitle data for tests."""
    return {
        'original': [
            {'start_time': 0.0, 'duration': 2.0, 'text': 'Hello'},
            {'start_time': 2.5, 'duration': 1.5, 'text': 'World'}
        ],
        'translated': {
            'es': [
                {'start_time': 0.0, 'duration': 2.0, 'text': 'Hola'},
                {'start_time': 2.5, 'duration': 1.5, 'text': 'Mundo'}
            ]
        }
    }

@pytest.fixture
def temp_media_dir(tmp_path):
    """Create a temporary directory for media files."""
    media_dir = tmp_path / "media"
    media_dir.mkdir()
    return media_dir

@pytest.fixture
def mock_ffmpeg(mocker):
    """Mock FFmpeg operations for testing."""
    return mocker.patch('modules.ffmpeg_utils.FFmpeg')
