"""Tests for the MediaProcessor class."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import tempfile
from pathlib import Path
import json
import os
import ffmpeg

from modules.media.processor import MediaProcessor

@pytest.fixture
def mock_ffmpeg():
    """Mock ffmpeg-python for testing."""
    with patch('modules.media.processor.ffmpeg') as mock:
        # Mock probe data
        mock.probe.return_value = {
            'streams': [{
                'codec_type': 'video',
                'width': 1920,
                'height': 1080,
                'duration': '60.0',
                'bit_rate': '5000000',
                'r_frame_rate': '30/1',
                'codec_name': 'h264'
            }],
            'format': {
                'duration': '60.0',
                'size': '38860000',
                'bit_rate': '5000000'
            }
        }
        
        # Mock stream operations
        stream_mock = MagicMock()
        mock.input.return_value = stream_mock
        mock.filter.return_value = stream_mock
        mock.output.return_value = stream_mock
        stream_mock.run.return_value = None
        
        yield mock

@pytest.fixture
def mock_ffmpeg_with_audio():
    """Mock ffmpeg-python with audio stream."""
    with patch('modules.media.processor.ffmpeg') as mock:
        mock.probe.return_value = {
            'streams': [{
                'codec_type': 'audio',
                'sample_rate': '44100',
                'channels': '2',
                'duration': '60.0',
                'bit_rate': '320000',
                'codec_name': 'aac'
            }],
            'format': {
                'duration': '60.0',
                'size': '2400000',
                'bit_rate': '320000'
            }
        }
        
        # Mock stream operations
        stream_mock = MagicMock()
        mock.input.return_value = stream_mock
        mock.filter.return_value = stream_mock
        mock.output.return_value = stream_mock
        stream_mock.run.return_value = None
        
        yield mock

@pytest.fixture
def processor():
    """Create MediaProcessor instance."""
    return MediaProcessor()

@pytest.fixture
def sample_video_file(tmp_path):
    """Create a sample video file."""
    video_file = tmp_path / "test_video.mp4"
    video_file.touch()
    with open(video_file, 'wb') as f:
        f.write(b'\x00' * 1024)
    return str(video_file)

@pytest.fixture
def sample_audio_file(tmp_path):
    """Create a sample audio file."""
    audio_file = tmp_path / "test_audio.wav"
    audio_file.touch()
    return str(audio_file)

class TestMediaProcessor:
    """Test cases for MediaProcessor class."""

    def test_initialization(self, processor):
        """Test processor initialization."""
        assert isinstance(processor, MediaProcessor)
        assert processor.probe_info is None
        assert processor.ffmpeg is not None

    def test_initialization_error(self):
        """Test initialization with missing ffmpeg."""
        with patch('modules.media.processor.ffmpeg', None):
            with pytest.raises(ImportError, match="FFmpeg-python is required"):
                MediaProcessor()

    def test_supported_formats(self, processor):
        """Test supported formats."""
        formats = processor.supported_formats()
        assert isinstance(formats, dict)
        assert 'video' in formats
        assert 'audio' in formats
        assert '.mp4' in formats['video']
        assert '.wav' in formats['audio']

    def test_probe_file_errors(self, processor, sample_video_file):
        """Test probe file error handling."""
        # Test non-existent file
        with pytest.raises(FileNotFoundError):
            processor._probe_file("nonexistent.mp4")

        # Test empty path
        with pytest.raises(FileNotFoundError):
            processor._probe_file("")

        # Test ffmpeg error
        with patch.object(processor.ffmpeg, 'probe', side_effect=ffmpeg.Error("FFmpeg error")):
            with pytest.raises(ValueError, match="FFmpeg error while probing"):
                processor._probe_file(sample_video_file)

        # Test unexpected error
        with patch.object(processor.ffmpeg, 'probe', side_effect=Exception("Unexpected")):
            with pytest.raises(RuntimeError, match="Unexpected error while probing"):
                processor._probe_file(sample_video_file)

    def test_get_video_info(self, processor, mock_ffmpeg, sample_video_file):
        """Test video info extraction."""
        info = processor.get_video_info(sample_video_file)
        
        assert info['duration'] == 60.0
        assert info['width'] == 1920
        assert info['height'] == 1080
        assert info['fps'] == 30.0
        assert info['codec'] == 'h264'
        assert info['bitrate'] == 5000000

    def test_get_video_info_errors(self, processor, mock_ffmpeg, sample_video_file):
        """Test video info error handling."""
        # Test no video stream
        mock_ffmpeg.probe.return_value = {'streams': []}
        with pytest.raises(ValueError, match="No video stream found"):
            processor.get_video_info(sample_video_file)

        # Test missing required fields
        mock_ffmpeg.probe.return_value = {'streams': [{'codec_type': 'video'}]}
        with pytest.raises(ValueError, match="Invalid video format"):
            processor.get_video_info(sample_video_file)

        # Test invalid duration
        mock_ffmpeg.probe.return_value = {
            'streams': [{
                'codec_type': 'video',
                'duration': 'invalid'
            }],
            'format': {}
        }
        with pytest.raises(ValueError, match="Invalid video format"):
            processor.get_video_info(sample_video_file)

    def test_get_audio_info(self, processor, mock_ffmpeg_with_audio, sample_audio_file):
        """Test audio info extraction."""
        info = processor.get_audio_info(sample_audio_file)
        
        assert info['duration'] == 60.0
        assert info['sample_rate'] == 44100
        assert info['channels'] == 2
        assert info['codec'] == 'aac'
        assert info['bitrate'] == 320000

    def test_get_audio_info_errors(self, processor, mock_ffmpeg_with_audio, sample_audio_file):
        """Test audio info error handling."""
        # Test no audio stream
        mock_ffmpeg_with_audio.probe.return_value = {'streams': []}
        with pytest.raises(ValueError, match="No audio stream found"):
            processor.get_audio_info(sample_audio_file)

        # Test missing required fields
        mock_ffmpeg_with_audio.probe.return_value = {'streams': [{'codec_type': 'audio'}]}
        with pytest.raises(ValueError, match="Invalid audio format"):
            processor.get_audio_info(sample_audio_file)

        # Test invalid sample rate
        mock_ffmpeg_with_audio.probe.return_value = {
            'streams': [{
                'codec_type': 'audio',
                'sample_rate': 'invalid'
            }],
            'format': {}
        }
        with pytest.raises(ValueError, match="Invalid audio format"):
            processor.get_audio_info(sample_audio_file)

    def test_process_file(self, processor, mock_ffmpeg, sample_video_file, tmp_path):
        """Test media file processing."""
        output_file = str(tmp_path / "output.mp4")
        
        # Test basic processing
        assert processor.process_file(sample_video_file, output_file)
        mock_ffmpeg.input.assert_called_with(sample_video_file)
        mock_ffmpeg.output.return_value.run.assert_called_once()

        # Test with video options
        mock_ffmpeg.output.return_value.run.reset_mock()
        options = {
            'video': True,
            'resolution': (1280, 720),
            'fps': 30
        }
        assert processor.process_file(sample_video_file, output_file, **options)
        assert mock_ffmpeg.filter.call_count >= 2  # Called for both resolution and fps

        # Test with audio options
        mock_ffmpeg.output.return_value.run.reset_mock()
        options = {
            'audio': True,
            'sample_rate': 44100,
            'channels': 2
        }
        assert processor.process_file(sample_video_file, output_file, **options)
        assert mock_ffmpeg.filter.call_count >= 2  # Called for both sample_rate and channels

    def test_process_file_errors(self, processor, mock_ffmpeg, sample_video_file, tmp_path):
        """Test process file error handling."""
        output_file = str(tmp_path / "output.mp4")

        # Test non-existent input
        with pytest.raises(FileNotFoundError):
            processor.process_file("nonexistent.mp4", output_file)

        # Test ffmpeg error
        mock_ffmpeg.output.return_value.run.side_effect = ffmpeg.Error("FFmpeg error")
        with pytest.raises(ValueError, match="FFmpeg processing error"):
            processor.process_file(sample_video_file, output_file)

        # Test unexpected error
        mock_ffmpeg.output.return_value.run.side_effect = Exception("Unexpected")
        with pytest.raises(RuntimeError, match="Unexpected error during processing"):
            processor.process_file(sample_video_file, output_file)

    def test_video_options_validation(self, processor, mock_ffmpeg, sample_video_file, tmp_path):
        """Test video options validation."""
        output_file = str(tmp_path / "output.mp4")

        # Test invalid resolution type
        with pytest.raises(ValueError, match="Resolution must be tuple of integers"):
            processor.process_file(sample_video_file, output_file, video=True, resolution=("invalid", 720))

        # Test invalid resolution values
        with pytest.raises(ValueError, match="Resolution must be tuple of integers"):
            processor.process_file(sample_video_file, output_file, video=True, resolution=(-1280, 720))

        # Test invalid fps type
        with pytest.raises(ValueError, match="FPS must be a positive number"):
            processor.process_file(sample_video_file, output_file, video=True, fps="invalid")

        # Test invalid fps value
        with pytest.raises(ValueError, match="FPS must be a positive number"):
            processor.process_file(sample_video_file, output_file, video=True, fps=-30)

    def test_audio_options_validation(self, processor, mock_ffmpeg, sample_video_file, tmp_path):
        """Test audio options validation."""
        output_file = str(tmp_path / "output.mp4")

        # Test invalid sample rate type
        with pytest.raises(ValueError, match="Sample rate must be a positive integer"):
            processor.process_file(sample_video_file, output_file, audio=True, sample_rate="invalid")

        # Test invalid sample rate value
        with pytest.raises(ValueError, match="Sample rate must be a positive integer"):
            processor.process_file(sample_video_file, output_file, audio=True, sample_rate=-44100)

        # Test invalid channels type
        with pytest.raises(ValueError, match="Channels must be a positive integer"):
            processor.process_file(sample_video_file, output_file, audio=True, channels="invalid")

        # Test invalid channels value
        with pytest.raises(ValueError, match="Channels must be a positive integer"):
            processor.process_file(sample_video_file, output_file, audio=True, channels=0)
