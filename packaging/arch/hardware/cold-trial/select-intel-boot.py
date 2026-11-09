#!/usr/bin/env python3
"""Apply upstream KaiT2en's integrated boot-GPU preference, without changing BootOrder."""
from pathlib import Path
import json
import os
import subprocess

EFI = Path('/sys/firmware/efi/efivars/gpu-power-prefs-fa4ce28d-b62f-4c99-9cc3-6815686e30f9')
STATE = Path('/var/lib/kait2en-hardware/cold-trial')


def main():
    if os.geteuid() != 0:
        raise SystemExit('Run with pkexec or sudo')
    if Path('/sys/class/dmi/id/product_name').read_text().strip() != 'MacBookPro16,1':
        raise SystemExit('Unsupported hardware')
    if 'kait2en.trial=1' not in Path('/proc/cmdline').read_text().split():
        raise SystemExit('Run only in the isolated KaiT2en trial')
    if not Path('/sys/module/t2gmux').exists():
        raise SystemExit('KaiT2en GMUX is not loaded')
    switch = Path('/sys/kernel/debug/vgaswitcheroo/switch').read_text()
    if not any(line.split(':')[1] == 'DIS' and line.split(':')[3] in ('DynPwr', 'DynOff')
               for line in switch.splitlines() if len(line.split(':')) >= 4):
        raise SystemExit('Upstream runtime-PM support condition is not met')
    before = EFI.read_bytes()
    desired = bytes.fromhex('0700000001000000')
    if len(before) != 8 or before[:4] != bytes.fromhex('07000000') or before[4:] not in (bytes(4), bytes.fromhex('01000000')):
        raise SystemExit('Unexpected firmware preference format; preserving it')
    backup = STATE / 'original-gpu-power-prefs.json'
    if not backup.exists():
        backup.write_text(json.dumps({'path': str(EFI), 'bytes_hex': before.hex()}, indent=2) + '\n')
        backup.chmod(0o600)
    if before == desired:
        print('Firmware preference already selects Intel; reboot is required for PCI boot ownership')
        return
    flags = subprocess.check_output(['lsattr', '-d', str(EFI)], text=True).split()[0]
    immutable = 'i' in flags
    try:
        if immutable:
            subprocess.run(['chattr', '-i', str(EFI)], check=True)
        EFI.write_bytes(desired)
        if EFI.read_bytes() != desired:
            raise RuntimeError('Firmware preference verification failed')
    finally:
        if immutable:
            subprocess.run(['chattr', '+i', str(EFI)], check=True)
    print('PASS: Intel boot preference written and read back; previous value backed up')
    print('No BootOrder, BootNext, bootloader, driver or live mux changes made')


if __name__ == '__main__':
    main()
