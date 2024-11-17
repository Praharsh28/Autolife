import unittest
import numpy as np
from pathlib import Path
from modules.utils.sync_utils import SubtitleSynchronizer, SyncPoint

class TestSubtitleSynchronizer(unittest.TestCase):
    def setUp(self):
        self.sync = SubtitleSynchronizer()
        
        # Sample subtitle data
        self.original_subs = [
            {'start_time': 0.0, 'duration': 2.0, 'text': 'Hello'},
            {'start_time': 2.5, 'duration': 1.5, 'text': 'World'},
            {'start_time': 4.0, 'duration': 2.0, 'text': 'Test'}
        ]
        
        self.translated_subs = [
            {'start_time': 0.2, 'duration': 1.8, 'text': 'Hola'},
            {'start_time': 2.8, 'duration': 1.4, 'text': 'Mundo'},
            {'start_time': 4.5, 'duration': 1.8, 'text': 'Prueba'}
        ]
        
    def test_find_sync_points(self):
        sync_points = self.sync.find_sync_points(self.original_subs, self.translated_subs)
        
        # Should find at least one sync point
        self.assertGreater(len(sync_points), 0)
        
        # Check sync point structure
        for point in sync_points:
            self.assertIsInstance(point, SyncPoint)
            self.assertGreaterEqual(point.confidence, 0.0)
            self.assertLessEqual(point.confidence, 1.0)
            
    def test_calculate_transform(self):
        # Add sync points manually
        self.sync.sync_points = [
            SyncPoint(0.0, 0.2, 0.9),
            SyncPoint(2.5, 2.8, 0.8),
            SyncPoint(4.0, 4.5, 0.85)
        ]
        
        scale, offset = self.sync.calculate_transform()
        
        # Check reasonable bounds
        self.assertGreater(scale, 0.5)
        self.assertLess(scale, 2.0)
        self.assertGreater(offset, -1.0)
        self.assertLess(offset, 1.0)
        
    def test_apply_sync(self):
        # Set transform parameters
        self.sync.time_scale = 0.9
        self.sync.time_offset = 0.2
        
        synced_subs = self.sync.apply_sync(self.translated_subs)
        
        # Check subtitle count preserved
        self.assertEqual(len(synced_subs), len(self.translated_subs))
        
        # Check timing adjustments
        for orig, synced in zip(self.translated_subs, synced_subs):
            # New time should be (old_time * scale + offset)
            expected_start = orig['start_time'] * 0.9 + 0.2
            self.assertAlmostEqual(synced['start_time'], expected_start, places=2)
            
    def test_pattern_matching(self):
        pattern1 = [1.0, 2.0, 1.5]
        pattern2 = [0.9, 1.8, 1.4]
        
        matches = self.sync._find_pattern_matches(pattern1, pattern2)
        
        # Should find the matching pattern
        self.assertGreater(len(matches), 0)
        
    def test_confidence_calculation(self):
        sub1 = {'duration': 2.0, 'text': 'Test'}
        sub2 = {'duration': 1.8, 'text': 'Prueba'}
        
        confidence = self.sync._calculate_confidence(sub1, sub2)
        
        # Check confidence bounds
        self.assertGreaterEqual(confidence, 0.0)
        self.assertLessEqual(confidence, 1.0)
        
if __name__ == '__main__':
    unittest.main()
