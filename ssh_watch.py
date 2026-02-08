import os
import re
import time
from collections import deque, defaultdict
from datetime import datetime, timezone, timedelta

from telegram_alert import send_message, md_title, md_kv, hostname, md


AUTH_LOG = os.environ.get("AUTH_LOG", "/var/log/auth.log")
BRUTE_FORCE_WINDOW = int(os.environ.get("SSH_BRUTE_WINDOW_SEC", "60"))
BRUTE_FORCE_THRESHOLD = int(os.environ.get("SSH_BRUTE_THRESHOLD", "5"))
ALERT_COOLDOWN = int(os.environ.get("SSH_BRUTE_COOLDOWN_SEC", "300"))
SLEEP_SEC = float(os.environ.get("SSH_TAIL_SLEEP_SEC", "0.5"))


FAILED_RE = re.compile(
    r"(Failed password for (?P<invalid>invalid user )?(?P<user>\S+) from (?P<ip>\S+))"
)
INVALID_RE = re.compile(
    r"(Invalid user (?P<user>\S+) from (?P<ip>\S+))"
)


class FileTailer:
    def __init__(self, path):
        self.path = path
        self.fp = None
        self.inode = None
        self.pos = 0

    def _open(self):
        self.fp = open(self.path, "r", encoding="utf-8", errors="ignore")
        st = os.fstat(self.fp.fileno())
        self.inode = st.st_ino
        self.fp.seek(0, os.SEEK_END)
        self.pos = self.fp.tell()

    def _reopen_if_rotated(self):
        try:
            st = os.stat(self.path)
        except FileNotFoundError:
            return
        if self.inode != st.st_ino or st.st_size < self.pos:
            try:
                if self.fp:
                    self.fp.close()
            except Exception:
                pass
            self._open()

    def lines(self):
        if self.fp is None:
            self._open()
        self._reopen_if_rotated()
        while True:
            line = self.fp.readline()
            if not line:
                break
            self.pos = self.fp.tell()
            yield line


def parse_failed(line):
    m = FAILED_RE.search(line)
    if m:
        return m.group("user"), m.group("ip")
    m = INVALID_RE.search(line)
    if m:
        return m.group("user"), m.group("ip")
    return None, None


def now_ts():
    tz = timezone(timedelta(hours=5))
    return datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")


def main():
    tailer = FileTailer(AUTH_LOG)
    attempts = defaultdict(lambda: deque())
    last_alert = {}

    while True:
        for line in tailer.lines():
            if "Failed password" not in line and "Invalid user" not in line:
                continue
            user, ip = parse_failed(line)
            if not ip:
                continue
            ts = time.time()
            dq = attempts[ip]
            dq.append(ts)
            while dq and (ts - dq[0]) > BRUTE_FORCE_WINDOW:
                dq.popleft()

            if len(dq) >= BRUTE_FORCE_THRESHOLD:
                last = last_alert.get(ip, 0)
                if (ts - last) >= ALERT_COOLDOWN:
                    last_alert[ip] = ts
                    msg = "\n".join([
                        md_title("🔐 SSH bruteforce urinish aniqlandi"),
                        md_kv("👤", "Foydalanuvchi", user or "unknown"),
                        md_kv("🌍", "IP", ip),
                        md_kv("⏰", "Vaqt", now_ts()),
                        md_kv("🖥️", "Server", hostname()),
                    ])
                    send_message(msg)
        time.sleep(SLEEP_SEC)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        # last-resort log to stderr
        print(f"ssh_watch error: {e}")
