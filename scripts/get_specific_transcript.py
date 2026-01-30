import json
from pathlib import Path

TARGETS = [
    ("Lourdes_Youko_Kurama", "PTT-20250817-WA0071.opus"),
    ("Jonatan_Verdun", "PTT-20260105-WA0058.opus"),
]

BASE_DIR = Path("SOURCE_OF_TRUTH/voice_note_transcripts")

for chat, filename in TARGETS:
    json_path = BASE_DIR / chat / "transcripts.json"
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            found = False
            for item in data:
                if item["file"] == filename:
                    print(f"\n=== {chat} / {filename} ===")
                    print(item["text"])
                    found = True
                    break
            if not found:
                print(f"File {filename} not found in {chat}")
    except Exception as e:
        print(f"Error reading {json_path}: {e}")
