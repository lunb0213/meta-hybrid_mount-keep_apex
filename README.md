# Hybrid Mount Keep APEX

Automatically tracks upstream releases from [Hybrid-Mount/meta-hybrid_mount](https://github.com/Hybrid-Mount/meta-hybrid_mount) while restoring Hybrid Mount management of `/apex`.

This repository does **not** maintain a long-lived fork of the full upstream source tree. For every upstream release, GitHub Actions fetches the corresponding official release tag, applies a minimal `/apex` patch, rebuilds the module, publishes a `-apex` release, and updates this repository's `update.json`.

## Features

- Automatically checks the latest upstream Hybrid Mount release
- Fetches the exact official release tag
- Restores `apex` to Hybrid Mount managed partitions
- Restores installer-side `apex` partition handling
- Adjusts related tests when needed
- Redirects the module `updateJson` to this repository
- Builds using the upstream project's own `cargo xtask` build system
- Publishes releases using the `vX.Y.Z-apex` naming convention
- Automatically maintains `update.json`
- Avoids long-lived merges, rebases, and accumulated fork history

## Difference From Upstream

The intended functional difference is limited to one behavior:

```text
Upstream Hybrid Mount
    ↓
does not manage /apex

This project
    ↓
restores Hybrid Mount management of /apex
```

For example:

```text
Upstream:
v6.1.4

This project:
v6.1.4-apex
```

The generated package will look similar to:

```text
Hybrid-Mount-6.1.4-apex-xxxx.zip
```

## Why This Project Exists

Hybrid Mount removed `/apex` from its managed partitions starting with the v6.1.x line to avoid interfering with Android's APEX activation flow in affected environments.

This project restores that behavior for users who intentionally still need Hybrid Mount to manage `/apex`.

## ⚠️ Risk Notice

`/apex` is not a normal static system partition.

It is managed by Android's `apexd` service and participates in the system boot-time APEX activation process. Additional OverlayFS or Magic Mount operations under `/apex` may cause:

- APEX activation failures
- `apexd-failed`
- Mount conflicts
- Boot failures
- Boot loops in severe cases

Upstream removed `/apex` support because such failures were observed in some environments, including Android 17.

Use this project only if you understand and accept that risk.

It is strongly recommended to have a reliable KernelSU/APatch safe mode, module-disable method, or other recovery path available before testing.

## MoveCertificate

Upstream Hybrid Mount may still blacklist `MoveCertificate`.

This project restores `/apex` support only. It does **not** automatically remove `MoveCertificate` from the upstream blacklist.

Therefore:

```text
Restoring /apex support
≠
forcing MoveCertificate to be mounted by Hybrid Mount
```

Any blacklist change should be evaluated separately.

## How Automatic Updates Work

The workflow periodically checks the latest upstream release.

```text
Check latest upstream release
        ↓
Check whether matching -apex release already exists
        ↓
Clone the official release tag
        ↓
Run scripts/keep-apex.py
        ↓
Restore /apex support
        ↓
Redirect updateJson
        ↓
Apply version from upstream release tag
        ↓
Build with upstream xtask
        ↓
Publish GitHub Release
        ↓
Update main/update.json
```

Each build starts from a clean official release tag.

The project does not merge from the previous custom release, so custom source history does not accumulate over time.

## Check Frequency

By default, GitHub Actions checks upstream every 6 hours:

```yaml
schedule:
  - cron: "17 */6 * * *"
```

You can also trigger it manually from:

```text
Actions
→ Sync Upstream + Restore APEX
→ Run workflow
```

## Repository Structure

```text
.
├── .github/
│   └── workflows/
│       └── sync-apex.yml
├── scripts/
│   └── keep-apex.py
├── README.md
├── README-zh.md
└── update.json
```

### `scripts/keep-apex.py`

The patch script is responsible for:

- Adding `apex` back to Rust `MANAGED_PARTITIONS`
- Adding `apex` back to `module/metainstall.sh`
- Adjusting related tests
- Redirecting the module's `updateJson`

The script intentionally fails if the expected upstream structure can no longer be found.

This is safer than silently producing a broken package after a major upstream refactor.

## Installation

Open this repository's **Releases** page and download the latest package:

```text
Hybrid-Mount-*-apex-*.zip
```

Install it with a KernelSU or APatch manager that supports MetaModule, then reboot.

## Update Channel

The build process rewrites Hybrid Mount's `updateJson` to this repository:

```text
https://raw.githubusercontent.com/<owner>/<repo>/main/update.json
```

This means installations of this project continue receiving `-apex` releases instead of switching back to the upstream build without `/apex` support.

## Versioning

If upstream releases:

```text
v6.1.4
```

this project publishes:

```text
v6.1.4-apex
```

with a package version similar to:

```text
6.1.4-apex
```

and a version code derived from the upstream numeric version:

```text
601004
```

The upstream release tag is treated as the source of truth for the version number.

## Build

GitHub Actions installs the required build environment, including:

- Node.js
- pnpm
- Rust stable
- Rust nightly
- cargo-ndk
- Android SDK
- Android NDK

The actual package build still uses Hybrid Mount's upstream build entry point:

```bash
cargo xtask build --ci
```

Therefore, module packaging logic remains controlled by upstream Hybrid Mount's own `xtask`.

## Upstream

Upstream project:

https://github.com/Hybrid-Mount/meta-hybrid_mount

This project is unofficial and is not affiliated with or endorsed by the upstream Hybrid Mount developers.

If an issue occurs only in this project's `-apex` build, verify whether it is caused by the restored `/apex` behavior before reporting it upstream.

## License

Hybrid Mount upstream is licensed under GPL-3.0-only.

Any redistribution or modification of upstream code must continue to comply with the applicable upstream license terms.

## Disclaimer

This project is provided as-is, without warranty.

By using it, you acknowledge that:

- It intentionally restores an upstream-removed `/apex` mounting behavior
- That behavior may interfere with Android APEX activation
- It may cause serious boot problems on some devices or Android versions
- You are responsible for having a recovery method available
