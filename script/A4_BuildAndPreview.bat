cd ../src/
lualatex songbook_A4.tex
songidx -l cs_CZ mainsongsindex.sxd mainsongsindex.sbx
lualatex songbook_A4.tex
move songbook_A4.pdf ../release/songbook_A4.pdf
cd ../release/
songbook_A4.pdf