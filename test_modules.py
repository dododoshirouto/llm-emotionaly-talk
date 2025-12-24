import sys
import os
import ctypes
from pathlib import Path

def print_result(name, success, message=""):
    if success:
        print(f"[OK] {name}: {message}")
    else:
        print(f"[NG] {name}: {message}")

def main():
    print("=== Module Verification Start ===\n")

    # 1. Setup paths for Voicevox Core
    # DLLs are in ./voicevox_core
    base_dir = Path(__file__).parent
    core_dir = base_dir / "voicevox_core"
    
    if not core_dir.exists():
        print_result("Environment", False, f"Directory not found: {core_dir}")
        return
    else:
        # Add to PATH so DLLs can be found
        os.environ["PATH"] = str(core_dir) + os.pathsep + os.environ["PATH"]
        # Also try to load explicitly if needed, but PATH update is usually enough for Windows
        print_result("Environment", True, f"voicevox_core dir found at {core_dir}")

    # 2. Check requests
    try:
        import requests
        print_result("requests", True, f"v{requests.__version__}")
    except Exception as e:
        print_result("requests", False, str(e))

    # 3. Check numpy
    try:
        import numpy
        print_result("numpy", True, f"v{numpy.__version__}")
    except Exception as e:
        print_result("numpy", False, str(e))

    # 4. Check pykakasi
    try:
        import pykakasi
        kks = pykakasi.kakasi()
        version = getattr(pykakasi, "__version__", "unknown")
        print_result("pykakasi", True, f"v{version} (Converter init OK)")
    except Exception as e:
        print_result("pykakasi", False, str(e))

    # 5. Check alkana
    try:
        import alkana
        res = alkana.get_kana("hello")
        if res == "ハロー":
            print_result("alkana", True, f"Conversion OK ('hello' -> '{res}')")
        else:
            print_result("alkana", False, f"Unexpected result: {res}")
    except Exception as e:
        print_result("alkana", False, str(e))

    # 6. Check voicevox_core
    try:
        from voicevox_core import VoicevoxCore, AccelerationMode
        
        # Initialize
        # Need open_jtalk config
        dict_dir = core_dir / "open_jtalk_dic_utf_8-1.11"
        if not dict_dir.exists():
            print_result("voicevox_core", False, f"Dictionary not found at {dict_dir}")
        else:
            # Attempt to initialize Core
            # Note: 0.15.x usually requires loading the library explicitly if not done by init?
            # actually VoicevoxCore(...) in python binding handles it if DLL is findable.
            core = VoicevoxCore(
                acceleration_mode=AccelerationMode.CPU,
                open_jtalk_dict_dir=str(dict_dir)
            )
            print_result("voicevox_core", True, "Initialization OK")
            
            # Check versions / speakers logic if needed (optional)
            # metas = core.metas
            # print(f"   -> Found {len(metas)} speakers")

    except ImportError as e:
        print_result("voicevox_core", False, f"ImportError: {e} (Maybe DLL missing in PATH?)")
    except Exception as e:
        print_result("voicevox_core", False, f"RuntimeError: {e}")

    print("\n=== Verification End ===")

if __name__ == "__main__":
    main()
