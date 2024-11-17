"""
Worker thread for converting SRT files to ASS format.
"""

import os
import re
import subprocess
from PyQt5.QtCore import QThread
from .worker_signals import WorkerSignals
from ..utilities import setup_logger
from ..constants import DEFAULT_TEMPLATE_PATH

class SrtToAssWorker(QThread):
    def __init__(self, files, template_file=None, style_name="Default", batch_size=4):
        """
        Initialize the SrtToAssWorker.
        
        Args:
            files (list): List of SRT files to convert
            template_file (str, optional): Path to ASS template file. Defaults to None.
            style_name (str, optional): Name of style to use. Defaults to "Default".
            batch_size (int, optional): Number of files to process simultaneously. Defaults to 4.
        """
        super().__init__()
        self.files = files
        self.template_file = template_file or DEFAULT_TEMPLATE_PATH
        self.style_name = style_name
        self.batch_size = batch_size
        self.signals = WorkerSignals()
        self.logger = setup_logger("SrtToAssWorker")

    def process_srt_to_ass(self, srt_file):
        """Convert a single SRT file to ASS format."""
        try:
            self.logger.info(f"Converting {srt_file} to ASS format")
            self.signals.log.emit(f"Converting {srt_file}")

            # Read the template file
            with open(self.template_file, 'r', encoding='utf-8') as f:
                template_content = f.read()

            # Read the SRT file
            with open(srt_file, 'r', encoding='utf-8') as f:
                srt_content = f.read()

            # Parse SRT content
            subtitle_blocks = re.split(r'\n\n+', srt_content.strip())
            events = []

            for block in subtitle_blocks:
                lines = block.strip().split('\n')
                if len(lines) >= 3:  # Valid subtitle block
                    # Parse timecode
                    timecode = lines[1]
                    start, end = timecode.split(' --> ')
                    
                    # Convert timecode format from SRT to ASS
                    start = self.convert_timestamp(start)
                    end = self.convert_timestamp(end)
                    
                    # Join all text lines
                    text = '\\N'.join(lines[2:])
                    
                    # Create ASS event line
                    event = f"Dialogue: 0,{start},{end},{self.style_name},,0,0,0,,{text}"
                    events.append(event)

            # Create ASS content
            ass_content = template_content + "\n\n[Events]\n"
            ass_content += "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
            ass_content += "\n".join(events)

            # Write ASS file
            ass_file = os.path.splitext(srt_file)[0] + '.ass'
            with open(ass_file, 'w', encoding='utf-8') as f:
                f.write(ass_content)

            self.logger.info(f"Successfully converted {srt_file} to {ass_file}")
            self.signals.file_completed.emit(srt_file, 100)
            return True

        except Exception as e:
            error_msg = f"Failed to convert {srt_file}: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            self.signals.error.emit(error_msg)
            return False

    def convert_timestamp(self, srt_timestamp):
        """Convert SRT timestamp format to ASS format."""
        # Remove milliseconds decimal point
        timestamp = srt_timestamp.replace(',', '.')
        # Ensure proper format (add leading zeros if needed)
        if len(timestamp) < 12:  # Missing leading zeros
            parts = timestamp.split(':')
            timestamp = f"{int(parts[0]):01d}:{int(parts[1]):02d}:{parts[2]}"
        return timestamp

    def run(self):
        """Execute the SRT to ASS conversion process."""
        try:
            self.logger.info("Starting batch conversion of files")
            total_files = len(self.files)
            completed = 0

            for srt_file in self.files:
                try:
                    if self.process_srt_to_ass(srt_file):
                        completed += 1
                        progress = (completed / total_files) * 100
                        self.signals.progress.emit(int(progress))
                except Exception as e:
                    self.logger.error(f"Error converting {srt_file}: {str(e)}")
                    self.signals.error.emit(f"Error converting {srt_file}: {str(e)}")

            self.logger.info("Conversion process completed")
            self.signals.log.emit("Conversion completed")
            self.signals.finished.emit()

        except Exception as e:
            error_msg = f"Critical error in conversion process: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            self.signals.error.emit(error_msg)
