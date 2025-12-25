import sys
import os
from pathlib import Path
import json

# Add src to path if running from elsewhere
sys.path.append(str(Path(__file__).parent))

# Ensure utf-8 output (for Japanese logging)
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

from llm_client import OllamaClient
from text_processing import TextProcessor
from emotion_dynamics import EmotionDynamics
from alignment import TokenMoraMapper
from tts_engine import TTSEngine

def main():
    print("=== LLM Emotional Talk Pipeline [Prototype] ===")
    
    # 1. Initialize
    print("\n[Init] Initializing modules...")
    try:
        llm = OllamaClient()
        tp = TextProcessor()
        dynamics = EmotionDynamics(decay_rate=0.7, pitch_sensitivity=0.2, speed_sensitivity=0.1) # Adjusted sensitivity
        mapper = TokenMoraMapper(tp)
        tts = TTSEngine() # Speaker 1 = Zundamon
        speaker_id = 1
        
    except Exception as e:
        print(f"Initialization failed: {e}")
        return

    # 2. Get Prompt
    user_input = "Tell me a short story about a brave cat."
    # Or asking user: user_input = input("You: ")
    print(f"\n[Input] Prompt: {user_input}")

    # 3. LLM Generation
    print("[LLM] Generating text (with emotion analysis)...")
    # Using a model that definitely exists or default.
    model_name = "dodo-metan-gpt-oss:latest" 
    
    # We use non-streaming for Phase 1 simplicity, but streaming is better for latency.
    # Logic: Get full response -> Process -> Speak.
    
    # [Adjustment] Increased token limit to 5000 to handle 'thinking' process without cutoff
    llm_res = llm.generate(model=model_name, prompt=user_input, options={"num_predict": 5000})

    if "error" in llm_res:
        print(f"LLM Error: {llm_res['error']}")
        return
        
    tokens = llm_res["tokens"]
    full_text = llm_res["response"]
    print(f"[LLM] Raw Response ({len(tokens)} tokens): '{full_text[:100]}...'")
    
    # [Filter] Strip out <think>...</think> tags if present
    import re
    # Remove <think> content (DOTALL to match across newlines)
    clean_text = re.sub(r'<think>.*?</think>', '', full_text, flags=re.DOTALL).strip()
    
    if clean_text != full_text:
        print(f"[Proc] Filtered out thinking process. Length: {len(full_text)} -> {len(clean_text)}")
        full_text = clean_text
        
    if not full_text.strip():
        print("[Error] LLM generated empty text (or only thinking). Skipping TTS.")
        return
    
    # 4. Text Processing & Alignment Preparation
    print("[Proc] Mapping tokens to emotional data stream...")
    # This maps Token -> [Mora-like objects with emotion] (Naive)
    aligned_values = mapper.map_tokens_to_moras(tokens)
    
    # 5. AudioQuery Generation
    print("[TTS] Generating AudioQuery...")
    # Note: voicevox_core 0.15+ audio_query returns an object usually.
    audio_query = tts.generate_audio_query(full_text, speaker_id)
    
    # [Adjustment] Increase base speed for natural Japanese conversation
    try:
        current_speed = getattr(audio_query, "speedScale", 1.0)
        setattr(audio_query, "speedScale", 1.2)
        print(f"[TTS] Adjusted base speed: {current_speed} -> 1.2")
    except Exception as e:
        print(f"[TTS] Warning: Could not set speedScale: {e}")
    
    # 6. Alignment & Modulation
    print("[Mod] applying emotional dynamics...")
    
    # Get parallel list of emotions matching the query structure
    mora_emotions = mapper.get_aligned_emotions(audio_query, aligned_values)
    
    # Flatten query access for modification
    # We need to modify 'audio_query' in place.
    # Helper to traverse
    def get_attr(obj, key):
        if isinstance(obj, dict):
            return obj.get(key)
        else:
            return getattr(obj, key)

    def set_attr(obj, key, val):
        if isinstance(obj, dict):
            obj[key] = val
        else:
            setattr(obj, key, val)

    accent_phrases = get_attr(audio_query, "accent_phrases")
    
    mora_idx = 0
    dynamics.reset()
    
    for phrase in accent_phrases:
        moras = get_attr(phrase, "moras")
        for mora in moras:
            # Get emotion for this mora
            emo = mora_emotions[mora_idx]
            
            # Physics Update
            # In Phase 2: Confidence -> Pitch, Entropy -> Speed
    # [Log] Token-wise modulation summary
    print("[Mod] applying emotional dynamics (Token-wise Log)...")
    print(f"{'Token':<15} | {'Conf':<6} | {'Ent':<6} | {'Avg P-Delta':<11} | {'Avg S-Delta':<11}")
    print("-" * 65)
    
    # Helper to print stats
    def print_token_stat(text, stats):
         if not stats['pitch_deltas']: return
         avg_p = sum(stats['pitch_deltas']) / len(stats['pitch_deltas'])
         avg_s = sum(stats['speed_deltas']) / len(stats['speed_deltas'])
         # Ensure utf-8 output for stdout
         p_txt = f"{avg_p:+.4f}"
         s_txt = f"{avg_s:+.4f}"
         print(f"{text:<15} | {stats['conf']:.2f}   | {stats['ent']:.2f}   | {p_txt:<11} | {s_txt:<11}")

    last_token_text = None
    last_token_stats = {"pitch_deltas": [], "speed_deltas": [], "conf": 0.0, "ent": 0.0}
    
    for phrase in accent_phrases:
        moras = get_attr(phrase, "moras")
        for mora in moras:
            # Get emotion for this mora
            emo = mora_emotions[mora_idx]
            current_token_text = emo.get("source_token", "?")
            
            # Check for token change
            if current_token_text != last_token_text:
                if last_token_text is not None:
                     print_token_stat(last_token_text, last_token_stats)
                
                # Reset for new token
                last_token_text = current_token_text
                last_token_stats = {
                    "pitch_deltas": [], 
                    "speed_deltas": [], 
                    "conf": emo.get('confidence', 1.0), 
                    "ent": emo.get('entropy', 0.0)
                }
            
            # Physics Update
            # In Phase 2: Confidence -> Pitch, Entropy -> Speed
            state = dynamics.update(emo.get('confidence', 1.0), emo.get('entropy', 0.0))
            
            pitch_delta = state['pitch_delta']
            speed_delta = state['speed_delta']
            
            # Record for stats
            last_token_stats['pitch_deltas'].append(pitch_delta)
            last_token_stats['speed_deltas'].append(speed_delta)
            
            # Apply
            # mora.pitch is usually 0.0.
            # mora.vowel_length is duration in seconds.
            
            try:
                current_pitch = get_attr(mora, "pitch")
                current_length = get_attr(mora, "vowel_length")
            except AttributeError:
                # Fallback if structure is different
                mora_idx += 1
                continue
            
            # Debug log - Removed per-mora log
            # print(f"  [Mora {mora_idx:03d}] ...")

            set_attr(mora, "pitch", current_pitch + pitch_delta)
            
            # Length should not be negative.
            new_length = max(0.01, current_length + speed_delta)
            set_attr(mora, "vowel_length", new_length)
            
            mora_idx += 1
            
    # Print final token
    if last_token_text:
        print_token_stat(last_token_text, last_token_stats)
            
    print("[Mod] Modulation complete.")
    
    # 7. Synthesis
    print("[TTS] Synthesizing...")
    wav_data = tts.synthesis(audio_query, speaker_id)
    
    output_file = "output_emotional.wav"
    with open(output_file, "wb") as f:
        f.write(wav_data)
        
    print(f"\n[Done] Saved to {output_file}")
    
    # Playback? (Requires pyaudio/simpleaudio, skipped for now)

if __name__ == "__main__":
    main()
