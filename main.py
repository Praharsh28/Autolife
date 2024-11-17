"""
Main entry point for the media processing application.
"""

import sys
import os
import traceback
from dotenv import load_dotenv
from PyQt5.QtWidgets import QApplication, QMessageBox
from modules.main_window import MainWindow
from modules.utilities import setup_logger, ensure_app_directories

def main():
    """Main application entry point."""
    try:
        # Load environment variables from .env file
        load_dotenv()
        
        # Ensure application directories exist
        ensure_app_directories()
        
        # Initialize logger
        logger = setup_logger('main')
        logger.info("Starting application")
        
        # Verify API token
        api_token = os.getenv('HUGGINGFACE_API_TOKEN')
        if not api_token:
            raise ValueError("Hugging Face API token not found. Please check your .env file.")
        
        # Create application instance
        app = QApplication(sys.argv)
        
        # Create and show main window
        window = MainWindow()
        window.show()
        
        # Start event loop
        sys.exit(app.exec_())
        
    except Exception as e:
        error_msg = f"Application failed to start: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_msg)
        QMessageBox.critical(None, "Fatal Error", error_msg)
        sys.exit(1)

if __name__ == "__main__":
    main()
