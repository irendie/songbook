#!/usr/bin/env bash
# Core build script for the songbook (Linux/macOS).
# Usage: ./build.sh <a4|a5|all|clean> [--preview] [--no-index] [--custom-sort] [--indexes-only]
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_DIR="$SCRIPT_DIR/../src"
RELEASE_DIR="$SCRIPT_DIR/../release"

usage() {
    cat <<'EOF'
Usage: build.sh <a4|a5|all|clean> [options]

Formats:
  a4              build the A4 songbook (songbook_A4.pdf)
  a5              build the A5 songbook (songbook.pdf)
  all             build both formats
  clean           remove auxiliary build files from src/

Options:
  --preview       open the resulting PDF(s) after the build
  --no-index      single LuaLaTeX pass, skip index generation
  --custom-sort   post-process the index with sort_index.py (Czech sorting)
  --indexes-only  stop after generating the index (no final PDF)
EOF
    exit 2
}

FORMAT=""
PREVIEW=0
INDEX=1
CUSTOM_SORT=0
INDEXES_ONLY=0

for arg in "$@"; do
    case "$arg" in
        a4|a5|all|clean) FORMAT="$arg" ;;
        --preview)       PREVIEW=1 ;;
        --no-index)      INDEX=0 ;;
        --custom-sort)   CUSTOM_SORT=1 ;;
        --indexes-only)  INDEXES_ONLY=1 ;;
        *) echo "Unknown argument: $arg" >&2; usage ;;
    esac
done

[[ -n "$FORMAT" ]] || usage

if [[ "$FORMAT" == "clean" ]]; then
    rm -f "$SRC_DIR"/*.aux "$SRC_DIR"/*.log "$SRC_DIR"/*.out \
          "$SRC_DIR"/*.sxc "$SRC_DIR"/*.sbx "$SRC_DIR"/*.sxd
    echo "Cleaned auxiliary files in src/."
    exit 0
fi

mkdir -p "$RELEASE_DIR"

build() {
    local job="$1" # LaTeX job name (songbook = A5, songbook_A4 = A4)
    cd "$SRC_DIR"
    echo
    echo "=== $job: LuaLaTeX pass 1 ==="
    lualatex -interaction=nonstopmode "$job.tex"
    if [[ "$INDEX" == 1 ]]; then
        echo "=== $job: generating song index ==="
        texlua "$SCRIPT_DIR/songidx/songidx.lua" -l cs_CZ.UTF-8 mainsongsindex.sxd mainsongsindex.sbx
        if [[ "$CUSTOM_SORT" == 1 ]]; then
            echo "=== $job: applying custom Czech sort ==="
            python3 "$SCRIPT_DIR/sort_index.py"
        fi
        [[ "$INDEXES_ONLY" == 1 ]] && return 0
        echo "=== $job: LuaLaTeX pass 2 ==="
        lualatex -interaction=nonstopmode "$job.tex"
    fi
    mv -f "$job.pdf" "$RELEASE_DIR/$job.pdf"
    echo "=== $job: PDF written to release/$job.pdf ==="
    if [[ "$PREVIEW" == 1 ]]; then
        if [[ "$(uname)" == "Darwin" ]]; then
            open "$RELEASE_DIR/$job.pdf"
        else
            xdg-open "$RELEASE_DIR/$job.pdf" >/dev/null 2>&1 &
        fi
    fi
}

case "$FORMAT" in
    a5)  build songbook ;;
    a4)  build songbook_A4 ;;
    all) build songbook; build songbook_A4 ;;
esac

echo
echo "Done."
