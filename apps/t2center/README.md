# T2 Control Center (`t2center`)

Apple T2 hardware control center for Omarchy Linux on Intel MacBooks with an Apple T2 security chip.

## Features

- **GPU Hybrid Power**: Live status of Intel UHD 630 primary scanout and AMD Radeon Pro 5300M in D3cold runtime suspend (0 W).
- **Thermals & Fan Management**: Live CPU, GPU and battery temperatures, fan speeds in RPM, and quick fan presets (Quiet, Balanced, SMC Auto curve).
- **Battery Charge Protection**: Battery capacity and status, with 80% healthy threshold toggle and 100% full charge toggle via sysfs `charge_control_end_threshold`.
- **T2 Video Transcoding**: Direct Apple T2 Apple Video Encoder (AVE) hardware transcode to H.265 (`hevc_v4l2m2m`) without waking the dGPU.
- **Omarchy Native**: Follows the live Omarchy palette and Hyprland rounding. Uses the desktop application font for labels, monospace for telemetry, and flat Qt buttons with keyboard focus and disabled states. Overview tiles and fan controls fit the 720×500 minimum window.

## Shortcuts

| Key | Action |
|---|---|
| `Q` | Quit |
| `R` / `Space` | Refresh hardware telemetry |
| `1`–`4` | Switch sections |
| `Tab` / `Shift+Tab` | Move between controls |
| `Space` on a focused button | Activate the button |
| `?` / `Escape` | Show / dismiss help |

App shortcuts pause while entering a video path.

## Build and Install

```bash
./bin/build
./bin/test
./bin/install
```

Run these commands from `apps/t2center/`. The package includes the
`/usr/libexec/t2-control` helper and its PolicyKit action. Active local
sessions may change fan presets and charge limits without another password
prompt; review `packaging/arch/omarchy/org.omarchy.t2control.policy` before
installing on a shared machine.

Hardware addressing currently targets MacBookPro16,1 with AMD at `03:00.0`
and battery `BAT0`; this is not automatic support for every T2 Mac.
Build and integration notes: [Arch / Omarchy guide](../../packaging/arch/README.md).
