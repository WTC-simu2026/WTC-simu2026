#!/usr/bin/env python3
"""Compose selected frames around the object labelled as a steel column."""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent
FRAME_ROOT = ROOT.parents[1] / "tmp" / "video" / "dustification_element_check"
OUTPUT = ROOT / "dustification_element_identity_check.png"


def font(size: int, bold: bool = False):
    path = Path("C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf")
    return ImageFont.truetype(str(path), size=size) if path.is_file() else ImageFont.load_default()


frames = [
    ("t_092,0.png", "92.0 s", "nombreux fragments solides visibles"),
    ("t_096,0.png", "96.0 s", "première cible fléchée"),
    ("t_100,0.png", "100.0 s", "petit contour sur bord du nuage"),
    ("t_104,0.png", "104.0 s", "cible apparente beaucoup plus large"),
    ("t_108,0.png", "108.0 s", "forme et poussière superposées"),
    ("t_112,0.png", "112.0 s", "matière impossible à identifier"),
    ("t_116,0.png", "116.0 s", "contraste en forte diminution"),
    ("t_124,0.png", "124.0 s", "trace masquée par le nuage"),
]

cols, rows = 4, 2
tile_w, tile_h = 420, 300
header_h = 90
sheet = Image.new("RGB", (cols * tile_w, header_h + rows * tile_h), (235, 235, 235))
draw = ImageDraw.Draw(sheet)
draw.rectangle((0, 0, sheet.width, header_h), fill=(28, 28, 28))
draw.text((18, 12), "WTC dustification — identité de l'élément fléché", fill="white", font=font(27, True))
draw.text((18, 49), "La légende 'steel column' n'est pas une mesure: la cible se confond avec poussière, fragments et arrière-plan.", fill=(220, 220, 220), font=font(18))

for index, (name, stamp, note) in enumerate(frames):
    row, col = divmod(index, cols)
    x, y = col * tile_w, header_h + row * tile_h
    with Image.open(FRAME_ROOT / name) as source:
        frame = source.convert("RGB")
        frame.thumbnail((tile_w - 12, tile_h - 60), Image.Resampling.LANCZOS)
    px = x + (tile_w - frame.width) // 2
    py = y + 43 + (tile_h - 50 - frame.height) // 2
    sheet.paste(frame, (px, py))
    draw.rectangle((x + 3, y + 3, x + tile_w - 4, y + tile_h - 4), outline=(70, 70, 70), width=2)
    draw.rectangle((x + 4, y + 4, x + tile_w - 4, y + 40), fill=(0, 0, 0))
    draw.text((x + 10, y + 9), f"{stamp} — {note}", fill="white", font=font(16, True))

sheet.save(OUTPUT, format="PNG")
print(OUTPUT)
