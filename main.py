"""
AutoLife Media Tools - Main Application Entry Point
Version: 1.1.0 (Stable Release)
"""

import sys
import os
import logging
import traceback
from dotenv import load_dotenv
from PyQt5.QtWidgets import QApplication, QMessageBox
from modules.main_window import MainWindow
from modules.utilities import setup_logger, ensure_app_directories
from modules.constants import VERSION, VERSION_NAME

def main():
    """Main application entry point."""
    # Initialize logger first
    logger = None
    try:
        # Ensure application directories exist
        ensure_app_directories()
        
        # Setup logging
        logger = setup_logger('main')
        
        # Load environment variables
        load_dotenv()
        
        # Verify API token
        api_token = os.getenv('HUGGINGFACE_API_TOKEN')
        if not api_token:
            raise ValueError("Hugging Face API token not found. Please check your .env file.")
        
        # Create application
        app = QApplication(sys.argv)
        
        # Log version information
        logger.info(f"Starting AutoLife Media Tools v{VERSION} ({VERSION_NAME})")
        
        # Create and show main window
        window = MainWindow()
        window.show()
        
        # Start event loop
        sys.exit(app.exec_())
        
    except Exception as e:
        error_msg = f"Application failed to start: {str(e)}\n{traceback.format_exc()}"
        if logger:
            logger.critical(error_msg, exc_info=True)
        QMessageBox.critical(None, "Fatal Error", error_msg)
        sys.exit(1)

if __name__ == "__main__":
    main()
