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

## Independent project identity

This fork is **t2-patches-for-omarchy**:
[github.com/alaireselene/t2-patches-for-omarchy](https://github.com/alaireselene/t2-patches-for-omarchy).
It is not affiliated with or endorsed by KaiT2en, Omarchy, the Omacom
Foundation or Apple. "For Omarchy" describes compatibility, not affiliation.

KaiT2en is named only to identify the upstream source and preserve attribution;
its name and logos are not this fork's branding. Existing upstream technical
identifiers are retained where required for compatibility. The Arch power-tools
recipe removes the upstream GTK wordmarks, and the inherited branded Fedora
installer and website publication jobs run only in the upstream repository.
Those upstream sources and their original notices remain available for reference.

The upstream restriction in [TRADEMARK.md](TRADEMARK.md) is preserved unchanged.
It withholds brand and endorsement permission; it does not remove permissions
granted by the applicable code licenses or prohibit compatibility with Omarchy.

## Arch / Omarchy installation

See [the integration guide](packaging/arch/README.md) for build order,
installation, hardware-specific limits and verification.
Do not run the Fedora installer on Omarchy.

Upstream Fedora documentation remains at
[kait2en.org](https://kait2en.org/documentation.html).

## Upstream community

For discussion of the upstream project, see its community on [Discord](https://discord.gg/AGfjRk4ydj) or on
[Matrix](https://matrix.to/#/%23kait2en:matrix.org).

## Contributing

Keep contributions focused on this independent patch set. Report fork-specific
issues in this repository; do not imply upstream authors support these changes.
Preserve original copyright, license and attribution notices when adapting code.

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
