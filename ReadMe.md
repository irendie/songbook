# Mr. Tavitel's songbook

Personal songbook written in LuaLaTeX using the [songs](https://songs.sourceforge.net/) package. It builds into two PDF formats: **A5** (`songbook.pdf`, for print) and **A4** (`songbook_A4.pdf`).

## Quick start

The fastest path on any OS with Docker installed — no TeX, no Nix, nothing else needed. A prebuilt toolchain image is published to GHCR by CI:

```bash
docker run --rm -v "$PWD:/songbook" ghcr.io/irendie/songbook:toolchain all   # PowerShell: -v "${PWD}:/songbook"
```

Or build the image yourself:

```bash
docker build -t songbook .
docker run --rm -v "$PWD:/songbook" songbook all
```

PDFs appear in `release/`. For faster incremental builds or editing, set up one of the environments below.

## Prerequisites

Pick **one** of the following environments:

### A. Nix (recommended — fully reproducible, Linux/macOS/WSL)

With [Nix](https://nixos.org/download/) installed, everything (TeX Live, `songs`/`songidx`, CMU fonts, Python, Czech locale) is provided by the dev shell:

```bash
nix-shell                    # classic, no experimental features needed
# or
nix develop                  # flakes
./script/build.sh all --custom-sort
```

[direnv](https://direnv.net/) users: `direnv allow` once and the shell activates automatically (see `.envrc`).

### B. NixOS on WSL (Windows)

Gives you the same Nix environment on any Windows machine:

1. One-time, from an **elevated** PowerShell, then reboot: `wsl --install --no-distribution`
2. Run `script\setup_nixos_wsl.ps1` — downloads [NixOS-WSL](https://github.com/nix-community/NixOS-WSL) and imports it as the `NixOS` distro
3. Build:

```powershell
wsl -d NixOS
cd /mnt/c/Repos/songbook
nix-shell --run './script/build.sh all --custom-sort'
```

### C. Docker

No local TeX needed — the image contains the full toolchain:

```bash
docker build -t songbook .
docker run --rm -v "$PWD:/songbook" songbook a4            # any build.sh arguments work
docker run --rm -v "${PWD}:/songbook" songbook all --preview # PowerShell syntax
```

PDFs land in `release/` on the host as usual (the repo is bind-mounted).

> Note: Docker runs as root, so it leaves root-owned auxiliary files in `src/`. If a later WSL/Linux build fails with "can't write on file", run `build clean` first.

### D. Manual installation

* A LaTeX distribution with **LuaLaTeX** (TeX Live or MiKTeX)
  * `songs` package — the `songidx` index generator itself is vendored in `script/songidx/` (GPL-2, from [songs upstream](https://songs.sourceforge.net/)) and runs via `texlua`, so nothing extra to install
  * `cm-unicode` font package — probably needs to be installed manually; the rest should auto-install (if package auto-installing is enabled in your LaTeX distribution)
* **Python 3** — only needed for the optional custom Czech index sorting (`--custom-sort`)
  * On Linux/macOS, the `cs_CZ.UTF-8` locale must be installed

### VS Code

The workspace ships build tasks (`Terminal → Run Build Task`, Ctrl+Shift+B): A4/A5/all builds, Docker build, and clean — they pick the right script for your OS automatically.

## Building

All builds are driven by a single parameterized script — `script/build.ps1` (Windows) or `script/build.sh` (Linux/macOS):

```
build.ps1 <a4|a5|all|clean> [-Preview] [-NoIndex] [-CustomSort] [-IndexesOnly]
build.sh  <a4|a5|all|clean> [--preview] [--no-index] [--custom-sort] [--indexes-only]
```

| Argument (`.ps1` / `.sh`) | Meaning |
|---|---|
| `a4` / `a5` / `all` | Which format(s) to build |
| `clean` | Remove auxiliary build files (`.aux`, `.log`, `.sxd`, ...) from `src/` |
| `-Preview` / `--preview` | Open the resulting PDF(s) after the build |
| `-NoIndex` / `--no-index` | Single LuaLaTeX pass, skip song index generation |
| `-CustomSort` / `--custom-sort` | Post-process the index with `sort_index.py` (proper Czech alphabet sorting, incl. `Ch`) |
| `-IndexesOnly` / `--indexes-only` | Stop after generating the index (no final PDF) |

Resulting PDFs are placed in `release/`.

### Examples

Windows (PowerShell):

```powershell
cd script
.\build.ps1 all -Preview
```

Linux/macOS:

```bash
cd script
./build.sh a5 --preview --custom-sort
```

## Project structure

| Path | Purpose |
|---|---|
| `src/songbook.tex` | A5 build entry point |
| `src/songbook_A4.tex` | A4 build entry point |
| `src/main.tex` | Shared document body |
| `src/campfire_songs.tex`, `src/other_songs.tex`, ... | Song collections |
| `src/settings_*.tex` | Font size / geometry settings per format |
| `script/` | Build scripts (`build.ps1`, `build.sh`, `sort_index.py`) |
| `flake.nix`, `shell.nix`, `nix/` | Nix dev shell with the full toolchain |
| `Dockerfile` | Container image for building without a local TeX install |
| `script/setup_nixos_wsl.ps1` | One-shot NixOS-on-WSL setup for Windows |
| `release/` | Build output (PDFs) |

## How the build works

1. LuaLaTeX pass — compiles the document and emits raw index data (`mainsongsindex.sxd`)
2. `songidx -l cs_CZ` — generates the sorted song index (`mainsongsindex.sbx`)
3. Optionally `sort_index.py` re-sorts the index using proper Czech collation (including the `Ch` digraph)
4. Second LuaLaTeX pass — compiles the final PDF with the index included
5. The PDF is moved to `release/`