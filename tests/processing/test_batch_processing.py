"""Tests for batch processing functionality."""

import pytest
from pathlib import Path
from modules.processing.batch_manager import BatchManager

@pytest.mark.batch
@pytest.mark.integration
class TestBatchProcessing:
    """Test suite for batch processing functionality."""
    
    @pytest.fixture
    def batch_manager(self):
        """Create BatchManager instance."""
        return BatchManager()
    
    def test_initialization(self, batch_manager):
        """Test batch manager initialization."""
        assert batch_manager is not None
        assert batch_manager.active_jobs == 0
        assert batch_manager.completed_jobs == 0
        
    @pytest.mark.slow
    def test_batch_video_processing(self, batch_manager, batch_helper, media_helper):
        """Test batch processing of video files."""
        # Create test videos
        videos = batch_helper.create_batch_files(3, 'video', duration=2)
        
        # Process videos
        completed = []
        def on_complete(file):
            completed.append(file)
            
        batch_manager.job_completed.connect(on_complete)
        batch_manager.process_files(videos)
        
        # Wait for completion
        batch_manager.wait_for_completion()
        assert len(completed) == len(videos)
        
        # Cleanup
        batch_helper.cleanup_batch_files(videos)
        
    @pytest.mark.slow
    def test_batch_audio_processing(self, batch_manager, batch_helper):
        """Test batch processing of audio files."""
        # Create test audio files
        audio_files = batch_helper.create_batch_files(3, 'audio', duration=2)
        
        # Process audio files
        completed = []
        def on_complete(file):
            completed.append(file)
            
        batch_manager.job_completed.connect(on_complete)
        batch_manager.process_files(audio_files)
        
        # Wait for completion
        batch_manager.wait_for_completion()
        assert len(completed) == len(audio_files)
        
        # Cleanup
        batch_helper.cleanup_batch_files(audio_files)
        
    @pytest.mark.error
    def test_error_handling(self, batch_manager, tmp_path):
        """Test error handling in batch processing."""
        # Invalid file
        invalid_file = tmp_path / "invalid.mp4"
        invalid_file.touch()
        
        errors = []
        def on_error(file, error):
            errors.append((file, error))
            
        batch_manager.job_error.connect(on_error)
        batch_manager.process_files([invalid_file])
        batch_manager.wait_for_completion()
        
        assert len(errors) == 1
        assert errors[0][0] == invalid_file
        
    def test_progress_tracking(self, batch_manager, batch_helper):
        """Test progress tracking during batch processing."""
        files = batch_helper.create_batch_files(2, 'video', duration=1)
        
        progress_updates = []
        def on_progress(file, progress):
            progress_updates.append((file, progress))
            
        batch_manager.job_progress.connect(on_progress)
        batch_manager.process_files(files)
        batch_manager.wait_for_completion()
        
        # Verify progress updates
        assert len(progress_updates) > 0
        for file, progress in progress_updates:
            assert 0 <= progress <= 100
            
        batch_helper.cleanup_batch_files(files)
        
    @pytest.mark.state
    def test_state_management(self, batch_manager, batch_helper):
        """Test batch manager state management."""
        files = batch_helper.create_batch_files(2, 'video', duration=1)
        
        # Initial state
        assert not batch_manager.is_processing()
        
        # Start processing
        batch_manager.process_files(files)
        assert batch_manager.is_processing()
        
        # Wait for completion
        batch_manager.wait_for_completion()
        assert not batch_manager.is_processing()
        assert batch_manager.completed_jobs == len(files)
        
        batch_helper.cleanup_batch_files(files)
        
    @pytest.mark.boundary
    def test_boundary_conditions(self, batch_manager):
        """Test boundary conditions."""
        # Empty file list
        batch_manager.process_files([])
        assert not batch_manager.is_processing()
        
        # None input
        with pytest.raises(ValueError):
            batch_manager.process_files(None)
            
        # Non-existent files
        non_existent = [Path("non_existent1.mp4"), Path("non_existent2.mp4")]
        batch_manager.process_files(non_existent)
        batch_manager.wait_for_completion()
        assert batch_manager.completed_jobs == 0
        
    @pytest.mark.serial
    def test_cancellation(self, batch_manager, batch_helper):
        """Test batch processing cancellation."""
        files = batch_helper.create_batch_files(5, 'video', duration=2)
        
        # Start processing
        batch_manager.process_files(files)
        assert batch_manager.is_processing()
        
        # Cancel processing
        batch_manager.cancel_all()
        batch_manager.wait_for_completion()
        
        assert not batch_manager.is_processing()
        assert batch_manager.completed_jobs < len(files)
        
        batch_helper.cleanup_batch_files(files)
