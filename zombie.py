import os
import signal
import subprocess
import sys
import time

# Короткий опыт завершается автоматически.
signal.signal(signal.SIGINT, signal.SIG_IGN)

sys.stdout.flush()
pid = os.fork()

if pid == 0:
    os._exit(42)

try:
    # Дожидаемся завершения, но пока не забираем статус.
    os.waitid(os.P_PID, pid, os.WEXITED | os.WNOWAIT)

    print(
        f"Parent PID={os.getpid()}, zombie PID={pid}",
        flush=True,
    )

    subprocess.run(
        [
            "ps", "-o", "pid,ppid,stat,rss,args",
            "-p", f"{os.getpid()},{pid}",
        ],
        check=True,
    )

    print("Zombie visible; waitpid in 2 seconds.", flush=True)
    time.sleep(2)

finally:
    _, status = os.waitpid(pid, 0)
    print(
        f"Reaped PID={pid}, code={os.waitstatus_to_exitcode(status)}",
        flush=True,
    )

print("After waitpid: only the header should remain.", flush=True)

subprocess.run(
    ["ps", "-o", "pid,ppid,stat,rss,args", "-p", str(pid)]
)
