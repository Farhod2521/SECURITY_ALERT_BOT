import os
import signal
import subprocess
import sys
import time


def _env_int(name, default):
    try:
        return int(os.environ.get(name, default))
    except Exception:
        return int(default)


def _env_bool(name, default=False):
    val = os.environ.get(name)
    if val is None:
        return default
    return val.strip().lower() in {"1", "true", "yes", "on"}


def _build_cmd(script_name):
    return [sys.executable, os.path.join(os.path.dirname(__file__), script_name)]


def main():
    restart_sec = _env_int("SECURITY_BOT_RESTART_SEC", "2")
    disable_ssh = _env_bool("DISABLE_SSH_WATCH", False)
    disable_nginx = _env_bool("DISABLE_NGINX_WATCH", False)
    disable_resource = _env_bool("DISABLE_RESOURCE_WATCH", False)

    procs = {}
    scripts = []
    if not disable_ssh:
        scripts.append("ssh_watch.py")
    if not disable_nginx:
        scripts.append("nginx_watch.py")
    if not disable_resource:
        scripts.append("resource_watch.py")

    if not scripts:
        print("main: no watchers enabled", file=sys.stderr)
        return 1

    def start(script):
        cmd = _build_cmd(script)
        return subprocess.Popen(cmd)

    def start_all():
        for s in scripts:
            procs[s] = start(s)

    def stop_all():
        for p in procs.values():
            try:
                p.terminate()
            except Exception:
                pass
        deadline = time.time() + 10
        for p in procs.values():
            try:
                remaining = max(0.0, deadline - time.time())
                p.wait(timeout=remaining)
            except Exception:
                try:
                    p.kill()
                except Exception:
                    pass

    stop = {"flag": False}

    def handle(_sig, _frame):
        stop["flag"] = True

    signal.signal(signal.SIGINT, handle)
    signal.signal(signal.SIGTERM, handle)

    start_all()

    while not stop["flag"]:
        for s, p in list(procs.items()):
            code = p.poll()
            if code is not None:
                # restart crashed process
                procs[s] = start(s)
        time.sleep(restart_sec)

    stop_all()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
