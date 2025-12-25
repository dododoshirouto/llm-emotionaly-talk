from typing import List, Dict, Any
from text_processing import TextProcessor

class TokenMoraMapper:
    def __init__(self, text_processor: TextProcessor):
        self.tp = text_processor

    def map_tokens_to_moras(self, tokens: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Takes a list of normalized LLM tokens (with 'token', 'prob', 'top_logprobs' etc.)
        Returns a list of 'mora-like' structures aligned with emotion values.
        
        This is an intermediate representation. 
        Real Voicevox AudioQuery moras will be matched against this later.
        """
        aligned_moras = []
        
        for token_data in tokens:
            text = token_data.get("token", "")
            confidence = token_data.get("prob", 1.0)
            
            # Use 'top_logprobs' to calculate naive entropy if not provided
            # For now standardizing logprobs/entropy handling might be outside scope here,
            # assuming 'entropy' might be pre-calculated or we use a placeholder.
            # Let's look for 'entropy' key, else 0.0
            entropy = token_data.get("entropy", 0.0)
            
            # Analyze token
            analysis = self.tp.analyze(text)
            read_str = analysis["reading"]
            mora_count = analysis["mora_count"]
            
            # If no moras (punctuation, spaces, etc), we still might want to track it 
            # or just skip for emotion mapping?
            # Voicevox has pauses.
            # Let's create an entry per moral
            
            if mora_count > 0:
                # Distribute this token's emotion to its moras
                # Simple strategy: Copy values.
                for _ in range(mora_count):
                    aligned_moras.append({
                        "source_token": text,
                        "confidence": confidence,
                        "entropy": entropy,
                        # We don't know exact char/mora assignment here without meticulous aligning
                        # But we just need the stream of values.
                    })
            else:
                # No moras (maybe silence/punctuation)
                pass
                
        return aligned_moras

    def get_aligned_emotions(self, audio_query: Any, aligned_values: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Returns a list of emotion data dicts that corresponds 1-to-1 with the 
        flattened moras of the provided audio_query.
        """
        # 1. Flatten the AudioQuery moras to count them and establish order
        #    Note: audio_query might be a Dict or an Object depending on binding.
        #    We assume attribute access 'accent_phrases' works or dict access.
        #    Safe way: try dict access, fall back to attribute.
        
        def get_attr(obj, key):
            if isinstance(obj, dict):
                return obj.get(key)
            else:
                return getattr(obj, key, [])

        accent_phrases = get_attr(audio_query, "accent_phrases")
        
        flattened_moras = []
        for phrase in accent_phrases:
            moras = get_attr(phrase, "moras")
            for mora in moras:
                flattened_moras.append(mora)
                
        # 2. Map aligned_tokens to these moras
        #    We assume the text processing phase aligned roughly correctly.
        #    We will stretch/compress or just map 1:1.
        
        final_emotions = []
        
        token_mora_idx = 0
        total_token_moras = len(aligned_values)
        
        for i, _ in enumerate(flattened_moras):
            if token_mora_idx < total_token_moras:
                # Copy emotion from the aligned token-mora
                final_emotions.append(aligned_values[token_mora_idx])
                token_mora_idx += 1
            else:
                # Padding if query is longer than expected
                final_emotions.append({
                    "confidence": 1.0, 
                    "entropy": 0.0,
                    "source_token": "__PAD__"
                })
                
        return final_emotions
