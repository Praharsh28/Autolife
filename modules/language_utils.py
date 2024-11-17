"""
Language utilities for multi-language subtitle generation and management.
"""

import re
import json
import unicodedata
from typing import Dict, List, Optional, Set, Tuple
from pathlib import Path
from .utilities import setup_logger
from .constants import (
    SUPPORTED_LANGUAGES,
    DEFAULT_LANGUAGE,
    LANGUAGE_MODELS,
    LANGUAGE_CODES,
    LANGUAGE_DIRECTIONS,
    PUNCTUATION_RULES,
    SUBTITLE_RULES
)

logger = setup_logger('language_utils')

class LanguageError(Exception):
    """Base exception for language-related errors."""
    pass

class LanguageDetector:
    """Language detection and validation."""
    
    def __init__(self):
        """Initialize language detector."""
        self.supported_languages = SUPPORTED_LANGUAGES
        self.language_codes = LANGUAGE_CODES
        
    def detect_language(self, text: str) -> str:
        """
        Detect language of text.
        
        Args:
            text: Input text
            
        Returns:
            str: Detected language code
        """
        try:
            # Use Whisper's language detection
            from transformers import WhisperProcessor
            processor = WhisperProcessor.from_pretrained("openai/whisper-base")
            detected_lang = processor.detect_language(text)
            
            # Map to our language codes
            if detected_lang in self.language_codes:
                return detected_lang
            
            # Default to English if unsure
            return DEFAULT_LANGUAGE
            
        except Exception as e:
            logger.error(f"Error detecting language: {str(e)}")
            return DEFAULT_LANGUAGE
            
    def is_supported(self, language_code: str) -> bool:
        """Check if language is supported."""
        return language_code in self.supported_languages
        
    def get_language_name(self, language_code: str) -> str:
        """Get full language name from code."""
        return self.supported_languages.get(language_code, "Unknown")
        
    def get_language_code(self, language_name: str) -> Optional[str]:
        """Get language code from name."""
        for code, name in self.supported_languages.items():
            if name.lower() == language_name.lower():
                return code
        return None

class TextFormatter:
    """Language-specific text formatting."""
    
    def __init__(self, language_code: str):
        """
        Initialize text formatter.
        
        Args:
            language_code: Language code to use for formatting
        """
        self.language_code = language_code
        self.rules = PUNCTUATION_RULES.get(language_code, PUNCTUATION_RULES[DEFAULT_LANGUAGE])
        self.subtitle_rules = SUBTITLE_RULES.get(language_code, SUBTITLE_RULES[DEFAULT_LANGUAGE])
        self.text_direction = LANGUAGE_DIRECTIONS.get(language_code, 'ltr')
        
    def format_text(self, text: str) -> str:
        """
        Format text according to language rules.
        
        Args:
            text: Input text
            
        Returns:
            str: Formatted text
        """
        # Apply basic cleanup
        text = text.strip()
        
        # Apply language-specific rules
        for pattern, replacement in self.rules['patterns'].items():
            text = re.sub(pattern, replacement, text)
            
        # Handle text direction
        if self.text_direction == 'rtl':
            # Add RTL marks for proper display
            text = '\u200F' + text + '\u200F'
            
        return text
        
    def format_subtitle(self, text: str, line_count: int = 2) -> List[str]:
        """
        Format text into subtitle lines.
        
        Args:
            text: Input text
            line_count: Maximum number of lines
            
        Returns:
            List[str]: Formatted subtitle lines
        """
        max_chars = self.subtitle_rules['max_chars_per_line']
        min_chars = self.subtitle_rules['min_chars_per_line']
        
        # Split into words while preserving punctuation
        words = re.findall(r'\S+|\s+', text)
        
        lines = []
        current_line = []
        current_length = 0
        
        for word in words:
            word_length = len(word)
            
            if current_length + word_length > max_chars:
                if current_line:
                    lines.append(''.join(current_line).strip())
                    current_line = []
                    current_length = 0
                    
                    if len(lines) >= line_count:
                        break
                        
            current_line.append(word)
            current_length += word_length
            
        if current_line and len(lines) < line_count:
            lines.append(''.join(current_line).strip())
            
        # Balance lines if needed
        if len(lines) > 1:
            lines = self._balance_lines(lines)
            
        return lines
        
    def _balance_lines(self, lines: List[str]) -> List[str]:
        """Balance subtitle lines for better readability."""
        if len(lines) <= 1:
            return lines
            
        # Try to make lines more even in length
        while len(lines) > 1:
            max_line = max(lines, key=len)
            max_index = lines.index(max_line)
            
            if len(max_line) <= self.subtitle_rules['min_chars_per_line']:
                break
                
            # Find best split point
            words = max_line.split()
            mid_point = len(max_line) // 2
            
            best_split = 0
            min_diff = float('inf')
            
            current_pos = 0
            for i, word in enumerate(words):
                current_pos += len(word) + 1
                diff = abs(current_pos - mid_point)
                
                if diff < min_diff:
                    min_diff = diff
                    best_split = i + 1
                    
            # Split the line
            first_part = ' '.join(words[:best_split])
            second_part = ' '.join(words[best_split:])
            
            if max_index > 0:
                # Combine with previous line
                lines[max_index - 1] = first_part
                lines[max_index] = second_part
            else:
                # Combine with next line
                lines[max_index] = first_part
                lines[max_index + 1] = second_part
                
        return lines

class TranslationManager:
    """Manage subtitle translation between languages."""
    
    def __init__(self):
        """Initialize translation manager."""
        self.detector = LanguageDetector()
        self.formatters: Dict[str, TextFormatter] = {}
        
    def get_formatter(self, language_code: str) -> TextFormatter:
        """Get or create text formatter for language."""
        if language_code not in self.formatters:
            self.formatters[language_code] = TextFormatter(language_code)
        return self.formatters[language_code]
        
    def translate_subtitles(
        self,
        subtitles: List[Dict],
        target_language: str,
        source_language: Optional[str] = None
    ) -> List[Dict]:
        """
        Translate subtitles to target language.
        
        Args:
            subtitles: List of subtitle dictionaries
            target_language: Target language code
            source_language: Optional source language code
            
        Returns:
            List[Dict]: Translated subtitles
        """
        try:
            # Validate target language
            if not self.detector.is_supported(target_language):
                raise LanguageError(f"Unsupported target language: {target_language}")
                
            # Detect source language if not provided
            if not source_language:
                sample_text = " ".join(sub['text'] for sub in subtitles[:5])
                source_language = self.detector.detect_language(sample_text)
                
            if source_language == target_language:
                return subtitles
                
            # Get formatters
            source_formatter = self.get_formatter(source_language)
            target_formatter = self.get_formatter(target_language)
            
            # Initialize translation model
            model_name = LANGUAGE_MODELS.get(
                (source_language, target_language),
                LANGUAGE_MODELS['default']
            )
            
            from transformers import AutoModelForSeq2SeqGeneration, AutoTokenizer
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            model = AutoModelForSeq2SeqGeneration.from_pretrained(model_name)
            
            translated_subtitles = []
            
            for subtitle in subtitles:
                # Prepare text for translation
                text = source_formatter.format_text(subtitle['text'])
                
                # Translate
                inputs = tokenizer(text, return_tensors="pt", padding=True)
                outputs = model.generate(**inputs)
                translated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
                
                # Format translated text
                formatted_text = target_formatter.format_text(translated_text)
                formatted_lines = target_formatter.format_subtitle(formatted_text)
                
                # Create new subtitle entry
                translated_subtitle = subtitle.copy()
                translated_subtitle['text'] = '\n'.join(formatted_lines)
                translated_subtitles.append(translated_subtitle)
                
            return translated_subtitles
            
        except Exception as e:
            logger.error(f"Error translating subtitles: {str(e)}")
            raise LanguageError(f"Translation failed: {str(e)}")
            
    def detect_and_format(self, text: str) -> Tuple[str, str]:
        """
        Detect language and format text accordingly.
        
        Args:
            text: Input text
            
        Returns:
            Tuple[str, str]: Language code and formatted text
        """
        try:
            # Detect language
            language_code = self.detector.detect_language(text)
            
            # Format text
            formatter = self.get_formatter(language_code)
            formatted_text = formatter.format_text(text)
            
            return language_code, formatted_text
            
        except Exception as e:
            logger.error(f"Error detecting and formatting text: {str(e)}")
            return DEFAULT_LANGUAGE, text
