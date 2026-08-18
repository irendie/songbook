# Converts LaTeX "songs" package sources (src/*.tex) to ChordPro files (chordpro/).
# Usage: python convert_to_chordpro.py
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
OUT_SONGS = ROOT / "songs"
OUT_CONFIG = ROOT / "config"

SONG_FILES = ["campfire_songs.tex", "other_songs.tex", "wip_songs.tex", "removed_songs.tex"]

NBSP = "\u00a0"


def find_balanced(text, start, open_ch="{", close_ch="}"):
    """text[start] must be open_ch. Returns (content, index_after_close)."""
    assert text[start] == open_ch
    depth = 0
    for i in range(start, len(text)):
        if text[i] == open_ch:
            depth += 1
        elif text[i] == close_ch:
            depth -= 1
            if depth == 0:
                return text[start + 1:i], i + 1
    raise ValueError(f"Unbalanced {open_ch} at {start}: {text[start:start+80]!r}")


def unescape(s):
    s = s.replace(r"\#", "#").replace(r"\&", "&").replace(r"\_", "_").replace(r"\%", "%")
    return s


def gtab_to_chord(name, spec):
    """Parse songs-package \\gtab spec into (name, base, frets, fingers)."""
    name = unescape(name)
    base = 1
    m = re.match(r"^(\d+):(.*)$", spec)
    if m:
        # songs \gtab shows the diagram from fret N; digits are relative offsets such
        # that absolute fret = digit + N - 2, which equals ChordPro base-fret = N - 1.
        base = max(1, int(m.group(1)) - 1)
        spec = m.group(2)
    fingers = None
    if ":" in spec:
        spec, fingers = spec.split(":", 1)
    frets = [c for c in spec if c in "xX0123456789"]
    if len(frets) == 5:  # tolerate a missing leading string (e.g. G+ "X5443")
        frets = ["x"] + frets
    frets = ["x" if c in "xX" else int(c) for c in frets]
    # keep the shape inside ChordPro's 4-fret diagram window
    numeric = [f for f in frets if isinstance(f, int) and f > 0]
    if numeric and max(numeric) > 4:
        shift = min(numeric) - 1
        if shift > 0:
            base += shift
            frets = [f - shift if isinstance(f, int) and f > 0 else f for f in frets]
    if fingers and set(fingers) != {"0"}:
        fingers = [int(c) for c in fingers if c.isdigit()]
    else:
        fingers = None
    return name, base, frets, fingers


def chord_define_directive(name, base, frets, fingers):
    s = f"{{define: {name} base-fret {base} frets " + " ".join(str(f) for f in frets)
    if fingers:
        s += " fingers " + " ".join(str(f) for f in fingers)
    return s + "}"


STRIP_MACROS = re.compile(
    r"\\(stopchordsalways|resumechordsalways|stopchords|resumechords|nolyrics|MultiwordChords)\b"
)


def convert_inline(s):
    """Convert inline LaTeX song markup to ChordPro text. May return embedded \n."""
    s = unescape(s)
    s = re.sub(r"\\\[\^?", "[", s)  # \[Am] -> [Am] (drop replay marker ^)
    s = re.sub(r"\\uv\{([^{}]*)\}", "\u201e\\1\u201c", s)
    s = re.sub(r"\\lrep(\{\})?", "|:", s)
    s = re.sub(r"\\rrep(\{\})?", ":|", s)
    s = re.sub(r"\\rep\{(\d+)\}", "\u00d7\\1", s)
    s = re.sub(r"\\hspace\*?\{[^{}]*\}", NBSP * 3, s)
    s = s.replace(r"\textdownarrow", "\u2193").replace(r"\textuparrow", "\u2191")
    s = re.sub(r"\\newline(\{\})?", "\n", s)
    s = re.sub(r"\\vskip\s*[\d.]+\s*(cm|mm|pt|em|ex)", "", s)
    s = STRIP_MACROS.sub("", s)
    s = s.replace("~", NBSP).replace(r"\,", " ")
    s = s.replace("{", "").replace("}", "")  # leftover grouping braces
    return s


def convert_textnote(content):
    """\\textnote{...} -> list of {define:...} and {comment:...} lines."""
    out = []
    # Pull out \gtab definitions first
    def grab_gtab(m):
        name, i = find_balanced(m.string, m.start(1) - 1)
        return ""
    while True:
        m = re.search(r"\\gtab", content)
        if not m:
            break
        name, i = find_balanced(content, content.index("{", m.end()))
        spec, j = find_balanced(content, content.index("{", i))
        out.append(chord_define_directive(*gtab_to_chord(name, spec)))
        content = content[:m.start()] + content[j:]
    for line in convert_inline(content).split("\n"):
        line = " ".join(line.split())
        if line:
            out.append(f"{{comment: {line}}}")
    return out


def parse_beginsong(line_rest):
    """line_rest starts with '{'. Returns (meta_lines, remainder_of_line)."""
    title, i = find_balanced(line_rest, 0)
    by = sr = None
    rest = line_rest[i:].lstrip()
    if rest.startswith("["):
        opts, j = find_balanced(rest, 0, "[", "]")
        rest = rest[j:]
        # split top-level commas
        parts, depth, cur = [], 0, ""
        for c in opts:
            if c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
            if c == "," and depth == 0:
                parts.append(cur)
                cur = ""
            else:
                cur += c
        parts.append(cur)
        for p in parts:
            if "=" not in p:
                continue
            k, v = p.split("=", 1)
            v = v.strip().strip("{}")
            if k.strip() == "by":
                by = v
            elif k.strip() == "sr":
                sr = v
    meta = [f"{{title: {convert_inline(title).strip()}}}"]
    if by:
        meta.append(f"{{artist: {convert_inline(by).strip()}}}")
        meta.append(f"{{subtitle: {convert_inline(by).strip()}}}")
    if sr:
        meta.append(f"{{subtitle: {convert_inline(sr).strip()}}}")
    return meta, rest


def convert_song_file(path):
    text = path.read_text(encoding="utf-8-sig")

    # Pre-pass: \uv{...} may span lines, convert on the whole text
    while True:
        m = re.search(r"\\uv(?=\{)", text)
        if not m:
            break
        content, after = find_balanced(text, m.end())
        text = text[:m.start()] + "\u201e" + content + "\u201c" + text[after:]

    # Multi-line aware pre-pass: replace \textnote{...} blocks with converted directives
    result = []
    i = 0
    while True:
        m = re.search(r"\\textnote", text[i:])
        if not m:
            result.append(text[i:])
            break
        start = i + m.start()
        result.append(text[i:start])
        content, after = find_balanced(text, text.index("{", start))
        result.append("\n".join(convert_textnote(content)))
        i = after
    text = "".join(result)

    out = []
    song_open = False
    in_tab = False
    tab_brace_depth = 0
    verse_num = 0
    pending = []  # directives seen before \beginsong (e.g. \songcolumns)

    def close_section(kind):
        nonlocal in_tab
        if in_tab:
            out.append("{end_of_tab}")
            in_tab = False
        else:
            out.append(f"{{end_of_{kind}}}")

    for raw in text.splitlines():
        line = raw.rstrip()
        stripped = line.strip()

        # whole-line LaTeX comments -> ChordPro remarks
        if stripped.startswith("%"):
            out.append("# " + stripped.lstrip("% "))
            continue
        # strip trailing comments
        line = re.sub(r"(?<!\\)%.*$", "", line).rstrip()
        stripped = line.strip()
        if not stripped:
            if not in_tab:
                out.append("")
            continue

        if in_tab:
            if stripped.startswith("\\endverse") or stripped.startswith("\\endchorus"):
                out.append("{end_of_tab}")
                in_tab = False
                continue
            if tab_brace_depth > 0:
                # verbatim tab content inside the \texttt{ group
                if stripped.startswith("\\vskip"):
                    out.append("")
                    continue
                content = stripped
                new_depth = tab_brace_depth + content.count("{") - content.count("}")
                if new_depth <= 0 and content.endswith("}"):
                    content = content[:-1]
                tab_brace_depth = new_depth
                out.append(content)
            else:
                # material after the \texttt{ group closed (e.g. a repeat marker)
                out.append(convert_inline(stripped).strip())
            continue

        # directives injected by the textnote pre-pass: pass through untouched
        if re.match(r"\{(define|comment):", stripped):
            out.append(stripped)
            continue

        m = re.match(r"\\beginsong(?=\{)", stripped)
        if m:
            if song_open:
                out.append("{new_song}")  # safety: unterminated song
            elif any(l.startswith("{title:") for l in out):
                out.append("{new_song}")
                out.append("")
            meta, rest = parse_beginsong(stripped[m.end():])
            out.extend(meta)
            out.extend(pending)
            pending.clear()
            song_open = True
            verse_num = 0
            if rest.strip():
                out.append(convert_inline(rest).strip())
            continue

        if stripped.startswith("\\endsong"):
            song_open = False
            continue

        m = re.match(r"\\songcolumns\{(\d+)\}", stripped.lstrip("{"))
        if m:
            (out if song_open else pending).append(f"{{columns: {m.group(1)}}}")
            continue

        m = re.match(r"\\capo\{(\d+)\}", stripped)
        if m:
            out.append(f"{{capo: {m.group(1)}}}")
            continue

        m = re.match(r"\\transpose\{(-?\d+)\}", stripped)
        if m:
            out.append(f"{{transpose: {m.group(1)}}}")
            continue

        m = re.match(r"\\(beginverse|beginchorus)", stripped)
        if m:
            kind = "verse" if m.group(1) == "beginverse" else "chorus"
            rest = stripped[m.end():]
            if kind == "verse":
                verse_num += 1
            if "\\texttt{" in rest:
                pre, tab_start = rest.split("\\texttt{", 1)
                label = f": {verse_num}." if kind == "verse" else ""
                out.append(f"{{start_of_tab{label}}}")
                in_tab = True
                tab_brace_depth = 1 + tab_start.count("{") - tab_start.count("}")
                first = tab_start.strip()
                if tab_brace_depth <= 0 and first.endswith("}"):
                    first = first[:-1]
                if first:
                    out.append(first)
                continue
            if kind == "verse":
                out.append(f"{{start_of_verse: {verse_num}.}}")
            else:
                out.append("{start_of_chorus}")
            rest = convert_inline(rest).strip()
            if rest:
                out.append(rest)
            continue

        if stripped.startswith("\\endverse"):
            close_section("verse")
            continue
        if stripped.startswith("\\endchorus"):
            close_section("chorus")
            continue

        # standalone \gtab lines (outside textnote)
        if stripped.startswith("\\gtab"):
            rest = stripped
            while True:
                m = re.search(r"\\gtab", rest)
                if not m:
                    break
                name, i2 = find_balanced(rest, rest.index("{", m.end()))
                spec, j2 = find_balanced(rest, rest.index("{", i2))
                out.append(chord_define_directive(*gtab_to_chord(name, spec)))
                rest = rest[:m.start()] + rest[j2:]
            continue

        if stripped.startswith("\\vskip"):
            out.append("")
            continue

        for sub in convert_inline(line).split("\n"):
            out.append(sub.rstrip())

    # tidy multiple blank lines
    tidy = []
    for l in out:
        if l == "" and tidy and tidy[-1] == "":
            continue
        tidy.append(l)

    # hoist {define:} lines to the song header so they precede first chord use
    hoisted = []
    song_start = None  # index right after the leading meta block of current song
    for l in tidy:
        if l.startswith("{title:"):
            hoisted.append(l)
            song_start = len(hoisted)
            continue
        if song_start is not None and re.match(
            r"\{(subtitle|artist|capo|transpose|columns):", l
        ):
            hoisted.append(l)
            song_start = len(hoisted)
            continue
        if l.startswith("{define:") and song_start is not None:
            if l not in hoisted[song_start - 1:]:  # skip duplicate defines per song
                hoisted.insert(song_start, l)
                song_start += 1
            continue
        hoisted.append(l)
    return "\n".join(hoisted).strip() + "\n"


# Chord-name variants used in the songs but missing from chords_list.tex
EXTRA_CHORDS = [
    ("Hmi", "2:(224432):"),   # = Hm
    ("F7maj", "X03210"),      # = Fmaj7
    ("E4sus", "022200"),      # = E4/Esus4
]


def convert_chords_list():
    text = (SRC / "chords_list.tex").read_text(encoding="utf-8-sig")
    chords = []
    i = 0
    while True:
        m = re.search(r"^[^%\n]*?\\gtab", text[i:], re.M)
        if not m:
            break
        start = i + m.end()
        name, j = find_balanced(text, text.index("{", start))
        spec, k = find_balanced(text, text.index("{", j))
        name, base, frets, fingers = gtab_to_chord(name, spec)
        entry = {"name": name, "base": base, "frets": frets}
        if fingers:
            entry["fingers"] = fingers
        chords.append(entry)
        i = k
    for name, spec in EXTRA_CHORDS:
        name, base, frets, fingers = gtab_to_chord(name, spec)
        chords.append({"name": name, "base": base, "frets": frets})
    lines = ["// Chord shapes converted from src/chords_list.tex (guitar).", "{", '  "chords": [']
    for n, c in enumerate(chords):
        frets = ", ".join(f'"{f}"' if f == "x" else str(f) for f in c["frets"])
        s = f'    {{ "name": "{c["name"]}", "base": {c["base"]}, "frets": [ {frets} ]'
        if "fingers" in c:
            s += ', "fingers": [ ' + ", ".join(str(f) for f in c["fingers"]) + " ]"
        s += " }" + ("," if n < len(chords) - 1 else "")
        lines.append(s)
    lines += ["  ]", "}"]
    (OUT_CONFIG / "chords.json").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"chords.json: {len(chords)} chord definitions")


def main():
    OUT_SONGS.mkdir(parents=True, exist_ok=True)
    OUT_CONFIG.mkdir(parents=True, exist_ok=True)
    for name in SONG_FILES:
        src = SRC / name
        dst = OUT_SONGS / (Path(name).stem + ".cho")
        converted = convert_song_file(src)
        dst.write_text(converted, encoding="utf-8")
        n_songs = converted.count("{title:")
        print(f"{dst.name}: {n_songs} songs")
    convert_chords_list()


if __name__ == "__main__":
    main()
