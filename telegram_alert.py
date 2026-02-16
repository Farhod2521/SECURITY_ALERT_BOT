import os
import re
import socket
import time

import requests


BOT_TOKEN_ENV = "TELEGRAM_BOT_TOKEN"
CHAT_ID_ENV = "TELEGRAM_CHAT_ID"
ENV_FILE_NAME = ".env"

_CUSTOM_EMOJI_TOKEN_RE = re.compile(r"\[\[CE:(\d+)\|([^\]]*)\]\]")
_CUSTOM_EMOJI_BASE_CACHE = {}


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


def _utf16_len(text):
    if text is None:
        return 0
    return len(str(text).encode("utf-16-le")) // 2


def _fetch_custom_emoji_bases(token, emoji_ids, timeout=10):
    if not emoji_ids:
        return {}
    url = f"https://api.telegram.org/bot{token}/getCustomEmojiStickers"
    try:
        resp = requests.post(url, json={"custom_emoji_ids": emoji_ids}, timeout=timeout)
        if resp.status_code != 200:
            return {}
        data = resp.json()
    except Exception:
        return {}

    if not data.get("ok"):
        return {}

    out = {}
    for item in data.get("result", []):
        emoji_id = str(item.get("custom_emoji_id", "")).strip()
        base_emoji = item.get("emoji")
        if emoji_id and base_emoji:
            out[emoji_id] = str(base_emoji)
    return out


def _render_custom_emojis(message, token, timeout=10):
    text = "" if message is None else str(message)
    matches = list(_CUSTOM_EMOJI_TOKEN_RE.finditer(text))
    if not matches:
        return text, None

    missing = []
    for m in matches:
        emoji_id = m.group(1)
        if emoji_id not in _CUSTOM_EMOJI_BASE_CACHE:
            missing.append(emoji_id)

    if missing:
        fresh = _fetch_custom_emoji_bases(token, sorted(set(missing)), timeout=timeout)
        _CUSTOM_EMOJI_BASE_CACHE.update(fresh)

    out_parts = []
    entities = []
    last = 0
    offset = 0

    for m in matches:
        prefix = text[last : m.start()]
        out_parts.append(prefix)
        offset += _utf16_len(prefix)

        emoji_id = m.group(1)
        fallback = m.group(2)
        base_emoji = _CUSTOM_EMOJI_BASE_CACHE.get(emoji_id)

        if base_emoji:
            out_parts.append(base_emoji)
            length = _utf16_len(base_emoji)
            entities.append(
                {
                    "offset": offset,
                    "length": length,
                    "type": "custom_emoji",
                    "custom_emoji_id": emoji_id,
                }
            )
            offset += length
        else:
            out_parts.append(fallback)
            offset += _utf16_len(fallback)

        last = m.end()

    tail = text[last:]
    out_parts.append(tail)
    rendered = "".join(out_parts)

    if not entities:
        return rendered, None
    return rendered, entities


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

    rendered_message, entities = _render_custom_emojis(message, token, timeout=timeout)
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    last_err = None
    for _ in range(retries):
        try:
            ok = True
            for chat_id in chat_ids:
                payload = {
                    "chat_id": chat_id,
                    "text": rendered_message,
                    "disable_web_page_preview": True,
                }
                if entities:
                    payload["entities"] = entities
                resp = requests.post(url, json=payload, timeout=timeout)
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
        return f"{icon} {label}: {'' if value is None else str(value)}"
    return f"{label}: {'' if value is None else str(value)}"


def md_title(text):
    return "" if text is None else str(text)


def md(text):
    return "" if text is None else str(text)


def md_custom_emoji(emoji_id, fallback=""):
    emoji_id = "" if emoji_id is None else str(emoji_id).strip()
    clean_fallback = "" if fallback is None else str(fallback)
    clean_fallback = clean_fallback.replace("|", "").replace("]", "")
    if emoji_id:
        return f"[[CE:{emoji_id}|{clean_fallback}]]"
    return clean_fallback


def md_icon(name, fallback=""):
    _load_env()
    env_name = f"TG_EMOJI_{str(name).strip().upper()}_ID"
    return md_custom_emoji(os.environ.get(env_name), fallback=fallback)


def md_title_icon(icon, text):
    clean_text = "" if text is None else str(text)
    if icon:
        return f"{icon} {clean_text}"
    return clean_text
