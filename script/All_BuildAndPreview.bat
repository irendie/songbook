cd ../src/
lualatex songbook.tex
songidx -l cs_CZ mainsongsindex.sxd mainsongsindex.sbx
lualatex songbook.tex
move songbook.pdf ../release/songbook.pdf
lualatex songbook_A4.tex
songidx -l cs_CZ mainsongsindex.sxd mainsongsindex.sbx
lualatex songbook_A4.tex
move songbook_A4.pdf ../release/songbook_A4.pdf
cd ../release/
songbook.pdf
songbook_A4.pdf