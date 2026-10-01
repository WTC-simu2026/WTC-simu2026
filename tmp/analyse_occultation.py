from __future__ import annotations

import csv
import hashlib
from pathlib import Path
from statistics import mean, median

import numpy as np
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(r"C:\Users\jeuxpc\Documents\Codex\2026-08-13\referenced-chatgpt-conversation-this-is-an")
SOURCE_DIR = ROOT / "outputs" / "analyse_cgi_plane" / "frames_82_88"
OUT_DIR = ROOT / "outputs" / "analyse_cgi_plane"
FPS = 30000 / 1001
# The first decoded frame after input seeking to 82 s has a relative PTS of
# 0.0152667 s (verified with FFmpeg showinfo).
START_TIME = 82.0152667
SELECTED = [91, 106, 121, 136, 151, 166]


def frame_time(number: int) -> float:
    return START_TIME + (number - 1) / FPS


def load_font(size: int) -> ImageFont.ImageFont:
    candidates = [
        Path(r"C:\Windows\Fonts\arial.ttf"),
        Path(r"C:\Windows\Fonts\segoeui.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size)
    return ImageFont.load_default()


def compute_differences(paths: list[Path]) -> dict[str, float | int]:
    rows: list[dict[str, str | int | float]] = []
    previous: np.ndarray | None = None
    previous_digest: str | None = None
    exact_duplicates = 0
    diffs: list[float] = []

    for index, path in enumerate(paths, start=1):
        rgb = np.asarray(Image.open(path).convert("RGB"), dtype=np.int16)
        digest = hashlib.sha256(rgb.tobytes()).hexdigest()
        if previous is None:
            mad = 0.0
            duplicate = False
        else:
            mad = float(np.abs(rgb - previous).mean())
            duplicate = digest == previous_digest
            diffs.append(mad)
            exact_duplicates += int(duplicate)
        rows.append(
            {
                "frame": index,
                "timestamp_s": f"{frame_time(index):.6f}",
                "mean_abs_rgb_difference_from_previous": f"{mad:.6f}",
                "exact_duplicate_of_previous": int(duplicate),
                "sha256_decoded_rgb": digest,
            }
        )
        previous = rgb
        previous_digest = digest

    csv_path = OUT_DIR / "07_differences_interframes.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    return {
        "frames": len(paths),
        "comparisons": len(diffs),
        "exact_duplicates": exact_duplicates,
        "mad_mean": mean(diffs),
        "mad_median": median(diffs),
        "mad_min": min(diffs),
        "mad_max": max(diffs),
    }


def make_contact_sheet() -> Path:
    title_font = load_font(29)
    label_font = load_font(25)
    note_font = load_font(22)

    crop_box = (245, 155, 755, 465)
    panel_w, panel_h = 765, 570
    margin = 28
    header_h = 105
    footer_h = 92
    sheet = Image.new(
        "RGB",
        (3 * panel_w + 4 * margin, 2 * panel_h + 3 * margin + header_h + footer_h),
        "#11161c",
    )
    draw = ImageDraw.Draw(sheet)
    draw.text(
        (margin, 22),
        "Occultation de l'aile par l'immeuble au premier plan — six images natives",
        fill="white",
        font=title_font,
    )
    draw.text(
        (margin, 61),
        "Trait rouge : ligne de toit. Les horodatages se rapportent au fichier X fourni.",
        fill="#cbd5e1",
        font=note_font,
    )

    for position, number in enumerate(SELECTED):
        row, col = divmod(position, 3)
        x0 = margin + col * (panel_w + margin)
        y0 = header_h + margin + row * (panel_h + margin)

        source = Image.open(SOURCE_DIR / f"frame_{number:04d}.png").convert("RGB")
        crop = source.crop(crop_box).resize((panel_w, 465), Image.Resampling.NEAREST)
        sheet.paste(crop, (x0, y0 + 58))

        timestamp = frame_time(number)
        draw.text(
            (x0, y0 + 12),
            f"Image {number:03d} — t = {timestamp:.3f} s",
            fill="white",
            font=label_font,
        )

        # The roof edge moves by only a few source pixels because of camera shake.
        # Coordinates below are in the enlarged crop and track that edge visually.
        source_y = {91: 184, 106: 184, 121: 179, 136: 176, 151: 180, 166: 176}[number]
        roof_y = y0 + 58 + int(source_y * 1.5)
        roof_x1 = x0 + int(68 * 1.5)
        roof_x2 = x0 + int(339 * 1.5)
        draw.line((roof_x1, roof_y, roof_x2, roof_y), fill="#ff2d2d", width=4)
        draw.ellipse(
            (roof_x2 - 10, roof_y - 10, roof_x2 + 10, roof_y + 10),
            outline="#ffe066",
            width=4,
        )

    footer_y = sheet.height - footer_h + 17
    draw.text(
        (margin, footer_y),
        "Observation : l'aile atteint la ligne de toit puis sa partie gauche est masquée progressivement ;",
        fill="#f8fafc",
        font=note_font,
    )
    draw.text(
        (margin, footer_y + 34),
        "aucune inversion de calques ni apparition de l'aile devant la façade n'est visible dans cette séquence.",
        fill="#f8fafc",
        font=note_font,
    )

    output = OUT_DIR / "06_occultation_native_annotee.png"
    sheet.save(output, optimize=True)
    return output


def main() -> None:
    paths = sorted(SOURCE_DIR.glob("frame_*.png"))
    if len(paths) != 180:
        raise RuntimeError(f"Expected 180 frames, found {len(paths)}")
    stats = compute_differences(paths)
    sheet = make_contact_sheet()
    print(f"sheet={sheet}")
    for key, value in stats.items():
        print(f"{key}={value}")


if __name__ == "__main__":
    main()
