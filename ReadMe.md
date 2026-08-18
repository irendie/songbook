# Mr. Tavitel's songbook
Personal songbook, rewritten from LuaLaTeX (`songs` package, see the `main` branch) to [ChordPro](https://www.chordpro.org/).

## Technology stack
* [ChordPro](https://www.chordpro.org/chordpro/chordpro-installation/) 6+ (reference implementation, Artistic License 2.0)
* Python 3 with `reportlab` (cover page generation; also used by the one-off conversion script)

## Project layout
* `songs/*.cho` – the songs in ChordPro format
  * `campfire_songs.cho`, `other_songs.cho` – included in the built songbook
  * `wip_songs.cho`, `removed_songs.cho` – not part of the build
* `config/common.json` – shared layout config (fonts, chorus bar, verse-number labels, alphabetical index)
* `config/A4.json`, `config/A5.json` – paper size and font sizes
* `config/chords.json` – guitar chord shapes (generated from `src/chords_list.tex` on the `main` branch)
* `script/ChordPro_A4_Build.bat`, `script/ChordPro_A5_Build.bat` (+ `*_BuildAndPreview.bat`) – build the PDFs into `release/`
* `script/make_cover.py` – generates the dated cover page embedded via `--front-matter`
* `script/convert_to_chordpro.py` – the LaTeX → ChordPro converter used for the migration (needs the `src/` sources from the `main` branch)

## Building
Install ChordPro, then run `script/ChordPro_A5_Build.bat` or `script/ChordPro_A4_Build.bat`.

## Notes and known differences from the LaTeX version
* Chords use Czech/German names (`H` = B natural, `B` = B♭). The custom shapes in
  `chords.json` make ChordPro recognize them, but automatic transposition
  (`{transpose}`) treats `B`/`H` with English semantics – double-check the one song
  using `{transpose: 5}`.
* The alphabetical song index is sorted by ChordPro's built-in sort, not the Czech
  collation previously provided by `script/sort_index.py` (so e.g. `Č` sorts after `C`
  but not according to full Czech rules).
* The closing thank-you page is not generated.
* The chord atlas ("Přehled akordů") is replaced by per-song chord diagrams
  (`pdf.diagrams.show: bottom`) using the same fingerings.