"""Tests for the SrtToAssWorker class."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import tempfile
from pathlib import Path
import os
from PyQt5.QtCore import QThread

from modules.workers.srt_to_ass_worker import SrtToAssWorker
from modules.workers.worker_signals import WorkerSignals

@pytest.fixture
def sample_srt_content():
    """Create sample SRT content."""
    return """1
00:00:01,000 --> 00:00:04,000
First subtitle line
Second line

2
00:00:05,000 --> 00:00:07,000
Another subtitle
    """

@pytest.fixture
def sample_srt_file(tmp_path, sample_srt_content):
    """Create a sample SRT file."""
    srt_file = tmp_path / "test.srt"
    srt_file.write_text(sample_srt_content, encoding='utf-8')
    return str(srt_file)

@pytest.fixture
def worker(sample_srt_file):
    """Create a SrtToAssWorker instance."""
    worker = SrtToAssWorker(sample_srt_file)
    yield worker
    worker.wait()
    worker.deleteLater()

class TestSrtToAssWorker:
    """Test cases for SrtToAssWorker class."""

    @pytest.mark.worker
    def test_worker_initialization(self, worker):
        """Test worker initialization."""
        assert isinstance(worker, QThread)
        assert isinstance(worker.signals, WorkerSignals)
        assert worker.srt_file.endswith('.srt')
        assert not worker.cancelled

    @pytest.mark.worker
    def test_srt_parsing(self, worker, sample_srt_content):
        """Test SRT file parsing."""
        subtitles = worker._parse_srt()
        
        assert len(subtitles) == 2
        first_sub = subtitles[0]
        assert first_sub['start_time'] == 1.0
        assert first_sub['end_time'] == 4.0
        assert "First subtitle line" in first_sub['text']

    @pytest.mark.worker
    def test_ass_conversion(self, worker, tmp_path):
        """Test conversion from SRT to ASS format."""
        output_file = tmp_path / "output.ass"
        
        # Convert file
        subtitles = worker._parse_srt()
        worker._convert_to_ass(subtitles, str(output_file))
        
        # Verify ASS file content
        assert output_file.exists()
        content = output_file.read_text(encoding='utf-8')
        
        # Check ASS format sections
        assert "[Script Info]" in content
        assert "[V4+ Styles]" in content
        assert "[Events]" in content
        
        # Check subtitle content
        assert "First subtitle line" in content
        assert "Dialogue:" in content

    @pytest.mark.worker
    def test_style_generation(self, worker):
        """Test ASS style generation."""
        style = worker._generate_ass_style()
        
        # Check style properties
        assert "Style: Default," in style
        assert "Arial," in style  # Font name
        assert "48," in style     # Font size
        assert "&H00FFFFFF," in style  # Primary color (white)

    @pytest.mark.worker
    def test_progress_reporting(self, worker, qtbot):
        """Test progress signal emission."""
        progress_values = []
        worker.signals.progress.connect(lambda v: progress_values.append(v))
        
        with qtbot.waitSignal(worker.signals.finished, timeout=1000):
            worker.start()
        
        # Verify progress updates
        assert 0 in progress_values  # Start
        assert 100 in progress_values  # Completion

    @pytest.mark.worker
    def test_error_handling(self, worker, qtbot):
        """Test error handling scenarios."""
        # Test invalid SRT file
        worker.srt_file = "nonexistent.srt"
        
        error_signal = Mock()
        worker.signals.error.connect(error_signal)
        
        with qtbot.waitSignal(worker.signals.error, timeout=1000):
            worker.start()
        
        assert error_signal.called
        assert "File not found" in str(error_signal.call_args[0][0])

    @pytest.mark.worker
    def test_cancellation(self, worker, qtbot):
        """Test worker cancellation."""
        cancel_signal = Mock()
        worker.signals.cancelled.connect(cancel_signal)
        
        # Start and immediately cancel
        worker.start()
        worker.cancel()
        
        with qtbot.waitSignal(worker.signals.cancelled, timeout=1000):
            worker.wait()
        
        assert cancel_signal.called
        assert worker.cancelled

    @pytest.mark.worker
    def test_output_file_handling(self, worker, tmp_path):
        """Test output file handling."""
        # Test with existing output file
        output_file = tmp_path / "existing.ass"
        output_file.touch()
        
        with patch('modules.workers.srt_to_ass_worker.os.path.exists') as mock_exists:
            mock_exists.return_value = True
            
            # Should handle existing file
            worker._prepare_output_file(str(output_file))
            assert not worker.cancelled

    @pytest.mark.worker
    def test_subtitle_formatting(self, worker):
        """Test subtitle text formatting."""
        input_text = "First line\\NSecond line"
        formatted = worker._format_ass_text(input_text)
        
        # Check line breaks
        assert "\\N" in formatted
        assert not "\\n" in formatted
        
        # Check text cleanup
        assert not "  " in formatted  # No double spaces
        assert not formatted.startswith(" ")  # No leading spaces
        assert not formatted.endswith(" ")   # No trailing spaces

    @pytest.mark.worker
    def test_timing_conversion(self, worker):
        """Test timing format conversion."""
        # Test SRT to ASS time conversion
        srt_time = "00:01:30,500"
        ass_time = worker._convert_time_format(srt_time)
        
        assert "1:30.50" in ass_time
        
        # Test edge cases
        assert "0:00.00" in worker._convert_time_format("00:00:00,000")
        assert "9:59.99" in worker._convert_time_format("09:59:59,990")

    @pytest.mark.worker
    def test_batch_processing(self, tmp_path):
        """Test processing multiple files."""
        # Create multiple SRT files
        srt_files = []
        for i in range(3):
            srt_file = tmp_path / f"test{i}.srt"
            srt_file.write_text("1\n00:00:01,000 --> 00:00:04,000\nTest", encoding='utf-8')
            srt_files.append(str(srt_file))
        
        # Process all files
        completed = []
        failed = []
        
        for srt_file in srt_files:
            worker = SrtToAssWorker(srt_file)
            try:
                worker.start()
                worker.wait()
                completed.append(srt_file)
            except Exception:
                failed.append(srt_file)
            finally:
                worker.deleteLater()
        
        assert len(completed) == len(srt_files)
        assert len(failed) == 0
