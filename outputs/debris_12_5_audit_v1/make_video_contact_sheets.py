#!/usr/bin/env python3
"""Build labelled overview sheets from read-only video frame derivatives."""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent


def font(size: int, bold: bool = False):
    path = Path("C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf")
    return ImageFont.truetype(str(path), size=size) if path.is_file() else ImageFont.load_default()


def timestamp(seconds: int) -> str:
    return f"{seconds // 60:02d}:{seconds % 60:02d}"


def make_sheet(source_dir: Path, output: Path, title: str) -> None:
    frames = sorted(source_dir.glob("frame_*.png"))
    cols, rows = 4, 6
    tile_w, tile_h = 470, 300
    sheet = Image.new("RGB", (cols * tile_w, 70 + rows * tile_h), (232, 232, 232))
    draw = ImageDraw.Draw(sheet)
    draw.rectangle((0, 0, sheet.width, 60), fill=(30, 30, 30))
    draw.text((18, 14), title, fill="white", font=font(28, bold=True))
    for index, frame_path in enumerate(frames[: cols * rows]):
        row, col = divmod(index, cols)
        x, y = col * tile_w, 70 + row * tile_h
        with Image.open(frame_path) as source:
            image = source.convert("RGB")
            image.thumbnail((tile_w - 12, tile_h - 42), Image.Resampling.LANCZOS)
        px = x + (tile_w - image.width) // 2
        py = y + 34 + (tile_h - 38 - image.height) // 2
        sheet.paste(image, (px, py))
        draw.rectangle((x + 4, y + 4, x + 96, y + 31), fill=(0, 0, 0))
        draw.text((x + 11, y + 7), timestamp(index * 10), fill="white", font=font(19, bold=True))
        draw.rectangle((x + 3, y + 3, x + tile_w - 4, y + tile_h - 4), outline=(65, 65, 65), width=2)
    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output, format="PNG")


def make_detail_sheets(
    source_dir: Path,
    output_stem: str,
    title: str,
    start_seconds: int,
    step_seconds: int,
) -> None:
    frames = sorted(source_dir.glob("frame_*.png"))
    cols, rows = 4, 6
    per_page = cols * rows
    tile_w, tile_h = 470, 300
    for page_index in range((len(frames) + per_page - 1) // per_page):
        subset = frames[page_index * per_page : (page_index + 1) * per_page]
        sheet = Image.new("RGB", (cols * tile_w, 70 + rows * tile_h), (232, 232, 232))
        draw = ImageDraw.Draw(sheet)
        draw.rectangle((0, 0, sheet.width, 60), fill=(30, 30, 30))
        draw.text(
            (18, 14),
            f"{title} - planche {page_index + 1}",
            fill="white",
            font=font(28, bold=True),
        )
        for local_index, frame_path in enumerate(subset):
            global_index = page_index * per_page + local_index
            row, col = divmod(local_index, cols)
            x, y = col * tile_w, 70 + row * tile_h
            with Image.open(frame_path) as source:
                image = source.convert("RGB")
                image.thumbnail((tile_w - 12, tile_h - 42), Image.Resampling.LANCZOS)
            px = x + (tile_w - image.width) // 2
            py = y + 34 + (tile_h - 38 - image.height) // 2
            sheet.paste(image, (px, py))
            draw.rectangle((x + 4, y + 4, x + 96, y + 31), fill=(0, 0, 0))
            draw.text(
                (x + 11, y + 7),
                timestamp(start_seconds + global_index * step_seconds),
                fill="white",
                font=font(19, bold=True),
            )
            draw.rectangle(
                (x + 3, y + 3, x + tile_w - 4, y + tile_h - 4),
                outline=(65, 65, 65),
                width=2,
            )
        sheet.save(ROOT / f"{output_stem}_{page_index + 1:02d}.png", format="PNG")


make_sheet(
    ROOT / "video_frames/controlled_expert/overview",
    ROOT / "controlled_expert_overview_contact_sheet.png",
    "Controlled Demolition Expert Speaks Out! - apercu toutes les 10 s",
)
make_sheet(
    ROOT / "video_frames/dustification/overview",
    ROOT / "dustification_overview_contact_sheet.png",
    "WTC dustification - apercu toutes les 10 s",
)
make_detail_sheets(
    ROOT / "video_frames/dustification/detail_000_040",
    "dustification_detail_000_040",
    "WTC dustification - detail 00:00 a 00:39, pas 1 s",
    0,
    1,
)
make_detail_sheets(
    ROOT / "video_frames/dustification/detail_080_131",
    "dustification_detail_080_131",
    "WTC dustification - detail 01:20 a 02:10, pas 1 s",
    80,
    1,
)
make_detail_sheets(
    ROOT / "video_frames/dustification/detail_130_227",
    "dustification_detail_130_227",
    "WTC dustification - detail 02:10 a 03:46, pas 1 s",
    130,
    1,
)
make_detail_sheets(
    ROOT / "video_frames/controlled_expert/detail_055_125",
    "controlled_expert_detail_055_125",
    "Controlled expert - images de debris 00:55 a 02:00, pas 5 s",
    55,
    5,
)
make_detail_sheets(
    ROOT / "video_frames/controlled_expert/detail_120_210",
    "controlled_expert_detail_120_210",
    "Controlled expert - comparaison WTC/demolition 02:00 a 03:25, pas 5 s",
    120,
    5,
)
