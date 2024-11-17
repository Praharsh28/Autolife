"""Performance tests for the application."""

import pytest
import time
from pathlib import Path
from modules.ui.subtitle_preview import SubtitlePreview
from modules.translation.translator import SubtitleTranslator
from modules.media.processor import MediaProcessor
from modules.processing.batch_manager import BatchManager

@pytest.mark.performance
class TestPerformance:
    """Test suite for performance benchmarking."""
    
    @pytest.fixture
    def performance_setup(self, media_helper, subtitle_helper):
        """Set up components for performance testing."""
        preview = SubtitlePreview()
        translator = SubtitleTranslator()
        processor = MediaProcessor()
        batch_manager = BatchManager()
        
        # Create test data
        video = media_helper.create_dummy_video(duration=10)
        subtitles = [
            subtitle_helper.create_subtitle(i, 1.0, f"Subtitle {i}")
            for i in range(0, 10, 1)
        ]
        
        return {
            'preview': preview,
            'translator': translator,
            'processor': processor,
            'batch_manager': batch_manager,
            'video': video,
            'subtitles': subtitles
        }
        
    @pytest.mark.benchmark
    def test_subtitle_preview_performance(self, performance_setup, ui_helper):
        """Test subtitle preview rendering performance."""
        preview = performance_setup['preview']
        subtitles = performance_setup['subtitles']
        
        # Measure rendering time
        start_time = time.time()
        for subtitle in subtitles:
            preview.set_subtitle(subtitle)
            ui_helper.wait_for(preview, timeout=100)
            
        total_time = time.time() - start_time
        avg_time = total_time / len(subtitles)
        
        assert avg_time < 0.1  # Average render time should be under 100ms
        
    @pytest.mark.benchmark
    @pytest.mark.network
    def test_translation_performance(self, performance_setup):
        """Test translation performance."""
        translator = performance_setup['translator']
        subtitles = performance_setup['subtitles']
        
        # Measure translation time
        start_time = time.time()
        translations = translator.translate_batch(subtitles, ["es", "fr"])
        total_time = time.time() - start_time
        
        assert len(translations) == 2
        assert total_time < 5.0  # Total translation time should be under 5 seconds
        
    @pytest.mark.benchmark
    @pytest.mark.slow
    def test_video_processing_performance(self, performance_setup, tmp_path):
        """Test video processing performance."""
        processor = performance_setup['processor']
        video = performance_setup['video']
        
        # Measure processing time
        start_time = time.time()
        output_file = tmp_path / "processed.mp4"
        
        processor.process_video(
            video,
            output_file,
            target_resolution=(1920, 1080),
            target_fps=30
        )
        
        total_time = time.time() - start_time
        assert total_time < 30.0  # Processing should take less than 30 seconds
        
        Path(video).unlink()
        output_file.unlink()
        
    @pytest.mark.benchmark
    @pytest.mark.gpu
    def test_gpu_processing_performance(self, performance_setup, tmp_path):
        """Test GPU-accelerated processing performance."""
        processor = performance_setup['processor']
        video = performance_setup['video']
        
        if not processor.has_gpu_support():
            pytest.skip("GPU support not available")
            
        # Compare CPU vs GPU processing time
        output_cpu = tmp_path / "cpu_processed.mp4"
        output_gpu = tmp_path / "gpu_processed.mp4"
        
        # CPU processing
        start_time = time.time()
        processor.process_video(
            video,
            output_cpu,
            target_resolution=(1920, 1080),
            target_fps=30
        )
        cpu_time = time.time() - start_time
        
        # GPU processing
        processor.enable_gpu()
        start_time = time.time()
        processor.process_video(
            video,
            output_gpu,
            target_resolution=(1920, 1080),
            target_fps=30
        )
        gpu_time = time.time() - start_time
        
        assert gpu_time < cpu_time  # GPU should be faster
        
        Path(video).unlink()
        output_cpu.unlink()
        output_gpu.unlink()
        
    @pytest.mark.benchmark
    def test_memory_usage(self, performance_setup, batch_helper):
        """Test memory usage during batch processing."""
        import psutil
        import os
        
        batch_manager = performance_setup['batch_manager']
        
        # Create large batch of files
        videos = batch_helper.create_batch_files(10, 'video', duration=5)
        
        # Monitor memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Process batch
        batch_manager.process_files(videos)
        batch_manager.wait_for_completion()
        
        # Check memory usage
        final_memory = process.memory_info().rss
        memory_increase = (final_memory - initial_memory) / 1024 / 1024  # MB
        
        assert memory_increase < 500  # Memory increase should be less than 500MB
        
        batch_helper.cleanup_batch_files(videos)
        
    @pytest.mark.benchmark
    @pytest.mark.slow
    def test_concurrent_performance(self, performance_setup, batch_helper):
        """Test performance with concurrent operations."""
        translator = performance_setup['translator']
        processor = performance_setup['processor']
        batch_manager = performance_setup['batch_manager']
        
        # Create test data
        videos = batch_helper.create_batch_files(5, 'video', duration=2)
        subtitles = performance_setup['subtitles']
        
        # Start concurrent operations
        start_time = time.time()
        
        # Translation task
        translation_task = translator.translate_batch_async(subtitles, ["es", "fr"])
        
        # Processing task
        batch_manager.process_files(videos)
        
        # Wait for completion
        translations = translation_task.result()
        batch_manager.wait_for_completion()
        
        total_time = time.time() - start_time
        
        assert len(translations) == 2
        assert total_time < 60.0  # Concurrent operations should complete within 60 seconds
        
        batch_helper.cleanup_batch_files(videos)
        
    @pytest.mark.benchmark
    def test_ui_responsiveness(self, performance_setup, ui_helper):
        """Test UI responsiveness under load."""
        preview = performance_setup['preview']
        subtitles = performance_setup['subtitles']
        
        # Measure UI response times
        response_times = []
        
        for subtitle in subtitles:
            start_time = time.time()
            preview.set_subtitle(subtitle)
            ui_helper.wait_for(preview, timeout=50)
            response_times.append(time.time() - start_time)
            
        avg_response = sum(response_times) / len(response_times)
        max_response = max(response_times)
        
        assert avg_response < 0.05  # Average response under 50ms
        assert max_response < 0.1  # Max response under 100ms
