"""Send lab alerts. Secrets and webhook addresses are never printed."""
import json
import os
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / "_7_board_test" / ".env")
STUDENT = os.getenv("STUDENT", "").strip()
N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", "").strip()
TIMEOUT = 10
ALERTS = [
    {"ip": "203.0.113.10", "level": 10, "rule": "5712", "fail_count": 1},
    {"ip": "203.0.113.11", "level": 3, "rule": "5712", "fail_count": 1},
]


def main():
    if not STUDENT or not N8N_WEBHOOK_URL:
        print("Missing STUDENT or N8N_WEBHOOK_URL in local .env")
        return 1
    payload = {"student": STUDENT, "alerts": ALERTS}
    print(json.dumps(payload, ensure_ascii=False))
    try:
        response = requests.post(N8N_WEBHOOK_URL, json=payload, timeout=TIMEOUT,
                                 allow_redirects=False)
    except requests.RequestException:
        print("[n8n] Transmission failed. Check server and local configuration.")
        return 1
    print(f"[n8n] POST -> {response.status_code}")
    if not 200 <= response.status_code < 300:
        print("[n8n] Request rejected. Check workflow configuration.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
