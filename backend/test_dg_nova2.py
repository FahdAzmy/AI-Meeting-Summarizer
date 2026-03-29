import requests
import mimetypes
from config.settings import Config

cfg = Config()
# Added model=nova-2 to see if it fixes the Deepgram endpoint crash
url = "https://api.deepgram.com/v1/listen?model=nova-2&diarize=true&punctuate=true&detect_language=true"
headers = {
    "Authorization": f"Token {cfg.DEEPGRAM_API_KEY}"
}

print("Testing Deepgram API connection with a fake MP4 file and model=nova-2...")
try:
    data = b'\x00\x00\x00\x18ftypmp42\x00\x00\x00\x00mp42mp41' + b'\x00' * 1024 # Fake MP4 header
    resp = requests.post(url, headers=headers, data=data, timeout=10)
    print("Status:", resp.status_code)
    print("Response:", resp.text)
except Exception as e:
    print("Error:", type(e).__name__, str(e))
