from pathlib import Path
from voicevox_core import VoicevoxCore, AccelerationMode
# import simpleaudio as sa # Use simpleaudio or similar if needed, or just return bytes.
# Plan says pyaudio for playback, but Voicevox generates wav bytes.
# We will focus on generation first.

import os

class TTSEngine:
    def __init__(self, core_dir: str = "./voicevox_core", use_gpu: bool = False):
        self.core_dir = Path(core_dir).absolute()
        self.dict_dir = self.core_dir / "open_jtalk_dic_utf_8-1.11"
        
        if not self.dict_dir.exists():
            raise FileNotFoundError(f"OpenJTalk dictionary not found at {self.dict_dir}")
        
        # Add core_dir to PATH for DLL loading
        if str(self.core_dir) not in os.environ["PATH"]:
            os.environ["PATH"] = str(self.core_dir) + os.pathsep + os.environ["PATH"]
            
        acceleration_mode = AccelerationMode.GPU if use_gpu else AccelerationMode.CPU
        
        # Initialize Core
        self.core = VoicevoxCore(
            acceleration_mode=acceleration_mode,
            open_jtalk_dict_dir=str(self.dict_dir)
        )
        
        # Load model is not needed for VoicevoxCore 0.15+? 
        # Typically needed to load speaker model.
        # But 'voicevox_core' (the python binding for shared lib) might need 'load_model(speaker_id)'?
        # Let's check documentation or assume 0.15+ style:
        # core.load_model(speaker_id) is required.
        self._loaded_speakers = set()

    def load_speaker(self, speaker_id: int):
        if speaker_id not in self._loaded_speakers:
            if not self.core.is_model_loaded(speaker_id):
                self.core.load_model(speaker_id)
            self._loaded_speakers.add(speaker_id)

    def generate_audio_query(self, text: str, speaker_id: int):
        self.load_speaker(speaker_id)
        return self.core.audio_query(text, speaker_id)

    def synthesis(self, query, speaker_id: int) -> bytes:
        self.load_speaker(speaker_id)
        return self.core.synthesis(query, speaker_id)

if __name__ == "__main__":
    # Test
    try:
        engine = TTSEngine()
        speaker = 1 # Zundamon Normal usually
        text = "これはテストです"
        
        print(f"Generating query for: {text}")
        query = engine.generate_audio_query(text, speaker)
        print("Query generated.")
        
        # We can modify query here if needed (Phase 2/3)
        
        print("Synthesizing...")
        wav_data = engine.synthesis(query, speaker)
        print(f"Wav data size: {len(wav_data)} bytes")
        
        # Save to file
        with open("test_output.wav", "wb") as f:
            f.write(wav_data)
        print("Saved to test_output.wav")
        
    except Exception as e:
        print(f"Error: {e}")
