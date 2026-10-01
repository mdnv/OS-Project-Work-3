import os
from pathlib import Path
import signal
import subprocess
import sys
import time

# Наблюдатель НЕ назначается subreaper.
signal.signal(signal.SIGINT, signal.SIG_IGN)

report_r, report_w = os.pipe()
release_r, release_w = os.pipe()

sys.stdout.flush()
parent = os.fork()

if parent == 0:
    os.close(report_r)
    os.close(release_w)

    original_parent = os.getpid()
    child = os.fork()

    if child != 0:
        os.close(report_w)
        os.close(release_r)
        os._exit(0)

    try:
        # Ждём реального изменения PPID.
        while os.getppid() == original_parent:
            time.sleep(0.01)

        message = (
            f"{os.getpid()} {original_parent} {os.getppid()}\n"
        )
        os.write(report_w, message.encode())
        os.close(report_w)

        # Пока наблюдатель делает ps, сирота остаётся живой.
        os.read(release_r, 1)
        os.close(release_r)
        os._exit(0)

    except BaseException:
        os._exit(1)

os.close(report_w)
os.close(release_r)

child = None

try:
    # Забираем статус своего непосредственного ребёнка.
    os.waitpid(parent, 0)

    with os.fdopen(report_r) as report:
        child, old_ppid, new_ppid = map(
            int, report.readline().split()
        )

    print(
        f"Orphan PID={child}: PPID {old_ppid} -> {new_ppid}",
        flush=True,
    )
    print("Orphan and its actual adopter:", flush=True)

    subprocess.run(
        [
            "ps", "-o", "pid,ppid,stat,rss,args",
            "-p", f"{child},{new_ppid}",
        ],
        check=True,
    )

finally:
    # Закрытие последнего пишущего конца даёт ребёнку EOF.
    os.close(release_w)

deadline = time.monotonic() + 10

while child is not None and Path(f"/proc/{child}").exists():
    if time.monotonic() > deadline:
        sys.exit(
            f"PID={child} still exists; inspect its STAT and adopter."
        )
    time.sleep(0.01)

print(
    "Orphan finished and was reaped. No demo processes remain.",
    flush=True,
)
