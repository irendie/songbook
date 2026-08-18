cd ../
python script/make_cover.py A4
chordpro --config=config/common.json --config=config/A4.json --config=config/chords.json --toc --front-matter=release/cover_A4.pdf --output=release/songbook_A4.pdf songs/campfire_songs.cho songs/other_songs.cho
del release\cover_A4.pdf
cd script
