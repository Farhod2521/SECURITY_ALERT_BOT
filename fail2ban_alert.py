import argparse
from datetime import datetime

from telegram_alert import send_message, md_title, md_kv, hostname


def now_ts():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def main():
    parser = argparse.ArgumentParser(description="Send Fail2Ban ban alerts to Telegram")
    parser.add_argument("--jail", required=True, help="Fail2Ban jail name")
    parser.add_argument("--ip", required=True, help="Banned IP address")
    args = parser.parse_args()

    msg = "\n".join([
        md_title("🚫 IP BLOCKED BY FAIL2BAN"),
        md_kv("🧱", "Jail", args.jail),
        md_kv("🌍", "IP", args.ip),
        md_kv("⏰", "Time", now_ts()),
        md_kv("🖥", "Server", hostname()),
    ])
    send_message(msg)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"fail2ban_alert error: {e}")
