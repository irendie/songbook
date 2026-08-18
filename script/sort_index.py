# Importy, díky kterým můžeme řadit dle české abecedy
import locale
import os
import re
import unicodedata

# Nastavení lokalizace pro řazení (názvy locale se liší mezi Windows a Linuxem)
for loc in ("cs_CZ.UTF-8", "cs_CZ", "cs"):
    try:
        locale.setlocale(locale.LC_ALL, loc)
        break
    except locale.Error:
        continue
else:
    raise SystemExit("Česká locale není nainstalována (cs_CZ.UTF-8 / cs_CZ / cs).")

# Cesta k indexu odvozená od umístění tohoto skriptu, aby nezáleželo na pracovním adresáři
index_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src", "mainsongsindex.sbx")

# Deklarace polí
titles = []

# Načítání názvů písní a jejich seřazení
with open(index_path, 'r', encoding='utf-8') as index_file:
    # Zapsání každého řádku, který obsahuje název písně, do pole titles
    for line in index_file:
        if line.startswith("\\idxentry{"):
            #Korekce UTF8 znaku
            sanitizedLine = re.sub(r'\\r\s(\S)', r'\1' + u'\u030a', line) 
            sanitizedLine = re.sub(r'\\v\s(\S)', r'\1' + u'\u030c', sanitizedLine)
            sanitizedLine = unicodedata.normalize('NFC', sanitizedLine)
            titles.append(sanitizedLine)
    # Seřazení pole titles
    titles.sort(key=locale.strxfrm)

# zápis zpět do souboru
with open(index_path, 'w', encoding='utf-8') as new_file:
    # deklarace proměnných, které jsou používány pro zjištění, zda máme začít další blok
    start = True
    last_letter = ""
    # P každý název v už seřazeném seznamu názvů zjistíme, jestli má začít blok od dalšího písmene, pokud ano, začneme další blok. Tak jako tak zapíšeme daný název
    for title in titles:
        # Načtení počátečního písmena písně
        current_letter = title[10].lower()
        # Zjišťování, zda jde o písmeno CH, a případný zápis CH místo C
        if current_letter == "c":
            if title[11].lower() == "h":
                current_letter = "ch"
        # Jsou-li poslední použité a aktuální písmeno rozdílné, začneme nový blok dle nového písmena
        if last_letter != current_letter:
            # Další 2 podmínky zakončují předchozí blok, ale pouze pokud už byl nějaký zapsán
            if not start:
                new_file.write("\\end{idxblock}\n")
            if start:
                start = False
            # Zápis začátku nového bloky
            new_file.write("\\begin{idxblock}{" + str(current_letter.upper()) + "}\n")
            # aktualizována hodnota posledního procesovaného písmene na aktuální hodnotu
            last_letter = current_letter
        # Zápis samotného názvu
        new_file.write(title)
    # Ukončení posledního bloku
    new_file.write("\\end{idxblock}\n")