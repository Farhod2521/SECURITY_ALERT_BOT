import os
import re
import time
from collections import deque, defaultdict
from datetime import datetime

from telegram_alert import send_message, md_title, md_kv, hostname, md


NGINX_ACCESS_LOG = os.environ.get("NGINX_ACCESS_LOG", "/var/log/nginx/access.log")
API_PREFIXES = os.environ.get("API_PREFIXES", "/api/,/v1/,/auth/").split(",")
FLOOD_WINDOW_SEC = int(os.environ.get("API_FLOOD_WINDOW_SEC", "60"))
FLOOD_THRESHOLD = int(os.environ.get("API_FLOOD_THRESHOLD", "100"))
FLOOD_COOLDOWN = int(os.environ.get("API_FLOOD_COOLDOWN_SEC", "300"))
SLEEP_SEC = float(os.environ.get("NGINX_TAIL_SLEEP_SEC", "0.5"))


ACCESS_RE = re.compile(r'^(?P<ip>\S+) \S+ \S+ \[(?P<time>[^\]]+)\] "(?P<method>\S+) (?P<path>\S+)')


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


def is_api_path(path):
    for pref in API_PREFIXES:
        pref = pref.strip()
        if pref and path.startswith(pref):
            return True
    return False


def now_ts():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def main():
    tailer = FileTailer(NGINX_ACCESS_LOG)
    hits = defaultdict(lambda: deque())
    last_alert = {}
    last_path = {}

    while True:
        for line in tailer.lines():
            m = ACCESS_RE.search(line)
            if not m:
                continue
            ip = m.group("ip")
            path = m.group("path").split("?")[0]
            if not is_api_path(path):
                continue
            ts = time.time()
            dq = hits[ip]
            dq.append(ts)
            last_path[ip] = path

            while dq and (ts - dq[0]) > FLOOD_WINDOW_SEC:
                dq.popleft()

            if len(dq) >= FLOOD_THRESHOLD:
                last = last_alert.get(ip, 0)
                if (ts - last) >= FLOOD_COOLDOWN:
                    last_alert[ip] = ts
                    msg = "\n".join([
                        md_title("🌊 API FLOOD DETECTED"),
                        md_kv("🌍", "IP", ip),
                        md_kv("📡", "Endpoint", last_path.get(ip, path)),
                        md_kv("📈", "Requests/min", str(len(dq))),
                        md_kv("🖥", "Server", hostname()),
                    ])
                    send_message(msg)
        time.sleep(SLEEP_SEC)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"nginx_watch error: {e}")
