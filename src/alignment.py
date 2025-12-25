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

    def align_with_audio_query(self, audio_query: Dict[str, Any], aligned_values: List[Dict[str, Any]]):
        """
        Injects the aligned emotion values into the AudioQuery's moras.
        Note: AudioQuery generation by Voicevox might differ slightly in mora count
        than our naive calculation. We must handle length mismatch safely.
        """
        # audio_query is a dict (JSON). It has 'accent_phrases'.
        # Each accent_phrase has 'moras'.
        # We need to flatten the query's moras to iterate.
        
        query_moras_ref = []
        for phrase in audio_query.get("accent_phrases", []):
            for mora in phrase.get("moras", []):
                query_moras_ref.append(mora)
                
        # Now match aligned_values to query_moras_ref
        # Naive matching: 1-to-1 until one runs out.
        # Better: Ratio-based interpolation?
        # Given we are "simulating" physics, 1-to-1 mapping with stretching/compressing
        # or just simple cutoff is okay for Phase 2 prototype.
        
        # Our Count vs True Count
        our_count = len(aligned_values)
        true_count = len(query_moras_ref)
        
        print(f"Alignment Debug: Est Moras: {our_count}, Actual Moras: {true_count}")
        
        # Mapping loop
        for i, q_mora in enumerate(query_moras_ref):
            if i < our_count:
                vals = aligned_values[i]
                # Inject temp values into mora for later consumption by Physics Engine?
                # Or apply Physics HERE?
                # Architecture: 
                # 1. Map Tokens -> Emotion Stream (Confidence/Entropy)
                # 2. Physics Engine processes Stream -> Dynamics Stream (Pitch/Speed Delta)
                # 3. Dynamics Stream applies to Moras.
                
                # We can store the raw emotion metrics in the mora dict for now
                q_mora["_emotion_confidence"] = vals["confidence"]
                q_mora["_emotion_entropy"] = vals["entropy"]
            else:
                # Out of bounds - use defaults
                q_mora["_emotion_confidence"] = 1.0
                q_mora["_emotion_entropy"] = 0.0

        return audio_query
