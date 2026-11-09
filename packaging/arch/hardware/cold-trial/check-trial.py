#!/usr/bin/env python3
"""Inspect or exercise the isolated KaiT2en boot; never unload a driver."""
from pathlib import Path
import argparse
import json
import os
import re
import statistics
import subprocess
import time

STATE = Path('/var/lib/kait2en-hardware/cold-trial')
GPU = Path('/sys/bus/pci/devices/0000:03:00.0')
BATTERY = Path('/sys/class/power_supply/BAT0')


def read(path):
    return Path(path).read_text().strip()


def run(*args, timeout=30):
    return subprocess.run(args, check=True, capture_output=True, text=True, timeout=timeout)


def checked():
    cmdline = read('/proc/cmdline').split()
    if 'kait2en.trial=1' not in cmdline and 't2gmux.boot_gpu=0' not in cmdline:
        raise RuntimeError('Neither trial nor permanent KaiT2en boot detected; refusing hardware changes')
    if read('/sys/class/dmi/id/product_name') != 'MacBookPro16,1':
        raise RuntimeError('Unsupported hardware')
    manifest = json.loads((STATE / 'manifest.json').read_text())
    if run('uname', '-r').stdout.strip() != manifest['kernel']:
        raise RuntimeError('Trial kernel version mismatch')
    for name, expected in manifest['modules'].items():
        path = Path('/sys/module') / name
        if not expected or not path.exists() or read(path / 'srcversion') != expected:
            raise RuntimeError('Wrong or missing loaded module: ' + name)
        if (path / 'refcnt').exists() and int(read(path / 'refcnt')) < 0:
            raise RuntimeError('Module is in a failed removal state: ' + name)
    for name in ('applesmc', 'sbs', 'apple_gmux'):
        if Path('/sys/module', name).exists():
            raise RuntimeError('Original driver unexpectedly loaded: ' + name)
    if read('/sys/bus/pci/devices/0000:00:02.0/boot_vga') != '1':
        raise RuntimeError('Intel does not own the boot display')
    if not (BATTERY / 'charge_control_end_threshold').exists():
        raise RuntimeError('Battery charge-limit extension is unavailable')
    log = run('journalctl', '-b', '-k', '--no-pager').stdout
    if re.search(r'BUG:|Oops:|atomic_dec_return\(&psy->use_cnt\)', log):
        raise RuntimeError('This boot contains a kernel Oops or battery lifetime warning')
    return next(p for p in Path('/sys/class/hwmon').glob('hwmon*') if read(p / 'name') == 't2smc')


def status(hwmon):
    return {'boot_id': read('/proc/sys/kernel/random/boot_id'),
            'gpu_runtime_status': read(GPU / 'power/runtime_status'),
            'gpu_power_state': read(GPU / 'power_state'),
            'gpu_suspended_ms': int(read(GPU / 'power/runtime_suspended_time')),
            'gpu_control': read(GPU / 'power/control'),
            'battery_status': read(BATTERY / 'status'),
            'charge_limit': int(read(BATTERY / 'charge_control_end_threshold')),
            'fans_rpm': {p.name: int(read(p)) for p in hwmon.glob('fan*_input')}}


def wait_state(expected, seconds=60):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if read(GPU / 'power/runtime_status') == expected:
            return
        time.sleep(1)
    raise RuntimeError('GPU did not become ' + expected)


def prepare(hwmon):
    run('systemctl', 'start', 't2-fancontrol.service')
    run('systemctl', 'is-active', 't2-fancontrol.service')
    (GPU / 'power_dpm_force_performance_level').write_text('auto')
    # The initramfs probes the GPU's HDMI-audio function before its codecs are
    # ready ("Cannot probe codecs") and the failed-but-bound function then holds
    # the GPU awake. Rebind only that function once udev has settled.
    run('udevadm', 'settle', '--timeout=20')
    hda_dev = Path('/sys/bus/pci/devices/0000:03:00.1')
    if hda_dev.exists() and not list(hda_dev.glob('sound/card*')):
        driver = Path('/sys/bus/pci/drivers/snd_hda_intel')
        if (driver / '0000:03:00.1').exists():
            (driver / 'unbind').write_text('0000:03:00.1')
        (driver / 'bind').write_text('0000:03:00.1')
        deadline = time.monotonic() + 10
        while not list(hda_dev.glob('sound/card*')):
            if time.monotonic() > deadline:
                raise RuntimeError('GPU HDMI audio did not probe after rebind')
            time.sleep(0.5)
    hda = hda_dev / 'power/control'
    if hda.exists():
        hda.write_text('auto')
    (GPU / 'power/control').write_text('auto')
    time.sleep(3)
    print(json.dumps(status(hwmon), indent=2))


def exercise(hwmon):
    render = next((GPU / 'drm').glob('renderD*')).name
    run('ffmpeg', '-hide_banner', '-loglevel', 'error', '-vaapi_device', '/dev/dri/' + render,
        '-f', 'lavfi', '-i', 'testsrc2=size=320x240:rate=30', '-vf', 'format=nv12,hwupload',
        '-frames:v', '30', '-c:v', 'h264_vaapi', '-f', 'null', '-', timeout=45)
    wait_state('suspended')
    print('PASS: AMD hardware encoding completed and the GPU returned to runtime suspend')
    print(json.dumps(status(hwmon), indent=2))


def compare(hwmon):
    labels = [p for p in hwmon.glob('power*_label') if read(p) == 'PSTR']
    if len(labels) != 1:
        raise RuntimeError('No unique PSTR system-power sensor is available')
    power = labels[0].with_name(labels[0].name.replace('_label', '_input'))
    brightness = {str(p): read(p) for p in Path('/sys/class/backlight').glob('*/brightness')}
    battery_status = read(BATTERY / 'status')
    results = []
    try:
        for phase, suspended in [('A1-low-DPM', False), ('B-runtime-suspend', True), ('A2-low-DPM', False)]:
            if suspended:
                (GPU / 'power_dpm_force_performance_level').write_text('auto')
                (GPU / 'power/control').write_text('auto')
                wait_state('suspended')
            else:
                (GPU / 'power/control').write_text('on')
                wait_state('active')
                (GPU / 'power_dpm_force_performance_level').write_text('low')
            time.sleep(10)
            samples = []
            for _ in range(40):
                if read(BATTERY / 'status') != battery_status:
                    raise RuntimeError('Charging state changed; comparison is invalid')
                if any(read(p) != value for p, value in brightness.items()):
                    raise RuntimeError('Display brightness changed; comparison is invalid')
                if read(GPU / 'power/runtime_status') != ('suspended' if suspended else 'active'):
                    raise RuntimeError('GPU left the requested state during measurement')
                samples.append({'watts': int(read(power)) / 1e6,
                                'loadavg': read('/proc/loadavg'), 'time': time.time()})
                time.sleep(1)
            results.append({'phase': phase, 'samples': samples,
                            'median_watts': statistics.median(s['watts'] for s in samples)})
            print(phase, results[-1]['median_watts'], 'W', flush=True)
    finally:
        (GPU / 'power_dpm_force_performance_level').write_text('auto')
        (GPU / 'power/control').write_text('auto')
        (STATE / 'power-comparison.json').write_text(json.dumps({
            'comparison': 'Low-DPM equivalent vs runtime suspend on the SAME new driver stack; not an old-driver benchmark',
            'brightness': brightness, 'battery_status': battery_status, 'results': results}, indent=2))
    print('Recorded A/B/A data. Review workload and drift before claiming an improvement.')


def battery_test(hwmon):
    limit = BATTERY / 'charge_control_end_threshold'
    original = int(read(limit))
    if read(BATTERY / 'status') != 'Charging' or int(read(BATTERY / 'capacity')) >= 95:
        raise RuntimeError('Charging below 95% is required to test stop/resume behavior')
    observed = []
    try:
        # Apple T2 SMC firmware ignores nonsensical limits like 1%; 50% is a valid
        # threshold safely below the 95% test entry gate.
        target = max(20, min(80, int(read(BATTERY / 'capacity')) - 10))
        limit.write_text(str(target))
        for _ in range(30):
            observed.append(read(BATTERY / 'status'))
            if observed[-1] in ('Not charging', 'Full'):
                break
            time.sleep(1)
        else:
            raise RuntimeError('Charge limit did not stop charging within 30 seconds')
    finally:
        limit.write_text(str(original))
    for _ in range(30):
        if read(BATTERY / 'status') == 'Charging':
            print('PASS: charge ceiling stopped charging; original ceiling restored and charging resumed')
            return
        time.sleep(1)
    raise RuntimeError('Original ceiling restored but charging did not resume within 30 seconds')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['status', 'prepare', 'exercise', 'compare', 'battery-test'], default='status', nargs='?')
    args = parser.parse_args()
    if args.action != 'status' and os.geteuid() != 0:
        raise RuntimeError('Run hardware exercises with sudo or pkexec')
    if args.action == 'prepare' and 'kait2en.trial=1' in read('/proc/cmdline').split():
        # Fan manual mode survives reboot. Restore native thermal control even
        # if a later GPU identity check fails and the trial cannot proceed.
        for monitor in Path('/sys/class/hwmon').glob('hwmon*'):
            if read(monitor / 'name') == 't2smc':
                for target in monitor.glob('fan*_target'):
                    target.write_text('0')
    hwmon = checked()
    if args.action == 'status':
        print(json.dumps(status(hwmon), indent=2))
    else:
        {'prepare': prepare, 'exercise': exercise, 'compare': compare, 'battery-test': battery_test}[args.action](hwmon)


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, RuntimeError, StopIteration, subprocess.SubprocessError) as error:
        raise SystemExit('KaiT2en validation failed: ' + str(error))
