import os
import socket
import time
import requests


BOT_TOKEN_ENV = "TELEGRAM_BOT_TOKEN"
CHAT_ID_ENV = "TELEGRAM_CHAT_ID"


def _escape_md_v2(text):
    # Telegram MarkdownV2 special chars must be escaped
    # See: _*[]()~`>#+-=|{}.! 
    if text is None:
        return ""
    text = str(text)
    escape_chars = r"_*[]()~`>#+-=|{}.!\\"
    out = []
    for ch in text:
        if ch in escape_chars:
            out.append("\\" + ch)
        else:
            out.append(ch)
    return "".join(out)


def hostname():
    try:
        return socket.gethostname()
    except Exception:
        return "unknown"


def send_message(message, retries=3, timeout=10):
    token = os.environ.get(BOT_TOKEN_ENV)
    chat_id = os.environ.get(CHAT_ID_ENV)
    if not token or not chat_id:
        raise RuntimeError("TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID is not set")

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "MarkdownV2",
        "disable_web_page_preview": True,
    }

    last_err = None
    for _ in range(retries):
        try:
            resp = requests.post(url, data=payload, timeout=timeout)
            if resp.status_code == 200:
                return True
            last_err = RuntimeError(f"Telegram API error: {resp.status_code} {resp.text}")
        except Exception as e:
            last_err = e
        time.sleep(1)
    if last_err:
        raise last_err
    return False


def md_kv(icon, label, value):
    if icon:
        return f"{icon} {label}: {_escape_md_v2(value)}"
    return f"{label}: {_escape_md_v2(value)}"


def md_title(text):
    return f"*{_escape_md_v2(text)}*"


def md(text):
    return _escape_md_v2(text)
