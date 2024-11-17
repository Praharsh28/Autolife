"""Tests for subtitle translation functionality."""

import pytest
from modules.translation.translator import SubtitleTranslator

@pytest.mark.translation
class TestTranslation:
    """Test suite for subtitle translation."""
    
    @pytest.fixture
    def translator(self):
        """Create SubtitleTranslator instance."""
        return SubtitleTranslator()
    
    def test_initialization(self, translator):
        """Test translator initialization."""
        assert translator is not None
        assert translator.supported_languages() is not None
        
    @pytest.mark.network
    def test_single_subtitle_translation(self, translator, subtitle_helper):
        """Test translation of a single subtitle."""
        subtitle = subtitle_helper.create_subtitle(0.0, 2.0, "Hello world")
        
        # Translate to Spanish
        translated = translator.translate_subtitle(subtitle, "es")
        assert translated is not None
        assert translated['text'] == "Hola mundo"
        assert translated['start_time'] == subtitle['start_time']
        assert translated['duration'] == subtitle['duration']
        
    @pytest.mark.network
    @pytest.mark.slow
    def test_batch_translation(self, translator, subtitle_helper):
        """Test batch translation of subtitles."""
        subtitles = [
            subtitle_helper.create_subtitle(0.0, 2.0, "Hello"),
            subtitle_helper.create_subtitle(2.0, 2.0, "World")
        ]
        
        # Translate to multiple languages
        translations = translator.translate_batch(subtitles, ["es", "fr"])
        
        assert "es" in translations
        assert "fr" in translations
        assert len(translations["es"]) == len(subtitles)
        assert len(translations["fr"]) == len(subtitles)
        
    @pytest.mark.error
    def test_error_handling(self, translator, subtitle_helper):
        """Test translation error handling."""
        subtitle = subtitle_helper.create_subtitle(0.0, 2.0, "Test")
        
        # Invalid language code
        with pytest.raises(ValueError):
            translator.translate_subtitle(subtitle, "invalid")
            
        # Empty text
        empty_subtitle = subtitle_helper.create_subtitle(0.0, 2.0, "")
        with pytest.raises(ValueError):
            translator.translate_subtitle(empty_subtitle, "es")
            
    @pytest.mark.network
    def test_language_detection(self, translator, subtitle_helper):
        """Test automatic language detection."""
        subtitles = [
            subtitle_helper.create_subtitle(0.0, 2.0, "Hello world"),
            subtitle_helper.create_subtitle(2.0, 2.0, "¡Hola mundo!"),
            subtitle_helper.create_subtitle(4.0, 2.0, "Bonjour le monde")
        ]
        
        languages = translator.detect_languages(subtitles)
        assert len(languages) == len(subtitles)
        assert languages[0] == "en"
        assert languages[1] == "es"
        assert languages[2] == "fr"
        
    @pytest.mark.network
    def test_translation_quality(self, translator, subtitle_helper):
        """Test translation quality metrics."""
        subtitle = subtitle_helper.create_subtitle(0.0, 2.0, 
            "The quick brown fox jumps over the lazy dog")
            
        translated = translator.translate_subtitle(subtitle, "es")
        quality = translator.assess_quality(subtitle, translated)
        
        assert 0.0 <= quality <= 1.0
        
    @pytest.mark.boundary
    def test_boundary_conditions(self, translator, subtitle_helper):
        """Test translation boundary conditions."""
        # Very long text
        long_text = "word " * 1000
        long_subtitle = subtitle_helper.create_subtitle(0.0, 2.0, long_text)
        
        translated = translator.translate_subtitle(long_subtitle, "es")
        assert translated is not None
        
        # Special characters
        special_subtitle = subtitle_helper.create_subtitle(0.0, 2.0, "Hello 🌍!")
        translated = translator.translate_subtitle(special_subtitle, "es")
        assert translated is not None
        
    @pytest.mark.state
    def test_state_management(self, translator):
        """Test translator state management."""
        # Cache management
        translator.clear_cache()
        assert translator.cache_size() == 0
        
        # API rate limiting
        assert translator.rate_limit_remaining() > 0
        
    @pytest.mark.config
    def test_configuration(self, translator):
        """Test translator configuration."""
        config = {
            "cache_size": 1000,
            "timeout": 30,
            "retry_attempts": 3
        }
        
        translator.configure(config)
        current_config = translator.get_configuration()
        
        assert current_config["cache_size"] == config["cache_size"]
        assert current_config["timeout"] == config["timeout"]
        assert current_config["retry_attempts"] == config["retry_attempts"]
