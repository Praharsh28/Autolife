import numpy as np
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from ..constants import MIN_LINE_DURATION, MAX_LINE_DURATION

@dataclass
class SyncPoint:
    """Represents a synchronization point between original and translated subtitles."""
    original_time: float
    translated_time: float
    confidence: float

class SubtitleSynchronizer:
    """Utility class for synchronizing translated subtitles with original ones."""
    
    def __init__(self):
        self.sync_points: List[SyncPoint] = []
        self.time_scale: float = 1.0
        self.time_offset: float = 0.0
        
    def find_sync_points(self, original: List[Dict], translated: List[Dict]) -> List[SyncPoint]:
        """
        Find synchronization points between original and translated subtitles.
        Uses duration patterns and subtitle count to establish sync points.
        """
        sync_points = []
        
        # Get duration patterns
        orig_pattern = self._get_duration_pattern(original)
        trans_pattern = self._get_duration_pattern(translated)
        
        # Find matching patterns
        matches = self._find_pattern_matches(orig_pattern, trans_pattern)
        
        # Convert matches to sync points
        for orig_idx, trans_idx in matches:
            confidence = self._calculate_confidence(
                original[orig_idx],
                translated[trans_idx]
            )
            
            sync_point = SyncPoint(
                original_time=float(original[orig_idx]['start_time']),
                translated_time=float(translated[trans_idx]['start_time']),
                confidence=confidence
            )
            sync_points.append(sync_point)
            
        self.sync_points = sync_points
        return sync_points
        
    def calculate_transform(self) -> Tuple[float, float]:
        """
        Calculate time scale and offset for synchronization.
        Returns (scale, offset) tuple.
        """
        if len(self.sync_points) < 2:
            return 1.0, 0.0
            
        # Sort by confidence and take top points
        points = sorted(self.sync_points, key=lambda x: x.confidence, reverse=True)
        points = points[:min(len(points), 5)]  # Use top 5 points
        
        # Calculate average scale and offset
        scales = []
        offsets = []
        
        for i in range(len(points) - 1):
            for j in range(i + 1, len(points)):
                p1, p2 = points[i], points[j]
                
                # Calculate scale
                orig_diff = p2.original_time - p1.original_time
                trans_diff = p2.translated_time - p1.translated_time
                
                if trans_diff != 0:
                    scale = orig_diff / trans_diff
                    if 0.5 <= scale <= 2.0:  # Reasonable range
                        scales.append(scale)
                        
                        # Calculate offset using this scale
                        offset = p1.original_time - (p1.translated_time * scale)
                        offsets.append(offset)
                        
        if not scales:
            return 1.0, 0.0
            
        # Use median to avoid outliers
        self.time_scale = float(np.median(scales))
        self.time_offset = float(np.median(offsets))
        
        return self.time_scale, self.time_offset
        
    def apply_sync(self, subtitles: List[Dict]) -> List[Dict]:
        """Apply synchronization to subtitles."""
        if self.time_scale == 1.0 and self.time_offset == 0.0:
            return subtitles
            
        synced_subtitles = []
        
        for sub in subtitles:
            start_time = float(sub['start_time']) * self.time_scale + self.time_offset
            duration = float(sub['duration']) * self.time_scale
            
            # Ensure duration is within bounds
            duration = max(MIN_LINE_DURATION, min(MAX_LINE_DURATION, duration))
            
            synced_sub = sub.copy()
            synced_sub['start_time'] = start_time
            synced_sub['duration'] = duration
            synced_subtitles.append(synced_sub)
            
        return synced_subtitles
        
    def _get_duration_pattern(self, subtitles: List[Dict]) -> List[float]:
        """Extract duration pattern from subtitles."""
        return [float(sub['duration']) for sub in subtitles]
        
    def _find_pattern_matches(self, pattern1: List[float],
                            pattern2: List[float]) -> List[Tuple[int, int]]:
        """Find matching patterns between two subtitle sequences."""
        matches = []
        window_size = 3
        
        for i in range(len(pattern1) - window_size + 1):
            p1 = pattern1[i:i + window_size]
            
            for j in range(len(pattern2) - window_size + 1):
                p2 = pattern2[j:j + window_size]
                
                if self._patterns_match(p1, p2):
                    matches.append((i, j))
                    
        return matches
        
    def _patterns_match(self, p1: List[float], p2: List[float],
                       threshold: float = 0.2) -> bool:
        """Check if two patterns match within threshold."""
        if len(p1) != len(p2):
            return False
            
        # Normalize patterns
        p1_norm = np.array(p1) / np.mean(p1)
        p2_norm = np.array(p2) / np.mean(p2)
        
        # Calculate difference
        diff = np.abs(p1_norm - p2_norm)
        return np.mean(diff) < threshold
        
    def _calculate_confidence(self, sub1: Dict, sub2: Dict) -> float:
        """Calculate confidence score for a potential sync point."""
        # Base confidence on duration similarity
        duration_diff = abs(float(sub1['duration']) - float(sub2['duration']))
        duration_conf = max(0, 1 - (duration_diff / max(sub1['duration'], sub2['duration'])))
        
        # Could add more factors like:
        # - Text length similarity
        # - Presence of numbers or timestamps
        # - Speaker changes
        
        return duration_conf
        
    def get_sync_quality(self) -> float:
        """Get overall synchronization quality score."""
        if not self.sync_points:
            return 0.0
            
        # Average confidence of sync points
        confidences = [p.confidence for p in self.sync_points]
        return float(np.mean(confidences))
        
    def get_sync_stats(self) -> Dict:
        """Get synchronization statistics."""
        return {
            'sync_points': len(self.sync_points),
            'time_scale': self.time_scale,
            'time_offset': self.time_offset,
            'quality_score': self.get_sync_quality()
        }
