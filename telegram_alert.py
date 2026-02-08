import os
import socket
import time
import requests


BOT_TOKEN_ENV = "TELEGRAM_BOT_TOKEN"
CHAT_ID_ENV = "TELEGRAM_CHAT_ID"
ENV_FILE_NAME = ".env"


def _load_env_file(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, val = line.split("=", 1)
                key = key.strip()
                val = val.strip().strip('"').strip("'")
                if key and key not in os.environ:
                    os.environ[key] = val
    except FileNotFoundError:
        return
    except Exception:
        # Best-effort .env loading; ignore parse errors
        return


def _load_env():
    env_path = os.environ.get("SECURITY_BOT_ENV")
    if env_path:
        _load_env_file(env_path)
        return
    here = os.path.dirname(os.path.abspath(__file__))
    _load_env_file(os.path.join(here, ENV_FILE_NAME))


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


def _get_chat_ids(raw):
    if not raw:
        return []
    # Allow comma-separated list
    parts = [p.strip() for p in str(raw).split(",")]
    return [p for p in parts if p]


def send_message(message, retries=3, timeout=10):
    _load_env()
    token = os.environ.get(BOT_TOKEN_ENV)
    chat_id_raw = os.environ.get(CHAT_ID_ENV)
    chat_ids = _get_chat_ids(chat_id_raw)
    if not token or not chat_ids:
        raise RuntimeError("TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID is not set")

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    last_err = None
    for _ in range(retries):
        try:
            ok = True
            for chat_id in chat_ids:
                payload = {
                    "chat_id": chat_id,
                    "text": message,
                    "parse_mode": "MarkdownV2",
                    "disable_web_page_preview": True,
                }
                resp = requests.post(url, data=payload, timeout=timeout)
                if resp.status_code != 200:
                    ok = False
                    last_err = RuntimeError(f"Telegram API error: {resp.status_code} {resp.text}")
            if ok:
                return True
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
