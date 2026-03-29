import os
import json
from dotenv import load_dotenv

# Load the keys from your .env file
load_dotenv()

from modules.summarisation import Summarisation

def run_summarisation_demo():
    print("=== AI Meeting Summarizer: Summary Pipeline Test ===")
    
    # Check if the user has actually added an API key
    llm_key = os.getenv("LLM_API_KEY", "")
    if llm_key == "" or "your_" in llm_key.lower():
        print("WARNING: It looks like you haven't added a real LLM_API_KEY to your .env file yet.")
        print("    The request to the AI provider will likely fail. Please update your .env file first!")
        print("-" * 50)

    # 1. Initialize our new engine
    print("\n[1/3] Starting the Summarisation engine...")
    try:
        bot = Summarisation()
    except Exception as e:
        print(f"FAILED to initialize engine: {e}")
        return

    print(f"      Provider: {os.getenv('LLM_BASE_URL', 'https://api.openai.com/v1')}")
    print(f"      Model: {bot.model}")

    # 2. Setup a fake meeting transcript
    print("\n[2/3] Preparing mock meeting transcript...")
    
    # We create a fake Arabic transcript that looks exactly like the output from the Transcription module
    mock_transcript = {
        "full_text": (
            "علي: السلام عليكم شباب، خلينا نبدأ اجتماع المتابعة الأسبوعي. أحمد، إيه أخبار نقل قاعدة البيانات؟\n"
            "أحمد: وعليكم السلام. واجهت شوية مشاكل مع خوادم MongoDB. محتاج أراجع الفهارس (Indexes) قبل ما أكمل. هخلص الموضوع ده على يوم الخميس إن شاء الله.\n"
            "علي: تمام، بس تأكد إنك تنسق مع عمر عشانه مستني الجداول دي عشان يخلص لوحة التحكم (Dashboard) في الواجهة الأمامية.\n"
            "عمر: أيوة مظبوط، أنا حالياً واقف على الرسوم البيانية لحد ما الداتا بيز تجهز.\n"
            "علي: مفهوم. خلينا ناخد قرار الحين: هنوقف شغل على أي ميزات جديدة لحد ما نقل قاعدة البيانات يخلص 100%. أحمد، جدول اجتماع مع عمر يوم الجمعة الصبح عشان تفك البلوك بتاعه.\n"
            "أحمد: اتفقنا، هبعتلك الدعوة يا عمر.\n"
            "علي: ممتاز. وكمان لاحظت إننا ناقصنا توثيق (Documentation) للروابط البرمجية (API endpoints) الجديدة. خلينا نتابع الموضوع ده الأسبوع الجاي."
        ),
        "segments": [
            {"speaker": "علي", "start": 0.0, "end": 10.0},
            {"speaker": "أحمد", "start": 10.0, "end": 25.0},
            {"speaker": "علي", "start": 25.0, "end": 35.0},
            {"speaker": "عمر", "start": 35.0, "end": 45.0},
            {"speaker": "علي", "start": 45.0, "end": 60.0},
            {"speaker": "أحمد", "start": 60.0, "end": 65.0},
            {"speaker": "علي", "start": 65.0, "end": 75.0},
        ],
        "diarisation_available": True,
        "duration_seconds": 75.0,
        "language": "Arabic (ar)"
    }
    
    # 3. Process the report
    print("\n[3/3] Sending transcript to the AI for summarization and extracting analytics...")
    try:
        report = bot.generate_report(mock_transcript)
        
        print("\n\n" + "="*50)
        print("SUCCESS! HERE IS THE FINAL REPORT:")
        print("="*50)
        
        print("\nSUMMARY:")
        print("-" * 20)
        print(report.get("summary"))
        
        print("\nACTION ITEMS:")
        print("-" * 20)
        for item in report.get("action_items", []):
            print(f"  - [{item.get('assignee')}] {item.get('task')} (Deadline: {item.get('deadline')})")
            
        print("\nDECISIONS MADE:")
        print("-" * 20)
        for d in report.get("decisions", []):
            print(f"  - {d}")
            
        print("\nFOLLOW-UP POINTS:")
        print("-" * 20)
        for f in report.get("follow_up", []):
            print(f"  - {f}")
            
        print("\nSPEAKER ANALYTICS (Pure Math):")
        print("-" * 20)
        stats = report.get("speaker_stats", {})
        print(f"Total duration: {stats.get('total_meeting_duration_sec')} seconds")
        print(f"Most active speaker: {stats.get('most_active_speaker')}")
        print("\nBreakdown:")
        for spkr in stats.get("speakers", []):
            print(f"  - {spkr.get('speaker')}: {spkr.get('percentage_of_meeting')}% ({spkr.get('total_speaking_time_sec')}s across {spkr.get('number_of_turns')} turns)")

        print("\n" + "="*50)
        
    except Exception as e:
        print(f"\nPIPELINE FAILED: {e}")
        print("Did you enter a valid API key in your .env file?")

if __name__ == "__main__":
    run_summarisation_demo()
