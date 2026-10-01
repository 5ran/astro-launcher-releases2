# Astro Launcher releases

Official compiled releases for Astro Launcher and supported macros.

- [Download Astro Launcher](https://ae-storefront.vercel.app/downloads/launcher/Astro-Launcher-2.0.1.exe)
- [Browse versioned releases](https://github.com/5ran/astro-launcher-releases2/releases)
- [Website](https://ae-storefront.vercel.app)

The launcher verifies each executable against the SHA-256 in its signed catalog.
GitHub is the primary download host; the website download links select Cloudflare
as a fallback if GitHub is unavailable. Existing version numbers and hashes are
preserved when a release is mirrored.

This repository contains release binaries and documentation only. It does not
contain application source, signing keys, customer information, or credentials.

## Corrected shared offsets

`offsets/offsets.json` is refreshed from Theo's feed by the Sync corrected offsets
GitHub Action, scheduled every 20 minutes and available through Run workflow.
Scheduled runs can be delayed by GitHub. Invalid downloads leave the last good
file intact. The updater tries Theo's primary endpoint and then its mirror.

`offsets/corrections.json` contains ONLY independently verified overrides keyed
by exact Roblox build. Current corrections: AbsoluteSize 260 (0x104) and
ImageColor3 2696 (0xA88), validated with three complete controlled UI cycles on
version-02c37bc51a384b8f. Other builds do not inherit these corrections.
Edit this JSON to add verified corrections; pushing it triggers a new sync.
The small sync script is release-feed infrastructure, not macro application source.

Astro Launcher 2.0.2 uses the GitHub snapshot for Get Latest, retains a local
backup, and keeps existing offsets if downloads fail. Customers must restart
running macros after updating offsets. Existing launchers need the 2.0.2 update
before their Get Latest uses this feed.

### Current build evidence and scope

For version-02c37bc51a384b8f, UI3 validation completed three full eight-phase
cycles on three ImageLabels (run-1790853533680.json): AbsolutePosition 252,
AbsoluteSize 260, AbsoluteRotation 216, BorderColor3 1340, ZIndex 1428,
and ImageColor3 2696. AbsolutePosition stores screen-space coordinates;
conversion to the Luau property requires the current live GUI inset.

WorldPivotData 232 (0xE8) passed five full 13-phase cycles on three models in
one Player process (run-1790854339781.json). Current-build getter/setter
inspection at RVA 0xF29DE9 / 0xF29EE5 confirms field 0xE8, low-two-bit mask,
48-byte payload, and the associated property descriptor named WorldPivot.
This is a tagged pointer, NOT an inline CFrame offset. Supported case:
explicitly assigned model pivot, no PrimaryPart, tag 2. Consumers must reread
and validate the pointer and matrix. Other tags/unassigned fallback layouts
are not covered; fresh-process repetitions for this new build remain outstanding.
No Model.WorldPivot inline offset is published.
