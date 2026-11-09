#!/usr/bin/env python3
"""Capture only GPU-path runtime-PM events in a private trace instance."""
from pathlib import Path
import os
import subprocess
import tempfile
import time

if os.geteuid() != 0:
    raise SystemExit('Run with pkexec or sudo')
base = Path('/sys/kernel/tracing/instances')
instance = base / ('kait2en-pm-' + str(os.getpid()))
control = Path('/sys/bus/pci/devices/0000:03:00.0/power/control')
original_control = control.read_text().strip()
instance.mkdir()
try:
    match = ' || '.join('name == "' + name + '"' for name in
                        ['0000:03:00.0', '0000:03:00.1', '0000:02:00.0', '0000:01:00.0'])
    for event in (instance / 'events/rpm').iterdir():
        if not event.is_dir() or not (event / 'filter').exists():
            continue
        (event / 'filter').write_text(match)
        (event / 'enable').write_text('1')
    (instance / 'tracing_on').write_text('1')
    # Request a normal runtime-idle evaluation, never a forced GPU shutdown.
    control.write_text('on')
    control.write_text('auto')
    time.sleep(20)
    (instance / 'tracing_on').write_text('0')
    trace = (instance / 'trace').read_text()
    output = Path('/var/lib/kait2en-hardware/cold-trial/runtime-pm-trace.txt')
    output.write_text(trace)
    print(trace)
finally:
    control.write_text(original_control)
    (instance / 'tracing_on').write_text('0')
    (instance / 'events/rpm/enable').write_text('0')
    instance.rmdir()
