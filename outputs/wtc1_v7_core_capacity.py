"""WTC 1 V7: section-derived core capacity and NIST push-down comparison.

This is a traceable reduced-order calculation, not a finite-element model.
It reads the manually transcribed 47-column schedule around floors 92-101,
computes gross axial-yield envelopes, and places them beside the incremental
force-displacement curve published by NIST for its isolated WTC 1 core model.
"""

from __future__ import annotations

import json
import math
import re
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = Path(__file__).resolve().parent
SCHEDULE_PATH = ROOT / "wtc1_3d_v4" / "data" / "core_sections_impact_zone.json"

KIP_TO_N = 4_448.2216152605
IN_TO_M = 0.0254
KIP_IN_TO_J = KIP_TO_N * IN_TO_M
STEEL_DENSITY_LB_IN3 = 490.0 / 1728.0
E_KSI = 29_000.0
STORY_LENGTH_IN = 144.0

# NIST NCSTAR 1-6D, Table 4-10, global WTC 1 model, Floor 98.
NIST_CORE_LOADS_KIP = {
    "before_impact": 34_029.0,
    "after_impact": 34_429.0,
    "100_min_case_b": 28_478.0,
}

# Approximate visual digitisation of NCSTAR 1-6D Figure 3-130.  The peak
# (4.9 in, 24,002 kip) and terminal displacement (9.4 in) are stated in text;
# the intermediate ordinates are read from the published graph.
NIST_CASE_B_PUSHDOWN = np.array(
    [
        [0.00, 0.0],
        [0.65, 5_000.0],
        [1.05, 7_700.0],
        [2.00, 14_200.0],
        [2.60, 17_000.0],
        [3.00, 18_500.0],
        [3.50, 20_500.0],
        [4.00, 22_000.0],
        [4.50, 23_500.0],
        [4.90, 24_002.0],
        [5.30, 23_600.0],
        [6.00, 22_800.0],
        [7.00, 22_000.0],
        [8.00, 21_100.0],
        [8.60, 20_500.0],
        [8.90, 19_500.0],
        [9.10, 18_000.0],
        [9.25, 16_500.0],
        [9.40, 15_300.0],
    ],
    dtype=float,
)

BAND_LABELS = {
    "101-98": "niveaux 99-100",
    "98-95": "niveaux 96-97",
    "95-92": "niveaux 93-94",
}


def wf_weight_lb_ft(shape: str) -> float:
    match = re.fullmatch(r"(?:12|14)WF([0-9.]+)", shape)
    if not match:
        raise ValueError(f"Designation WF non reconnue: {shape}")
    return float(match.group(1))


def gross_area_in2(segment: dict[str, object]) -> tuple[float, str]:
    if segment["kind"] == "WF":
        weight = wf_weight_lb_ft(str(segment["shape"]))
        area = weight / (STEEL_DENSITY_LB_IN3 * 12.0)
        return area, "nominal_weight_divided_by_steel_density"
    if segment["kind"] == "BOX":
        return float(segment["gross_area_in2"]), str(segment["gross_area_status"])
    raise ValueError(f"Type de section non reconnu: {segment['kind']}")


def calculate() -> dict[str, object]:
    source = json.loads(SCHEDULE_PATH.read_text(encoding="utf-8"))
    per_column: list[dict[str, object]] = []
    aggregates: dict[str, dict[str, object]] = {}

    for band in BAND_LABELS:
        band_rows: list[dict[str, object]] = []
        for column in source["columns"]:
            segment = column["segments"][band]
            area, area_method = gross_area_in2(segment)
            fy = float(segment["fy_ksi"])
            py = area * fy
            stiffness = E_KSI * area / STORY_LENGTH_IN
            row = {
                "column_id": int(column["id"]),
                "band": band,
                "sheet": column["sheet"],
                "pdf_page": int(column["pdf_page"]),
                "kind": segment["kind"],
                "designation": segment.get("shape", f"BOX-{segment.get('column_type')}"),
                "fy_ksi": fy,
                "gross_area_in2": area,
                "gross_area_method": area_method,
                "nominal_axial_yield_kip": py,
                "elastic_axial_stiffness_kip_per_in": stiffness,
            }
            band_rows.append(row)
            per_column.append(row)

        total_area = sum(float(r["gross_area_in2"]) for r in band_rows)
        total_py = sum(float(r["nominal_axial_yield_kip"]) for r in band_rows)
        total_k = sum(float(r["elastic_axial_stiffness_kip_per_in"]) for r in band_rows)
        aggregate = {
            "label": BAND_LABELS[band],
            "column_count": len(band_rows),
            "wf_count": sum(r["kind"] == "WF" for r in band_rows),
            "box_count": sum(r["kind"] == "BOX" for r in band_rows),
            "gross_area_in2": total_area,
            "area_weighted_fy_ksi": total_py / total_area,
            "nominal_axial_yield_kip": total_py,
            "nominal_axial_yield_MN": total_py * KIP_TO_N / 1e6,
            "elastic_axial_stiffness_kip_per_in": total_k,
            "aggregate_nominal_yield_shortening_mm": total_py / total_k * IN_TO_M * 1_000.0,
            "ratio_py_to_core_load_before_impact": total_py / NIST_CORE_LOADS_KIP["before_impact"],
            "ratio_py_to_core_load_100_min": total_py / NIST_CORE_LOADS_KIP["100_min_case_b"],
            "load_fraction_of_py_before_impact": NIST_CORE_LOADS_KIP["before_impact"] / total_py,
            "load_fraction_of_py_100_min": NIST_CORE_LOADS_KIP["100_min_case_b"] / total_py,
        }
        aggregates[band] = aggregate

    x_in = NIST_CASE_B_PUSHDOWN[:, 0]
    f_kip = NIST_CASE_B_PUSHDOWN[:, 1]
    work_j = float(np.trapezoid(f_kip, x_in) * KIP_IN_TO_J)
    pushdown = {
        "source": "NIST NCSTAR 1-6D Figure 3-130 and accompanying text",
        "model_scope": "isolated WTC 1 core, Case B temperature condition, incremental imposed push-down",
        "peak_additional_load_kip": 24_002.0,
        "peak_additional_load_MN": 24_002.0 * KIP_TO_N / 1e6,
        "displacement_at_peak_in": 4.9,
        "displacement_at_peak_mm": 4.9 * IN_TO_M * 1_000.0,
        "terminal_displacement_in": 9.4,
        "terminal_displacement_mm": 9.4 * IN_TO_M * 1_000.0,
        "peak_reported_fraction_of_pre_pushdown_column_force": 0.61,
        "digitised_incremental_work_MJ": work_j / 1e6,
        "digitised_points": [
            {"displacement_in": float(x), "additional_load_kip": float(f)}
            for x, f in NIST_CASE_B_PUSHDOWN
        ],
    }

    return {
        "model": "WTC1_V7_CORE_SECTION_CAPACITY",
        "version": "7.0.0",
        "source_schedule": str(SCHEDULE_PATH),
        "constants": {
            "steel_density_lb_in3": STEEL_DENSITY_LB_IN3,
            "elastic_modulus_ksi": E_KSI,
            "assumed_story_length_in": STORY_LENGTH_IN,
        },
        "nist_global_core_loads_floor_98_kip": NIST_CORE_LOADS_KIP,
        "aggregates": aggregates,
        "nist_isolated_core_pushdown": pushdown,
        "per_column": per_column,
        "limitations": [
            "Gross axial yield is not a buckling or design resistance.",
            "The one-storey elastic length is a reduced-order assumption, not an effective buckling length.",
            "The NIST push-down curve is incremental and belongs to a different isolated-core model; it is not added directly to the global-model loads.",
            "Intermediate push-down ordinates are approximate visual digitisation; the stated peak and terminal displacement are exact report values.",
            "The schedule transcription still requires an independent second reading.",
        ],
    }


def _fonts():
    from PIL import ImageFont

    try:
        regular = ImageFont.truetype(r"C:\Windows\Fonts\arial.ttf", 24)
        small = ImageFont.truetype(r"C:\Windows\Fonts\arial.ttf", 20)
        title = ImageFont.truetype(r"C:\Windows\Fonts\arialbd.ttf", 30)
        panel = ImageFont.truetype(r"C:\Windows\Fonts\arialbd.ttf", 25)
    except OSError:
        regular = small = title = panel = ImageFont.load_default()
    return regular, small, title, panel


def write_plot(result: dict[str, object]) -> Path:
    from PIL import Image, ImageDraw

    regular, small, title_font, panel_font = _fonts()
    width, height = 2700, 1030
    img = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img)
    draw.text((width // 2, 38), "WTC 1 – V7 : noyau, sections réelles et réponse NIST", fill=(20, 20, 20), font=title_font, anchor="mm")

    boxes = [(105, 135, 805, 825), (1000, 135, 1700, 825), (1895, 135, 2595, 825)]
    colors = [(42, 105, 180), (232, 136, 31), (46, 152, 83)]

    def xy(box, x, y, xmin, xmax, ymin, ymax):
        x0, y0, x1, y1 = box
        return (
            int(x0 + (x - xmin) / (xmax - xmin) * (x1 - x0)),
            int(y1 - (y - ymin) / (ymax - ymin) * (y1 - y0)),
        )

    def axes(box, heading, xlabel, ylabel, xmax, ymax, xticks, yticks):
        x0, y0, x1, y1 = box
        draw.rectangle(box, outline=(35, 35, 35), width=2)
        draw.text(((x0 + x1) // 2, y0 - 46), heading, fill=(15, 15, 15), font=panel_font, anchor="mm")
        draw.text(((x0 + x1) // 2, y1 + 62), xlabel, fill=(25, 25, 25), font=regular, anchor="mm")
        draw.text((x0 + 12, y0 + 10), ylabel, fill=(70, 70, 70), font=small, anchor="la")
        for tick in xticks:
            p0 = xy(box, tick, 0, 0, xmax, 0, ymax)
            p1 = xy(box, tick, ymax, 0, xmax, 0, ymax)
            draw.line((p0, p1), fill=(225, 225, 225), width=1)
            draw.text((p0[0], y1 + 10), f"{tick:g}", fill=(40, 40, 40), font=small, anchor="ma")
        for tick in yticks:
            p0 = xy(box, 0, tick, 0, xmax, 0, ymax)
            p1 = xy(box, xmax, tick, 0, xmax, 0, ymax)
            draw.line((p0, p1), fill=(225, 225, 225), width=1)
            draw.text((x0 - 10, p0[1]), f"{tick:g}", fill=(40, 40, 40), font=small, anchor="rm")

    # Panel 1: section-derived gross axial yield compared with global-model core loads.
    box = boxes[0]
    axes(box, "A. Capacité axiale nominale", "Bandes de raccordement", "Force (MN)", 4, 600, [], [0, 150, 300, 450, 600])
    aggregates = result["aggregates"]
    for i, (band, color) in enumerate(zip(BAND_LABELS, colors), start=1):
        val = float(aggregates[band]["nominal_axial_yield_MN"])
        left = xy(box, i - 0.30, 0, 0, 4, 0, 600)[0]
        right = xy(box, i + 0.30, 0, 0, 4, 0, 600)[0]
        top = xy(box, i, val, 0, 4, 0, 600)[1]
        draw.rectangle((left, top, right, box[3]), fill=color)
        draw.text((i * 0 + (left + right) // 2, top - 10), f"{val:.0f}", fill=(20, 20, 20), font=small, anchor="ms")
        draw.text(((left + right) // 2, box[3] + 38), band, fill=(20, 20, 20), font=small, anchor="ma")
    for load_key, dash_color in (("before_impact", (170, 30, 45)), ("100_min_case_b", (100, 70, 140))):
        mn = NIST_CORE_LOADS_KIP[load_key] * KIP_TO_N / 1e6
        y = xy(box, 0, mn, 0, 4, 0, 600)[1]
        for x in range(box[0], box[2], 20):
            draw.line((x, y, min(x + 11, box[2]), y), fill=dash_color, width=4)
    draw.text((box[0] + 15, box[1] + 52), "— 151 MN avant impact\n— 127 MN à 100 min", fill=(95, 35, 75), font=small)

    # Panel 2: elastic pre-yield curves derived from aggregate areas and grades.
    box = boxes[1]
    axes(box, "B. Loi élastique nominale", "Raccourcissement axial (mm)", "Force (MN)", 7, 600, [0, 1, 2, 3, 4, 5, 6, 7], [0, 150, 300, 450, 600])
    for band, color in zip(BAND_LABELS, colors):
        agg = aggregates[band]
        py_kip = float(agg["nominal_axial_yield_kip"])
        k = float(agg["elastic_axial_stiffness_kip_per_in"])
        dy_mm = py_kip / k * IN_TO_M * 1_000.0
        points = [xy(box, 0, 0, 0, 7, 0, 600), xy(box, dy_mm, py_kip * KIP_TO_N / 1e6, 0, 7, 0, 600)]
        draw.line(points, fill=color, width=6)
        px, py = points[-1]
        draw.ellipse((px - 7, py - 7, px + 7, py + 7), fill=color)
        draw.text((px + 10, py - 8), f"{band}: {dy_mm:.1f} mm", fill=color, font=small, anchor="ls")
    draw.text((box[0] + 18, box[3] - 82), "Hypothèse : L = 3,66 m, E = 29 000 ksi\nNe représente pas le flambement.", fill=(70, 70, 70), font=small)

    # Panel 3: official incremental isolated-core push-down curve.
    box = boxes[2]
    axes(box, "C. NIST : push-down du noyau isolé", "Déplacement additionnel (in)", "Charge additionnelle (kip)", 10, 30_000, [0, 2, 4, 6, 8, 10], [0, 5_000, 10_000, 15_000, 20_000, 25_000, 30_000])
    curve = [xy(box, x, f, 0, 10, 0, 30_000) for x, f in NIST_CASE_B_PUSHDOWN]
    fill_poly = [xy(box, 0, 0, 0, 10, 0, 30_000), *curve, xy(box, 9.4, 0, 0, 10, 0, 30_000)]
    draw.polygon(fill_poly, fill=(220, 232, 248))
    draw.line(curve, fill=(38, 73, 142), width=6, joint="curve")
    peak = xy(box, 4.9, 24_002, 0, 10, 0, 30_000)
    draw.ellipse((peak[0] - 8, peak[1] - 8, peak[0] + 8, peak[1] + 8), fill=(190, 45, 50))
    draw.text((peak[0] + 12, peak[1] - 10), "24 002 kip à 4,9 in", fill=(130, 25, 35), font=small, anchor="ls")
    work = float(result["nist_isolated_core_pushdown"]["digitised_incremental_work_MJ"])
    draw.text((box[0] + 18, box[3] - 54), f"Aire numérisée ≈ {work:.1f} MJ", fill=(55, 55, 55), font=small)

    draw.text(
        (width // 2, 975),
        "Les panneaux A–B sont des enveloppes nominales issues des sections. Le panneau C est une courbe NIST incrémentale d’un modèle isolé : les forces ne doivent pas être additionnées directement.",
        fill=(55, 55, 55),
        font=small,
        anchor="mm",
    )
    path = OUT_DIR / "synthese_wtc1_v7_noyau.png"
    img.save(path)
    return path


def write_report(result: dict[str, object]) -> Path:
    agg = result["aggregates"]
    push = result["nist_isolated_core_pushdown"]
    lines = [
        "# WTC 1 — V7 : capacité du noyau issue des sections réelles",
        "",
        "## Résultat principal",
        "",
        "Les 47 nomenclatures du Drawing Book 3 remplacent désormais l’enveloppe abstraite utilisée dans les versions précédentes. La somme des charges axiales de plastification brute vaut **{:.1f} MN**, **{:.1f} MN** et **{:.1f} MN** pour les trois bandes 101–98, 98–95 et 95–92. Au niveau 98, NIST donne pour le noyau **151,4 MN avant impact** et **126,7 MN à 100 min**. La charge représente donc environ 23 à 41 % de la plastification axiale brute suivant la bande et l’instant.".format(
            agg["101-98"]["nominal_axial_yield_MN"],
            agg["98-95"]["nominal_axial_yield_MN"],
            agg["95-92"]["nominal_axial_yield_MN"],
        ),
        "",
        "Ce résultat ne doit pas être lu comme une marge de sécurité réelle : une colonne chauffée, endommagée et fléchie peut perdre sa stabilité bien avant `A × Fy`. Il permet cependant de mesurer la réduction globale que le scénario doit expliquer, au lieu de la cacher dans un coefficient de résistance libre.",
        "",
        "Le point le plus important est interne aux calculs officiels : le push-down NIST du **noyau isolé**, après la condition thermique Case B, atteint encore **24 002 kip (106,7 MN) de charge additionnelle à 4,9 in (124 mm)**, soit 61 % de la force des colonnes avant push-down. Dans ce sous-modèle, le noyau seul garde donc une réserve substantielle. L’amorce globale décrite par NIST dépend nécessairement du couplage noyau–planchers–façades–hat truss et des instabilités géométriques ; elle ne peut pas être reproduite honnêtement par un bloc supérieur posé sur une résistance verticale unique.",
        "",
        "## Capacités calculées",
        "",
        "| Bande | Niveaux représentés | Aire brute (in²) | Fy moyen pondéré (ksi) | A·Fy (kip) | A·Fy (MN) | A·Fy / charge noyau avant impact |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for band in BAND_LABELS:
        a = agg[band]
        lines.append(
            f"| {band} | {a['label']} | {a['gross_area_in2']:.1f} | {a['area_weighted_fy_ksi']:.1f} | {a['nominal_axial_yield_kip']:,.0f} | {a['nominal_axial_yield_MN']:.1f} | {a['ratio_py_to_core_load_before_impact']:.2f} |".replace(",", " ")
        )
    lines += [
        "",
        "## Faits établis utilisés",
        "",
        "- Drawing Book 3 : 47 colonnes identifiées 501–508, 601–608, 701–708, 801–807, 901–908 et 1001–1008 ; sections et nuances transcrites pour les bandes 101–98, 98–95 et 95–92.",
        "- La feuille 3-AB2-9 montre que les types caissons 313–356 et 368–382 utilisent deux plaques n°1 et deux plaques n°2 ; les aires des types 377, 378 et 379 sont donc calculables sans supposer leur multiplicité.",
        "- NCSTAR 1-6D, tableau 4-10 : charges du noyau au niveau 98 de 34 029 kip avant impact, 34 429 kip après impact et 28 478 kip à 100 min pour le modèle global Case B.",
        "- NCSTAR 1-6D, figure 3-130 et texte associé : maximum de push-down additionnel de 24 002 kip à 4,9 in ; calcul arrêté à 9,4 in ; pic égal à 61 % de la force des colonnes avant push-down dans le modèle de noyau isolé.",
        "",
        "## Hypothèses de V7",
        "",
        "- Pour les profilés WF, l’aire brute est déduite du poids nominal avec une masse volumique de 490 lb/ft³. C’est une très bonne reconstruction de l’aire, mais pas une propriété certifiée au centième.",
        "- La pré-pente élastique emploie `E = 29 000 ksi` et une longueur axiale d’un étage de 144 in. Cette longueur ne constitue pas un facteur de flambement effectif.",
        "- `A × Fy` est une borne de plastification axiale brute, pas une résistance de calcul et encore moins une énergie absorbable sur un étage.",
        "- Les points intermédiaires de la figure 3-130 sont numérisés visuellement. Le pic et les déplacements 4,9/9,4 in proviennent directement du texte NIST.",
        "",
        "## Archives locales : statut séparé",
        "",
        "Le seul élément d’archive locale utilisé comme donnée de structure dans V7 est le Drawing Book 3. Aucune affirmation provenant de vidéos, d’articles militants ou de commentaires d’archives n’entre dans les calculs. Le relevé des 47 feuilles reste marqué **transcription manuelle à relire indépendamment**.",
        "",
        "## Contradictions apparentes et incertitudes",
        "",
        "- **Pas une contradiction formelle :** la réserve du noyau isolé et l’effondrement du modèle global peuvent coexister si les planchers, façades et transferts de charge rendent l’ensemble instable. Mais ce couplage devient le mécanisme à démontrer quantitativement.",
        "- **Limite forte :** la courbe officielle ne couvre que 239 mm, environ 6,5 % d’un étage. Son aire numérisée vaut environ **{:.1f} MJ** ; elle ne donne pas l’énergie de destruction du noyau sur 3,66 m.".format(push["digitised_incremental_work_MJ"]),
        "- **Données manquantes :** températures et défauts géométriques colonne par colonne, moments, dommages de l’impact, conditions d’appui, connexions et participation des planchers. Sans eux, une simulation 3D visuellement exacte ne serait pas encore mécaniquement prédictive.",
        "",
        "## Suite V8 proposée",
        "",
        "1. Affecter aux 47 identifiants les charges et états NIST à 100 min, notamment les colonnes 904, 1004, 1005 et 1006 signalées flambées dans le sous-modèle Case B.",
        "2. Ajouter la façade et les transferts par planchers/hat truss afin de tester si le système global perd réellement sa réserve alors que le noyau isolé en conserve.",
        "3. Utiliser Blender pour l’animation et la vérification géométrique, mais confier la rupture à un solveur structurel explicite ; Blender seul ne remplace pas cette étape.",
        "",
        "![Synthèse V7](synthese_wtc1_v7_noyau.png)",
    ]
    path = OUT_DIR / "rapport_wtc1_v7_noyau.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def main() -> None:
    result = calculate()
    json_path = OUT_DIR / "resultats_wtc1_v7_noyau.json"
    json_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    plot_path = write_plot(result)
    report_path = write_report(result)
    print(f"JSON: {json_path}")
    print(f"Figure: {plot_path}")
    print(f"Rapport: {report_path}")
    for band, values in result["aggregates"].items():
        print(
            f"{band}: {values['nominal_axial_yield_kip']:,.0f} kip = "
            f"{values['nominal_axial_yield_MN']:.1f} MN; "
            f"Py/Pcore(before)={values['ratio_py_to_core_load_before_impact']:.2f}"
        )
    print(
        "NIST push-down digitised work: "
        f"{result['nist_isolated_core_pushdown']['digitised_incremental_work_MJ']:.1f} MJ"
    )


if __name__ == "__main__":
    main()
