"""
Module for converting SRT subtitles to ASS format.
"""

import os
import re
from typing import List, Dict

class SRTToASSConverter:
    def __init__(self, template_path: str = None):
        """Initialize the converter with optional template path."""
        self.template_path = template_path or os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            'templates',
            'default.ass'
        )
        
    def convert(self, srt_file: str, output_file: str = None) -> str:
        """
        Convert SRT file to ASS format.
        
        Args:
            srt_file: Path to input SRT file
            output_file: Optional path for output ASS file
            
        Returns:
            str: Path to the generated ASS file
        """
        if not output_file:
            output_file = os.path.splitext(srt_file)[0] + '.ass'
            
        # Read SRT content
        with open(srt_file, 'r', encoding='utf-8') as f:
            srt_content = f.read()
            
        # Read template
        with open(self.template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()
            
        # Parse SRT
        srt_entries = self._parse_srt(srt_content)
        
        # Convert to ASS events
        ass_events = self._convert_to_ass_events(srt_entries)
        
        # Replace [Events] section in template
        final_content = re.sub(
            r'\[Events\][^\[]*Format:[^\n]*\n',
            '[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n' + ass_events,
            template_content
        )
        
        # Write output
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(final_content)
            
        return output_file
        
    def _parse_srt(self, content: str) -> List[Dict]:
        """Parse SRT content into structured format."""
        entries = []
        blocks = content.strip().split('\n\n')
        
        for block in blocks:
            lines = block.split('\n')
            if len(lines) >= 3:  # Valid subtitle block
                # Parse timecode
                times = lines[1].split(' --> ')
                if len(times) == 2:
                    entries.append({
                        'start': self._convert_srt_to_ass_time(times[0].strip()),
                        'end': self._convert_srt_to_ass_time(times[1].strip()),
                        'text': '\n'.join(lines[2:])
                    })
        
        return entries
        
    def _convert_to_ass_events(self, entries: List[Dict]) -> str:
        """Convert parsed entries to ASS events."""
        events = []
        for entry in entries:
            # Double escape the newline for ASS format
            text = entry['text'].replace('\n', r'\\N')
            event = f"Dialogue: 0,{entry['start']},{entry['end']},Default,,0,0,0,,{text}"
            events.append(event)
        
        return '\n'.join(events)
        
    def _convert_srt_to_ass_time(self, srt_time: str) -> str:
        """Convert SRT time format to ASS format."""
        # SRT: 00:00:00,000 -> ASS: 0:00:00.00
        parts = srt_time.replace(',', ':').split(':')
        if len(parts) == 4:
            h, m, s, ms = parts
            # Convert milliseconds to centiseconds
            cs = str(int(ms) // 10).zfill(2)
            return f"{int(h)}:{m}:{s}.{cs}"
        return "0:00:00.00"
