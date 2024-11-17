"""Subtitle translation functionality for the AutoLife application."""

import os
import logging
from transformers import M2M100ForConditionalGeneration, M2M100Tokenizer
from typing import List, Dict, Optional

class SubtitleTranslator:
    """Class for handling subtitle translation using transformers."""
    
    def __init__(self, model_name: str = "facebook/m2m100_418M"):
        """Initialize the translator with a specific model.
        
        Args:
            model_name (str): Name of the translation model to use
        """
        self.model_name = model_name
        self.tokenizer = M2M100Tokenizer.from_pretrained(model_name)
        self.model = M2M100ForConditionalGeneration.from_pretrained(model_name)
        
    def translate_text(self, text: str, target_lang: str) -> str:
        """Translate a single piece of text.
        
        Args:
            text (str): Text to translate
            target_lang (str): Target language code
            
        Returns:
            str: Translated text
        """
        try:
            self.tokenizer.src_lang = "en"
            encoded = self.tokenizer(text, return_tensors="pt")
            generated_tokens = self.model.generate(
                **encoded,
                forced_bos_token_id=self.tokenizer.get_lang_id(target_lang)
            )
            return self.tokenizer.batch_decode(generated_tokens, skip_special_tokens=True)[0]
        except Exception as e:
            logging.error(f"Translation error: {str(e)}")
            return text
            
    def translate_subtitles(self, subtitles: List[Dict], target_lang: str) -> List[Dict]:
        """Translate a list of subtitle dictionaries.
        
        Args:
            subtitles (List[Dict]): List of subtitle dictionaries
            target_lang (str): Target language code
            
        Returns:
            List[Dict]: List of translated subtitle dictionaries
        """
        translated_subs = []
        for sub in subtitles:
            translated_text = self.translate_text(sub['text'], target_lang)
            translated_sub = sub.copy()
            translated_sub['text'] = translated_text
            translated_subs.append(translated_sub)
        return translated_subs
