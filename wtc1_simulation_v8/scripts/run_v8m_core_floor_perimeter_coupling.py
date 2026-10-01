"""WTC 1 V8M - cold core/floor/perimeter compatibility envelope.

V8M does not assign the published seat capacities directly as vertical springs.
It uses geometric compatibility: a horizontal composite floor path develops
axial tension when the core and perimeter have different vertical movements;
only the vertical component of that tension transfers core load to the wall.
The published horizontal and vertical seat limits cap the physical cases.

This is a reduced-order force-displacement audit, not an ANSYS reproduction.
"""

from __future__ import annotations

import json
import math
import time
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[2]
V8 = ROOT / "wtc1_simulation_v8"
CONFIG = V8 / "data" / "v8m_core_floor_perimeter_coupling.json"
V8L_RESULT = V8 / "output" / "resultats_wtc1_v8l_multietages_froid.json"
OUT_JSON = V8 / "output" / "resultats_wtc1_v8m_couplage_perimetre_froid.json"
OUT_REPORT = V8 / "output" / "rapport_wtc1_v8m_couplage_perimetre_froid.md"
OUT_PNG = V8 / "output" / "synthese_wtc1_v8m_couplage_perimetre_froid.png"

FACE_SPAN_KEY = {
    "north": "long_span_north_south_in",
    "south": "long_span_north_south_in",
    "east": "short_span_east_west_in",
    "west": "short_span_east_west_in",
}


def load_inputs() -> tuple[dict[str, object], dict[str, object]]:
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    v8l = json.loads(V8L_RESULT.read_text(encoding="utf-8"))
    expected = float(config["inherited_v8l_target"]["loaded_disconnected_component_kip"])
    actual = sum(
        float(row["load_kip"])
        for row in v8l["summary"]["best_reconstructed_case"][
            "loaded_disconnected_components"
        ]
    )
    if not math.isclose(actual, expected, rel_tol=0.0, abs_tol=1e-6):
        raise ValueError(f"V8L target drift: expected {expected}, found {actual}")
    return config, v8l


def angle_area_in2(legs: list[float], thickness: float) -> float:
    return thickness * (float(legs[0]) + float(legs[1]) - thickness)


def pair_ea_kip(config: dict[str, object], concrete_factor: float) -> dict[str, float]:
    material = config["material_and_section_hypotheses"]
    top_area = angle_area_in2(
        material["top_angle_legs_in"], float(material["top_angle_thickness_in"])
    )
    bottom_area = angle_area_in2(
        material["bottom_angle_legs_in"],
        float(material["bottom_angle_thickness_in"]),
    )
    steel_area = (
        float(material["angles_per_chord_per_truss"])
        * (top_area + bottom_area)
        * float(material["trusses_per_pair"])
    )
    slab_area = (
        float(material["slab_width_per_pair_in"])
        * float(material["slab_average_thickness_in"])
    )
    steel_ea = steel_area * float(material["steel_modulus_ksi"])
    concrete_ea = (
        slab_area
        * float(material["lightweight_concrete_modulus_ksi"])
        * concrete_factor
    )
    return {
        "top_angle_area_in2": top_area,
        "bottom_angle_area_in2": bottom_area,
        "steel_area_per_pair_in2": steel_area,
        "slab_area_per_pair_in2": slab_area,
        "steel_ea_kip": steel_ea,
        "effective_concrete_ea_kip": concrete_ea,
        "total_ea_kip": steel_ea + concrete_ea,
    }


def pair_response(
    drop_in: float,
    span_in: float,
    ea_kip: float,
    horizontal_capacity_kip: float | None,
    vertical_capacity_kip: float | None,
) -> dict[str, float | bool]:
    diagonal = math.hypot(span_in, drop_in)
    extension = diagonal - span_in
    elastic_tension = ea_kip * extension / span_in
    tension = elastic_tension
    horizontal_capped = False
    if horizontal_capacity_kip is not None and tension > horizontal_capacity_kip:
        tension = horizontal_capacity_kip
        horizontal_capped = True
    vertical = tension * drop_in / diagonal if diagonal else 0.0
    vertical_capped = False
    if vertical_capacity_kip is not None and vertical > vertical_capacity_kip:
        vertical = vertical_capacity_kip
        vertical_capped = True
    return {
        "span_in": span_in,
        "drop_in": drop_in,
        "extension_in": extension,
        "elastic_tension_kip": elastic_tension,
        "tension_kip": tension,
        "vertical_transfer_kip": vertical,
        "horizontal_capped": horizontal_capped,
        "vertical_capped": vertical_capped,
    }


def topology_response(
    config: dict[str, object],
    topology_name: str,
    concrete_factor: float,
    regime_name: str,
    drop_in: float,
) -> dict[str, object]:
    topology = config["path_topologies"][topology_name]
    regime = config["connection_regimes"][regime_name]
    geometry = config["derived_geometry"]
    ea = pair_ea_kip(config, concrete_factor)
    face_rows: list[dict[str, object]] = []
    total = 0.0
    for face, pair_count_value in topology["pairs_per_face"].items():
        pair_count = int(pair_count_value)
        floor_count = int(topology["floor_count"])
        active_path_count = pair_count * floor_count
        span = float(geometry[FACE_SPAN_KEY[face]])
        response = pair_response(
            drop_in,
            span,
            float(ea["total_ea_kip"]),
            (
                None
                if regime["horizontal_tension_capacity_per_pair_kip"] is None
                else float(regime["horizontal_tension_capacity_per_pair_kip"])
            ),
            (
                None
                if regime["vertical_capacity_per_pair_kip"] is None
                else float(regime["vertical_capacity_per_pair_kip"])
            ),
        )
        face_transfer = active_path_count * float(response["vertical_transfer_kip"])
        total += face_transfer
        face_rows.append(
            {
                "face": face,
                "pair_count_per_floor": pair_count,
                "floor_count": floor_count,
                "active_path_count": active_path_count,
                "face_transfer_kip": face_transfer,
                "pair_response": response,
            }
        )
    return {
        "drop_in": drop_in,
        "total_vertical_transfer_kip": total,
        "face_rows": face_rows,
        "pair_ea": ea,
    }


def required_drop(
    config: dict[str, object],
    topology_name: str,
    concrete_factor: float,
    regime_name: str,
    target_kip: float,
) -> float | None:
    analysis = config["analysis"]
    maximum = float(analysis["maximum_root_search_drop_in"])
    high_response = topology_response(
        config, topology_name, concrete_factor, regime_name, maximum
    )
    if float(high_response["total_vertical_transfer_kip"]) < target_kip:
        return None
    low = 0.0
    high = maximum
    tolerance = float(analysis["root_tolerance_in"])
    while high - low > tolerance:
        middle = 0.5 * (low + high)
        value = float(
            topology_response(
                config, topology_name, concrete_factor, regime_name, middle
            )["total_vertical_transfer_kip"]
        )
        if value >= target_kip:
            high = middle
        else:
            low = middle
    return high


def perimeter_screen(
    config: dict[str, object], response: dict[str, object]
) -> dict[str, object]:
    analysis = config["analysis"]
    rows: list[dict[str, object]] = []
    for face_row in response["face_rows"]:
        face = str(face_row["face"])
        existing = float(analysis["perimeter_after_impact_floor98_loads_kip"][face])
        count = int(analysis["perimeter_surviving_column_proxy"][face])
        capacity = count * float(
            analysis["perimeter_column151_room_local_buckling_capacity_kip"]
        )
        increment = float(face_row["face_transfer_kip"])
        rows.append(
            {
                "face": face,
                "existing_after_impact_load_kip": existing,
                "increment_from_floor_path_kip": increment,
                "prototype_aggregate_capacity_kip": capacity,
                "prototype_dcr": (existing + increment) / capacity,
                "passes_prototype_screen": existing + increment <= capacity,
            }
        )
    return {
        "passes_all_faces": all(bool(row["passes_prototype_screen"]) for row in rows),
        "maximum_prototype_dcr": max(float(row["prototype_dcr"]) for row in rows),
        "rows": rows,
        "warning": "Column 151 is only a prototype screen, not a perimeter schedule.",
    }


def case_rows(config: dict[str, object]) -> list[dict[str, object]]:
    target = float(config["inherited_v8l_target"]["loaded_disconnected_component_kip"])
    official_differential = abs(
        float(config["analysis"]["official_floor98_to_floor93_core_change_difference_kip"])
    )
    physical_limit = float(config["analysis"]["physical_gate_maximum_drop_in"])
    rows: list[dict[str, object]] = []
    for topology_name in config["path_topologies"]:
        for concrete_factor in config["material_and_section_hypotheses"][
            "concrete_effectiveness_factors"
        ]:
            factor = float(concrete_factor)
            for regime_name in config["connection_regimes"]:
                references = {
                    str(drop): topology_response(
                        config, topology_name, factor, regime_name, float(drop)
                    )
                    for drop in config["analysis"]["reference_relative_drops_in"]
                }
                target_drop = required_drop(
                    config, topology_name, factor, regime_name, target
                )
                official_drop = required_drop(
                    config, topology_name, factor, regime_name, official_differential
                )
                response_at_target = (
                    None
                    if target_drop is None
                    else topology_response(
                        config, topology_name, factor, regime_name, target_drop
                    )
                )
                wall_screen = (
                    None
                    if response_at_target is None
                    else perimeter_screen(config, response_at_target)
                )
                is_physical = regime_name == "published_seat_capped"
                gate_pass = bool(
                    is_physical
                    and target_drop is not None
                    and target_drop <= physical_limit
                    and wall_screen is not None
                    and wall_screen["passes_all_faces"]
                )
                rows.append(
                    {
                        "topology": topology_name,
                        "topology_status": config["path_topologies"][topology_name][
                            "status"
                        ],
                        "concrete_effectiveness_factor": factor,
                        "connection_regime": regime_name,
                        "connection_status": config["connection_regimes"][regime_name][
                            "status"
                        ],
                        "reference_responses": references,
                        "required_drop_for_v8l_component_in": target_drop,
                        "required_drop_for_official_956kip_difference_in": official_drop,
                        "perimeter_screen_at_v8l_target": wall_screen,
                        "physical_gate_pass": gate_pass,
                    }
                )
    return rows


def select_row(
    rows: list[dict[str, object]],
    topology: str,
    factor: float,
    regime: str,
) -> dict[str, object]:
    for row in rows:
        if (
            row["topology"] == topology
            and math.isclose(float(row["concrete_effectiveness_factor"]), factor)
            and row["connection_regime"] == regime
        ):
            return row
    raise KeyError((topology, factor, regime))


def font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    candidates = [
        Path("C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf"),
        Path("C:/Windows/Fonts/calibrib.ttf" if bold else "C:/Windows/Fonts/calibri.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size)
    return ImageFont.load_default()


def render_plot(payload: dict[str, object]) -> None:
    canvas = Image.new("RGB", (1900, 1120), "white")
    draw = ImageDraw.Draw(canvas)
    navy = (31, 43, 61)
    red = (190, 57, 57)
    green = (50, 145, 90)
    amber = (218, 142, 42)
    blue = (53, 112, 183)
    grey = (218, 222, 229)
    draw.text(
        (950, 48),
        "WTC 1 V8M - couplage froid noyau / planchers / facades",
        anchor="mm",
        font=font(36, True),
        fill=navy,
    )

    # Force-displacement curves for physically capped, full-composite cases.
    x0, y0, w, h = 170, 190, 945, 660
    draw.text(
        (x0 + w / 2, y0 - 105),
        "Transfert vertical avec limites publiees des sieges",
        anchor="mm",
        font=font(26, True),
        fill=navy,
    )
    xmax = 100.0
    ymax = 5200.0
    for tick in range(0, 101, 20):
        x = x0 + tick / xmax * w
        draw.line((x, y0, x, y0 + h), fill=grey, width=1)
        draw.text((x, y0 + h + 12), str(tick), anchor="ma", font=font(16), fill=navy)
    for tick in range(0, 5001, 1000):
        y = y0 + h - tick / ymax * h
        draw.line((x0, y, x0 + w, y), fill=grey, width=1)
        draw.text((x0 - 12, y), f"{tick:,}".replace(",", " "), anchor="rm", font=font(16), fill=navy)
    draw.rectangle((x0, y0, x0 + w, y0 + h), outline=navy, width=2)
    draw.text((x0 + w / 2, y0 + h + 52), "deplacement relatif noyau-facade (in)", anchor="mm", font=font(18, True), fill=navy)
    draw.text((x0 - 92, y0 + h / 2), "transfert (kip)", anchor="mm", font=font(18, True), fill=navy)

    curve_specs = [
        ("north_damage_scaled_5floors", red, "nord endommage - 5 etages"),
        ("north_full_5floors", amber, "nord intact - 5 etages"),
        ("all_faces_north_damage_scaled_5floors", blue, "4 faces, nord endommage - 5 etages"),
        ("all_faces_full_6floors", green, "4 faces intactes - 6 etages"),
    ]
    for topology, color, label in curve_specs:
        points = []
        for step in range(0, 201):
            drop = xmax * step / 200.0
            value = float(
                topology_response(
                    payload["configuration"],
                    topology,
                    1.0,
                    "published_seat_capped",
                    drop,
                )["total_vertical_transfer_kip"]
            )
            points.append((x0 + drop / xmax * w, y0 + h - min(value, ymax) / ymax * h))
        draw.line(points, fill=color, width=4)
    target = float(payload["target_component_kip"])
    ty = y0 + h - target / ymax * h
    draw.line((x0, ty, x0 + w, ty), fill=red, width=3)
    draw.text((x0 + 12, ty - 8), "cible V8L : 4 772 kip", anchor="lb", font=font(17, True), fill=red)
    official = abs(float(payload["official_difference_kip"]))
    oy = y0 + h - official / ymax * h
    draw.line((x0, oy, x0 + w, oy), fill=navy, width=2)
    draw.text((x0 + 12, oy - 8), "difference officielle : 956 kip", anchor="lb", font=font(16, True), fill=navy)
    dx = x0 + 25.0 / xmax * w
    draw.line((dx, y0, dx, y0 + h), fill=amber, width=3)
    draw.text((dx + 8, y0 + 78), "25 in : grande deformation", font=font(16, True), fill=amber)
    for index, (_, color, label) in enumerate(curve_specs):
        lx = x0 + 30 + (index % 2) * 480
        ly = y0 - 54 + (index // 2) * 28
        draw.line((lx, ly, lx + 42, ly), fill=color, width=5)
        draw.text((lx + 52, ly), label, anchor="lm", font=font(15, True), fill=navy)

    # Summary cards.
    rx, ry = 1180, 145
    draw.text((1490, ry - 30), "Seuils calcules", anchor="mm", font=font(27, True), fill=navy)
    cards = payload["summary"]["selected_case_cards"]
    for index, card in enumerate(cards):
        y = ry + index * 128
        draw.rounded_rectangle((rx, y, 1810, y + 104), radius=12, fill=(244, 246, 249), outline=grey, width=2)
        draw.text((rx + 18, y + 18), card["label"], font=font(17, True), fill=navy)
        value = card["required_drop_in"]
        value_label = "impossible" if value is None else f"{float(value):.1f} in"
        draw.text((rx + 18, y + 55), value_label, font=font(28, True), fill=red if value is None or float(value) > 25.0 else green)
        draw.text((rx + 210, y + 61), card["note"], font=font(14), fill=navy)

    draw.rounded_rectangle((95, 935, 1810, 1035), radius=18, fill=(249, 229, 229))
    draw.text((952, 968), payload["summary"]["gate_label"], anchor="mm", font=font(29, True), fill=red)
    draw.text((952, 1007), payload["summary"]["gate_explanation"], anchor="mm", font=font(18, True), fill=navy)
    draw.text((952, 1080), "Le hat truss froid reste separe : credit impose = 0 kip.", anchor="mm", font=font(18, True), fill=navy)
    canvas.save(OUT_PNG)


def write_report(payload: dict[str, object]) -> None:
    summary = payload["summary"]
    best = summary["best_physical_case"]
    informed = summary["damage_informed_physical_case"]
    uncapped = summary["uncapped_shell_comparison"]
    rows = [
        "# WTC 1 - V8M : couplage froid noyau-planchers-facades",
        "",
        "## Resultat principal",
        "",
        summary["report_conclusion"],
        "",
        (
            f"Le meilleur cas physiquement plafonne transfere {best['transfer_at_25in_kip']:.0f} kip "
            f"a 25 in et exige {best['required_drop_in']:.1f} in pour reprendre les "
            "4 772 kip de la composante V8L. Le cas qui conserve le proxy de dommages nord "
            f"exige {informed['required_drop_in']:.1f} in. Ces deplacements depassent le seuil "
            "de 25 in que NIST classait deja comme deplacement vertical significatif du plancher."
        ),
        "",
        (
            f"En supprimant les limites de connexion, la coque equivalente la plus raide atteint "
            f"la cible a {uncapped['required_drop_in']:.1f} in. Ce resultat montre la sensibilite "
            "a la loi de connexion; il ne constitue pas une capacite physique mesuree."
        ),
        "",
        "## Faits et resultats officiels",
        "",
        "- Une connexion interieure de paire de fermes porte environ 16 kip en service et sa capacite horizontale publiee a 20 C est 44 kip.",
        "- Le modele de ferme composite de reference avait une portee longue de 713 in, une dalle tributaire de 80 in par paire et une epaisseur moyenne de 4,3 in.",
        "- Les coques de plancher du modele global avaient une raideur membranaire calibree sur le modele de ferme, mais la valeur numerique equivalente n'est pas publiee dans les pages sourcees.",
        "- NIST utilise ces coques pour l'action de diaphragme et le transfert lorsque le noyau descend sensiblement par rapport aux facades.",
        "- Apres impact, le changement de charge du noyau est +400 kip aux niveaux 98 et 105; V8M ne credite donc aucun transfert froid additionnel par le hat truss.",
        "",
        "## Hypotheses propres a V8M",
        "",
        "- La membrane suit une geometrie de cable: seul le composant vertical de la traction axiale transfere la charge.",
        "- Les sections de corniere de la Figure 4-23 sont converties en aire brute en negligeant les conges; trois fractions de beton efficace (0, 0,25 et 1,0) encadrent la raideur inconnue.",
        "- Toutes les paires actives d'un cas subissent le meme deplacement relatif. C'est une enveloppe superieure de compatibilite, pas une carte as-built.",
        "- Le proxy nord endommage conserve 11 paires par niveau; les enveloppes intactes en utilisent 31 par face.",
        "- Le prototype de poteau exterieur 151 sert seulement a verifier que la facade n'est pas le premier plafond arithmetique; il ne remplace pas le calendrier complet des plaques.",
        "",
        "## Resultats selectionnes",
        "",
        "| Topologie | Limite de connexion | Beton efficace | Transfert a 25 in | Deplacement requis pour 4 772 kip | Gate physique |",
        "|---|---|---:|---:|---:|---|",
    ]
    for row in payload["selected_rows"]:
        required = row["required_drop_for_v8l_component_in"]
        required_label = "impossible" if required is None else f"{float(required):.1f} in"
        transfer = float(row["reference_responses"]["25.0"]["total_vertical_transfer_kip"])
        rows.append(
            f"| {row['topology']} | {row['connection_regime']} | {float(row['concrete_effectiveness_factor']):.2f} | {transfer:.0f} kip | {required_label} | {'oui' if row['physical_gate_pass'] else 'non'} |"
        )
    rows.extend(
        [
            "",
            "## Comparaison au modele officiel",
            "",
            (
                f"La difference de changement de charge du noyau entre les niveaux 98 et 93 est de "
                f"956 kip dans les tableaux NIST. Le cas physiquement plafonne et endommage atteint "
                f"cette valeur a {informed['required_drop_for_956kip_in']:.1f} in. Ce rapprochement "
                "ne calibre pas le modele, car la difference officielle inclut aussi les charges des "
                "elements severes et n'isole pas la contribution des planchers."
            ),
            "",
            "## Contradictions et informations manquantes",
            "",
            "- V8M ne trouve pas de chemin plancher-facade physiquement plafonne capable de reprendre 4 772 kip avant grande deformation.",
            "- Le cas de coque non plafonnee peut mathematiquement fermer le chemin, mais depend d'une raideur equivalente non publiee et ignore la rupture horizontale de 44 kip.",
            "- L'echec ne contredit pas a lui seul le modele global NIST: V8L peut encore sous-representer la redistribution interne dans les dalles et poutres du noyau, et la topologie as-built manque.",
            "- Les affectations exactes des sieges, la carte de survie des fermes et les fichiers SAP2000/ANSYS restent manquants.",
            "",
            "## Decision du gate",
            "",
            summary["gate_decision"],
            "",
            f"Temps d'execution : {payload['runtime_seconds']:.2f} s. Les {summary['case_count']} enveloppes sont conservees dans le JSON V8M.",
        ]
    )
    OUT_REPORT.write_text("\n".join(rows) + "\n", encoding="utf-8")


def main() -> None:
    started = time.perf_counter()
    config, v8l = load_inputs()
    rows = case_rows(config)
    physical_rows = [
        row for row in rows if row["connection_regime"] == "published_seat_capped"
    ]
    physical_passes = [row for row in physical_rows if row["physical_gate_pass"]]
    best_physical_row = min(
        (row for row in physical_rows if row["required_drop_for_v8l_component_in"] is not None),
        key=lambda row: (
            round(float(row["required_drop_for_v8l_component_in"]), 3),
            -float(row["concrete_effectiveness_factor"]),
        ),
    )
    damage_informed_row = select_row(
        rows,
        "all_faces_north_damage_scaled_5floors",
        1.0,
        "published_seat_capped",
    )
    uncapped_row = select_row(
        rows, "all_faces_full_6floors", 1.0, "uncapped_global_shell"
    )
    north_damage_row = select_row(
        rows, "north_damage_scaled_5floors", 1.0, "published_seat_capped"
    )
    north_full_row = select_row(
        rows, "north_full_5floors", 1.0, "published_seat_capped"
    )
    selected = [
        north_damage_row,
        north_full_row,
        damage_informed_row,
        select_row(rows, "all_faces_full_5floors", 1.0, "published_seat_capped"),
        best_physical_row,
        uncapped_row,
    ]
    reference_drops = [
        float(value) for value in config["analysis"]["reference_relative_drops_in"]
    ]
    validation_checks = {
        "case_count_is_45": len(rows) == 45,
        "all_reference_curves_monotonic": all(
            all(
                float(row["reference_responses"][str(later)]["total_vertical_transfer_kip"])
                >= float(row["reference_responses"][str(earlier)]["total_vertical_transfer_kip"])
                for earlier, later in zip(reference_drops, reference_drops[1:])
            )
            for row in rows
        ),
        "all_zero_drop_transfers_are_zero": all(
            math.isclose(
                float(
                    topology_response(
                        config,
                        str(row["topology"]),
                        float(row["concrete_effectiveness_factor"]),
                        str(row["connection_regime"]),
                        0.0,
                    )["total_vertical_transfer_kip"]
                ),
                0.0,
                rel_tol=0.0,
                abs_tol=1e-12,
            )
            for row in rows
        ),
        "north_damage_physical_asymptote_below_v8l_target": (
            11 * 5 * 44.0
            < float(config["inherited_v8l_target"]["loaded_disconnected_component_kip"])
        ),
        "hat_truss_cold_credit_is_zero": math.isclose(
            float(config["analysis"]["hat_truss_cold_credit_kip"]),
            0.0,
            rel_tol=0.0,
            abs_tol=1e-12,
        ),
    }
    if not all(validation_checks.values()):
        raise RuntimeError(f"V8M validation failed: {validation_checks}")
    gate_passed = bool(physical_passes)
    report_conclusion = (
        "Le chemin froid plancher-facade ne ferme pas le cut-set V8L dans les limites publiees. "
        "Meme l'enveloppe intacte sur quatre faces et six niveaux exige une descente relative "
        "bien superieure a 25 in; avec le proxy de dommages nord, le seuil est encore plus eleve. "
        "Le plafond provient de la geometrie membranaire et de la traction horizontale des sieges, "
        "pas de la resistance axiale des facades."
    )
    gate_label = "GATE FROID NON VALIDE : planchers-facades insuffisants avant grande deformation"
    gate_explanation = "La coque non plafonnee passe plus tot, mais elle ne valide pas les connexions physiques."
    gate_decision = (
        "**NON VALIDE.** Aucun cas respectant la limite horizontale publiee de 44 kip ne reprend "
        "la composante V8L a 25 in ou moins. La prochaine iteration doit auditer la raideur "
        "equivalente et la redistribution interne du noyau a partir des fichiers globaux ou de "
        "substituts calibres; la thermique et Blender dynamique restent suspendus."
    )
    runtime = time.perf_counter() - started
    payload = {
        "model": "WTC1_V8M_CORE_FLOOR_PERIMETER_COUPLING",
        "version": "8.12.0",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "runtime_seconds": runtime,
        "configuration_file": str(CONFIG.relative_to(ROOT)).replace("\\", "/"),
        "configuration": config,
        "facts_transferred": config["official_facts"],
        "model_assumptions": config["material_and_section_hypotheses"],
        "target_component_kip": float(
            config["inherited_v8l_target"]["loaded_disconnected_component_kip"]
        ),
        "official_difference_kip": float(
            config["analysis"]["official_floor98_to_floor93_core_change_difference_kip"]
        ),
        "hat_truss_path": {
            "cold_credit_kip": float(config["analysis"]["hat_truss_cold_credit_kip"]),
            "later_80min_transfer_kip_not_credited": float(
                config["analysis"]["later_80min_hat_transfer_kip_not_credited"]
            ),
            "accounting": "separate_from_office_floor_path",
        },
        "case_rows": rows,
        "selected_rows": selected,
        "validation_checks": validation_checks,
        "summary": {
            "case_count": len(rows),
            "physical_case_count": len(physical_rows),
            "physical_gate_pass_count": len(physical_passes),
            "gate_passed": gate_passed,
            "best_physical_case": {
                "topology": best_physical_row["topology"],
                "concrete_effectiveness_factor": best_physical_row[
                    "concrete_effectiveness_factor"
                ],
                "required_drop_in": best_physical_row[
                    "required_drop_for_v8l_component_in"
                ],
                "transfer_at_25in_kip": best_physical_row["reference_responses"][
                    "25.0"
                ]["total_vertical_transfer_kip"],
                "perimeter_screen": best_physical_row[
                    "perimeter_screen_at_v8l_target"
                ],
            },
            "damage_informed_physical_case": {
                "topology": damage_informed_row["topology"],
                "required_drop_in": damage_informed_row[
                    "required_drop_for_v8l_component_in"
                ],
                "required_drop_for_956kip_in": damage_informed_row[
                    "required_drop_for_official_956kip_difference_in"
                ],
                "transfer_at_25in_kip": damage_informed_row[
                    "reference_responses"
                ]["25.0"]["total_vertical_transfer_kip"],
            },
            "uncapped_shell_comparison": {
                "topology": uncapped_row["topology"],
                "required_drop_in": uncapped_row[
                    "required_drop_for_v8l_component_in"
                ],
                "warning": "no published horizontal or vertical connection cap",
            },
            "north_damage_only_maximum_transfer_kip": 11 * 5 * 44.0,
            "hat_truss_cold_credit_kip": 0.0,
            "thermal_runs_authorized": False,
            "blender_coupling_authorized": False,
            "report_conclusion": report_conclusion,
            "gate_label": gate_label,
            "gate_explanation": gate_explanation,
            "gate_decision": gate_decision,
            "selected_case_cards": [
                {
                    "label": "Nord endommage, 5 etages",
                    "required_drop_in": north_damage_row[
                        "required_drop_for_v8l_component_in"
                    ],
                    "note": "maximum theorique 2 420 kip",
                },
                {
                    "label": "Nord intact, 5 etages",
                    "required_drop_in": north_full_row[
                        "required_drop_for_v8l_component_in"
                    ],
                    "note": "limite 44 kip conservee",
                },
                {
                    "label": "4 faces, nord endommage",
                    "required_drop_in": damage_informed_row[
                        "required_drop_for_v8l_component_in"
                    ],
                    "note": "enveloppe globale 5 etages",
                },
                {
                    "label": "4 faces intactes, 6 etages",
                    "required_drop_in": best_physical_row[
                        "required_drop_for_v8l_component_in"
                    ],
                    "note": "meilleur cas physique",
                },
                {
                    "label": "Coque non plafonnee",
                    "required_drop_in": uncapped_row[
                        "required_drop_for_v8l_component_in"
                    ],
                    "note": "comparaison, pas validation",
                },
            ],
        },
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    write_report(payload)
    render_plot(payload)
    print(
        json.dumps(
            {
                "status": "ok",
                "cases": len(rows),
                "physical_passes": len(physical_passes),
                "best_physical_required_drop_in": best_physical_row[
                    "required_drop_for_v8l_component_in"
                ],
                "damage_informed_required_drop_in": damage_informed_row[
                    "required_drop_for_v8l_component_in"
                ],
                "uncapped_required_drop_in": uncapped_row[
                    "required_drop_for_v8l_component_in"
                ],
                "runtime_seconds": runtime,
                "outputs": [str(OUT_JSON), str(OUT_REPORT), str(OUT_PNG)],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
