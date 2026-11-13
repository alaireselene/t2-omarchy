# Apple T2 patches for Omarchy

Independent Arch Linux / Omarchy integration based on
[KaiT2en-Fedora](https://github.com/kaiT2en/KaiT2en-Fedora), preserving upstream
history, source attribution and component licenses. Not an official KaiT2en,
Omarchy or Apple release; no upstream endorsement is implied.

Modified from KaiT2en-Fedora cf64a1f since 2026-11-09.
The upstream source is pinned at `cf64a1fcee7cfb790c74847c8356965aa42e2160`;
fork-specific changes include the Arch packaging and Omarchy integration.

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

The applicable licenses and original author notices are preserved per component.
Complete license texts are included in this repository:

- [GNU GPL version 2](LICENSES/GPL-2.0-only.txt) for the kernel components,
  subject to each file's license notice.
- [GNU GPL version 3](LICENSES/GPL-3.0-or-later.txt) for the GPL-3.0-or-later
  programs, protocols, DSP profiles, scripts and documentation.
- Independently licensed and third-party components retain their own notices.

See [LICENSING.md](LICENSING.md) for the component breakdown and preserved
attribution requirements. On 2026-11-14, this fork added the missing GPL-2.0
text and corrected Arch package delivery of the full GPL license texts.

The code licenses do not grant the KAIT2EN name or logo. Their use, and what
the project stands for, are described in [TRADEMARK.md](TRADEMARK.md) and
[VALUES.md](VALUES.md).
