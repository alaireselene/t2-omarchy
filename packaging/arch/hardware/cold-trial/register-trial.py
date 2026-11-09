#!/usr/bin/env python3
"""Verify the built trial UKI and add an opt-in boot entry; keep the default unchanged."""
from pathlib import Path
import hashlib
import json
import os
import shutil
import subprocess
import tempfile

SOURCE = Path(__file__).resolve().parent
STATE = Path('/var/lib/kait2en-hardware/cold-trial')
IMAGE = Path('/boot/EFI/Linux/omarchy_kait2en_trial.efi')


def run(*args, **kwargs):
    return subprocess.run(args, check=True, capture_output=True, text=True, **kwargs)


def put(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    path.chmod(0o644)


def main():
    if os.geteuid() != 0:
        raise SystemExit('Run with pkexec or sudo')
    inputs = json.loads((SOURCE / 'inputs.json').read_text())
    originals = json.loads((STATE / 'original-hashes.json').read_text())
    manifest = json.loads((STATE / 'manifest.json').read_text())
    for name, expected in originals.items():
        if hashlib.sha256(Path(name).read_bytes()).hexdigest() != expected:
            raise RuntimeError('Original boot artifact changed: ' + name)
    helper = Path('/usr/local/bin/gpu-amd-dpm-low')
    if hashlib.sha256(helper.read_bytes()).hexdigest() != inputs['helper_sha256']:
        raise RuntimeError('Original helper changed; review before installing its trial guard')
    menu = (SOURCE / 'limine.conf').read_text()
    original_menu = Path('/boot/limine.conf').read_text()
    if not menu.startswith(original_menu) or menu.count('/KaiT2en hardware trial\n') != 1:
        raise RuntimeError('Candidate menu must preserve the original byte-for-byte and add one trial entry')
    if '#'+hashlib.blake2b(IMAGE.read_bytes()).hexdigest() not in menu:
        raise RuntimeError('Trial image hash does not match the candidate menu')
    with tempfile.TemporaryDirectory(prefix='kait2en-image-check-', dir='/var/tmp') as temporary:
        root = Path(temporary)
        run('lsinitcpio', '-x', str(IMAGE), cwd=root)
        run('objcopy', '--dump-section', '.cmdline=' + str(root / 'embedded-cmdline'), str(IMAGE), str(root / 'image-copy'))
        cmdline = (root / 'embedded-cmdline').read_bytes().rstrip(b'\0\n').decode().split()
        for arg in ('kait2en.trial=1', 't2gmux.boot_gpu=0', 'module_blacklist=applesmc,sbs,apple_gmux'):
            if arg not in cmdline:
                raise RuntimeError('Missing embedded trial parameter: ' + arg)
        if any(arg.startswith('apple_gmux.force_igd=') for arg in cmdline):
            raise RuntimeError('Original GMUX parameter leaked into trial image')
        if (root / 'etc/modprobe.d/99-kait2en-validation-hold.conf').exists():
            raise RuntimeError('Trial image still contains the new-driver hold')
        module_dir = root / 'usr/lib/modules' / manifest['kernel']
        for name, expected in manifest['modules'].items():
            matches = [p for p in module_dir.rglob('*.ko*') if p.name.split('.ko')[0].replace('-', '_') == name]
            if len(matches) != 1:
                raise RuntimeError('Wrong number of image modules for ' + name)
            actual = run('modinfo', '-F', 'srcversion', str(matches[0])).stdout.strip()
            if actual != expected:
                raise RuntimeError('Wrong module identity in image: ' + name)
        config = (root / 'config').read_text()
        if not (config.index('t2smc') < config.index('t2sbs') < config.index('t2gmux')):
            raise RuntimeError('Unsafe early module ordering')
    # Install only runtime-neutral guards on the original boot.
    shutil.copy2(helper, STATE / 'original-gpu-amd-dpm-low')
    shutil.copy2('/boot/limine.conf', STATE / 'original-limine.conf')
    for unit in ('t2fanrd.service', 'gpu-amd-dpm-low.service', 'gpu-amd-dpm-low-poll.service', 'gpu-amd-dpm-low-poll.timer'):
        put(Path('/etc/systemd/system') / (unit + '.d/90-kait2en-trial.conf'),
            '[Unit]\nConditionKernelCommandLine=!kait2en.trial=1\n')
    run('install', '-Dm755', str(SOURCE / 'check-trial.py'), '/usr/libexec/kait2en-hardware-check')
    put(Path('/etc/systemd/system/kait2en-hardware-trial.service'), '''[Unit]
Description=Prepare and check the opt-in KaiT2en hardware trial
ConditionKernelCommandLine=kait2en.trial=1
After=systemd-modules-load.service
Before=multi-user.target

[Service]
Type=oneshot
ExecStart=/usr/libexec/kait2en-hardware-check prepare
RemainAfterExit=yes
TimeoutStartSec=60

[Install]
WantedBy=multi-user.target
''')
    run('install', '-m755', str(SOURCE / 'gpu-amd-dpm-low'), str(helper))
    run('systemctl', 'daemon-reload')
    run('systemctl', 'enable', 'kait2en-hardware-trial.service')
    run('install', '-m600', str(SOURCE / 'limine.conf'), '/boot/limine.conf')
    run('limine-enroll-config')
    put(STATE / 'registration.json', json.dumps({'image_hash': hashlib.blake2b(IMAGE.read_bytes()).hexdigest(),
        'original_uki_sha256': originals['/boot/EFI/Linux/omarchy_linux-t2.efi'],
        'entry': 'KaiT2en hardware trial', 'default_changed': False}, indent=2) + '\n')
    print('PASS: embedded modules, command line, load order and image hash verified')
    print('PASS: opt-in trial registered; normal boot image and default selection retained')


if __name__ == '__main__':
    main()
