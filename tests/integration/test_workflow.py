"""Integration tests for complete subtitle workflow."""

import pytest
from pathlib import Path
from modules.ui.subtitle_preview import SubtitlePreview
from modules.translation.translator import SubtitleTranslator
from modules.media.processor import MediaProcessor
from modules.processing.batch_manager import BatchManager

@pytest.mark.integration
class TestSubtitleWorkflow:
    """Test suite for end-to-end subtitle workflows."""
    
    @pytest.fixture
    def workflow_setup(self, qapp, media_helper, subtitle_helper):
        """Set up components for workflow testing."""
        preview = SubtitlePreview()
        translator = SubtitleTranslator()
        processor = MediaProcessor()
        batch_manager = BatchManager()
        
        # Create test media files
        video = media_helper.create_dummy_video(duration=5)
        subtitles = [
            subtitle_helper.create_subtitle(0.0, 2.0, "Hello world"),
            subtitle_helper.create_subtitle(2.5, 2.0, "Testing workflow")
        ]
        subtitle_file = subtitle_helper.create_subtitle_file(subtitles)
        
        return {
            'preview': preview,
            'translator': translator,
            'processor': processor,
            'batch_manager': batch_manager,
            'video': video,
            'subtitle_file': subtitle_file,
            'subtitles': subtitles
        }
        
    def teardown_method(self, method):
        """Clean up test files."""
        # Implemented in fixture cleanup
        pass
        
    @pytest.mark.slow
    def test_complete_workflow(self, workflow_setup, ui_helper, tmp_path):
        """Test complete subtitle workflow from import to preview."""
        # Extract components
        preview = workflow_setup['preview']
        translator = workflow_setup['translator']
        processor = workflow_setup['processor']
        video = workflow_setup['video']
        subtitles = workflow_setup['subtitles']
        
        # Step 1: Process video
        video_info = processor.get_video_info(video)
        assert video_info['duration'] == 5
        
        # Step 2: Translate subtitles
        translations = translator.translate_batch(subtitles, ["es", "fr"])
        assert len(translations["es"]) == len(subtitles)
        assert len(translations["fr"]) == len(subtitles)
        
        # Step 3: Preview subtitles
        for subtitle in subtitles:
            preview.set_subtitle(subtitle)
            ui_helper.wait_for(preview)
            assert preview.get_visible_text() == subtitle['text']
            
        # Step 4: Apply styles
        style = {"font_size": 24, "color": "#FFFFFF"}
        preview.apply_style(style)
        assert preview.current_style == style
        
    @pytest.mark.slow
    @pytest.mark.network
    def test_batch_workflow(self, workflow_setup, batch_helper, tmp_path):
        """Test batch processing workflow."""
        processor = workflow_setup['processor']
        batch_manager = workflow_setup['batch_manager']
        translator = workflow_setup['translator']
        
        # Create multiple test files
        videos = batch_helper.create_batch_files(3, 'video', duration=2)
        
        # Process videos
        completed = []
        def on_complete(file):
            completed.append(file)
            
        batch_manager.job_completed.connect(on_complete)
        batch_manager.process_files(videos)
        batch_manager.wait_for_completion()
        
        assert len(completed) == len(videos)
        
        # Translate subtitles for each video
        for video in completed:
            info = processor.get_video_info(video)
            subtitles = processor.extract_subtitles(video)
            translations = translator.translate_batch(subtitles, ["es"])
            assert len(translations["es"]) == len(subtitles)
            
        batch_helper.cleanup_batch_files(videos)
        
    @pytest.mark.error
    def test_error_recovery(self, workflow_setup, ui_helper):
        """Test error recovery in workflow."""
        preview = workflow_setup['preview']
        translator = workflow_setup['translator']
        processor = workflow_setup['processor']
        subtitles = workflow_setup['subtitles']
        
        # Test translation error recovery
        with pytest.raises(ValueError):
            translator.translate_batch(subtitles, ["invalid_lang"])
            
        # Recover and try valid language
        translations = translator.translate_batch(subtitles, ["es"])
        assert len(translations["es"]) == len(subtitles)
        
        # Test preview error recovery
        with pytest.raises(ValueError):
            preview.set_subtitle(None)
            
        # Recover with valid subtitle
        preview.set_subtitle(subtitles[0])
        ui_helper.wait_for(preview)
        assert preview.get_visible_text() == subtitles[0]['text']
        
    @pytest.mark.slow
    def test_style_workflow(self, workflow_setup, ui_helper):
        """Test subtitle styling workflow."""
        preview = workflow_setup['preview']
        subtitles = workflow_setup['subtitles']
        
        # Apply different styles
        styles = [
            {"font_size": 18, "color": "#FFFFFF"},
            {"font_size": 24, "color": "#FFFF00"},
            {"font_size": 32, "color": "#00FF00"}
        ]
        
        for subtitle, style in zip(subtitles, styles):
            preview.set_subtitle(subtitle)
            preview.apply_style(style)
            ui_helper.wait_for(preview)
            
            assert preview.current_style == style
            assert preview.get_visible_text() == subtitle['text']
            
    @pytest.mark.network
    def test_translation_workflow(self, workflow_setup):
        """Test translation workflow with multiple languages."""
        translator = workflow_setup['translator']
        subtitles = workflow_setup['subtitles']
        
        # Translate to multiple languages
        languages = ["es", "fr", "de", "it"]
        translations = translator.translate_batch(subtitles, languages)
        
        # Verify translations
        for lang in languages:
            assert lang in translations
            assert len(translations[lang]) == len(subtitles)
            
        # Verify timing preservation
        for lang in languages:
            for orig, trans in zip(subtitles, translations[lang]):
                assert trans['start_time'] == orig['start_time']
                assert trans['duration'] == orig['duration']
                
    @pytest.mark.gpu
    @pytest.mark.slow
    def test_performance_workflow(self, workflow_setup, batch_helper, tmp_path):
        """Test performance-critical workflow with GPU acceleration."""
        processor = workflow_setup['processor']
        batch_manager = workflow_setup['batch_manager']
        
        if not processor.has_gpu_support():
            pytest.skip("GPU support not available")
            
        # Create high-resolution test videos
        videos = batch_helper.create_batch_files(2, 'video', duration=5)
        
        # Enable GPU acceleration
        processor.enable_gpu()
        
        # Process videos with high-quality settings
        for video in videos:
            output_file = tmp_path / f"processed_{Path(video).name}"
            processor.process_video(
                video,
                output_file,
                target_resolution=(3840, 2160),  # 4K
                target_fps=60
            )
            
            # Verify output
            info = processor.get_video_info(output_file)
            assert info['width'] == 3840
            assert info['height'] == 2160
            assert info['fps'] == 60
            
        batch_helper.cleanup_batch_files(videos)
