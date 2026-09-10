#!/usr/bin/env python3
"""Capture a command's real stdout through a PTY with wall-clock timing.

Produces a JSONL cast file compatible with a small terminal renderer
([delay_seconds, "text"]) — the same principle as an asciinema cast: real
output, real timing, faithfully replayed. No invented content.
"""
import argparse, json, os, pty, select, sys, time

def capture(argv, out_path, cols=80, rows=30, env=None):
    start = time.monotonic()
    events = []
    # Simulate a terminal size so the child lays out like a real terminal.
    os.environ["COLUMNS"] = str(cols)
    os.environ["LINES"] = str(rows)
    if env:
        os.environ.update(env)

    pid, fd = pty.fork()
    if pid == 0:
        os.execvp(argv[0], argv)

    buf = b""
    last = start
    try:
        while True:
            r, _, _ = select.select([fd], [], [], 0.05)
            if r:
                try:
                    data = os.read(fd, 4096)
                except OSError:
                    break
                if not data:
                    break
                now = time.monotonic()
                buf += data
                events.append([round(now - last, 4), data.decode("utf-8", "replace")])
                last = now
            else:
                # check child exit
                wpid, status = os.waitpid(pid, os.WNOHANG)
                if wpid == pid:
                    # drain remaining
                    while True:
                        try:
                            data = os.read(fd, 4096)
                        except OSError:
                            break
                        if not data:
                            break
                        now = time.monotonic()
                        events.append([round(now - last, 4), data.decode("utf-8", "replace")])
                        last = now
                    break
    finally:
        try:
            os.close(fd)
        except OSError:
            pass

    with open(out_path, "w") as f:
        json.dump({"cols": cols, "rows": rows, "events": events}, f)
    print(f"captured {len(events)} events -> {out_path}")
    return 0

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--cols", type=int, default=80)
    ap.add_argument("--rows", type=int, default=30)
    ap.add_argument("--env", default="", help="comma-separated KEY=VALUE")
    ap.add_argument("cmd", nargs=argparse.REMAINDER)
    a = ap.parse_args()
    cmd = a.cmd
    if cmd and cmd[0] == "--":
        cmd = cmd[1:]
    if not cmd:
        ap.error("need a command (after --)")
    env = {}
    if a.env:
        for kv in a.env.split(","):
            if "=" in kv:
                k, v = kv.split("=", 1)
                env[k] = v
    return capture(cmd, a.out, a.cols, a.rows, env or None)

if __name__ == "__main__":
    sys.exit(main())
