import unittest
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent / "src"))

from emotion_dynamics import EmotionDynamics

class TestEmotionDynamics(unittest.TestCase):
    def test_initial_state(self):
        ed = EmotionDynamics()
        self.assertEqual(ed.pitch_val, 0.0)
        self.assertEqual(ed.speed_val, 0.0)
        
    def test_decay(self):
        ed = EmotionDynamics(decay_rate=0.5, pitch_sensitivity=0, speed_sensitivity=0)
        ed.pitch_val = 1.0
        ed.speed_val = 1.0
        
        # Update with no impact inputs (conf=1.0, ent=0.0)
        ed.update(confidence=1.0, entropy=0.0)
        
        self.assertAlmostEqual(ed.pitch_val, 0.5)
        self.assertAlmostEqual(ed.speed_val, 0.5)
        
        ed.update(confidence=1.0, entropy=0.0)
        self.assertAlmostEqual(ed.pitch_val, 0.25)
        self.assertAlmostEqual(ed.speed_val, 0.25)

    def test_impact(self):
        ed = EmotionDynamics(decay_rate=1.0, pitch_sensitivity=10.0, speed_sensitivity=1.0)
        
        # Low confidence (0.5) -> Impact = (1.0 - 0.5) * 10.0 = 5.0
        # Pitch subtracts impact -> -5.0
        res = ed.update(confidence=0.5, entropy=0.0)
        self.assertEqual(res["pitch_delta"], -5.0)
        
        # Accumulate
        # High Entropy (0.5) -> Impact = 0.5 * 1.0 = 0.5
        # Speed adds impact -> 0.0 + 0.5 = 0.5
        res = ed.update(confidence=1.0, entropy=0.5)
        self.assertEqual(res["pitch_delta"], -5.0) # Decay 1.0 so no change from prev
        self.assertEqual(res["speed_delta"], 0.5)

if __name__ == '__main__':
    unittest.main()
