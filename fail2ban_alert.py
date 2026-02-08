import argparse
from datetime import datetime

from telegram_alert import send_message, md_title, md_kv, hostname


def now_ts():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def main():
    parser = argparse.ArgumentParser(description="Fail2Ban ban ogohlantirishlarini Telegramga yuborish")
    parser.add_argument("--jail", required=True, help="Fail2Ban jail nomi")
    parser.add_argument("--ip", required=True, help="Bloklangan IP manzil")
    args = parser.parse_args()

    msg = "\n".join([
        md_title("🚫 Fail2Ban: IP bloklandi"),
        md_kv("🧷", "Qamoq", args.jail),
        md_kv("🌍", "IP", args.ip),
        md_kv("⏰", "Vaqt", now_ts()),
        md_kv("🖥️", "Server", hostname()),
    ])
    send_message(msg)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"fail2ban_alert error: {e}")
