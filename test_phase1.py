import sys
import os
from pathlib import Path

# Add src to sys.path
sys.path.append(str(Path(__file__).parent / "src"))

from text_processing import TextProcessor
from llm_client import OllamaClient
from tts_engine import TTSEngine

def main():
    print("=== Phase 1 Integration Test ===\n")

    # 1. Text Processing
    print("[1] Testing TextProcessor...")
    tp = TextProcessor()
    text = "Hello World"
    res = tp.analyze(text)
    print(f"  Input: {text}")
    print(f"  Result: {res}")
    if res['mora_count'] > 0:
        print("  -> OK")
    else:
        print("  -> NG")

    # 2. LLM Client
    print("\n[2] Testing OllamaClient...")
    client = OllamaClient()
    # Use 'tinyllama' or 'qwen2.5:0.5b' or 'llama2' - we need to know what's available.
    # We will try a lightweight one or default.
    model = "dodo-metan-gpt-oss:latest" # Updated to available model
    print(f"  Requesting generation from {model}...")
    
    try:
        # Simple short prompt
        llm_res = client.generate(model=model, prompt="Say hi.", options={"num_predict": 10})
        if "error" in llm_res:
             print(f"  -> Error: {llm_res['error']}")
             # Not fatal for this script if model wrong, but worth noting.
        else:
            print(f"  Response: {llm_res['response']}")
            print(f"  Tokens: {len(llm_res['tokens'])}")
            print("  -> OK")
    except Exception as e:
        print(f"  -> Exception: {e}")

    # 3. TTS Engine
    print("\n[3] Testing TTSEngine...")
    try:
        tts = TTSEngine()
        speaker_id = 1
        print("  Generating AudioQuery...")
        query = tts.generate_audio_query("これはテストです", speaker_id)
        print("  Synthesizing...")
        wav_data = tts.synthesis(query, speaker_id)
        print(f"  Generated {len(wav_data)} bytes")
        
        out_path = "phase1_test.wav"
        with open(out_path, "wb") as f:
            f.write(wav_data)
        print(f"  Saved to {out_path}")
        print("  -> OK")
    except Exception as e:
        print(f"  -> Error: {e}")

    print("\n=== Test Complete ===")

if __name__ == "__main__":
    main()
