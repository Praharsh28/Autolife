import unittest
from pathlib import Path
import tempfile
import time
from modules.processing.batch_manager import BatchManager, ProcessingStatus, ProcessingTask

class TestBatchManager(unittest.TestCase):
    def setUp(self):
        self.manager = BatchManager(max_concurrent=2)
        self.temp_dir = tempfile.mkdtemp()
        
        # Create test files
        self.test_files = []
        for i in range(3):
            path = Path(self.temp_dir) / f"test_{i}.mp4"
            path.touch()
            self.test_files.append(path)
            
        # Test languages
        self.test_langs = ['es', 'fr', 'de']
        
    def tearDown(self):
        self.manager.stop_processing()
        
        # Cleanup test files
        for file in self.test_files:
            file.unlink()
        Path(self.temp_dir).rmdir()
        
    def test_add_task(self):
        task_id = self.manager.add_task(self.test_files[0], self.test_langs)
        
        # Check task added
        self.assertIn(task_id, self.manager.tasks)
        
        # Check task properties
        task = self.manager.tasks[task_id]
        self.assertEqual(task.file_path, self.test_files[0])
        self.assertEqual(task.target_languages, self.test_langs)
        self.assertEqual(task.status, ProcessingStatus.PENDING)
        
    def test_duplicate_task(self):
        # Add same task twice
        task_id1 = self.manager.add_task(self.test_files[0], ['es'])
        task_id2 = self.manager.add_task(self.test_files[0], ['fr'])
        
        # Should be same task with combined languages
        self.assertEqual(task_id1, task_id2)
        task = self.manager.tasks[task_id1]
        self.assertEqual(set(task.target_languages), {'es', 'fr'})
        
    def test_start_stop_processing(self):
        self.manager.start_processing()
        
        # Check workers started
        self.assertTrue(self.manager.running)
        self.assertEqual(len(self.manager.workers), 2)  # max_concurrent=2
        
        self.manager.stop_processing()
        
        # Check workers stopped
        self.assertFalse(self.manager.running)
        self.assertEqual(len(self.manager.workers), 0)
        
    def test_cancel_task(self):
        task_id = self.manager.add_task(self.test_files[0], self.test_langs)
        self.manager.cancel_task(task_id)
        
        # Check task cancelled
        task = self.manager.tasks[task_id]
        self.assertEqual(task.status, ProcessingStatus.CANCELLED)
        
    def test_task_callbacks(self):
        completed_tasks = []
        error_tasks = []
        progress_updates = []
        
        def on_complete(task_id, task):
            completed_tasks.append(task_id)
            
        def on_error(task_id, error):
            error_tasks.append(task_id)
            
        def on_progress(task_id, progress):
            progress_updates.append((task_id, progress))
            
        self.manager.on_task_complete = on_complete
        self.manager.on_task_error = on_error
        self.manager.on_progress_update = on_progress
        
        # Add and process task
        task_id = self.manager.add_task(self.test_files[0], self.test_langs)
        self.manager.start_processing()
        
        # Wait for processing
        time.sleep(2)
        
        # Check callbacks triggered
        self.assertGreater(len(progress_updates), 0)
        self.assertEqual(len(completed_tasks) + len(error_tasks), 1)
        
    def test_concurrent_processing(self):
        # Add multiple tasks
        task_ids = [
            self.manager.add_task(file, self.test_langs)
            for file in self.test_files
        ]
        
        self.manager.start_processing()
        time.sleep(1)  # Let processing start
        
        # Check concurrent processing
        processing_count = sum(
            1 for task in self.manager.tasks.values()
            if task.status == ProcessingStatus.PROCESSING
        )
        self.assertLessEqual(processing_count, 2)  # max_concurrent=2
        
if __name__ == '__main__':
    unittest.main()
