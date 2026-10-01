"""Render the V8F summary from an existing result JSON without recomputing."""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[2]
V8 = ROOT / "wtc1_simulation_v8"
SOURCE = V8 / "output" / "resultats_wtc1_v8f_transfert_vertical.json"
OUTPUT = V8 / "output" / "synthese_wtc1_v8f_transfert_vertical.png"
TIMES = [20, 40, 60, 80, 100]
GAMMAS = [0.5, 1.0, 2.0, 4.0]
SCHEMES = ["local_four", "local_eight", "global_capacity"]
DAMAGES = ["nist_removed_only", "moderate95_light99", "moderate80_light95"]


def heat_color(value: float) -> tuple[int, int, int]:
    stops = [
        (0.0, (24, 15, 54)),
        (0.35, (111, 31, 95)),
        (0.7, (220, 75, 65)),
        (1.0, (252, 221, 92)),
    ]
    for (a, ca), (b, cb) in zip(stops, stops[1:]):
        if value <= b:
            f = (value - a) / (b - a)
            return tuple(round(ca[k] + f * (cb[k] - ca[k])) for k in range(3))
    return stops[-1][1]


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    name = "C:/Windows/Fonts/seguisb.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf"
    try:
        return ImageFont.truetype(name, size)
    except OSError:
        return ImageFont.load_default()


def main() -> None:
    rows = json.loads(SOURCE.read_text(encoding="utf-8"))["ensemble_rows"]
    baseline = [
        row
        for row in rows
        if row["redistribution"] == "local_four"
        and row["damage_residual_case"] == "nist_removed_only"
        and row["transfer_amplification"] == 1.0
        and row["elastic_modulus_tail"] == "linear_to_5pct_at_1000c"
    ]
    matrix = [
        [
            next(
                row["system_no_equilibrium_fraction"]
                for row in baseline
                if row["time_min"] == time and row["gamma"] == gamma
            )
            for gamma in GAMMAS
        ]
        for time in TIMES
    ]
    sensitivity = [
        row
        for row in rows
        if row["time_min"] == 100
        and row["elastic_modulus_tail"] == "linear_to_5pct_at_1000c"
        and row["gamma"] == 1.0
        and row["transfer_amplification"] == 1.0
    ]
    sens_matrix = [
        [
            next(
                row["system_no_equilibrium_fraction"]
                for row in sensitivity
                if row["redistribution"] == scheme
                and row["damage_residual_case"] == damage
            )
            for damage in DAMAGES
        ]
        for scheme in SCHEMES
    ]

    image = Image.new("RGB", (1900, 920), "white")
    draw = ImageDraw.Draw(image)
    draw.text((950, 42), "WTC 1 - V8F : chemin de charge vertical couple", anchor="ma", font=font(42, True), fill=(20, 25, 35))
    draw.text((950, 102), "200 champs par case - robustesse, pas probabilite physique", anchor="ma", font=font(26), fill=(90, 95, 105))

    left_x, top_y, cw, ch = 160, 245, 130, 90
    draw.text((left_x + 2*cw, 175), "Cas de base", anchor="ma", font=font(30, True), fill=(25, 30, 40))
    for j, gamma in enumerate(GAMMAS):
        draw.text((left_x + j*cw + cw/2, top_y - 32), str(gamma).replace(".", ","), anchor="mm", font=font(23), fill=(35, 40, 50))
    for row_index, time in enumerate(reversed(TIMES)):
        source_index = TIMES.index(time)
        y = top_y + row_index*ch
        draw.text((left_x - 22, y + ch/2), str(time), anchor="rm", font=font(23), fill=(35, 40, 50))
        for j, value in enumerate(matrix[source_index]):
            x = left_x + j*cw
            draw.rectangle((x, y, x+cw, y+ch), fill=heat_color(value), outline="white", width=3)
            draw.text((x+cw/2, y+ch/2), f"{100*value:.0f}%", anchor="mm", font=font(24, True), fill="white" if value < 0.78 else (25, 20, 25))
    draw.text((left_x + 2*cw, top_y + 5*ch + 42), "gamma : diffusion vers localisation", anchor="ma", font=font(23), fill=(45, 50, 60))
    draw.text((12, top_y + 2.5*ch), "Temps", anchor="lm", font=font(23), fill=(45, 50, 60))

    right_x, right_y, rw, rh = 1050, 285, 190, 112
    draw.text((right_x + 1.5*rw, 175), "A 100 min - gamma=1 - amplification 1,00", anchor="ma", font=font(30, True), fill=(25, 30, 40))
    for j, label in enumerate(["100/100", "95/99", "80/95"]):
        draw.text((right_x + j*rw + rw/2, right_y - 34), label, anchor="mm", font=font(23), fill=(35, 40, 50))
    for i, values in enumerate(sens_matrix):
        y = right_y + i*rh
        draw.text((right_x - 25, y + rh/2), ["4 voisines", "8 voisines", "globale"][i], anchor="rm", font=font(23), fill=(35, 40, 50))
        for j, value in enumerate(values):
            x = right_x + j*rw
            draw.rectangle((x, y, x+rw, y+rh), fill=heat_color(value), outline="white", width=3)
            draw.text((x+rw/2, y+rh/2), f"{100*value:.0f}%", anchor="mm", font=font(25, True), fill="white" if value < 0.78 else (25, 20, 25))
    draw.text((right_x + 1.5*rw, right_y + 3*rh + 46), "Capacite residuelle moderate/light (%)", anchor="ma", font=font(23), fill=(45, 50, 60))
    draw.text((950, 840), "Une case sans equilibre indique l'echec du reseau statique impose, pas une preuve d'effondrement global.", anchor="ma", font=font(24), fill=(90, 45, 45))
    image.save(OUTPUT)
    print(OUTPUT)


if __name__ == "__main__":
    main()
