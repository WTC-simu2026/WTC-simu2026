"""Create the compact scientific summary figure for IMPACT-I02A with Pillow."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "wtc1_simulation_v8/output/impact_i02a_structured_wing"
FIGURE = OUTPUT / "synthese_impact_i02a.png"
FONT_REGULAR = Path("C:/Windows/Fonts/arial.ttf")
FONT_BOLD = Path("C:/Windows/Fonts/arialbd.ttf")


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def font(size: int, bold: bool = False):
    return ImageFont.truetype(str(FONT_BOLD if bold else FONT_REGULAR), size)


def ramp(value: float) -> tuple[int, int, int]:
    stops = [(0.0, (20, 20, 45)), (0.25, (88, 24, 96)), (0.5, (187, 55, 84)), (0.75, (249, 142, 8)), (1.0, (252, 255, 164))]
    value = min(max(value, 0.0), 1.0)
    for index in range(len(stops) - 1):
        a, ca = stops[index]
        b, cb = stops[index + 1]
        if value <= b:
            t = (value - a) / (b - a)
            return tuple(round(ca[channel] + t * (cb[channel] - ca[channel])) for channel in range(3))
    return stops[-1][1]


def draw_wrapped(draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: str, width_chars: int, used_font, fill, line_gap: int = 4):
    words = text.split()
    lines = []
    current = ""
    for word in words:
        trial = word if not current else current + " " + word
        if len(trial) <= width_chars:
            current = trial
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    x, y = xy
    for line in lines:
        draw.text((x, y), line, font=used_font, fill=fill)
        y += used_font.size + line_gap
    return y


def line_plot(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], series: list[tuple[list[float], list[float], tuple[int, int, int], int]], xlim, ylim, title: str, ylabel: str):
    left, top, right, bottom = box
    draw.rectangle(box, fill="white", outline="#cbd5e1", width=1)
    margin_left, margin_bottom, margin_top, margin_right = 72, 52, 48, 20
    x0, y0 = left + margin_left, bottom - margin_bottom
    x1, y1 = right - margin_right, top + margin_top
    for fraction in np.linspace(0, 1, 5):
        py = round(y0 - fraction * (y0 - y1))
        draw.line((x0, py, x1, py), fill="#e5e7eb", width=1)
        value = ylim[0] + fraction * (ylim[1] - ylim[0])
        draw.text((left + 4, py - 8), f"{value:.2g}", font=font(15), fill="#475569")
    draw.line((x0, y0, x1, y0), fill="#111827", width=2)
    draw.line((x0, y0, x0, y1), fill="#111827", width=2)
    for fraction in np.linspace(0, 1, 5):
        px = round(x0 + fraction * (x1 - x0))
        value = xlim[0] + fraction * (xlim[1] - xlim[0])
        draw.text((px - 14, y0 + 8), f"{value:.2g}", font=font(15), fill="#475569")
    for xs, ys, color, width in series:
        points = []
        for x, y in zip(xs, ys):
            px = x0 + (x - xlim[0]) / (xlim[1] - xlim[0]) * (x1 - x0)
            py = y0 - (y - ylim[0]) / (ylim[1] - ylim[0]) * (y0 - y1)
            points.append((round(px), round(py)))
        draw.line(points, fill=color, width=width, joint="curve")
    draw.text((left + 10, top + 9), title, font=font(20, True), fill="#0f172a")
    draw.text((left + 4, top + 32), ylabel, font=font(14), fill="#334155")


def main() -> None:
    nominal = load_json(OUTPUT / "CONTACT_M050_R1/history_si.json")
    half_dt = load_json(OUTPUT / "CONTACT_DT045_R1/history_si.json")
    audit = load_json(OUTPUT / "campaign_audit.json")
    npz = np.load(OUTPUT / "CONTACT_M050_R1/computed_frames.npz")
    points0 = npz["points_mm"][0]
    points1 = npz["points_mm"][-1]
    quads = npz["quads"]
    parts = npz["parts"]
    epsp = npz["epsp"][-1]
    centers0 = points0[quads].mean(axis=1)
    centers1 = points1[quads].mean(axis=1)

    image = Image.new("RGB", (1800, 1120), "#f8fafc")
    draw = ImageDraw.Draw(image)
    draw.text((45, 25), "WTC1 — IMPACT-I02A : première section d’aile structurée, non érosive", font=font(34, True), fill="#0f172a")
    comparison = audit["comparison"]
    draw.text(
        (45, 72),
        f"m = {comparison['structured_mass_kg']:.3f} kg  ·  v0 = 198.03072 m/s  ·  J(1,195 ms) = {comparison['structured_impulse_Ns']:.1f} N·s  ·  écart demi-pas = {100*comparison['half_dt_impulse_difference_fraction']:.3f} %",
        font=font(21),
        fill="#334155",
    )

    left_box = (45, 115, 935, 950)
    draw.rectangle(left_box, fill="white", outline="#cbd5e1")
    draw.text((65, 132), "Projection x-z du maillage calculé à 1,195 ms", font=font(24, True), fill="#0f172a")
    plot_box = (110, 190, 875, 880)
    xlim, zlim = (-1750.0, 1750.0), (-450.0, 2100.0)

    def pixel(x, z):
        px = plot_box[0] + (x - xlim[0]) / (xlim[1] - xlim[0]) * (plot_box[2] - plot_box[0])
        py = plot_box[3] - (z - zlim[0]) / (zlim[1] - zlim[0]) * (plot_box[3] - plot_box[1])
        return round(px), round(py)

    for fraction in np.linspace(0, 1, 6):
        px = round(plot_box[0] + fraction * (plot_box[2] - plot_box[0]))
        py = round(plot_box[1] + fraction * (plot_box[3] - plot_box[1]))
        draw.line((px, plot_box[1], px, plot_box[3]), fill="#eef2f7")
        draw.line((plot_box[0], py, plot_box[2], py), fill="#eef2f7")
    draw.rectangle(plot_box, outline="#64748b", width=2)
    pz0 = pixel(0, 0)[1]
    draw.line((plot_box[0], pz0, plot_box[2], pz0), fill="#111827", width=2)
    facade = parts <= 2
    wing = parts >= 3
    for x, z in centers0[wing][:, (0, 2)]:
        px, py = pixel(x, z)
        draw.point((px, py), fill="#bfdbfe")
    for x, z in centers1[facade][:, (0, 2)]:
        px, py = pixel(x, z)
        draw.point((px, py), fill="#64748b")
    for (x, z), strain in zip(centers1[wing][:, (0, 2)], epsp[wing]):
        px, py = pixel(x, z)
        color = ramp(float(min(strain, 0.5) / 0.5))
        draw.ellipse((px - 1, py - 1, px + 1, py + 1), fill=color)
    draw.text((120, 895), "bleu pâle : position initiale  ·  gris : façade  ·  couleur : εp plafonné à 0,5", font=font(17), fill="#334155")
    draw.text((50, 505), "z (mm)", font=font(16), fill="#334155")
    draw.text((450, 925), "envergure locale x (mm)", font=font(16), fill="#334155")
    draw.line((815, 300, 815, 420), fill="#111827", width=3)
    draw.polygon([(807, 412), (823, 412), (815, 432)], fill="#111827")
    draw.text((745, 270), "sens impact", font=font(16), fill="#111827")

    t_nom = [row["t_ms"] for row in nominal]
    t_half = [row["t_ms"] for row in half_dt]
    line_plot(
        draw,
        (970, 115, 1755, 500),
        [
            (t_nom, [abs(row["contact_impulse_Ns"]) for row in nominal], (29, 78, 216), 4),
            (t_nom, [abs(row["wing_delta_pz_Ns"]) for row in nominal], (14, 165, 233), 2),
            (t_half, [abs(row["contact_impulse_Ns"]) for row in half_dt], (220, 38, 38), 2),
        ],
        (0.0, 1.2),
        (0.0, 4600.0),
        "Contact ↔ quantité de mouvement",
        "impulsion (N·s)",
    )
    draw.text((1090, 474), "bleu : contact  ·  cyan : Δp aile  ·  rouge : demi-pas", font=font(14), fill="#334155")

    initial_ke = nominal[0]["global_ke_J"]
    line_plot(
        draw,
        (970, 530, 1755, 915),
        [
            (t_nom, [(initial_ke - row["global_ke_J"]) / 1e6 for row in nominal], (29, 78, 216), 4),
            (t_nom, [row["global_ie_J"] / 1e6 for row in nominal], (220, 38, 38), 3),
            (t_nom, [row["wing_ie_J"] / 1e6 for row in nominal], (234, 88, 12), 2),
            (t_nom, [row["part_hourglass_total_J"] / 1e6 for row in nominal], (124, 58, 237), 2),
        ],
        (0.0, 1.2),
        (0.0, 0.65),
        "Bilan énergétique du témoin",
        "énergie (MJ)",
    )
    draw.text((1035, 889), "bleu : perte Ec  ·  rouge : Ei totale  ·  orange : Ei aile  ·  violet : sablier", font=font(14), fill="#334155")

    max_epsp = audit["max_effective_plastic_strain_by_part_nominal"]
    warning = (
        "Rupture et rivets désactivés. Pics εp peau / longeron / nervure = "
        f"{max_epsp['3']:.2f} / {max_epsp['4']:.2f} / {max_epsp['5']:.2f}. "
        "L’état tardif est hors domaine constitutif : ce résultat ne prouve ni une aile intacte, ni une rupture réelle, ni le scénario global."
    )
    draw.rounded_rectangle((45, 975, 1755, 1085), radius=14, fill="#fff1f2", outline="#f43f5e", width=2)
    draw_wrapped(draw, (70, 993), warning, 170, font(20, True), "#991b1b", 5)
    image.save(FIGURE)
    metadata = {
        "file": str(FIGURE.relative_to(ROOT)).replace("\\", "/"),
        "sha256": sha256(FIGURE),
        "bytes": FIGURE.stat().st_size,
        "source_npz_sha256": sha256(OUTPUT / "CONTACT_M050_R1/computed_frames.npz"),
        "scope": "Scientific diagnostic figure from saved solver states; not a reconstruction of the real event.",
    }
    (OUTPUT / "render_metadata.json").write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(metadata, ensure_ascii=False))


if __name__ == "__main__":
    main()
