import os
import time
import json
from dotenv import load_dotenv

from config.settings import Config
from modules.audio_capture import AudioCapture
from modules.transcription import Transcription
from modules.summarisation import Summarisation

def run_full_pipeline_demo():
    print("======================================================")
    print("🎙️ AI Meeting Summarizer: FULL END-TO-END PIPELINE 🧠")
    print("======================================================")
    
    # Check for keys quickly
    load_dotenv()
    if os.getenv("LLM_API_KEY", "") == "" or "your_" in os.getenv("LLM_API_KEY", "").lower():
        print("⚠️ WARNING: You have no LLM_API_KEY set. The final step will fail.")
        
    print("\nPREREQUISITE: Ensure OBS Studio is OPEN and WebSocket is turned on!")
    print("-" * 50)

    try:
        # --- 1. AUDIO CAPTURE ---
        print("\n[1/3] AUDIO CAPTURE (OBS Studio)")
        cfg = Config()
        obs_bot = AudioCapture(config=cfg)
        obs_bot.healthcheck()
        print("      ✅ Connected to OBS successfully.")

        print("      --> STARTING RECORDING. SPEAK ARABIC (or English) FOR 20 SECONDS! <--")
        obs_bot.start()
        
        # 20 second countdown
        for i in range(20, 0, -1):
            print(f"      Recording... {i}s remaining", end='\r')
            time.sleep(1)
            
        print("\n      Stopping recording... waiting for OBS to save the file:")
        audio_file_path = obs_bot.stop()
        time.sleep(2)  # Give OBS a moment to flush the file to disk
        print(f"      ✅ Audio saved to: {audio_file_path}")

        # --- 2. TRANSCRIPTION ---
        print("\n[2/3] TRANSCRIPTION (Deepgram/AssemblyAI)")

        # language_code options:
        #   None  → auto-detect from the audio (Arabic or English) ← RECOMMENDED
        #   "en"  → force English only
        #   "ar"  → force Arabic only
        transcriber = Transcription(provider="assemblyai", language_code=None)

        
        print(f"      Sending audio for speech-to-text (with speaker separation)...")
        start_time = time.time()
        transcript_result = transcriber.transcribe(audio_file_path)
        elapsed = time.time() - start_time
        
        print(f"      ✅ Transcription finished in {elapsed:.2f} seconds!")
        print(f"      Language Detected: {transcript_result.get('language')}")
        
        # --- 3. SUMMARISATION ---
        print("\n[3/3] SUMMARISATION & ANALYSIS (LLM)")
        bot = Summarisation()
        print(f"      LLM Provider: {os.getenv('LLM_BASE_URL', 'https://api.openai.com/v1')} | Model: {bot.model}")
        print("      Sending transcript to AI to build structured meeting report...")
        
        report = bot.generate_report(transcript_result)
        
        # --- DONE! PRINT EVERYTHING ---
        print("\n\n" + "="*60)
        print("🎯 FINAL PIPELINE OUTPUT:")
        print("="*60)
        
        print("\n📝 RAW TRANSCRIPT:")
        print("-" * 20)
        print(transcript_result.get("full_text"))
        
        print("\n✨ AI SUMMARY:")
        print("-" * 20)
        print(report.get("summary"))
        
        print("\n📌 ACTION ITEMS:")
        print("-" * 20)
        action_items = report.get("action_items", [])
        if not action_items:
            print("  - None assigned")
        for item in action_items:
            print(f"  - [{item.get('assignee')}] {item.get('task')} (Deadline: {item.get('deadline')})")
            
        print("\n⚖️ DECISIONS:")
        print("-" * 20)
        for d in report.get("decisions", []):
            print(f"  - {d}")
            
        print("\n🔍 FOLLOW-UP POINTS:")
        print("-" * 20)
        for f in report.get("follow_up", []):
            print(f"  - {f}")
            
        print("\n📊 SPEAKER ANALYTICS (Pure Math):")
        print("-" * 20)
        stats = report.get("speaker_stats")
        if stats:
            print(f"Total meeting duration: {stats.get('total_meeting_duration_sec')} seconds")
            print(f"Most active speaker: {stats.get('most_active_speaker')}")
            for spkr in stats.get("speakers", []):
                print(f"  - {spkr.get('speaker')}: {spkr.get('percentage_of_meeting')}% ({spkr.get('total_speaking_time_sec')}s across {spkr.get('number_of_turns')} turns)")
        else:
            print("  - Diarisation not available for this recording.")
            
        print("\n" + "="*60)
        
    except Exception as e:
        print(f"\n❌ PIPELINE ERROR: {e}")
        print("Check your OBS connection and API keys in the .env file.")

if __name__ == "__main__":
    run_full_pipeline_demo()
