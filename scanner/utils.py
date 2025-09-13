import os, yaml, requests
from dotenv import load_dotenv

# Load variables from .env file if present
load_dotenv(override=False)

def env(name, default=None):
    """Get environment variable with optional default."""
    return os.getenv(name, default)

def load_allowlist(path):
    """Load YAML allowlist file and return a set of items."""
    if not os.path.exists(path):
        return set()
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return set(data.get("allowlist", []) or [])

def send_slack(message, attachments=None):
    """
    Send a message to Slack using the webhook URL in SLACK_WEBHOOK.
    If not configured, skip silently.
    """
    webhook = env("SLACK_WEBHOOK")
    if not webhook:
        print("[!] SLACK_WEBHOOK not set, skipping Slack notification")
        return

    payload = {"text": message}
    if attachments:
        payload["attachments"] = attachments

    try:
        resp = requests.post(webhook, json=payload, timeout=10)
        if resp.status_code != 200:
            print(f"[!] Slack webhook error {resp.status_code}: {resp.text}")
        else:
            print("[+] Sent Slack notification")
    except Exception as e:
        print(f"[!] Slack notification failed: {e}")
