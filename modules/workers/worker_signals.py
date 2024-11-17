"""
Worker signals for thread communication.
"""

from PyQt5.QtCore import QObject, pyqtSignal

class WorkerSignals(QObject):
    """
    Defines the signals available from a running worker thread.
    """
    finished = pyqtSignal()
    error = pyqtSignal(str)
    progress = pyqtSignal(int)
    log = pyqtSignal(str)
    file_completed = pyqtSignal(str, int)  # Emits filename and progress value
    status = pyqtSignal(str)  # Emits status messages
    result = pyqtSignal(object)  # Emits the result data
