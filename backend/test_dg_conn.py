import requests
import json
import os
from config.settings import Config

cfg = Config()
url = "https://api.deepgram.com/v1/listen?diarize=true&punctuate=true&detect_language=true"
headers = {
    "Authorization": f"Token {cfg.DEEPGRAM_API_KEY}",
    "Content-Type": "audio/wav"
}
print("Testing Deepgram API connectivity...")
try:
    # We will send a tiny bit of zeroes
    data = b'\x00' * 1024
    resp = requests.post(url, headers=headers, data=data, timeout=10)
    print("Status:", resp.status_code)
    print("Response:", resp.text)
except Exception as e:
    print("Error:", e)
