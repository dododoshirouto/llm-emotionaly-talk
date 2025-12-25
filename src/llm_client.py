import requests
import json
from typing import Dict, Any, Generator, List
import subprocess
import time
import random

class OllamaClient:
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self.api_generate = f"{base_url}/api/generate"
        self._check_and_start_ollama()

    def _check_and_start_ollama(self):
        """
        Check if Ollama server is running, and start it if not.
        """
        try:
            requests.get(self.base_url)
            print("Ollama is already running.")
            return
        except requests.exceptions.ConnectionError:
            print("Ollama is not running. Attempting to start...")
        
        try:
            # subprocess.Popen will start the process in background
            # 'ollama serve' is the standard command
            # Creationflags=0x08000000 (CREATE_NO_WINDOW) to hide window if desired, 
            # but let's keep it simple or use CREATE_NEW_CONSOLE if needed.
            # On Windows, 'ollama' might be a shell command.
            # We use shell=True or find absolute path if needed.
            # Assuming 'ollama' is in PATH as verified by 'where ollama'
            subprocess.Popen("ollama serve", shell=True, creationflags=subprocess.CREATE_NEW_CONSOLE)
            
            # Wait for it to become responsive
            print("Waiting for Ollama to start...")
            for i in range(10):
                try:
                    time.sleep(2)
                    requests.get(self.base_url)
                    print("Ollama started successfully.")
                    return
                except requests.exceptions.ConnectionError:
                    if i == 9:
                         print("Timed out waiting for Ollama to start.")
            
        except FileNotFoundError:
             print("Ollama executable not found in PATH.")
        except Exception as e:
             print(f"Failed to start Ollama: {e}")

    def generate_stream(self, model: str, prompt: str, system: str = "", options: Dict[str, Any] = None) -> Generator[Dict[str, Any], None, None]:
        """
        Generator that yields processed chunks from Ollama.
        """
        payload = {
            "model": model,
            "prompt": prompt,
            "system": system,
            "stream": True,  # Keep streaming for real-time processing
            "options": options or {}
        }
        
        # To get logprobs, we usually need specific model support or API support.
        # Standard Ollama API currently (v0.1.x) might simplified response.
        # We'll check if we can get equivalent info.
        
        try:
            with requests.post(self.api_generate, json=payload, stream=True) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if line:
                        chunk = json.loads(line)
                        yield self._normalize(chunk)
                        
        except requests.exceptions.RequestException as e:
            print(f"Error calling Ollama: {e}")
            yield {"error": str(e)}

    def generate(self, model: str, prompt: str, system: str = "", options: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Non-streaming generation.
        """
        full_response = ""
        tokens = []
        
        for chunk in self.generate_stream(model, prompt, system, options):
            if "error" in chunk:
                return chunk
            
            if "token" in chunk:
                full_response += chunk["token"]
                tokens.append(chunk)
                
            if chunk.get("done", False):
                break
                
        return {
            "response": full_response,
            "tokens": tokens
        }

    def _normalize(self, chunk: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize Ollama response chunk to system standard.
        """
        # Debug: Print raw chunk to debug empty content
        # if not hasattr(self, "_debug_printed"):
        #      print(f"DEBUG First Chunk: {chunk}")
        #      self._debug_printed = True 
        
        # chunk structure typical:
        # { "model": "...", "created_at": "...", "response": "t", "done": false }
        # If 'logprobs' is supported/enabled, it might be in context?
        # Currently, Ollama might not return token-level probabilities in simple streaming mode easily
        # without looking at logits, which requires advanced setup or specific endpoints.
        # For Phase 1, we will handle the basic "response" field.
        # IF we cannot get logprobs, we will mock them or use a Placeholder for Phase 2 implementation.
        
        return {
            "token": chunk.get("response", ""),
            "done": chunk.get("done", False),
            
            # [MOCK] Emotional Data Injection
            # If API doesn't provide 'prob', we use SAFE DEFAULTS (Neutral).
            # prob: 1.0 (Confident)
            # entropy: 0.0 (Clear)
            
            "prob": chunk.get("prob", 1.0),
            "entropy": chunk.get("entropy", 0.0),
            
            # Future: Real extraction logic
            # "top_logprobs": [] 
        }

if __name__ == "__main__":
    client = OllamaClient()
    print("Sending request to Ollama...")
    # Assume 'qwen2.5:0.5b' or similar exists, or use 'llama3'
    # Adding a small timeout or check could be good.
    # We will use 'tinyllama' or whatever is available, but let's try a generic default.
    # User likely has models installed.
    
    # Simple test with non-streaming
    res = client.generate(model="qwen2.5:0.5b", prompt="Hello, how are you?")
    print("Response:", res["response"])
    print("Token count:", len(res["tokens"]))
