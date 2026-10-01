import argparse
import os
from pathlib import Path
import sys


def memory(label):
    fields = {}

    for line in Path("/proc/self/smaps_rollup").read_text().splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            fields[key] = int(value.split()[0])

    private = fields["Private_Clean"] + fields["Private_Dirty"]

    print(
        f"{label}: PID={os.getpid()} "
        f"RSS={fields['Rss']} KiB "
        f"PSS={fields['Pss']} KiB "
        f"PRIVATE={private} KiB",
        flush=True,
    )


parser = argparse.ArgumentParser()
parser.add_argument("--size", type=int, default=4_000_000)
args = parser.parse_args()

if args.size < 1:
    parser.error("--size must be positive")

# Большой список создаётся ДО fork.
data = [0] * args.size

print(f"List: {len(data)} elements", flush=True)
memory("PARENT before fork")
sys.stdout.flush()

pid = os.fork()

if pid == 0:
    try:
        memory("CHILD before write")

        # Изменяем существующий унаследованный список.
        for i in range(len(data)):
            data[i] = 1

        memory("CHILD after write")

        print(
            f"CHILD data[0]={data[0]} data[-1]={data[-1]}",
            flush=True,
        )
        os._exit(0)

    except BaseException as error:
        print(
            f"CHILD error: {error}",
            file=sys.stderr,
            flush=True,
        )
        os._exit(1)

# Родитель сохраняет свой список и ждёт ребёнка.
try:
    _, status = os.waitpid(pid, 0)
except KeyboardInterrupt:
    _, status = os.waitpid(pid, 0)

print(
    f"PARENT data[0]={data[0]} data[-1]={data[-1]}",
    flush=True,
)
print(
    f"Child code={os.waitstatus_to_exitcode(status)}",
    flush=True,
)
