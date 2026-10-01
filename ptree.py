import os
from pathlib import Path

processes = {}

for entry in Path("/proc").iterdir():
    if not entry.name.isdigit():
        continue

    try:
        fields = {}
        for line in (entry / "status").read_text().splitlines():
            key, value = line.split(":", 1)
            fields[key] = value.strip()

        # Первое значение Uid — реальный UID владельца процесса.
        if int(fields["Uid"].split()[0]) != os.getuid():
            continue

        pid = int(entry.name)
        processes[pid] = {
            "ppid": int(fields["PPid"]),
            "name": fields["Name"],
            "state": fields["State"].split()[0],
            "rss": int(fields.get("VmRSS", "0 kB").split()[0]),
        }
    except (OSError, ValueError, KeyError):
        # Процесс мог завершиться во время чтения /proc.
        continue

children = {}
for pid, info in processes.items():
    children.setdefault(info["ppid"], []).append(pid)

roots = sorted(
    pid
    for pid, info in processes.items()
    if info["ppid"] not in processes
)

print(f"UID={os.getuid()}; RSS in KiB")
seen = set()

for root in roots:
    stack = [(root, 0)]

    while stack:
        pid, depth = stack.pop()

        if pid in seen:
            continue
        seen.add(pid)

        info = processes[pid]
        print(
            "  " * depth
            + f"PID={pid} PPID={info['ppid']} "
            + f"STATE={info['state']} RSS={info['rss']} KiB "
            + f"NAME={info['name']!r}"
        )

        stack.extend(
            (child, depth + 1)
            for child in sorted(children.get(pid, []), reverse=True)
        )
