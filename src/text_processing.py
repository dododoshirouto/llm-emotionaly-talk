import re
import alkana
import pykakasi

class TextProcessor:
    def __init__(self):
        self.kks = pykakasi.kakasi()
        # New API doesn't use setMode or getConverter in the same way for simple conversion?
        # Actually proper usage of 2.x+ is:
        # kks = pykakasi.kakasi()
        # result = kks.convert(text)
        # result is a list of dicts.
        pass

    def get_kana(self, text: str) -> str:
        """
        Convert mixed text (English/Japanese) to Katakana/Hiragana reading.
        English words are converted to Katakana via alkana.
        """
        def replace_eng(match):
            word = match.group(0)
            kana = alkana.get_kana(word.lower())
            if kana:
                return kana
            return word

        text_with_kana = re.sub(r'[a-zA-Z]+', replace_eng, text)
        
        # Use pykakasi new API
        converted = self.kks.convert(text_with_kana)
        # converted is list of items: [{'orig': '...', 'hira': '...', 'kana': '...', 'hepburn': '...', 'kunrei': '...', 'passport': '...'}]
        # We want 'hira' (Hiragana) or 'kana' (Katakana). Let's use Hiragana for reading.
        
        result_str = ""
        for item in converted:
            result_str += item['hira']
            
        return result_str

    def count_moras(self, text: str) -> int:
        """
        Estimate the number of moras in the text.
        This is needed for Phase 2 alignment.
        """
        kana = self.get_kana(text)
        # Naive mora counting (counting chars, excluding small ya/yu/yo/tsu if following?)
        # A simple approximation for now:
        # Filter out characters that are not independent moras (like small tsu, small ya/yu/yo) PRECEDING a vowel? 
        # Actually standard mora counting: 
        # - Small ya, yu, yo (ャ, ュ, ョ) are part of previous mora.
        # - Small tsu (ッ) IS a mora.
        # - Long vowel mark (ー) IS a mora.
        
        # Hiragana checks
        # Small ya/yu/yo/a/i/u/e/o shouldn't count if they modify previous char?
        # Actually small a/i/u/e/o (ex. ファ) -> Fu+a -> 1 mora or 2? 
        # Usually counted as 1 mora in 'Fa'.
        
        # Let's count all chars, subtract for small ya/yu/yo/wa (?) attached to prev.
        # Simpler: regex count.
        
        count = len(kana)
        # Subtract for small ya/yu/yo (only if they follow a valid mora base? assume yes)
        # ぁぃぅぇぉ are tricky. ファ (fa) = 1 mora. But あぁ (a a) = 2 moras?
        # Let's treat small ya/yu/yo as non-mora (modifiers).
        
        modifiers = getattr(self, '_modifiers', None)
        if not modifiers:
            # defined common small kana
            self._modifiers = set("ぁぃぅぇぉゃゅょゎァィゥェォャュョヮ")
            # Note: Voicevox AquesTalk style might differ.
            # But standard Japanese:
            # きゃ (kya) = 1 mora.
            # ふぁ (fa) = 1 mora.
            # っと (tto) = 2 moras (small tsu is 1).
        
        mora_count = 0
        for i, char in enumerate(kana):
            if char in self._modifiers:
                # usually these don't count as a stand-alone mora
                pass
            else:
                mora_count += 1
                
        # Special case: small tsu (っ/ッ) IS 1 mora.
        # But it is in _modifiers? No, small tsu is distinct.
        # My set above includes ぁぃぅぇぉ... let's refine.
        
        # Proper list of non-mora small characters (contracted sounds):
        # ゃ ゅ ょ ゎ (ya, yu, yo, wa) - usually attached. 
        # ぁ ぃ ぅ ぇ ぉ (a, i, u, e, o) - can be attached (fa, ti, etc) or standalone.
        # For simplicity in Phase 1, let's treat them as non-mora if they are small.
        # Except 'ッ' (small tsu) which IS a mora.
        
        return mora_count

    def analyze(self, text: str) -> dict:
        reading = self.get_kana(text)
        mora_count = 0
        
        # Refined mora counting logic
        # Count all chars first
        # Subtract 1 for each Cy/Cw/V combinations (small chars)
        # But keep small tsu (ッ/っ) as 1 mora.
        
        small_kana = set("ぁぃぅぇぉゃゅょゎァィゥェォャュョヮ")
        # ッ/っ is NOT in this set, so it counts as 1.
        
        for c in reading:
            if c not in small_kana:
                mora_count += 1
                
        return {
            "original": text,
            "reading": reading,
            "mora_count": mora_count
        }

if __name__ == "__main__":
    tp = TextProcessor()
    samples = [
        "Hello World",
        "これはテストです。",
        "Running in the 90s",
        "Pythonのライブラリ",
        "ちょっと待って",
        "ファイル"
    ]
    for s in samples:
        print(f"Input: {s}")
        print(f"Result: {tp.analyze(s)}")
        print("-" * 20)
