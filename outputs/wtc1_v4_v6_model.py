"""Reduced-order WTC 1 initiation/propagation sensitivity model (V4-V6).

This is not a finite-element reconstruction.  It keeps traceable, separately
labelled inputs from NIST reports and applies explicit modelling assumptions.
Run with Python 3; it writes a CSV and a PNG next to this file.
"""

from __future__ import annotations

import csv
import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np


OUT_DIR = Path(__file__).resolve().parent
G = 9.80665  # m/s2
STORY_H = 3.66  # m, nominal tower storey height used in V1-V3
KIP_TO_N = 4_448.2216152605
KIP_IN_TO_J = 112.98482902762

# NIST NCSTAR 1-6D, Table 4-10, WTC 1 Case B, total gravity load at floor 98.
TOP_LOAD_KIP = 73_144.0
TOP_WEIGHT_N = TOP_LOAD_KIP * KIP_TO_N
TOP_MASS_KG = TOP_WEIGHT_N / G
PRIOR_LITERATURE_MASS_KG = 54.06e6  # V2-V3 comparison value, not the V4 baseline

# NIST Table 4-10 totals at floors 96 and 98 differ by 6,752 kip.
# Dividing by two gives a reduced-order mean storey mass for accretion.
STORY_WEIGHT_KIP = (79_896.0 - 73_144.0) / 2.0
STORY_MASS_KG = STORY_WEIGHT_KIP * KIP_TO_N / G


def perimeter_area_and_zweak(t1: float, l2: float, l3: float) -> tuple[float, float]:
    """Approximate area and weak-axis plastic modulus of a NIST box column.

    Dimensions are inches.  NIST Table 6-1a supplies two 13.5-in side plates
    of thickness t1 and two 1/4-in face plates of lengths l2 and l3.  Zweak is
    a rectangular-plate assembly approximation; it is intentionally exposed
    as a model input rather than presented as an as-built tabulated property.
    """
    area = 2.0 * 13.5 * t1 + 0.25 * l2 + 0.25 * l3
    # Side-plate first moments plus face-plate areas at a 6.75-in lever arm.
    zweak = 2.0 * (t1 * 13.5**2 / 4.0) + 0.25 * (l2 + l3) * 6.75
    return area, zweak


BOX_TYPES = {
    120: perimeter_area_and_zweak(0.2500, 13.500, 15.750),
    121: perimeter_area_and_zweak(0.3125, 13.375, 15.750),
    122: perimeter_area_and_zweak(0.3750, 13.250, 15.750),
    123: perimeter_area_and_zweak(0.4375, 13.125, 15.750),
    124: perimeter_area_and_zweak(0.5000, 13.000, 15.750),
    125: perimeter_area_and_zweak(0.5625, 12.875, 15.750),
}

# NIST NCSTAR 1-3A, Table 2-3: specified grades of WTC 1 perimeter
# column pieces intersecting floors 92-100.  These counts define a grade
# distribution; they are NOT 978 simultaneous columns at one cross-section.
PERIMETER_GRADE_COUNTS = {
    45: 0,
    46: 1,
    50: 26,
    55: 225,
    60: 246,
    65: 196,
    70: 122,
    75: 83,
    80: 40,
    85: 16,
    90: 7,
    100: 16,
}
PERIMETER_FY_WEIGHTED_KSI = sum(
    fy * count for fy, count in PERIMETER_GRADE_COUNTS.items()
) / sum(PERIMETER_GRADE_COUNTS.values())


# Approximate digitisation of NIST NCSTAR 1-6C Figure 6-14, after peak load.
# x is additional axial shortening after the peak, in inches; q=P/P_peak.
# The plot only supports about 40 mm of post-peak shortening, not a full storey.
POSTBUCKLING_CURVES = {
    "rapide_1_etage_RT": (
        np.array([0.00, 0.15, 0.35, 0.65, 1.15, 1.55]),
        np.array([1.00, 0.80, 0.58, 0.40, 0.26, 0.19]),
    ),
    "intermediaire_2_etages": (
        np.array([0.00, 0.15, 0.35, 0.65, 1.15, 1.55]),
        np.array([1.00, 0.90, 0.72, 0.55, 0.38, 0.28]),
    ),
    "ductile_3_etages_400C": (
        np.array([0.00, 0.15, 0.35, 0.65, 1.15, 1.55]),
        np.array([1.00, 0.92, 0.76, 0.66, 0.49, 0.35]),
    ),
}


def interp_q(curve_name: str, x_m: np.ndarray) -> np.ndarray:
    xin, q = POSTBUCKLING_CURVES[curve_name]
    return np.interp(x_m / 0.0254, xin, q)


def v4_initiation(curve_name: str, load_fraction: float) -> dict[str, float | str]:
    """Integrate motion over 1-40 mm beyond a column-system peak.

    load_fraction is the fraction of the total gravity load whose load path
    enters the selected post-buckling curve.  Remaining paths retain their
    pre-instability load.  Thus R/W=(1-lambda)+lambda*q(x).
    """
    x = np.linspace(0.001, 0.03937, 4_000)  # 1 mm perturbation to 1.55 in
    q = interp_q(curve_name, x)
    r_over_w = (1.0 - load_fraction) + load_fraction * q
    deficit = np.maximum(0.0, 1.0 - r_over_w)
    dx = np.diff(x)
    work_per_weight = np.zeros_like(x)
    work_per_weight[1:] = np.cumsum(0.5 * (deficit[:-1] + deficit[1:]) * dx)
    velocity = np.sqrt(2.0 * G * work_per_weight)
    # From rest at 1 mm; use average segment velocity after the first segment.
    dt = np.divide(
        dx,
        0.5 * (velocity[:-1] + velocity[1:]),
        out=np.zeros_like(dx),
        where=(velocity[:-1] + velocity[1:]) > 1e-12,
    )
    return {
        "version": "V4",
        "scenario": f"{curve_name}; lambda={load_fraction:.2f}",
        "x_final_mm": x[-1] * 1_000.0,
        "r_sur_w_final": r_over_w[-1],
        "v_final_m_s": velocity[-1],
        "temps_s_depuis_1mm": float(dt.sum()),
        "travail_deficit_MJ": work_per_weight[-1] * TOP_WEIGHT_N / 1e6,
    }


@dataclass(frozen=True)
class FoldingScenario:
    name: str
    perimeter_z_in3: float
    perimeter_fy_ksi: float
    core_z_in3: float
    core_fy_ksi: float
    temperature_factor: float
    plastic_rotation_sum_rad: float
    engagement_fraction: float


FOLDING_SCENARIOS = (
    FoldingScenario(
        "fragilise",
        BOX_TYPES[120][1],
        55.0,
        60.0,  # W12x92 weak-axis lower envelope
        36.0,
        0.55,
        2.0 * math.pi,
        0.35,
    ),
    FoldingScenario(
        "central",
        float(np.mean([v[1] for v in BOX_TYPES.values()])),
        PERIMETER_FY_WEIGHTED_KSI,
        75.0,  # mixed weak-axis core envelope
        40.0,
        0.75,
        2.0 * math.pi,
        0.65,
    ),
    FoldingScenario(
        "favorable_arret",
        BOX_TYPES[125][1],
        75.0,
        140.0,  # W14x184 / strong weak-axis upper envelope
        50.0,
        1.00,
        4.0 * math.pi,
        1.00,
    ),
)


def plastic_folding_energy(s: FoldingScenario) -> dict[str, float | str]:
    """Column-only plastic mechanism envelope for one storey.

    Work = sum(Mp * total plastic rotation).  There are 236 perimeter and 47
    core columns.  Temperature and engagement factors are explicit scenarios.
    Connections, slabs, pulverisation and ejection are intentionally omitted.
    """
    common = s.temperature_factor * s.plastic_rotation_sum_rad * s.engagement_fraction
    perimeter_j = (
        236.0
        * s.perimeter_fy_ksi
        * s.perimeter_z_in3
        * KIP_IN_TO_J
        * common
    )
    core_j = 47.0 * s.core_fy_ksi * s.core_z_in3 * KIP_IN_TO_J * common
    total_j = perimeter_j + core_j
    gravity_j = TOP_WEIGHT_N * STORY_H
    prior_gravity_j = PRIOR_LITERATURE_MASS_KG * G * STORY_H
    return {
        "version": "V5",
        "scenario": s.name,
        "energie_facade_GJ": perimeter_j / 1e9,
        "energie_noyau_GJ": core_j / 1e9,
        "energie_totale_GJ": total_j / 1e9,
        "Mgh_GJ": gravity_j / 1e9,
        "alpha_U_sur_Mgh": total_j / gravity_j,
        "alpha_si_masse_54_06Mt": total_j / prior_gravity_j,
    }


def v6_propagation(
    scenario: FoldingScenario,
    damaged_factor: float,
    capture_fraction: float,
    n_damaged: int = 5,
    max_stories: int = 98,
) -> tuple[dict[str, float | str], list[tuple[int, float]]]:
    """Discrete crush-down energy/momentum sensitivity.

    Column work below the source zone is scaled in proportion to accumulated
    supported mass.  The first n_damaged storeys receive a damage multiplier.
    A perfectly inelastic capture of a fraction of each storey follows each
    descent.  This is a reduced-order assumption, not a NIST propagation model.
    """
    v5 = plastic_folding_energy(scenario)
    base_u_j = float(v5["energie_totale_GJ"]) * 1e9
    mass = TOP_MASS_KG
    kinetic_j = 0.0
    history: list[tuple[int, float]] = []
    arrested_at: int | None = None

    for story in range(1, max_stories + 1):
        scale = mass / TOP_MASS_KG
        damage = damaged_factor if story <= n_damaged else 1.0
        resistance_j = base_u_j * scale * damage
        available_j = kinetic_j + mass * G * STORY_H - resistance_j
        if available_j <= 0.0:
            arrested_at = story
            history.append((story, 0.0))
            break
        v_before_capture = math.sqrt(2.0 * available_j / mass)
        captured_mass = capture_fraction * STORY_MASS_KG
        v_after_capture = mass / (mass + captured_mass) * v_before_capture
        mass += captured_mass
        kinetic_j = 0.5 * mass * v_after_capture**2
        history.append((story, v_after_capture))

    result = {
        "version": "V6",
        "scenario": scenario.name,
        "facteur_endommage": damaged_factor,
        "fraction_accretee": capture_fraction,
        "etage_arret": arrested_at if arrested_at is not None else "aucun_dans_domaine",
        "etages_franchis": (arrested_at - 1) if arrested_at is not None else len(history),
        "v_max_m_s": max(v for _, v in history),
        "v_finale_m_s": history[-1][1],
    }
    return result, history


def write_csv(rows: list[dict[str, object]]) -> None:
    path = OUT_DIR / "resultats_wtc1_v4_v6.csv"
    fields: list[str] = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_plot(
    v4_rows: list[dict[str, object]],
    histories: dict[str, list[tuple[int, float]]],
) -> None:
    from PIL import Image, ImageDraw, ImageFont

    width, height = 2200, 850
    img = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype(r"C:\Windows\Fonts\arial.ttf", 26)
        small = ImageFont.truetype(r"C:\Windows\Fonts\arial.ttf", 22)
        title_font = ImageFont.truetype(r"C:\Windows\Fonts\arialbd.ttf", 31)
    except OSError:
        font = small = title_font = ImageFont.load_default()

    panels = ((110, 90, 1030, 720), (1190, 90, 2110, 720))
    colors = ((31, 119, 180), (255, 127, 14), (44, 160, 44))

    def axes_box(box: tuple[int, int, int, int], title: str, xlabel: str, ylabel: str) -> None:
        x0, y0, x1, y1 = box
        draw.rectangle(box, outline=(30, 30, 30), width=2)
        draw.text(((x0 + x1) // 2, 35), title, fill="black", font=title_font, anchor="mm")
        draw.text(((x0 + x1) // 2, y1 + 58), xlabel, fill="black", font=font, anchor="mm")
        draw.text((x0 - 80, (y0 + y1) // 2), ylabel, fill="black", font=small, anchor="mm")

    def xy_map(
        box: tuple[int, int, int, int],
        xval: float,
        yval: float,
        xmin: float,
        xmax: float,
        ymin: float,
        ymax: float,
    ) -> tuple[int, int]:
        x0, y0, x1, y1 = box
        px = x0 + (xval - xmin) / (xmax - xmin) * (x1 - x0)
        py = y1 - (yval - ymin) / (ymax - ymin) * (y1 - y0)
        return int(px), int(py)

    # Left panel: system resistance ratio for the middle NIST curve.
    box = panels[0]
    axes_box(box, "V4 - courbe NIST ramenee au systeme", "Raccourcissement post-pic (mm)", "R/W")
    xmin, xmax, ymin, ymax = 0.0, 40.0, 0.55, 1.02
    for tick in np.linspace(0, 40, 5):
        p0 = xy_map(box, tick, ymin, xmin, xmax, ymin, ymax)
        p1 = xy_map(box, tick, ymax, xmin, xmax, ymin, ymax)
        draw.line((p0, p1), fill=(225, 225, 225), width=1)
        draw.text((p0[0], box[3] + 10), f"{tick:.0f}", fill="black", font=small, anchor="ma")
    for tick in (0.6, 0.7, 0.8, 0.9, 1.0):
        p0 = xy_map(box, xmin, tick, xmin, xmax, ymin, ymax)
        p1 = xy_map(box, xmax, tick, xmin, xmax, ymin, ymax)
        draw.line((p0, p1), fill=(225, 225, 225), width=1)
        draw.text((box[0] - 10, p0[1]), f"{tick:.1f}", fill="black", font=small, anchor="rm")
    x = np.linspace(0.0, 0.03937, 500)
    q = interp_q("intermediaire_2_etages", x)
    for color, lam in zip(colors, (0.13, 0.30, 0.52)):
        values = (1 - lam) + lam * q
        points = [xy_map(box, xm * 1000, y, xmin, xmax, ymin, ymax) for xm, y in zip(x, values)]
        draw.line(points, fill=color, width=5)
    for i, (color, lam) in enumerate(zip(colors, (0.13, 0.30, 0.52))):
        y = 120 + i * 38
        draw.line((735, y, 785, y), fill=color, width=5)
        draw.text((800, y), f"lambda={lam:.2f}", fill="black", font=small, anchor="lm")

    # Right panel: V6 velocities.  A zero at the last point marks arrest.
    box = panels[1]
    axes_box(box, "V6 - sensibilite de propagation", "Etages franchis / etage teste", "Vitesse (m/s)")
    max_story = max(max(p[0] for p in h) for h in histories.values())
    max_v = max(max(p[1] for p in h) for h in histories.values())
    xmax2 = max(10.0, float(max_story))
    ymax2 = max(5.0, math.ceil(max_v / 5.0) * 5.0)
    for tick in np.linspace(0, xmax2, 6):
        p0 = xy_map(box, tick, 0, 0, xmax2, 0, ymax2)
        p1 = xy_map(box, tick, ymax2, 0, xmax2, 0, ymax2)
        draw.line((p0, p1), fill=(225, 225, 225), width=1)
        draw.text((p0[0], box[3] + 10), f"{tick:.0f}", fill="black", font=small, anchor="ma")
    for tick in np.linspace(0, ymax2, 6):
        p0 = xy_map(box, 0, tick, 0, xmax2, 0, ymax2)
        p1 = xy_map(box, xmax2, tick, 0, xmax2, 0, ymax2)
        draw.line((p0, p1), fill=(225, 225, 225), width=1)
        draw.text((box[0] - 10, p0[1]), f"{tick:.0f}", fill="black", font=small, anchor="rm")
    for i, ((name, history), color) in enumerate(zip(histories.items(), colors)):
        points = [xy_map(box, n, v, 0, xmax2, 0, ymax2) for n, v in history]
        if len(points) > 1:
            draw.line(points, fill=color, width=5)
        for px, py in points if len(points) < 15 else points[-1:]:
            draw.ellipse((px - 5, py - 5, px + 5, py + 5), fill=color)
        y = 120 + i * 38
        draw.line((1780, y, 1830, y), fill=color, width=5)
        draw.text((1845, y), name, fill="black", font=small, anchor="lm")

    img.save(OUT_DIR / "synthese_wtc1_v4_v6.png")


def main() -> None:
    v4_rows = [
        v4_initiation(curve, lam)
        for curve in POSTBUCKLING_CURVES
        for lam in (0.13, 0.30, 0.52)
    ]
    v5_rows = [plastic_folding_energy(s) for s in FOLDING_SCENARIOS]

    v6_parameters = {
        "fragilise": (0.50, 0.70),
        "central": (0.50, 0.80),
        "favorable_arret": (0.25, 1.00),
    }
    v6_rows: list[dict[str, object]] = []
    histories: dict[str, list[tuple[int, float]]] = {}
    for scenario in FOLDING_SCENARIOS:
        damage, capture = v6_parameters[scenario.name]
        result, history = v6_propagation(scenario, damage, capture)
        v6_rows.append(result)
        histories[scenario.name] = history

    write_csv([*v4_rows, *v5_rows, *v6_rows])
    write_plot(v4_rows, histories)

    print(f"Top load: {TOP_LOAD_KIP:,.0f} kip = {TOP_WEIGHT_N / 1e6:.2f} MN")
    print(f"Top mass equivalent: {TOP_MASS_KG / 1e6:.2f} million kg")
    print(f"Mgh per storey: {TOP_WEIGHT_N * STORY_H / 1e9:.3f} GJ")
    print(f"Weighted perimeter grade: {PERIMETER_FY_WEIGHTED_KSI:.2f} ksi")
    print("Box type area/Zweak (in2/in3):")
    for typ, (area, z) in BOX_TYPES.items():
        print(f"  {typ}: {area:.3f} / {z:.2f}")
    print("\nV4:")
    for row in v4_rows:
        print(row)
    print("\nV5:")
    for row in v5_rows:
        print(row)
    print("\nV6:")
    for row in v6_rows:
        print(row)


if __name__ == "__main__":
    main()
