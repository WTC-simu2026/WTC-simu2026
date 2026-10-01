#!/usr/bin/env python3
"""Compose selected read-only derivatives around the edited core/spire sequence."""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent
FRAME_ROOT = ROOT.parents[1] / "tmp" / "video" / "dustification_physics_check"
OUTPUT = ROOT / "dustification_core_continuity_check.png"


def font(size: int, bold: bool = False):
    path = Path("C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf")
    return ImageFont.truetype(str(path), size=size) if path.is_file() else ImageFont.load_default()


frames = [
    ("t_160,0.png", "160.0 s", "vue A"),
    ("t_171,2.png", "171.2 s", "fin vue A"),
    ("t_171,8.png", "171.8 s", "vue B après coupe"),
    ("t_194,7.png", "194.7 s", "fin vue B"),
    ("t_195,3.png", "195.3 s", "vue C après coupe"),
    ("t_207,5.png", "207.5 s", "fin vue C"),
    ("t_208,2.png", "208.2 s", "vue D après coupe"),
    ("t_220,0.png", "220.0 s", "structure encore visible"),
    ("t_222,0.png", "222.0 s", "partie haute encore visible"),
    ("t_224,0.png", "224.0 s", "silhouette plus courte"),
    ("t_225,0.png", "225.0 s", "mince trace résiduelle"),
    ("t_226,0.png", "226.0 s", "plus distinguable du nuage"),
]

cols, rows = 4, 3
tile_w, tile_h = 420, 300
header_h = 90
sheet = Image.new("RGB", (cols * tile_w, header_h + rows * tile_h), (235, 235, 235))
draw = ImageDraw.Draw(sheet)
draw.rectangle((0, 0, sheet.width, header_h), fill=(28, 28, 28))
draw.text((18, 12), "WTC dustification — continuité de la séquence du noyau", fill="white", font=font(27, True))
draw.text((18, 49), "Les vues A–D sont séparées par des coupes de montage; elles ne forment pas une trajectoire unique.", fill=(220, 220, 220), font=font(19))

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
    draw.text((x + 11, y + 9), f"{stamp} — {note}", fill="white", font=font(18, True))
    if index in (2, 4, 6):
        draw.rectangle((x + 4, y + 42, x + 110, y + 72), fill=(170, 20, 20))
        draw.text((x + 13, y + 46), "COUPE", fill="white", font=font(18, True))

sheet.save(OUTPUT, format="PNG")
print(OUTPUT)
