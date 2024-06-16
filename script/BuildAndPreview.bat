cd ../src/
lualatex songbook.tex
songidx -l cs_CZ mainsongsindex.sxd mainsongsindex.sbx
lualatex songbook.tex
move songbook.pdf ../release/songbook.pdf
cd ../release/
songbook.pdf