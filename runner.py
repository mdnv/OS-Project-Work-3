import argparse
import os
import signal
import sys
import time

parser = argparse.ArgumentParser()
parser.add_argument("n", type=int)
parser.add_argument("command", nargs=argparse.REMAINDER)
args = parser.parse_args()

if args.command[:1] == ["--"]:
    args.command = args.command[1:]

if args.n < 1 or not args.command:
    parser.error("Use: python3 runner.py N -- command arguments")


def interrupt(signum, frame):
    raise KeyboardInterrupt


signal.signal(signal.SIGTERM, interrupt)

active = {}
failed = False

try:
    # Сначала создаём всех детей: они работают параллельно.
    for number in range(1, args.n + 1):
        sys.stdout.flush()
        sys.stderr.flush()

        started = time.monotonic()
        pid = os.fork()

        if pid == 0:
            try:
                signal.signal(signal.SIGINT, signal.SIG_DFL)
                signal.signal(signal.SIGTERM, signal.SIG_DFL)
                os.execvp(args.command[0], args.command)
            except OSError as error:
                os.write(2, f"exec failed: {error}\n".encode())
                os._exit(
                    127 if isinstance(error, FileNotFoundError) else 126
                )

        active[pid] = (number, started)
        print(f"START #{number} PID={pid}", flush=True)

    # Забираем завершившихся детей в порядке их завершения.
    while active:
        pid, status = os.waitpid(-1, 0)
        finished = time.monotonic()
        number, started = active.pop(pid)
        code = os.waitstatus_to_exitcode(status)

        failed = failed or code != 0

        print(
            f"END #{number} PID={pid} code={code} "
            f"time={finished - started:.3f}s",
            flush=True,
        )

except KeyboardInterrupt:
    print("\nInterrupted; cleaning up children.", file=sys.stderr)
    failed = True

except OSError as error:
    print(f"OS error: {error}", file=sys.stderr)
    failed = True

finally:
    # При ошибке или прерывании убираем оставшихся прямых детей.
    for pid in active:
        try:
            os.kill(pid, signal.SIGKILL)
        except ProcessLookupError:
            pass

    for pid in active:
        try:
            os.waitpid(pid, 0)
        except ChildProcessError:
            pass

sys.exit(1 if failed else 0)
