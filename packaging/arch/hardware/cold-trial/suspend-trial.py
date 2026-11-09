#!/usr/bin/env python3
"""One guarded suspend/resume cycle for the KaiT2en trial; records before/after evidence."""
from pathlib import Path
import json
import os
import re
import subprocess
import time

if os.geteuid() != 0:
    raise SystemExit('Run with pkexec or sudo')
if 'kait2en.trial=1' not in Path('/proc/cmdline').read_text().split():
    raise SystemExit('Trial boot only')
GPU = Path('/sys/bus/pci/devices/0000:03:00.0')
HDA = Path('/sys/bus/pci/devices/0000:03:00.1')


def snap():
    hw = next(p for p in Path('/sys/class/hwmon').glob('hwmon*') if (p / 'name').read_text().strip() == 't2smc')
    return {'gpu': (GPU / 'power/runtime_status').read_text().strip(),
            'gpu_state': (GPU / 'power_state').read_text().strip(),
            'hda_cards': len(list(HDA.glob('sound/card*'))),
            'battery': (Path('/sys/class/power_supply/BAT0/status')).read_text().strip(),
            'ceiling': (Path('/sys/class/power_supply/BAT0/charge_control_end_threshold')).read_text().strip(),
            'fans': {p.name: int(p.read_text()) for p in hw.glob('fan*_input')},
            'fan_service': subprocess.run(['systemctl', 'is-active', 't2-fancontrol.service'], capture_output=True, text=True).stdout.strip(),
            'wifi': subprocess.run(['iw', 'dev', 'wlp5s0', 'link'], capture_output=True, text=True).stdout.splitlines()[:1]}


before = snap()
mark = time.strftime('%Y-%m-%d %H:%M:%S')
# RTC alarm on the system clock; if the platform ignores it a key press resumes.
subprocess.run(['rtcwake', '-m', 'no', '-s', '45'], check=True)
start = time.monotonic()
subprocess.run(['systemctl', 'suspend'], check=True)
elapsed = time.monotonic() - start
time.sleep(12)
after = snap()
log = subprocess.run(['journalctl', '-k', '--since', mark, '--no-pager'], capture_output=True, text=True).stdout
bad = [l for l in log.splitlines() if re.search(r'BUG:|Oops:|WARNING:|amdgpu.*(ERROR|timeout|failed)|brcmf.*(timeout|fail)|t2smc.*(fail|error)|call trace', l, re.I)]
result = {'suspend_call_seconds': round(elapsed, 1), 'before': before, 'after': after, 'suspicious_kernel_lines': bad[:25]}
Path('/var/lib/kait2en-hardware/cold-trial/suspend-resume.json').write_text(json.dumps(result, indent=2))
print(json.dumps(result, indent=2))
