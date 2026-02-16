import os
import time
from datetime import datetime, timedelta, timezone

import psutil

from telegram_alert import send_message, md_kv, md_icon, md_title_icon, hostname


CPU_THRESHOLD = float(os.environ.get("CPU_THRESHOLD", "60"))
CPU_DURATION_SEC = int(os.environ.get("CPU_DURATION_SEC", "30"))
CPU_COOLDOWN_SEC = int(os.environ.get("CPU_COOLDOWN_SEC", "300"))

RAM_THRESHOLD = float(os.environ.get("RAM_THRESHOLD", "80"))
RAM_COOLDOWN_SEC = int(os.environ.get("RAM_COOLDOWN_SEC", "300"))

SLEEP_SEC = float(os.environ.get("RESOURCE_WATCH_SLEEP_SEC", "1"))


def now_ts():
    tz = timezone(timedelta(hours=5))
    return datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")


def main():
    cpu_over_seconds = 0
    last_cpu_alert = 0
    last_ram_alert = 0
    ram_check_counter = 0

    while True:
        cpu = psutil.cpu_percent(interval=None)
        if cpu >= CPU_THRESHOLD:
            cpu_over_seconds += 1
        else:
            cpu_over_seconds = 0

        now = time.time()
        if cpu_over_seconds >= CPU_DURATION_SEC and (now - last_cpu_alert) >= CPU_COOLDOWN_SEC:
            last_cpu_alert = now
            msg = "\n".join(
                [
                    md_title_icon(md_icon("CPU_TITLE", "🔥"), "CPU yuklamasi yuqori"),
                    md_kv(md_icon("CPU", "🧠"), "CPU yuklama", f"{cpu:.1f}%"),
                    md_kv(md_icon("DURATION", "⏳"), "Davomiylik", f"{CPU_DURATION_SEC}s+"),
                    md_kv(md_icon("SERVER", "🖥️"), "Server", hostname()),
                ]
            )
            send_message(msg)

        ram_check_counter += 1
        if ram_check_counter >= 5:
            ram_check_counter = 0
            ram = psutil.virtual_memory().percent
            if ram >= RAM_THRESHOLD and (now - last_ram_alert) >= RAM_COOLDOWN_SEC:
                last_ram_alert = now
                msg = "\n".join(
                    [
                        md_title_icon(md_icon("RAM_TITLE", "💾"), "Xotira (RAM) yuklamasi yuqori"),
                        md_kv(md_icon("RAM", "💽"), "RAM ishlatilishi", f"{ram:.1f}%"),
                        md_kv(md_icon("SERVER", "🖥️"), "Server", hostname()),
                    ]
                )
                send_message(msg)

        time.sleep(SLEEP_SEC)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"resource_watch error: {e}")
