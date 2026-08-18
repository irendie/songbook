# Generates the songbook cover page (front matter for ChordPro builds).
# Usage: python make_cover.py A4|A5
import sys
from datetime import date
from pathlib import Path

from reportlab.lib.pagesizes import A4, A5
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas

ROOT = Path(__file__).resolve().parent.parent
FONT = "C:/Windows/Fonts/times.ttf"


def draw_smallcaps(c, text, center_x, y, size, small_ratio=0.75):
    """Emulate LaTeX \\textsc: lowercase letters as smaller capitals."""
    small = size * small_ratio
    parts = [(ch.upper(), size if not ch.islower() else small) for ch in text]
    width = sum(pdfmetrics.stringWidth(ch, "Times", s) for ch, s in parts)
    t = c.beginText(center_x - width / 2, y)
    for ch, s in parts:
        t.setFont("Times", s)
        t.textOut(ch)
    c.drawText(t)


def main():
    fmt = sys.argv[1] if len(sys.argv) > 1 else "A5"
    pagesize = {"A4": A4, "A5": A5}[fmt]
    pdfmetrics.registerFont(TTFont("Times", FONT))
    out = ROOT / "release" / f"cover_{fmt}.pdf"
    c = Canvas(str(out), pagesize=pagesize)
    w, h = pagesize
    title_size = 25 if fmt == "A4" else 20
    sub_size = 12 if fmt == "A5" else 14
    draw_smallcaps(c, "Štěpánův zpěvník", w / 2, h / 2 + title_size, title_size)
    version = f"Verze {date.today():%Y-%m-%d}, {fmt} formát"
    draw_smallcaps(c, version, w / 2, h / 2 - sub_size * 2, sub_size)
    c.showPage()
    c.save()
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
