import unittest
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent / "src"))

from alignment import TokenMoraMapper
from text_processing import TextProcessor

class TestAlignment(unittest.TestCase):
    def setUp(self):
        self.tp = TextProcessor()
        self.mapper = TokenMoraMapper(self.tp)

    def test_token_to_moras(self):
        # "こんにちは" -> 5 moras
        tokens = [
            {"token": "こんにちは", "prob": 0.8, "entropy": 0.1}
        ]
        
        moras = self.mapper.map_tokens_to_moras(tokens)
        self.assertEqual(len(moras), 5)
        self.assertEqual(moras[0]["confidence"], 0.8)
        self.assertEqual(moras[0]["source_token"], "こんにちは")

    def test_alignment_integration(self):
        # Mock AudioQuery structure
        query = {
            "accent_phrases": [
                {
                    "moras": [
                        {"text": "こ", "pitch": 0.0},
                        {"text": "ん", "pitch": 0.0},
                        {"text": "に", "pitch": 0.0},
                        {"text": "ち", "pitch": 0.0},
                        {"text": "は", "pitch": 0.0}
                    ]
                }
            ]
        }
        
        tokens = [{"token": "こんにちは", "prob": 0.5, "entropy": 0.2}]
        aligned_vals = self.mapper.map_tokens_to_moras(tokens)
        
        result = self.mapper.align_with_audio_query(query, aligned_vals)
        
        # Check if internal "private" keys were added
        mora0 = result["accent_phrases"][0]["moras"][0]
        self.assertTrue("_emotion_confidence" in mora0)
        self.assertEqual(mora0["_emotion_confidence"], 0.5)

if __name__ == '__main__':
    unittest.main()
