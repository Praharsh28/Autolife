"""Helper functions and classes for testing the media subtitle processing application."""

import os
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Union

import pytest
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QWidget

class UITestHelper:
    """Helper class for UI testing."""
    
    @staticmethod
    def wait_for(widget: QWidget, timeout: int = 1000):
        """Wait for widget to process events."""
        QTest.qWait(timeout)
        
    @staticmethod
    def click_button(button: QWidget):
        """Simulate button click."""
        QTest.mouseClick(button, Qt.LeftButton)
        
    @staticmethod
    def enter_text(widget: QWidget, text: str):
        """Enter text into widget."""
        widget.setFocus()
        QTest.keyClicks(widget, text)
        
    @staticmethod
    def select_item(widget: QWidget, index: int):
        """Select item at index in list/combo widget."""
        widget.setCurrentIndex(index)
        
    @staticmethod
    def drag_and_drop(source: QWidget, target: QWidget, data: str):
        """Simulate drag and drop operation."""
        mime_data = source.mimeData()
        mime_data.setText(data)
        target.dropEvent(mime_data)

class SubtitleTestHelper:
    """Helper class for subtitle testing."""
    
    @staticmethod
    def create_subtitle(start: float, duration: float, text: str) -> Dict:
        """Create a subtitle entry."""
        return {
            'start_time': start,
            'duration': duration,
            'text': text
        }
    
    @staticmethod
    def create_subtitle_file(subtitles: List[Dict], format: str = 'srt') -> Path:
        """Create a temporary subtitle file."""
        content = ''
        if format == 'srt':
            for i, sub in enumerate(subtitles, 1):
                start = SubtitleTestHelper._format_time(sub['start_time'])
                end = SubtitleTestHelper._format_time(sub['start_time'] + sub['duration'])
                content += f"{i}\n{start} --> {end}\n{sub['text']}\n\n"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix=f'.{format}', delete=False) as f:
            f.write(content)
            return Path(f.name)
    
    @staticmethod
    def _format_time(seconds: float) -> str:
        """Format time for subtitle file."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:06.3f}".replace('.', ',')

class MediaTestHelper:
    """Helper class for media file testing."""
    
    @staticmethod
    def create_dummy_video(duration: int = 10) -> Path:
        """Create a dummy video file for testing."""
        import numpy as np
        import cv2
        
        # Create a temporary file
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as f:
            filename = f.name
            
        # Create video
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(filename, fourcc, 30.0, (640,480))
        
        # Generate frames
        for _ in range(duration * 30):  # 30 fps
            frame = np.zeros((480,640,3), np.uint8)
            out.write(frame)
            
        out.release()
        return Path(filename)
    
    @staticmethod
    def create_dummy_audio(duration: int = 10) -> Path:
        """Create a dummy audio file for testing."""
        import numpy as np
        from scipy.io import wavfile
        
        # Create audio data
        sample_rate = 44100
        t = np.linspace(0, duration, duration * sample_rate)
        data = np.sin(2*np.pi*440*t)  # 440 Hz sine wave
        
        # Save to file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            wavfile.write(f.name, sample_rate, data.astype(np.float32))
            return Path(f.name)

class BatchTestHelper:
    """Helper class for batch processing tests."""
    
    @staticmethod
    def create_batch_files(num_files: int, 
                          file_type: str = 'video',
                          duration: int = 10) -> List[Path]:
        """Create multiple media files for batch testing."""
        files = []
        for _ in range(num_files):
            if file_type == 'video':
                files.append(MediaTestHelper.create_dummy_video(duration))
            elif file_type == 'audio':
                files.append(MediaTestHelper.create_dummy_audio(duration))
        return files
    
    @staticmethod
    def cleanup_batch_files(files: List[Path]):
        """Clean up temporary batch files."""
        for file in files:
            try:
                file.unlink()
            except OSError:
                pass

@pytest.fixture
def ui_helper():
    """Provide UI test helper."""
    return UITestHelper()

@pytest.fixture
def subtitle_helper():
    """Provide subtitle test helper."""
    return SubtitleTestHelper()

@pytest.fixture
def media_helper():
    """Provide media test helper."""
    return MediaTestHelper()

@pytest.fixture
def batch_helper():
    """Provide batch test helper."""
    return BatchTestHelper()
