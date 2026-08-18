cd ../
python script/make_cover.py A5
chordpro --config=config/common.json --config=config/A5.json --config=config/chords.json --toc --front-matter=release/cover_A5.pdf --output=release/songbook_A5.pdf songs/campfire_songs.cho songs/other_songs.cho
del release\cover_A5.pdf
cd script
