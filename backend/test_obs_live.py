import time
import os
import sys

# Ensure backend root is in search path
backend_root = os.path.dirname(os.path.abspath(__file__))
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

# Import our capture module
from modules.audio_capture import AudioCapture
from config.settings import Config

def manual_test():
    print("--- OBS WebSocket Live Manual Test ---")
    
    # 1. Setup config and module instance
    try:
        cfg = Config()
        print(f"Connecting to OBS at {cfg.OBS_HOST}:{cfg.OBS_PORT}...")
        bot = AudioCapture(config=cfg)
    except Exception as e:
        print(f"FAILED to initialize or connect: {e}")
        return

    # 2. Perform Healthcheck
    try:
        if bot.healthcheck():
            print("SUCCESS: OBS is responding correctly to healthcheck.\n")
    except Exception as e:
        print(f"FAILED Healthcheck: {e}")
        return

    # 3. Test Recording Lifecycle (Start -> Wait -> Stop)
    try:
        print("Recording starting in 5 seconds (check OBS to see progress)...")
        bot.start()
        
        # Recording for 5 seconds
        for i in range(5, 0, -1):
            print(f"Recording... {i}")
            time.sleep(1)
            
        print("Stopping recording...")
        
        # --- Debug: inspect the raw response first ---
        raw = bot.client.stop_record()
        print(f"\n[DEBUG] Response type : {type(raw)}")
        print(f"[DEBUG] Response attrs : {vars(raw) if hasattr(raw, '__dict__') else dir(raw)}")
        
        # Manually extract path for verification
        path = (
            getattr(raw, "output_path", None)
            or getattr(raw, "outputPath", None)
            or (vars(raw).get("output_path") if hasattr(raw, "__dict__") else None)
            or (vars(raw).get("outputPath") if hasattr(raw, "__dict__") else None)
        )
        file_path = path
        print(f"[DEBUG] Extracted path: {file_path}\n")

        print("\n--- TEST COMPLETED SUCCESSFULLY ---")
        print(f"Recording saved at: {file_path}")
        print("Please check the above path to hear the captured audio.")
        
    except Exception as e:
        print(f"\nFAILED test sequence: {e}")

if __name__ == "__main__":
    manual_test()
