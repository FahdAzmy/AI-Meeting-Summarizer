import os
import time

from config.settings import Config
from modules.audio_capture import AudioCapture
from modules.transcription import Transcription

def run_end_to_end_demo():
    print("=== AI Meeting Summarizer Demo ===")
    print("Make sure OBS Studio is OPEN and WebSocket is turned on!")
    print("-" * 35)

    try:
        # 1. Connect to OBS
        print("[1/3] Connecting to OBS...")
        cfg = Config()
        obs_bot = AudioCapture(config=cfg)
        obs_bot.healthcheck()
        print("      Connected successfully!\n")

        # 2. Record audio
        print("[2/3] Starting OBS Recording for 10 seconds...")
        print("      --> SPEAK INTO YOUR MICROPHONE NOW! (Arabic or English) <--")
        obs_bot.start()
        
        # Countdown
        for i in range(10, 0, -1):
            print(f"      Recording... {i}s remaining", end='\r')
            time.sleep(1)
            
        print("\n      Stopping recording... waiting 2s for OBS to save the file:")
        audio_file_path = obs_bot.stop()
        time.sleep(2)
        print(f"      Saved file: {audio_file_path}\n")

        # 3. Transcribe with Deepgram
        print(f"[3/3] Sending audio to Deepgram for Deep Learning Transcription...")
        transcriber = Transcription(provider="assemblyai")
        
        start_time = time.time()
        result = transcriber.transcribe(audio_file_path)
        elapsed = time.time() - start_time
        
        print(f"      Transcription finished in {elapsed:.2f} seconds!\n")
        
        print("=" * 35)
        print("📝 FINAL TRANSCRIPT:")
        print("=" * 35)
        print(f"Language Detected: {result.get('language')}")
        print(f"Text String: \n\n{result.get('full_text')}\n")
        
        if result.get('diarisation_available'):
            print("--- Speaker Breakdown ---")
            for segment in result.get('segments', []):
                print(f"[{segment['start_time']}s - {segment['end_time']}s] {segment['speaker']}: {segment['text']}")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print("Did you remember to open OBS Studio?")

if __name__ == "__main__":
    run_end_to_end_demo()
