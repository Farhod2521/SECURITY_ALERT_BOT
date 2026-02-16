import argparse
from datetime import datetime, timedelta, timezone

from telegram_alert import send_message, md_kv, md_icon, md_title_icon, hostname


def now_ts():
    tz = timezone(timedelta(hours=5))
    return datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")


def main():
    parser = argparse.ArgumentParser(description="Fail2Ban ban ogohlantirishlarini Telegramga yuborish")
    parser.add_argument("--jail", required=True, help="Fail2Ban jail nomi")
    parser.add_argument("--ip", required=True, help="Bloklangan IP manzil")
    args = parser.parse_args()

    msg = "\n".join(
        [
            md_title_icon(md_icon("FAIL2BAN_TITLE", "🚫"), "Fail2Ban: IP bloklandi"),
            md_kv(md_icon("JAIL", "🧷"), "Qamoq", args.jail),
            md_kv(md_icon("IP", "🌍"), "IP", args.ip),
            md_kv(md_icon("TIME", "⏰"), "Vaqt", now_ts()),
            md_kv(md_icon("SERVER", "🖥️"), "Server", hostname()),
        ]
    )
    send_message(msg)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"fail2ban_alert error: {e}")
