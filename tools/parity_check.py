"""Parity check: compare raw `dmesg -w` lines with GUI engine events.

Run this script to capture live dmesg lines for N seconds and compare against
events returned by `KernelLogReader.get_new_logs()` to report misses.
"""

import subprocess
import threading
import time
from collections import deque

from core.kernel_log_reader import KernelLogReader


def run_dmesg_reader(lines: deque, stop_event: threading.Event):
    proc = subprocess.Popen(['dmesg', '-w', '-L'], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, bufsize=1)
    try:
        while not stop_event.is_set():
            line = proc.stdout.readline()
            if not line:
                break
            lines.append(line.rstrip('\n'))
    finally:
        try:
            proc.terminate()
        except Exception:
            pass


def parity_check(duration: float = 10.0):
    reader = KernelLogReader()
    print('Initializing engine...')
    reader._initialize_engine_sync()
    print('Engine initialized; starting parity capture')

    lines = deque()
    stop_event = threading.Event()
    t = threading.Thread(target=run_dmesg_reader, args=(lines, stop_event), daemon=True)
    t.start()

    start = time.time()
    captured_events = []
    try:
        while time.time() - start < duration:
            new = reader.get_new_logs()
            if new:
                for e in new:
                    captured_events.append(e.get('raw'))
            time.sleep(0.05)
    finally:
        stop_event.set()
        t.join(timeout=1)

    # Compare
    dm = list(lines)
    ev = list(captured_events)

    print(f'Captured dmesg lines: {len(dm)}')
    print(f'Captured engine events: {len(ev)}')

    # Simple matching by substring: event raw should appear in dmesg lines
    unmatched_lines = [l for l in dm if not any(l.strip() == e.strip() or l.strip() in e.strip() for e in ev)]
    unmatched_events = [e for e in ev if not any(e.strip() == l.strip() or e.strip() in l.strip() for l in dm)]

    print(f'Unmatched dmesg lines: {len(unmatched_lines)}')
    if unmatched_lines:
        print('Sample unmatched dmesg lines:')
        for s in unmatched_lines[:10]:
            print(' -', s)

    print(f'Unmatched engine events: {len(unmatched_events)}')
    if unmatched_events:
        print('Sample unmatched engine events:')
        for s in unmatched_events[:10]:
            print(' -', s)


if __name__ == '__main__':
    parity_check(10.0)
