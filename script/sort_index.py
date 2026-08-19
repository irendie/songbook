"""Re-sort the songidx-generated song index (src/mainsongsindex.sbx).

Uses Czech collation (including the 'Ch' digraph, which gets its own index
block) and orders the blocks Latin -> Cyrillic -> any other alphabet.
"""
import locale
import os
import re
import unicodedata

# Locale names differ between Windows, Linux, and NixOS.
for loc in ("cs_CZ.utf8", "cs_CZ.UTF-8", "cs_CZ", "cs", "Czech"):
    try:
        locale.setlocale(locale.LC_COLLATE, loc)
        break
    except locale.Error:
        continue
else:
    raise SystemExit(
        "Czech locale is not installed "
        "(tried cs_CZ.utf8 / cs_CZ.UTF-8 / cs_CZ / cs / Czech)."
    )

# Resolve the index relative to this script so the working directory doesn't matter.
INDEX_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "src", "mainsongsindex.sbx"
)

ENTRY_PREFIX = "\\idxentry{"


def sanitize(line: str) -> str:
    """Replace songidx accent macros (\\r = ring, \\v = caron) with combining
    characters and normalize to NFC so collation sees real letters."""
    line = re.sub(r"\\r\s(\S)", "\\1\u030a", line)
    line = re.sub(r"\\v\s(\S)", "\\1\u030c", line)
    return unicodedata.normalize("NFC", line)


def title_of(entry: str) -> str:
    return entry[len(ENTRY_PREFIX):]


def script_group(title: str) -> int:
    """Sort group of the title's first letter: 0 = Latin, 1 = Cyrillic, 2 = other."""
    for char in title:
        if char.isalpha():
            name = unicodedata.name(char, "")
            if "LATIN" in name:
                return 0
            if "CYRILLIC" in name:
                return 1
            return 2
    return 2


def block_letter(title: str) -> str:
    """Index block heading for a title; 'Ch' is a standalone letter in Czech."""
    if title[:2].lower() == "ch":
        return "CH"
    return title[:1].upper()


def sort_key(entry: str):
    title = title_of(entry)
    return (script_group(title), locale.strxfrm(title))


with open(INDEX_PATH, encoding="utf-8") as index_file:
    entries = [sanitize(line) for line in index_file if line.startswith(ENTRY_PREFIX)]

entries.sort(key=sort_key)

# Rewrite the index, opening a new block whenever the leading letter changes.
with open(INDEX_PATH, "w", encoding="utf-8") as index_file:
    previous_letter = None
    for entry in entries:
        letter = block_letter(title_of(entry))
        if letter != previous_letter:
            if previous_letter is not None:
                index_file.write("\\end{idxblock}\n")
            index_file.write("\\begin{idxblock}{" + letter + "}\n")
            previous_letter = letter
        index_file.write(entry)
    if previous_letter is not None:
        index_file.write("\\end{idxblock}\n")
