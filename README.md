# T2 Omarchy

Independent Arch Linux / Omarchy integration based on
[KaiT2en-Fedora](https://github.com/kaiT2en/KaiT2en-Fedora), preserving upstream
history, source attribution and component licenses. Not an official KaiT2en,
Omarchy or Apple release; no upstream endorsement is implied.

This fork collects the local DSP audio port, native hardware packages,
Omarchy update hooks, guarded hardware validation tools and T2 Control Center.

## Arch / Omarchy installation

See [the integration guide](packaging/arch/README.md) for build order,
installation, hardware-specific limits and verification.
Do not run the Fedora installer on Omarchy.

Upstream Fedora documentation remains at
[kait2en.org](https://kait2en.org/documentation.html).

## Community

Join the KAIT2EN community on [Discord](https://discord.gg/AGfjRk4ydj) or on
[Matrix](https://matrix.to/#/%23kait2en:matrix.org).

## Contributing

Contributions are welcome, especially when they move KAIT2EN fixes closer to
clean upstream Linux support.

Please keep changes and PR descriptions focused.
**We will reject PRs and Issues when we notice we are talking to AI!**
At least talk to us in person.
We are not interested in workarounds.
We are not interested in major AI refactories.
There is a distinct difference between making broken things work and fixing things.

## License

KAIT2EN-owned scripts, howto documents, project text and helper code are MIT
licensed.

Kernel modules, apps and third-party tools may include code with different
origins. Those components keep their own licenses in their directories.

The kernel modules are GPL-2.0; everything else KAIT2EN writes, apps, protocols,
audio DSP profiles and scripts, is GPL-3.0-or-later. The full breakdown is in
[LICENSING.md](LICENSING.md).

The code licenses do not grant the KAIT2EN name or logo. Their use, and what
the project stands for, are described in [TRADEMARK.md](TRADEMARK.md) and
[VALUES.md](VALUES.md).
