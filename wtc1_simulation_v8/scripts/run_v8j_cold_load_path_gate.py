"""WTC 1 V8J - cold load-path gate and disconnected cut-set audit.

V8J does not tune V8I until it stands.  It reproduces the 20 C post-impact
failure, identifies the loaded component that becomes disconnected, and then
compares that cut demand with the published floor-seat and hat-truss envelopes.
The comparison is deliberately capacity-only: a truss-seat capacity is not
silently converted into a core-to-perimeter force-displacement spring.
"""

from __future__ import annotations

import json
import math
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[2]
V8 = ROOT / "wtc1_simulation_v8"
sys.path.insert(0, str((V8 / "scripts").resolve()))
import run_v8i_core_slab_catenary as v8i  # noqa: E402


CONFIG = V8 / "data" / "v8j_cold_load_path_gate.json"
COMPONENTS = V8 / "data" / "nist_wtc1_component_capacities_v8g.json"
OUT_JSON = V8 / "output" / "resultats_wtc1_v8j_gate_froid.json"
OUT_REPORT = V8 / "output" / "rapport_wtc1_v8j_gate_froid.md"
OUT_PNG = V8 / "output" / "synthese_wtc1_v8j_gate_froid.png"

SELECTED_SLAB_CASES = [
    "no_slab_v8h_reference",
    "high_ratio_full_area",
    "cold_upper_envelope",
]


def load_inputs() -> dict[str, object]:
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    transfer = json.loads(v8i.TRANSFER.read_text(encoding="utf-8"))
    aisc = json.loads(v8i.AISC.read_text(encoding="utf-8"))
    prior_b = json.loads(v8i.V8B_RESULT.read_text(encoding="utf-8"))
    parameters = json.loads(v8i.PARAMETERS.read_text(encoding="utf-8"))
    v8i_config = json.loads(v8i.CONFIG.read_text(encoding="utf-8"))
    components = json.loads(COMPONENTS.read_text(encoding="utf-8"))
    return {
        "config": config,
        "transfer": transfer,
        "aisc": aisc,
        "prior_b": prior_b,
        "parameters": parameters,
        "v8i_config": v8i_config,
        "components": components,
    }


def prepare_model(inputs: dict[str, object]) -> dict[str, object]:
    parameters = inputs["parameters"]
    prior_b = inputs["prior_b"]
    coords = {
        int(row["id"]): (float(row["x_m"]), float(row["y_m"]))
        for row in parameters["core_layout_reconstruction"]["columns"]
    }
    prepared: dict[int, dict[str, object]] = {}
    for floor in v8i.FLOORS_DESC:
        floor_data = prior_b["floor_inputs"][str(floor)]
        prepared[floor] = {
            "sections": {
                int(key): value for key, value in floor_data["sections"].items()
            },
            "removed": set(int(value) for value in floor_data["initial_removed"]),
        }
    return {
        "coords": coords,
        "edges": v8i.v8h.nearest_four_edges(coords),
        "prepared": prepared,
        "beam_shape": inputs["aisc"]["shapes"][v8i.BEAM_PROFILE],
        "fy_params": inputs["transfer"]["steel_temperature_model"][
            "yield_ratio_parameters"
        ],
        "e_params": inputs["transfer"]["steel_temperature_model"][
            "young_modulus_parameters"
        ],
    }


def slab_case(inputs: dict[str, object], case_id: str) -> dict[str, object]:
    return next(
        row for row in inputs["v8i_config"]["slab_cases"] if row["id"] == case_id
    )


def cold_path(
    inputs: dict[str, object], model: dict[str, object], case_id: str, demand_kip: float
) -> dict[str, object]:
    coords = model["coords"]
    edges = model["edges"]
    case = slab_case(inputs, case_id)
    width_m = v8i.area_normalized_width_m(
        coords, edges, float(case["active_area_fraction"])
    )[0]
    reference_field = {column: 0.5 for column in coords}
    cold_thermal = {str(floor): [[20.0, 20.0]] for floor in v8i.FLOORS_DESC}
    return v8i.simulate_path(
        demand_kip,
        reference_field,
        1.0,
        0,
        model["prepared"],
        cold_thermal,
        coords,
        edges,
        model["beam_shape"],
        case,
        width_m,
        model["fy_params"],
        model["e_params"],
        fixed_temperature_fraction=0.0,
    )


def maximum_stable_demand(
    inputs: dict[str, object], model: dict[str, object], case_id: str, upper_kip: float
) -> dict[str, float]:
    lower = 0.0
    upper = upper_kip
    for _ in range(28):
        midpoint = 0.5 * (lower + upper)
        if cold_path(inputs, model, case_id, midpoint)["equilibrium_all_floors"]:
            lower = midpoint
        else:
            upper = midpoint
    return {
        "maximum_stable_demand_kip": lower,
        "minimum_failed_demand_kip": upper,
        "deficit_from_post_impact_demand_kip": upper_kip - lower,
    }


def edge_definitions_at_20c(
    inputs: dict[str, object],
    model: dict[str, object],
    case_id: str,
) -> list[dict[str, object]]:
    coords = model["coords"]
    edges = model["edges"]
    case = slab_case(inputs, case_id)
    width_m = v8i.area_normalized_width_m(
        coords, edges, float(case["active_area_fraction"])
    )[0]
    definitions: list[dict[str, object]] = []
    for first, second in edges:
        length_m = math.dist(coords[first], coords[second])
        beam = v8i.v8h.beam_law(
            model["beam_shape"],
            length_m,
            20.0,
            v8i.BEAM_CONNECTION_FACTOR,
            v8i.BEAM_ACTIVE_PLANES,
            model["fy_params"],
            model["e_params"],
        )
        membrane = v8i.membrane_law(
            length_m,
            width_m,
            float(case["reinforcement_ratio"]),
            float(case["wire_yield_ksi_rt"]),
            float(case["ultimate_strain"]),
            20.0,
            model["fy_params"],
            model["e_params"],
        )
        definitions.append(
            {
                "i": first,
                "j": second,
                "beam_stiffness": beam["initial_stiffness_kip_per_in"],
                "beam_capacity": beam["yield_force_kip"],
                "beam_yield_displacement": beam["yield_displacement_in"],
                "beam_ultimate_displacement": beam["ultimate_displacement_in"],
                "membrane_law": membrane,
            }
        )
    return definitions


def detailed_cut_set(
    inputs: dict[str, object], model: dict[str, object], demand_kip: float
) -> dict[str, object]:
    case_id = "cold_upper_envelope"
    coords = model["coords"]
    prepared = model["prepared"]
    incoming = v8i.v8b.initial_loads(
        demand_kip, prepared[99]["sections"], {}, "capacity_proportional"
    )
    case = slab_case(inputs, case_id)
    width_m = v8i.area_normalized_width_m(
        coords, model["edges"], float(case["active_area_fraction"])
    )[0]
    passed_floors: list[dict[str, object]] = []
    for floor in [99, 98, 97]:
        state = v8i.story_response(
            incoming,
            {column: 20.0 for column in coords},
            prepared[floor]["sections"],
            prepared[floor]["removed"],
            coords,
            model["edges"],
            model["beam_shape"],
            case,
            width_m,
            model["fy_params"],
            model["e_params"],
        )
        passed_floors.append(
            {
                "floor": floor,
                "equilibrium": bool(state["equilibrium"]),
                "final_peak_dcr": float(state["final_peak_dcr"]),
                "maximum_abs_displacement_in": float(
                    state["maximum_abs_displacement_in"]
                ),
            }
        )
        incoming = {
            int(key): float(value) for key, value in state["final_loads"].items()
        }

    floor = 96
    sections = prepared[floor]["sections"]
    survivors = set(sections) - prepared[floor]["removed"]
    column_stiffness = {
        column: v8i.v8b.elastic_modulus_ksi(
            20.0, model["e_params"], v8i.TAIL
        )
        * float(sections[column]["area_in2"])
        / v8i.v8h.STORY_LENGTH_IN
        for column in survivors
    }
    raw = v8i.solve_composite_network(
        {column: float(incoming.get(column, 0.0)) for column in sections},
        survivors,
        column_stiffness,
        edge_definitions_at_20c(inputs, model, case_id),
        set(),
        set(),
        {},
    )
    fractured_beams = {
        tuple(sorted(int(value) for value in edge))
        for edge in raw.get("fractured_beams", [])
    }
    fractured_membranes = {
        tuple(sorted(int(value) for value in edge))
        for edge in raw.get("fractured_membranes", [])
    }
    adjacency = {column: set() for column in sections}
    for first, second in model["edges"]:
        key = tuple(sorted((first, second)))
        if key in fractured_beams and key in fractured_membranes:
            continue
        adjacency[first].add(second)
        adjacency[second].add(first)

    unseen = set(sections)
    components: list[dict[str, object]] = []
    while unseen:
        start = unseen.pop()
        component = {start}
        stack = [start]
        while stack:
            current = stack.pop()
            for neighbor in adjacency[current]:
                if neighbor in unseen:
                    unseen.remove(neighbor)
                    component.add(neighbor)
                    stack.append(neighbor)
        components.append(
            {
                "nodes": sorted(component),
                "has_surviving_column_support": not component.isdisjoint(survivors),
                "incoming_load_kip": sum(
                    float(incoming.get(column, 0.0)) for column in component
                ),
            }
        )
    disconnected = next(
        row
        for row in components
        if not row["has_surviving_column_support"]
        and abs(float(row["incoming_load_kip"])) > 1e-6
    )
    return {
        "selected_slab_case": case_id,
        "passed_floors": passed_floors,
        "failure_floor": floor,
        "failure_reason": raw["reason"],
        "initially_removed_columns_floor_96": sorted(prepared[floor]["removed"]),
        "fractured_beam_edges": sorted([list(edge) for edge in fractured_beams]),
        "fractured_membrane_edges": sorted(
            [list(edge) for edge in fractured_membranes]
        ),
        "connected_components_after_fracture": components,
        "disconnected_loaded_component": disconnected,
        "disconnected_load_fraction_of_core_demand": float(
            disconnected["incoming_load_kip"]
        )
        / demand_kip,
    }


def seat_capacity_audit(
    inputs: dict[str, object], cut_load_kip: float
) -> dict[str, object]:
    config = inputs["config"]
    seats = inputs["components"]["floor_truss_seats"]
    temperatures = [float(value) for value in seats["temperatures_c"]]
    cold_index = temperatures.index(
        float(config["seat_path_cases"]["exterior_seat_temperature_c"])
    )
    full_pairs = int(config["seat_path_cases"]["full_undamaged_face_pairs"])
    damage_pairs = int(config["seat_path_cases"]["north_damage_scaled_pairs"])
    service_per_pair = float(
        config["seat_path_cases"]["normal_service_load_per_pair_kip"]
    )
    rows: list[dict[str, object]] = []
    for detail, curve in seats["exterior_vertical_capacity_kip"].items():
        capacity = float(curve[cold_index])
        required_pairs = math.ceil(cut_load_kip / capacity)
        rows.append(
            {
                "exterior_seat_detail": detail,
                "capacity_per_pair_at_20c_kip": capacity,
                "required_pairs_for_cut_load": required_pairs,
                "full_face_capacity_31_pairs_kip": full_pairs * capacity,
                "full_face_capacity_screen_pass": full_pairs * capacity >= cut_load_kip,
                "damage_scaled_capacity_11_pairs_kip": damage_pairs * capacity,
                "damage_scaled_capacity_screen_pass": damage_pairs * capacity
                >= cut_load_kip,
            }
        )
    return {
        "cut_load_kip": cut_load_kip,
        "service_load_equivalent_pairs": cut_load_kip / service_per_pair,
        "full_face_pair_count": full_pairs,
        "north_damage_scaled_pair_count": damage_pairs,
        "mean_capacity_per_pair_at_20c_kip": statistics.mean(
            float(row["capacity_per_pair_at_20c_kip"]) for row in rows
        ),
        "rows": rows,
        "interpretation": (
            "The full-face arithmetic envelope straddles the cut demand, while "
            "the 11-pair north-damage proxy does not pass for any published exterior "
            "seat detail. Neither result proves a physical bridge because the actual "
            "seat map, floor-truss stiffness, load compatibility and impact survival "
            "of the path are not established."
        ),
    }


def hat_truss_audit(inputs: dict[str, object]) -> dict[str, object]:
    hat = inputs["components"]["hat_truss"]
    transfer_80 = float(hat["net_outward_transfer_history_kip"]["80"])
    controlling_dcr = max(float(value) for value in hat["outtrigger_dcr_at_80_min"].values())
    calibrated_capacity = transfer_80 / controlling_dcr
    return {
        "post_impact_core_change_floor_98_kip": 400.0,
        "post_impact_core_change_floor_105_kip": 400.0,
        "post_impact_differential_core_transfer_change_kip": 0.0,
        "official_net_outward_transfer_history_kip": hat[
            "net_outward_transfer_history_kip"
        ],
        "demonstrated_80min_transfer_kip": transfer_80,
        "controlling_80min_outrigger_dcr": controlling_dcr,
        "nist_calibrated_capacity_kip": calibrated_capacity,
        "cold_gate_credit_kip": 0.0,
        "interpretation": (
            "The hat truss was mechanically active after impact and redistributed wall "
            "loads, but the official tables do not show net differential core unloading "
            "at the cold post-impact state. Crediting the later 6,748 kip transfer to the "
            "cold gate would double count a thermal-time response."
        ),
    }


def font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    candidates = [
        Path("C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf"),
        Path("C:/Windows/Fonts/calibrib.ttf" if bold else "C:/Windows/Fonts/calibri.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size)
    return ImageFont.load_default()


def render_plot(
    model: dict[str, object], cut: dict[str, object], seats: dict[str, object]
) -> None:
    canvas = Image.new("RGB", (1900, 1120), "white")
    draw = ImageDraw.Draw(canvas)
    navy = (30, 43, 62)
    red = (190, 57, 57)
    blue = (55, 119, 177)
    green = (55, 145, 93)
    grey = (115, 122, 132)
    light = (235, 238, 242)
    draw.text(
        (950, 48),
        "WTC 1 V8J - gate froid et chemin de charge manquant",
        anchor="mm",
        font=font(36, True),
        fill=navy,
    )

    # Left panel: V8I proxy cut set at Floor 96.
    x0, y0, width, height = 95, 160, 770, 710
    draw.text(
        (x0 + width / 2, y0 - 45),
        "Floor 96 : composante chargee isolee",
        anchor="mm",
        font=font(27, True),
        fill=navy,
    )
    coords = model["coords"]
    xs = [point[0] for point in coords.values()]
    ys = [point[1] for point in coords.values()]
    scale = min(width / (max(xs) - min(xs) + 3), height / (max(ys) - min(ys) + 3))

    def point(column: int) -> tuple[float, float]:
        x, y = coords[column]
        return (
            x0 + width / 2 + scale * x,
            y0 + height / 2 - scale * y,
        )

    cut_edges = {
        tuple(sorted(edge)) for edge in cut["fractured_beam_edges"]
    } & {tuple(sorted(edge)) for edge in cut["fractured_membrane_edges"]}
    for first, second in model["edges"]:
        color = red if tuple(sorted((first, second))) in cut_edges else (200, 204, 210)
        line_width = 5 if color == red else 2
        draw.line((*point(first), *point(second)), fill=color, width=line_width)
    disconnected = set(cut["disconnected_loaded_component"]["nodes"])
    removed = set(cut["initially_removed_columns_floor_96"])
    for column in sorted(coords):
        px, py = point(column)
        fill = red if column in disconnected else ((255, 183, 77) if column in removed else blue)
        radius = 13 if column in disconnected else 9
        draw.ellipse((px - radius, py - radius, px + radius, py + radius), fill=fill, outline="white", width=2)
        if column in disconnected:
            draw.text((px, py - 24), str(column), anchor="ms", font=font(15, True), fill=red)
    cut_load = float(cut["disconnected_loaded_component"]["incoming_load_kip"])
    draw.rounded_rectangle((x0 + 55, y0 + height + 20, x0 + width - 55, y0 + height + 118), radius=18, fill=(249, 229, 229))
    draw.text((x0 + width / 2, y0 + height + 50), "503-504-505-604 sans appui survivant", anchor="mm", font=font(23, True), fill=red)
    draw.text((x0 + width / 2, y0 + height + 88), f"charge du cut-set : {cut_load:.0f} kip ({100*float(cut['disconnected_load_fraction_of_core_demand']):.1f} % du noyau)", anchor="mm", font=font(21), fill=navy)

    # Right panel: aggregate seat capacity screening.
    rx, ry, rw, rh = 990, 160, 820, 710
    draw.text((rx + rw / 2, ry - 45), "Sieges exterieurs a 20 C : test de capacite seul", anchor="mm", font=font(27, True), fill=navy)
    rows = seats["rows"]
    axis_max = max(
        cut_load,
        max(float(row["full_face_capacity_31_pairs_kip"]) for row in rows),
    ) * 1.08
    label_width = 115
    chart_x = rx + label_width
    chart_w = rw - label_width - 30
    row_h = rh / len(rows)
    for tick in range(0, 8001, 1000):
        x = chart_x + chart_w * tick / axis_max
        if x > chart_x + chart_w:
            continue
        draw.line((x, ry, x, ry + rh), fill=light, width=2)
        draw.text((x, ry + rh + 28), f"{tick/1000:.0f}k", anchor="ma", font=font(17), fill=grey)
    demand_x = chart_x + chart_w * cut_load / axis_max
    draw.line((demand_x, ry - 8, demand_x, ry + rh + 8), fill=red, width=5)
    draw.text((demand_x, ry - 18), f"cut {cut_load:.0f}", anchor="ms", font=font(18, True), fill=red)
    for index, row in enumerate(rows):
        cy = ry + (index + 0.5) * row_h
        draw.text((chart_x - 13, cy), f"#{row['exterior_seat_detail']}", anchor="rm", font=font(18, True), fill=navy)
        full = float(row["full_face_capacity_31_pairs_kip"])
        damaged = float(row["damage_scaled_capacity_11_pairs_kip"])
        full_x = chart_x + chart_w * full / axis_max
        damaged_x = chart_x + chart_w * damaged / axis_max
        draw.rounded_rectangle((chart_x, cy - 22, full_x, cy - 2), radius=6, fill=green)
        draw.rounded_rectangle((chart_x, cy + 5, damaged_x, cy + 25), radius=6, fill=(226, 151, 55))
        draw.text((min(full_x + 8, chart_x + chart_w), cy - 12), f"31x {full:.0f}", anchor="lm", font=font(15), fill=navy)
        draw.text((min(damaged_x + 8, chart_x + chart_w), cy + 15), f"11x {damaged:.0f}", anchor="lm", font=font(15), fill=navy)

    draw.rounded_rectangle((95, 980, 1805, 1070), radius=18, fill=(244, 232, 191))
    draw.text((950, 1008), "GATE FROID NON VALIDE", anchor="mm", font=font(29, True), fill=(135, 88, 20))
    draw.text((950, 1045), "La capacite brute peut etre suffisante dans certaines bornes, mais la topologie, la rigidite, la ductilite et la survie du chemin ne sont pas etablies.", anchor="mm", font=font(20, True), fill=navy)
    canvas.save(OUT_PNG)


def write_report(payload: dict[str, object]) -> None:
    cut = payload["cold_cut_set"]
    seats = payload["office_floor_to_perimeter_capacity_screen"]
    hat = payload["hat_truss_path"]
    cut_load = float(cut["disconnected_loaded_component"]["incoming_load_kip"])
    rows = [
        "# WTC 1 - V8J : gate froid et audit du chemin de charge manquant",
        "",
        "## Resultat principal",
        "",
        "V8J reproduit le cas post-impact entierement froid de V8I sans changer sa resistance. Le premier echec n'est pas une surcharge globale : au niveau 96, sept aretes du proxy poutre+dalle se rompent et isolent les colonnes 503, 504, 505 et 604, deja retirees comme appuis verticaux dans le damage set Case B. Cette composante conserve une charge de **{:.0f} kip**, soit **{:.1f} %** de la demande noyau de 34 429 kip, mais ne possede plus d'appui survivant dans le graphe V8I.".format(cut_load, 100.0 * float(cut["disconnected_load_fraction_of_core_demand"])),
        "",
        "Ce diagnostic invalide une interpretation precedente trop simple : V8I ne dit pas que le noyau reel etait globalement trop faible a froid. Il dit que la topologie nearest-four du sous-modele ne contient pas le chemin reel qui a redistribue cette charge. Le gate froid reste donc **non valide** et aucune transition thermique ni animation Blender n'est autorisee a partir de ce reseau.",
        "",
        "## Faits et sorties officielles",
        "",
        "- NIST donne environ 16 kip de charge de service par siege supportant une paire de fermes; a 20 C, les capacites verticales des sieges exterieurs publies vont de 94 a 207 kip.",
        "- NIST rapporte 38 poteaux sur 59 severes ou lourdement endommages sur la facade nord, ainsi que de graves dommages aux planchers nord entre les colonnes 112 et 145 sur les niveaux 94 a 98.",
        "- Immediatement apres impact, le changement de charge du noyau publie est +400 kip aux niveaux 98 et 105. Le differentiel est donc nul : le hat truss redistribue les charges de facade, mais NIST ne montre pas a cet instant de delestage net supplementaire du noyau entre ces deux niveaux.",
        "- A 80 min, NIST montre au contraire un transfert thermique net d'environ 6 748 kip du noyau vers les facades; l'outrigger E atteint un DCR de 0,97. Ce resultat tardif ne peut pas etre credite au cas froid sans double comptage.",
        "",
        "## Observations provenant des archives locales",
        "",
        "- L'inventaire en lecture seule de `FloorTrussSystems-20260813T183023Z-1-001.zip` contient 522 fichiers, tous images ou videos; il ne contient aucun fichier de modele ou de mesures tabulaires.",
        "- Une recherche par noms de fichiers dans le depot local n'a pas trouve WTCAB, Drawing Book 5/6, BeamSched, C32T1 ni de fichier de solveur structurel avec les extensions testees. Cette recherche ne prouve pas que ces donnees sont absentes de toute archive compressee non inspectee.",
        "",
        "## Resultats derives du sous-modele",
        "",
        "| Cas de dalle | Demande froide maximale encore stable | Deficit par rapport a 34 429 kip |",
        "|---|---:|---:|",
    ]
    for row in payload["cold_gate_cases"]:
        rows.append(
            f"| {row['slab_case']} | {row['maximum_stable_demand_kip']:.0f} kip | {row['deficit_from_post_impact_demand_kip']:.0f} kip |"
        )
    rows.extend(
        [
            "",
            "La valeur maximale stable est un seuil du proxy, pas une capacite as-built. Dans le cas froid superieur, la rupture du cut-set isole exactement quatre noeuds sans appui; le chargement isole vaut {:.0f} kip.".format(cut_load),
            "",
            "## Ecran de capacite des sieges de plancher",
            "",
            "| Detail de siege exterieur | Capacite par paire a 20 C | Paires requises | 31 paires, face intacte | 11 paires, proxy nord endommage |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    for row in seats["rows"]:
        rows.append(
            "| #{detail} | {cap:.0f} kip | {needed} | {full:.0f} kip ({full_status}) | {damaged:.0f} kip ({damaged_status}) |".format(
                detail=row["exterior_seat_detail"],
                cap=row["capacity_per_pair_at_20c_kip"],
                needed=row["required_pairs_for_cut_load"],
                full=row["full_face_capacity_31_pairs_kip"],
                full_status="passe" if row["full_face_capacity_screen_pass"] else "echoue",
                damaged=row["damage_scaled_capacity_11_pairs_kip"],
                damaged_status="passe" if row["damage_scaled_capacity_screen_pass"] else "echoue",
            )
        )
    rows.extend(
        [
            "",
            "Le proxy d'une face nord reduite a 11 paires ne couvre pas le cut-set, meme avec le siege exterieur le plus resistant publie. Une face intacte de 31 paires couvre la demande pour certains details, mais pas pour les quatre details a 94 kip. Cette comparaison reste une enveloppe de capacite : elle ne fournit ni la rigidite, ni la deformation ultime, ni l'affectation des details, ni la carte de survie des fermes.",
            "",
            "## Hypotheses propres a V8J",
            "",
            "- Le nombre 31 vient de la largeur de tour divisee par la largeur tributaire de 6,67 ft d'une paire de fermes. Le nombre 11 est un simple prorata des 21 poteaux nord non classes severes/lourdement endommages; il ne remplace pas une carte siege par siege.",
            "- Le cut-set provient de la topologie nearest-four et des lois force-deplacement V8I. Il identifie une exigence de transfert du proxy, pas la geometrie du plancher reel.",
            "- Aucune capacite de siege n'est transformee en ressort vertical noyau-facade. Cette conversion exigerait la raideur de la ferme, sa geometrie, ses appuis, sa ductilite, le comportement de dalle composite et la survie apres impact.",
            "- Le hat truss est separe en chemin froid et chemin thermique. Le credit froid impose est {:.0f} kip; la capacite calibree NIST d'environ {:.0f} kip reste une verification interne du modele officiel, pas une capacite independante.".format(float(hat["cold_gate_credit_kip"]), float(hat["nist_calibrated_capacity_kip"])),
            "",
            "## Contradictions et informations manquantes",
            "",
            "- Le resultat observe - la tour reste debout - contredit le reseau V8I/V8J s'il est traite comme chemin autonome. Il ne contredit pas encore une structure reelle qui contenait des poutres, dalles, fermes, facades et assemblages absents du proxy.",
            "- La nomenclature Drawing Book 5 des poutres du noyau, les connexions Drawing Book 6, l'affectation des huit details de sieges du niveau 96 et une carte des fermes survivantes ne sont pas disponibles dans le corpus de travail actuel.",
            "- NIST fournit des modeles globaux a diaphragmes equivalents et des modeles de sous-systemes, mais pas dans les pages inspectees une loi reduite force-deplacement directement transposable au cut-set 503-504-505-604.",
            "- La prochaine iteration doit reconstruire la vraie topologie des poutres/assemblages du niveau 96 ou obtenir les fichiers de Drawing Book 5/6. Tant que ce chemin n'est pas specifie, augmenter une resistance abstraite serait du calibrage circulaire.",
            "",
            "## Decision du gate",
            "",
            "**NON VALIDE.** V8J localise et quantifie le chemin manquant, mais ne demontre pas encore une loi force-deplacement survivante capable de porter les {:.0f} kip. Les cas thermiques et Blender restent suspendus a cette verification.".format(cut_load),
            "",
            f"Temps d'execution : {payload['runtime_seconds']:.2f} s. Configuration, diagnostic du graphe, enveloppes de capacite et sources sont conserves dans le JSON V8J.",
        ]
    )
    OUT_REPORT.write_text("\n".join(rows) + "\n", encoding="utf-8")


def main() -> None:
    started = time.perf_counter()
    inputs = load_inputs()
    model = prepare_model(inputs)
    history = inputs["transfer"]["nist_global_core_loads_floor_98_kip"][
        "case_b_time_history"
    ]
    demand = float(history["after_impact"])

    cold_cases: list[dict[str, object]] = []
    for case_id in SELECTED_SLAB_CASES:
        state = cold_path(inputs, model, case_id, demand)
        threshold = maximum_stable_demand(inputs, model, case_id, demand)
        cold_cases.append(
            {
                "slab_case": case_id,
                "post_impact_demand_kip": demand,
                "equilibrium_at_post_impact_demand": bool(
                    state["equilibrium_all_floors"]
                ),
                "first_failed_floor": state["first_failed_floor"],
                "failure_reason": state["floors"][str(state["first_failed_floor"])][
                    "reason"
                ],
                **threshold,
            }
        )

    cut = detailed_cut_set(inputs, model, demand)
    cut_load = float(cut["disconnected_loaded_component"]["incoming_load_kip"])
    seats = seat_capacity_audit(inputs, cut_load)
    hat = hat_truss_audit(inputs)
    runtime_seconds = time.perf_counter() - started
    payload = {
        "model": "WTC1_V8J_COLD_LOAD_PATH_GATE",
        "version": "8.9.0",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "runtime_seconds": runtime_seconds,
        "configuration_file": str(CONFIG.relative_to(ROOT)).replace("\\", "/"),
        "facts_transferred": inputs["config"]["official_facts"],
        "local_archive_observations": inputs["config"][
            "local_archive_observations"
        ],
        "model_assumptions": inputs["config"]["model_hypotheses"],
        "gate_definition": inputs["config"]["gate"],
        "cold_gate_cases": cold_cases,
        "cold_cut_set": cut,
        "office_floor_to_perimeter_capacity_screen": seats,
        "hat_truss_path": hat,
        "gate_result": {
            "passed": False,
            "status": "NOT_VALIDATED_MISSING_FORCE_DISPLACEMENT_PATH",
            "reason": (
                "V8J quantifies a loaded disconnected component and finds that "
                "published capacity envelopes straddle its demand, but the actual "
                "surviving topology, stiffness, ductility and connection assignment "
                "are not available."
            ),
            "thermal_runs_authorized": False,
            "blender_coupling_authorized": False,
        },
        "missing_information": [
            "Drawing Book 5 core beam schedule and real Floor 96 beam topology",
            "Drawing Book 6 core connection details",
            "Floor 96 seat-detail assignment and surviving floor-truss map",
            "compatible force-displacement law for the core-floor-perimeter bridge",
            "perimeter plate-thickness schedule at Floors 94-99",
        ],
    }
    OUT_JSON.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    write_report(payload)
    render_plot(model, cut, seats)
    print(
        json.dumps(
            {
                "status": "ok",
                "gate_passed": False,
                "cut_load_kip": cut_load,
                "failure_floor": cut["failure_floor"],
                "outputs": [str(OUT_JSON), str(OUT_REPORT), str(OUT_PNG)],
                "runtime_seconds": runtime_seconds,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
