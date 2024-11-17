"""Tests for media file processing functionality."""

import pytest
from pathlib import Path
from modules.media.processor import MediaProcessor

@pytest.mark.media
@pytest.mark.parallel
class TestMediaProcessing:
    """Test suite for media file processing."""
    
    @pytest.fixture
    def processor(self):
        """Create MediaProcessor instance."""
        return MediaProcessor()
    
    @pytest.mark.unit
    def test_initialization(self, processor):
        """Test processor initialization."""
        assert processor is not None
        assert processor.supported_formats() is not None
        
    @pytest.mark.ffmpeg
    @pytest.mark.slow
    def test_video_extraction(self, processor, media_helper):
        """Test video information extraction."""
        video_file = media_helper.create_dummy_video(duration=5)
        
        info = processor.get_video_info(video_file)
        assert info['duration'] == 5
        assert info['width'] == 640
        assert info['height'] == 480
        assert info['fps'] == 30
        
        Path(video_file).unlink()
        
    @pytest.mark.ffmpeg
    def test_audio_extraction(self, processor, media_helper):
        """Test audio information extraction."""
        audio_file = media_helper.create_dummy_audio(duration=5)
        
        info = processor.get_audio_info(audio_file)
        assert info['duration'] == 5
        assert info['sample_rate'] == 44100
        assert info['channels'] == 1
        
        Path(audio_file).unlink()
        
    @pytest.mark.slow
    @pytest.mark.ffmpeg
    def test_video_processing(self, processor, media_helper, tmp_path):
        """Test video processing operations."""
        video_file = media_helper.create_dummy_video(duration=2)
        output_file = tmp_path / "processed.mp4"
        
        # Basic processing test
        assert processor.get_video_info(video_file)['duration'] == 2
        
        Path(video_file).unlink()
        
    @pytest.mark.unit
    def test_error_handling(self, processor):
        """Test error handling in processor."""
        with pytest.raises(FileNotFoundError):
            processor.get_video_info("nonexistent.mp4")
            
    @pytest.mark.unit
    def test_format_conversion(self, processor):
        """Test format conversion utilities."""
        formats = processor.supported_formats()
        assert isinstance(formats, dict)
        assert 'video' in formats
        assert 'audio' in formats
        
    @pytest.mark.unit
    def test_boundary_conditions(self, processor):
        """Test boundary conditions."""
        with pytest.raises(ValueError):
            processor._probe_file("")
            
    @pytest.mark.unit
    def test_state_management(self, processor):
        """Test state management."""
        assert processor.probe_info is None
        
    @pytest.mark.unit
    def test_configuration(self, processor):
        """Test configuration handling."""
        assert processor.SUPPORTED_VIDEO_FORMATS
        assert processor.SUPPORTED_AUDIO_FORMATS
        
    @pytest.mark.gpu
    @pytest.mark.skipif(not pytest.GPU_AVAILABLE, reason="GPU not available")
    def test_gpu_acceleration(self, processor):
        """Test GPU acceleration features."""
        pass  # GPU tests implementation
