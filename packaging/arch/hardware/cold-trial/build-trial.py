#!/usr/bin/env python3
"""Build an isolated UKI without replacing any installed GPU module or default UKI."""
from pathlib import Path
import hashlib
import json
import os
import shutil
import subprocess
import sys

SOURCE = Path(__file__).resolve().parent
STATE = Path('/var/lib/kait2en-hardware/cold-trial')
KERNEL = '7.2.11-arch1-Watanare-T2-1-t2'
IMAGE = Path('/boot/EFI/Linux/omarchy_kait2en_trial.efi')


def run(*args, **kwargs):
    return subprocess.run(args, check=True, text=True, **kwargs)


def put(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    path.chmod(0o644)


def main():
    if os.geteuid() != 0:
        raise SystemExit('Run with pkexec or sudo')
    if Path('/sys/class/dmi/id/product_name').read_text().strip() != 'MacBookPro16,1':
        raise SystemExit('Unsupported model')
    if subprocess.check_output(['uname', '-r'], text=True).strip() != KERNEL:
        raise SystemExit('Kernel version mismatch')
    if Path('/sys/module/t2smc').exists():
        raise SystemExit('Build only from the recovered original-driver boot')
    inputs = json.loads((SOURCE / 'inputs.json').read_text())
    original = Path('/boot/limine.conf')
    if hashlib.sha256(original.read_bytes()).hexdigest() != inputs['limine_sha256']:
        raise SystemExit('Boot menu changed; recapture it before staging')
    if IMAGE.exists():
        raise SystemExit('Trial image already exists; inspect before replacing')
    STATE.mkdir(parents=True, exist_ok=True)
    STATE.chmod(0o755)
    root = STATE / 'root'
    if root.exists():
        raise SystemExit('Staging tree already exists; inspect it before rebuilding')
    modules = root / 'usr/lib/modules' / KERNEL
    modules.mkdir(parents=True, exist_ok=True)
    (root / 'lib').symlink_to('usr/lib', target_is_directory=True)
    installed = Path('/usr/lib/modules') / KERNEL
    for path in installed.iterdir():
        if path.name == 'build':
            continue
        run('cp', '-a', '--reflink=auto', str(path), str(modules))
    extra = modules / 'updates/kait2en-trial'
    extra.mkdir(parents=True, exist_ok=True)
    artifacts = {
        'amdgpu': SOURCE.parent / 'gpu/pkg/kait2en-hybrid-gpu/usr/lib/modules' / KERNEL / 'updates/kait2en-hybrid/amdgpu.ko',
        'snd-hda-intel': SOURCE.parent / 'gpu/pkg/kait2en-hybrid-gpu/usr/lib/modules' / KERNEL / 'updates/kait2en-hybrid/snd-hda-intel.ko',
        't2gmux': SOURCE.parents[3] / 'modules/t2gmux/t2gmux.ko',
    }
    expected = {}
    for name, artifact in artifacts.items():
        version = subprocess.check_output(['modinfo', '-F', 'vermagic', str(artifact)], text=True)
        if not version.startswith(KERNEL + ' '):
            raise RuntimeError(f'{name}: module version mismatch')
        shutil.copy2(artifact, extra / (name + '.ko'))
        expected[name.replace('-', '_')] = subprocess.check_output(
            ['modinfo', '-F', 'srcversion', str(artifact)], text=True).strip()
    for name in ('t2smc', 't2sbs'):
        expected[name] = subprocess.check_output(['modinfo', '-F', 'srcversion', name], text=True).strip()
    run('depmod', '-b', str(root), KERNEL)
    cmdline = [arg for arg in inputs['boot_cmdline'].split()
               if not arg.startswith(('apple_gmux.force_igd=', 'module_blacklist=', 'kait2en.trial='))]
    cmdline += ['module_blacklist=applesmc,sbs,apple_gmux', 't2gmux.boot_gpu=0', 'kait2en.trial=1']
    put(STATE / 'cmdline', ' '.join(cmdline) + '\n')
    put(STATE / 'modprobe.conf', 'blacklist applesmc\nblacklist sbs\nblacklist apple_gmux\nsoftdep amdgpu pre: t2gmux\n')
    put(STATE / 'hooks/kait2en_trial', '''build() {
    # Remove only the copy of our validation hold inside this trial image.
    rm -f "$BUILDROOT/etc/modprobe.d/99-kait2en-validation-hold.conf"
    add_file /var/lib/kait2en-hardware/cold-trial/modprobe.conf /etc/modprobe.d/99-kait2en-trial.conf
}
help() { echo 'Isolated KaiT2en hardware trial configuration'; }
''')
    put(STATE / 'mkinitcpio.conf', '''source /etc/mkinitcpio.conf
for config in /etc/mkinitcpio.conf.d/*.conf; do source "$config"; done
# Explicit order: the SMC exists before the battery is registered; GMUX before GPUs.
MODULES=(t2smc t2sbs t2gmux i915 amdgpu snd_hda_intel "${MODULES[@]}")
HOOKS+=(kait2en_trial)
''')
    put(STATE / 'manifest.json', json.dumps({'kernel': KERNEL, 'modules': expected,
        'original_cmdline': inputs['boot_cmdline'], 'image': str(IMAGE)}, indent=2) + '\n')
    original_image = Path('/boot/EFI/Linux/omarchy_linux-t2.efi')
    hashes = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in (original, original_image)}
    put(STATE / 'original-hashes.json', json.dumps(hashes, indent=2) + '\n')
    env = dict(os.environ, MKINITCPIO_INSTALL=str(STATE / 'hooks') + ':/etc/initcpio/install:/usr/lib/initcpio/install')
    run('/usr/bin/mkinitcpio', '-k', KERNEL, '-r', str(root), '-c', str(STATE / 'mkinitcpio.conf'),
        '--cmdline', str(STATE / 'cmdline'), '--kernelimage', str(installed / 'vmlinuz'),
        '--nopost', '-U', str(IMAGE), env=env)
    for path, before in hashes.items():
        if hashlib.sha256(Path(path).read_bytes()).hexdigest() != before:
            raise RuntimeError('Original boot artifact changed: ' + path)
    print('PASS: isolated image built; original boot menu and UKI unchanged')
    print('Trial image BLAKE2b:', hashlib.blake2b(IMAGE.read_bytes()).hexdigest())


if __name__ == '__main__':
    main()
