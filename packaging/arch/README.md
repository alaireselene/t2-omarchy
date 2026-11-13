# Arch / Omarchy integration

This independent fork collects the local Apple T2 port. It is based on
[KaiT2en-Fedora](https://github.com/kaiT2en/KaiT2en-Fedora); it is not an official
KaiT2en, Omarchy or Apple release. Upstream source history and notices are retained.

## Source layout

| Path, relative to the repository root | Purpose |
|---|---|
| `dsp/packaging/PKGBUILD`, `t2-dsp.install` | Model-specific speaker/microphone DSP package and ownership-aware lifecycle |
| `packaging/arch/bankstown/` | Bankstown LV2 dependency recipe |
| `packaging/arch/hardware/` | Split SMC/battery and GMUX DKMS packages |
| `packaging/arch/hardware/gpu/` | Coordinated AMDGPU/HDA kernel patches, original patch attribution and kernel-pinned package |
| `packaging/arch/hardware/power-tools/` | Fan, SMC calibration and zone-power applications with native systemd units |
| `packaging/arch/hardware/{touchid,ave,touchbar}/` | Touch ID, AVE/Sidecar and optional Touch Bar recipes |
| `packaging/arch/hardware/cold-trial/` | Guarded cold-boot, firmware preference, runtime-PM, battery and suspend validation tools |
| `packaging/arch/omarchy/` | Latest Bash update hooks, control helper/PolicyKit action and persistent hardware-preparation files |
| `apps/t2center/` | Omarchy-themed Qt control center, translations, desktop entry, source and existing checks |

KaiT2en-derived recipes pin the locally used upstream source commit
`cf64a1fcee7cfb790c74847c8356965aa42e2160`. Updating the fork's upstream history
does not silently change those package sources. Bankstown pins
`e9829c9bccf5ed73768135c0ddd506f5a6690f9e`. Rust builds use committed lockfiles.
No Fedora binary packages are used.

## Audio build and installation

Start with an Arch build environment (`base-devel`, Git, Rust/Cargo). Install
PipeWire audio, WirePlumber >= 0.5.8, `lsp-plugins-lv2` and the T2
`t2bce_audio-alsa-ucm-conf` package. From the repository root:

```sh
(cd packaging/arch/bankstown && makepkg -si)
(cd dsp/packaging && makepkg -si)
```

The DSP install hook runs upstream's ownership-aware `package-actions configure`:
it selects the DMI-specific graph and tracks generated configuration. Reboot
normally so udev assigns the audio card ID before PipeWire opens it. Do not
stack Omarchy's speaker tuning or another speaker DSP on top of this graph.
On MacBookPro16,1 the expected nodes are `audio_effect.t2-161-speakers` and
`audio_effect.t2-161-mic`. Preserve explicit USB/Bluetooth/headset defaults.

The post-update hook is an opt-in user hook, not part of the audio package:

```sh
install -Dm755 packaging/arch/omarchy/90-kait2en-audio \
  "$HOME/.config/omarchy/hooks/post-update.d/90-kait2en-audio"
bash "$HOME/.config/omarchy/hooks/post-update.d/90-kait2en-audio"
```

This is the corrected Bash hook, not the superseded Python copy that Omarchy
invoked through Bash. It checks the model/graphs, can restart user PipeWire once,
disables competing Omarchy tuning and replaces a raw built-in mic default only.
It may interrupt playback when recovering missing nodes.

Rollback: remove `t2-dsp` with pacman and reboot. The lifecycle engine removes
unchanged generated files using its ownership receipt, preserving modified files.
Bankstown and LSP can remain installed.

## Hardware packages: build before activation

The hardware recipes are not a one-command installer. Building a package is
separate from selecting drivers, editing the boot image or enabling services.
Keep a known-good encrypted-disk boot path and local console access.

Build the split DKMS package in `packaging/arch/hardware/`; install only the
resulting packages needed for the planned trial. Build power tools after the
battery package. Build Touch ID, AVE and Touch Bar separately in their respective
directories with `makepkg`; review their configs before installing/enabling them.
No new service is automatically enabled by these recipes.

The GPU recipe deliberately requires `linux-t2=7.2.11.arch1-1` and matching
headers, for kernel `7.2.11-arch1-Watanare-T2-1-t2`. It builds AMDGPU and GPU HDMI
HDA together from Linux 7.2.11 (SHA256
`fd0fc479f983a8c05313f13e9c36330fe6651cf725396748c40d5cd93fa1e6a4`). Rebuild
and review for another kernel; never remove the exact dependency to force-load
an incompatible module. Original patches are kept in `gpu/upstream-patches/`.

**Never hot-unload a battery provider while a t2smc battery extension is
attached.** An early local hot-swap triggered a kernel Oops in
`power_supply_unregister_extension`. Use a cold boot. Load `t2smc` before `t2sbs`,
and `t2gmux` before the GPU drivers; do not stack old/new fan controllers.

The exported permanent configuration under `omarchy/` preserves the local
module ordering, blacklist/soft dependency and GPU HDMI-audio rebind/runtime-PM
helper. It targets MacBookPro16,1: Intel `00:02.0`, AMD `03:00.0`, HDA `03:00.1`,
`BAT0` and T2 NCM interface `enp4s0f1u1`. Review all addresses before use. These
files are not installed or enabled by the control-center package. If deploying
manually, map the helper to `/usr/libexec/kait2en-hardware-prep`, the service to
`/etc/systemd/system/`, the modprobe fragment to `/etc/modprobe.d/` and the
mkinitcpio fragment to `/etc/mkinitcpio.conf.d/`. The boot command line must use
`t2gmux.boot_gpu=0`, not `apple_gmux.force_igd=1`, only after coordinated driver
selection. Rebuild/review the boot image using the machine's own boot tooling;
no copied boot menu or unattended reboot is supplied.

The `90-kait2en-hardware` hook diagnoses the fully activated stack. Install it
in the same user hook directory as the audio hook only after promotion; it
will report missing packages/drivers/services on an audio-only installation.
It does not install missing packages or activate kernel drivers.

Touch ID defaults to `T2_TOUCHID_BIND_USER=none`, not the original workstation's
account. Configure `/etc/kait2en/t2-touchid.conf` for the intended Linux account
before enabling `kait2en-t2-touchid.service`; macOS enrollment remains a separate
prerequisite. AVE ships the service and Sidecar module, not a hardware-success
guarantee. The optional Touch Bar daemon must not run alongside `tiny-dfr`.

## Cold-trial tools and intentionally private inputs

These tools preserve the original guarded trial workflow; they are not portable
automatic boot provisioning. `build-trial.py` refuses the wrong model/kernel,
a changed boot menu, an existing trial image and a boot already using t2smc.
It expects the GPU recipe's staged modules and a locally built
`modules/t2gmux/t2gmux.ko` (`make -C modules/t2gmux`). `register-trial.py` checks
embedded module identities, ordering, command-line arguments and UKI hash,
then appends an opt-in entry while retaining the default boot image.

`cold-trial/inputs.json` is intentionally local and ignored. Its required fields
are `limine_sha256` (SHA256 of the current `/boot/limine.conf`), `helper_sha256`
(SHA256 of `/usr/local/bin/gpu-amd-dpm-low`), `kernel` and `boot_cmdline` (the
machine's current `/proc/cmdline`, stripped of its final newline). After building,
`cold-trial/limine.conf` must be prepared locally from the actual current menu
plus one `/KaiT2en hardware trial` entry, the generated image's BLAKE2b digest
and its embedded trial arguments. Registration rejects any mismatch. Do not
copy another machine's UUIDs, resume offset, hashes or encrypted-root arguments.

The old GPU helper is retained here only for the original-stack fallback/trial
workflow. Do not reinstall it over the promoted runtime-PM stack. Runtime
checks use `/var/lib/kait2en-hardware/cold-trial/manifest.json` written by the
builder; copy `check-trial.py` to `/usr/libexec/kait2en-hardware-check` only as
part of that reviewed workflow. Status is read-only; `prepare`, `exercise`,
`battery-test`, `compare`, firmware preference and suspend tools mutate hardware
state and require deliberate local operation. No trial, firmware, charge-limit,
suspend or reboot commands are run merely to publish this fork.

## T2 Control Center

From `apps/t2center/`, run `./bin/build`, `./bin/test`, then `./bin/install`.
Its package now includes the previously separately installed `t2-control` helper
and PolicyKit action. The action permits active local users to change charge
limits and fan presets without another password prompt; review before deploying
on shared machines. The helper and GUI currently assume the hardware addresses
listed above. The original GTK power applications remain available separately.

## Publication verification

The relocated control center built successfully, its existing check returned
`OK`, and an actual Arch package contained the GUI, desktop entry, privileged
helper and PolicyKit action. The isolated PipeWire smoke scenario loaded all
24 DSP graphs and 48 nodes without opening hardware. Shell/Python syntax,
PolicyKit XML and all nine recipe metadata generators were checked.

These checks do not establish support on other models, acoustic quality,
physical headphone/display hotplug, Touch ID enrollment, AVE success, battery
calibration safety or complete cross-OS firmware persistence. Build outputs,
package archives, recordings, fingerprint data, local boot menus, disk UUIDs,
firmware backups, runtime logs and private trial inputs are intentionally absent.

## Additional manually installed integration

The recovered desktop plugin is exported in `omarchy/plugins/sonnt.t2/`.
Copy that directory under `~/.config/omarchy/plugins/`, preserving its ID, and
add `{"id": "sonnt.t2"}` to the desired existing `bar.layout` section in
`~/.config/omarchy/shell.json`. Do not replace the rest of the shell config.
The Apple-icon panel shows live hardware telemetry, fan presets and charge
controls and launches `t2center`. Install the control-center package first.
The plugin is exported unchanged; it was not reloaded or visually re-tested
as part of publication.

Both exported hooks also serve the original `post-boot.d` event: install copies
of `90-kait2en-audio` and `90-kait2en-hardware` there under the same activation
conditions described above. The original boot and update hook contents matched.

`omarchy/gpu-aq-drm-devices` is sourced, not executed. Install it in
`~/.local/bin/` and merge the source line from `omarchy/uwsm/env-hyprland` into
the existing uwsm environment file. It checks the model, PCI IDs and Intel boot
ownership, exports Intel first and keeps AMD as a secondary compositor device
when available. This preserves external-display detection without restarting
Hyprland. The final boot-argument fragment is exported separately under
`omarchy/limine-entry-tool/gpu-igd.conf`; review it before installing under
`/etc/limine-entry-tool.d/` and rebuilding any boot image.

The power-tools recipe removes the upstream wordmark widgets before compiling
the three GTK applications. It does not install the upstream logo assets.
Original source, copyright and license attribution are preserved.
Each header has an **About** button opening the original author credits and
legal notices, the full GPLv3 text and dated independent-fork modifications.
The package also includes each application's unchanged notice as
`/usr/share/licenses/kait2en-power-tools/<project>.LICENSE`.

The AVE recipe now packages the locally used native service, including
`UMask=0000` and `Group=root`. **Security tradeoff:** the zero umask can create
world-readable/writable files or sockets unless the daemon explicitly narrows
their permissions. This preserves the prior local AVE permission fix, not a
claim that the service is hardened for multiuser machines. Review the service
and its created objects before enabling it on a shared system.

`omarchy/pam-fingerprint.auth` contains only the two intended authentication
rules, not snapshots of `/etc/pam.d/sudo` or `/etc/pam.d/polkit-1`. Back up and
review both PAM stacks, keep an authenticated recovery terminal open, and
insert those rules before the existing auth rules without deleting the existing
password fallback. The Omarchy closed-lid helper skips fingerprint auth when
the lid is closed. This is opt-in: no PAM files are modified by package install.

Historical local hardware evidence, not re-run during publication: AMD
encoding followed by D3cold and charge stop/restoration passed; a 60-frame
1080p30 T2 HEVC MP4 was verified. Touch ID enrollment/binding was observed,
but successful PAM fingerprint authentication was not demonstrated.
**Suspend/resume did not pass**: the trial entered deep suspend, then a fresh
boot and a long-power-button shutdown were recorded. It remains an unresolved
deployment risk, not a validated feature.

Publication checks also staged the AVE and power-tools package functions using
the existing real build outputs: the AVE binary, native service and Sidecar
DKMS source were present, and both GTK wordmark assets matched the installed
upstream originals. The plugin manifest/entrypoint and POSIX compositor
environment were checked without modifying the running shell or hardware.
