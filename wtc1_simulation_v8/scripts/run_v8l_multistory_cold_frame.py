"""WTC 1 V8L - multistory cold core-frame redistribution audit.

The model gives every core-column/floor intersection one vertical displacement
DOF.  Surviving column segments are axial springs; floor beams are bounded
bilinear transfer springs.  This is the first V8 iteration in which a load can
move sideways at an upper floor before encountering a severed column segment
below.  It remains a reduced-order audit, not an ANSYS/CalculiX reproduction.
"""

from __future__ import annotations

import json
import math
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[2]
V8 = ROOT / "wtc1_simulation_v8"
sys.path.insert(0, str((V8 / "scripts").resolve()))
import run_v8b_stability_network as v8b  # noqa: E402
import run_v8h_mechanical_core_transfer as v8h  # noqa: E402
import run_v8i_core_slab_catenary as v8i  # noqa: E402


CONFIG = V8 / "data" / "v8l_multistory_cold_frame.json"
V8B_RESULT = V8 / "output" / "resultats_wtc1_v8b.json"
AISC = V8 / "data" / "aisc_historic_wf_properties.json"
TRANSFER = V8 / "data" / "nist_wtc1_transfer.json"
PARAMETERS = ROOT / "wtc1_3d_v4" / "data" / "wtc1_parameters.json"
V8H_CONFIG = V8 / "data" / "v8h_core_beam_network.json"
OUT_JSON = V8 / "output" / "resultats_wtc1_v8l_multietages_froid.json"
OUT_REPORT = V8 / "output" / "rapport_wtc1_v8l_multietages_froid.md"
OUT_PNG = V8 / "output" / "synthese_wtc1_v8l_multietages_froid.png"

GROUND = (93, 0)


def load_inputs() -> dict[str, object]:
    return {
        "config": json.loads(CONFIG.read_text(encoding="utf-8")),
        "v8b": json.loads(V8B_RESULT.read_text(encoding="utf-8")),
        "aisc": json.loads(AISC.read_text(encoding="utf-8")),
        "transfer": json.loads(TRANSFER.read_text(encoding="utf-8")),
        "parameters": json.loads(PARAMETERS.read_text(encoding="utf-8")),
        "v8h_config": json.loads(V8H_CONFIG.read_text(encoding="utf-8")),
    }


def orthogonal_edges(columns: set[int]) -> list[tuple[int, int]]:
    rows = {
        5: list(range(501, 509)),
        6: list(range(601, 609)),
        7: list(range(701, 709)),
        8: list(range(801, 808)),
        9: list(range(901, 909)),
        10: list(range(1001, 1009)),
    }
    edges: set[tuple[int, int]] = set()
    for row in rows.values():
        present = [column for column in row if column in columns]
        for first, second in zip(present, present[1:]):
            edges.add((first, second))
    ordered_rows = [rows[key] for key in sorted(rows)]
    for upper, lower in zip(ordered_rows, ordered_rows[1:]):
        by_digit_upper = {column % 100: column for column in upper if column in columns}
        by_digit_lower = {column % 100: column for column in lower if column in columns}
        for digit in sorted(set(by_digit_upper) & set(by_digit_lower)):
            edges.add(tuple(sorted((by_digit_upper[digit], by_digit_lower[digit]))))
    return sorted(edges)


def topology_edges(inputs: dict[str, object]) -> dict[str, list[tuple[int, int]]]:
    columns = {
        int(row["id"])
        for row in inputs["parameters"]["core_layout_reconstruction"]["columns"]
    }
    moment = [
        tuple(int(value) for value in edge)
        for edge in inputs["v8h_config"]["moment_beam_topology"]["edges"]
    ]
    return {
        "nist_moment_only": sorted(tuple(sorted(edge)) for edge in moment),
        "orthogonal_floor96_reconstruction": orthogonal_edges(columns),
    }


def prepared(inputs: dict[str, object]) -> tuple[dict[int, dict[str, object]], dict[int, tuple[float, float]]]:
    floor_data: dict[int, dict[str, object]] = {}
    for floor in inputs["config"]["model_cases"]["floors"]:
        source = inputs["v8b"]["floor_inputs"][str(floor)]
        floor_data[int(floor)] = {
            "sections": {int(key): value for key, value in source["sections"].items()},
            "removed": {int(value) for value in source["initial_removed"]},
        }
    coords = {
        int(row["id"]): (float(row["x_m"]), float(row["y_m"]))
        for row in inputs["parameters"]["core_layout_reconstruction"]["columns"]
    }
    return floor_data, coords


def beam_damage(
    inputs: dict[str, object], damage_case: str
) -> set[tuple[int, int, int]]:
    base = {
        tuple(sorted(int(value) for value in edge))
        for edge in inputs["config"]["beam_damage_definition"]["floor96_removed_edges"]
    }
    if damage_case == "no_beam_damage_upper_bound":
        floors: list[int] = []
    elif damage_case == "floor96_figure_damage":
        floors = [96]
    elif damage_case == "repeat_floor96_damage_floors94_98":
        floors = [94, 95, 96, 97, 98]
    else:
        raise ValueError(damage_case)
    return {(floor, first, second) for floor in floors for first, second in base}


def make_springs(
    inputs: dict[str, object],
    floor_data: dict[int, dict[str, object]],
    coords: dict[int, tuple[float, float]],
    edges: list[tuple[int, int]],
    profile: str,
    connection_factor: float,
    damage_case: str,
) -> tuple[list[dict[str, object]], dict[str, object]]:
    floors = [int(value) for value in inputs["config"]["model_cases"]["floors"]]
    columns = sorted(coords)
    beam_shape = inputs["aisc"]["shapes"][profile]
    fy_params = inputs["transfer"]["steel_temperature_model"]["yield_ratio_parameters"]
    e_params = inputs["transfer"]["steel_temperature_model"]["young_modulus_parameters"]
    prefractured_beams = beam_damage(inputs, damage_case)
    springs: list[dict[str, object]] = []

    for floor in floors:
        sections = floor_data[floor]["sections"]
        removed = floor_data[floor]["removed"]
        for column in columns:
            section = sections[column]
            lower = GROUND if floor == min(floors) else (floor - 1, column)
            springs.append(
                {
                    "kind": "column",
                    "floor": floor,
                    "column": column,
                    "a": (floor, column),
                    "b": lower,
                    "stiffness": 29000.0 * float(section["area_in2"]) / v8h.STORY_LENGTH_IN,
                    "capacity": float(section["room_pn_kip_k1"]),
                    "state": "fractured" if column in removed else "elastic",
                    "initial_damage": column in removed,
                }
            )

    for floor in floors:
        for first, second in edges:
            law = v8h.beam_law(
                beam_shape,
                math.dist(coords[first], coords[second]),
                20.0,
                connection_factor,
                int(inputs["config"]["model_cases"]["active_planes_per_floor"]),
                fy_params,
                e_params,
            )
            key = (floor, *tuple(sorted((first, second))))
            springs.append(
                {
                    "kind": "beam",
                    "floor": floor,
                    "edge": [first, second],
                    "a": (floor, first),
                    "b": (floor, second),
                    "stiffness": float(law["initial_stiffness_kip_per_in"]),
                    "capacity": float(law["yield_force_kip"]),
                    "yield_displacement": float(law["yield_displacement_in"]),
                    "ultimate_displacement": float(law["ultimate_displacement_in"]),
                    "state": "fractured" if key in prefractured_beams else "elastic",
                    "sign": 0.0,
                    "initial_damage": key in prefractured_beams,
                }
            )
    metadata = {
        "column_spring_count": sum(row["kind"] == "column" for row in springs),
        "beam_spring_count": sum(row["kind"] == "beam" for row in springs),
        "initial_removed_column_segments": sum(
            row["kind"] == "column" and row["initial_damage"] for row in springs
        ),
        "initial_removed_beam_edges": sum(
            row["kind"] == "beam" and row["initial_damage"] for row in springs
        ),
    }
    return springs, metadata


def connected_to_ground(
    nodes: list[tuple[int, int]],
    loads: np.ndarray,
    load_factor: float,
    springs: list[dict[str, object]],
) -> str | None:
    adjacency = {node: set() for node in [*nodes, GROUND]}
    for spring in springs:
        if spring["state"] == "fractured":
            continue
        a, b = spring["a"], spring["b"]
        adjacency[a].add(b)
        adjacency[b].add(a)
    index = {node: position for position, node in enumerate(nodes)}
    seen = {GROUND}
    stack = [GROUND]
    while stack:
        current = stack.pop()
        for neighbor in adjacency[current]:
            if neighbor not in seen:
                seen.add(neighbor)
                stack.append(neighbor)
    scale = max(float(np.sum(np.abs(loads))) * load_factor, 1.0)
    floating_load = sum(
        load_factor * float(loads[index[node]]) for node in nodes if node not in seen
    )
    if abs(floating_load) > 1e-9 * scale:
        return "disconnected_loaded_component"
    return None


def failure_diagnostics(
    nodes: list[tuple[int, int]],
    loads: np.ndarray,
    load_factor: float,
    springs: list[dict[str, object]],
) -> dict[str, object]:
    adjacency = {node: set() for node in [*nodes, GROUND]}
    for spring in springs:
        if spring["state"] == "fractured":
            continue
        a, b = spring["a"], spring["b"]
        adjacency[a].add(b)
        adjacency[b].add(a)
    index = {node: position for position, node in enumerate(nodes)}
    unseen = set(nodes)
    components: list[dict[str, object]] = []
    while unseen:
        start = unseen.pop()
        component = {start}
        stack = [start]
        while stack:
            current = stack.pop()
            for neighbor in adjacency[current]:
                if neighbor == GROUND or neighbor not in unseen:
                    continue
                unseen.remove(neighbor)
                component.add(neighbor)
                stack.append(neighbor)
        touches_ground = any(GROUND in adjacency[node] for node in component)
        component_load = load_factor * sum(
            float(loads[index[node]]) for node in component
        )
        if not touches_ground and abs(component_load) > 1e-6:
            components.append(
                {
                    "nodes": [[floor, column] for floor, column in sorted(component)],
                    "load_kip": component_load,
                }
            )
    return {
        "loaded_disconnected_components": components[:8],
        "additional_fractured_beam_count": sum(
            spring["kind"] == "beam"
            and spring["state"] == "fractured"
            and not spring["initial_damage"]
            for spring in springs
        ),
        "initially_removed_beam_count": sum(
            spring["kind"] == "beam" and spring["initial_damage"]
            for spring in springs
        ),
        "additional_failed_column_count": sum(
            spring["kind"] == "column"
            and spring["state"] == "fractured"
            and not spring["initial_damage"]
            for spring in springs
        ),
    }


def assemble(
    nodes: list[tuple[int, int]],
    loads: np.ndarray,
    load_factor: float,
    springs: list[dict[str, object]],
) -> tuple[np.ndarray | None, str | None]:
    reason = connected_to_ground(nodes, loads, load_factor, springs)
    if reason:
        return None, reason
    index = {node: position for position, node in enumerate(nodes)}
    matrix = np.zeros((len(nodes), len(nodes)), dtype=float)
    rhs = load_factor * loads.copy()
    for spring in springs:
        if spring["state"] == "fractured":
            continue
        a, b = spring["a"], spring["b"]
        ia = index[a]
        stiffness = float(spring["stiffness"])
        constant = 0.0
        tangent = stiffness
        if spring["kind"] == "beam" and spring["state"] == "plastic":
            tangent = v8h.HARDENING_RATIO * stiffness
            constant = float(spring["sign"]) * (
                float(spring["capacity"])
                - tangent * float(spring["yield_displacement"])
            )
        matrix[ia, ia] += tangent
        rhs[ia] -= constant
        if b != GROUND:
            ib = index[b]
            matrix[ib, ib] += tangent
            matrix[ia, ib] -= tangent
            matrix[ib, ia] -= tangent
            rhs[ib] += constant
    try:
        displacement = np.linalg.solve(matrix, rhs)
    except np.linalg.LinAlgError:
        return None, "singular_multistory_network"
    if not np.all(np.isfinite(displacement)):
        return None, "non_finite_displacement"
    return displacement, None


def spring_force(
    spring: dict[str, object],
    displacement: np.ndarray,
    index: dict[tuple[int, int], int],
) -> tuple[float, float]:
    a, b = spring["a"], spring["b"]
    delta = float(displacement[index[a]])
    if b != GROUND:
        delta -= float(displacement[index[b]])
    if spring["state"] == "fractured":
        return delta, 0.0
    if spring["kind"] == "beam" and spring["state"] == "plastic":
        tangent = v8h.HARDENING_RATIO * float(spring["stiffness"])
        force = tangent * delta + float(spring["sign"]) * (
            float(spring["capacity"])
            - tangent * float(spring["yield_displacement"])
        )
    else:
        force = float(spring["stiffness"]) * delta
    return delta, force


def solve_case(
    inputs: dict[str, object],
    floor_data: dict[int, dict[str, object]],
    coords: dict[int, tuple[float, float]],
    edges: list[tuple[int, int]],
    profile: str,
    connection_factor: float,
    damage_case: str,
    demand_kip: float,
) -> dict[str, object]:
    floors = [int(value) for value in inputs["config"]["model_cases"]["floors"]]
    columns = sorted(coords)
    nodes = [(floor, column) for floor in floors for column in columns]
    index = {node: position for position, node in enumerate(nodes)}
    top_loads = v8b.initial_loads(
        demand_kip,
        floor_data[max(floors)]["sections"],
        {},
        "capacity_proportional",
    )
    loads = np.zeros(len(nodes), dtype=float)
    for column, value in top_loads.items():
        loads[index[(max(floors), int(column))]] = float(value)
    springs, metadata = make_springs(
        inputs,
        floor_data,
        coords,
        edges,
        profile,
        connection_factor,
        damage_case,
    )
    displacement: np.ndarray | None = None
    added_column_failures: list[tuple[int, int]] = []
    for load_factor in np.linspace(
        1.0 / int(inputs["config"]["model_cases"]["load_steps"]),
        1.0,
        int(inputs["config"]["model_cases"]["load_steps"]),
    ):
        for _ in range(
            int(inputs["config"]["model_cases"]["maximum_active_set_iterations"])
        ):
            displacement, reason = assemble(nodes, loads, float(load_factor), springs)
            if displacement is None:
                step = 1.0 / int(inputs["config"]["model_cases"]["load_steps"])
                return {
                    "equilibrium": False,
                    "reason": reason,
                    "metadata": metadata,
                    "added_column_failures": [list(value) for value in added_column_failures],
                    "final_load_factor": float(load_factor),
                    "maximum_stable_load_factor": max(0.0, float(load_factor) - step),
                    **failure_diagnostics(nodes, loads, float(load_factor), springs),
                }
            changed = False
            for spring in springs:
                if spring["state"] == "fractured":
                    continue
                delta, force = spring_force(spring, displacement, index)
                if spring["kind"] == "column":
                    if force > float(spring["capacity"]) * (1.0 + 1e-8):
                        spring["state"] = "fractured"
                        added_column_failures.append(
                            (int(spring["floor"]), int(spring["column"]))
                        )
                        changed = True
                else:
                    if spring["state"] == "elastic" and abs(delta) > float(
                        spring["yield_displacement"]
                    ) * (1.0 + 1e-8):
                        spring["state"] = "plastic"
                        spring["sign"] = 1.0 if delta >= 0.0 else -1.0
                        changed = True
                    if spring["state"] == "plastic" and abs(delta) > float(
                        spring["ultimate_displacement"]
                    ):
                        spring["state"] = "fractured"
                        changed = True
            if not changed:
                break
        else:
            return {
                "equilibrium": False,
                "reason": "multistory_active_set_not_converged",
                "metadata": metadata,
                "added_column_failures": [list(value) for value in added_column_failures],
                "final_load_factor": float(load_factor),
                "maximum_stable_load_factor": max(
                    0.0,
                    float(load_factor)
                    - 1.0 / int(inputs["config"]["model_cases"]["load_steps"]),
                ),
                **failure_diagnostics(nodes, loads, float(load_factor), springs),
            }

    assert displacement is not None
    ground_reactions: dict[int, float] = {}
    column_rows: list[dict[str, object]] = []
    beam_rows: list[dict[str, object]] = []
    for spring in springs:
        delta, force = spring_force(spring, displacement, index)
        if spring["kind"] == "column":
            row = {
                "floor": int(spring["floor"]),
                "column": int(spring["column"]),
                "state": spring["state"],
                "force_kip": force,
                "capacity_kip": float(spring["capacity"]),
                "dcr_compression": max(force, 0.0) / float(spring["capacity"]),
                "relative_displacement_in": delta,
                "initial_damage": bool(spring["initial_damage"]),
            }
            column_rows.append(row)
            if spring["b"] == GROUND:
                ground_reactions[int(spring["column"])] = force
        else:
            beam_rows.append(
                {
                    "floor": int(spring["floor"]),
                    "edge": spring["edge"],
                    "state": spring["state"],
                    "force_kip": force,
                    "capacity_kip": float(spring["capacity"]),
                    "relative_displacement_in": delta,
                    "initial_damage": bool(spring["initial_damage"]),
                }
            )
    reaction_total = sum(ground_reactions.values())
    residual = abs(reaction_total - demand_kip) / demand_kip
    return {
        "equilibrium": residual < 1e-6,
        "reason": "stable" if residual < 1e-6 else "force_residual",
        "metadata": metadata,
        "final_load_factor": 1.0,
        "maximum_stable_load_factor": 1.0,
        "ground_reaction_total_kip": reaction_total,
        "relative_force_residual": residual,
        "maximum_abs_displacement_in": float(np.max(np.abs(displacement))),
        "maximum_column_dcr": max(
            (float(row["dcr_compression"]) for row in column_rows), default=0.0
        ),
        "maximum_beam_force_kip": max(
            (abs(float(row["force_kip"])) for row in beam_rows), default=0.0
        ),
        "plastic_beam_count": sum(row["state"] == "plastic" for row in beam_rows),
        "fractured_beam_count": sum(row["state"] == "fractured" for row in beam_rows),
        "added_column_failures": [list(value) for value in added_column_failures],
        "ground_reactions_kip": {str(key): value for key, value in ground_reactions.items()},
        "critical_columns": sorted(
            column_rows,
            key=lambda row: float(row["dcr_compression"]),
            reverse=True,
        )[:12],
        "critical_beams": sorted(
            beam_rows,
            key=lambda row: abs(float(row["force_kip"])),
            reverse=True,
        )[:12],
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


def render_plot(payload: dict[str, object]) -> None:
    canvas = Image.new("RGB", (1900, 1120), "white")
    draw = ImageDraw.Draw(canvas)
    navy = (31, 43, 61)
    red = (190, 57, 57)
    green = (50, 145, 90)
    amber = (222, 148, 50)
    grey = (225, 228, 233)
    draw.text(
        (950, 48),
        "WTC 1 V8L - redistribution froide multi-etages 94-99",
        anchor="mm",
        font=font(36, True),
        fill=navy,
    )

    # Left panel: Case B vertical segment map for the four V8K nodes.
    x0, y0, w, h = 90, 150, 690, 760
    draw.text((x0 + w / 2, y0 - 35), "Segments Case B", anchor="mm", font=font(27, True), fill=navy)
    columns = [503, 504, 505, 604]
    floors = [99, 98, 97, 96, 95, 94, 93]
    removed = payload["case_b_removed_segments"]
    for fi, floor in enumerate(floors):
        y = y0 + 60 + fi * 95
        draw.text((x0 + 35, y), str(floor), anchor="rm", font=font(20, True), fill=navy)
        draw.line((x0 + 55, y, x0 + w - 25, y), fill=grey, width=2)
    for ci, column in enumerate(columns):
        x = x0 + 140 + ci * 135
        draw.text((x, y0 + 18), str(column), anchor="mm", font=font(22, True), fill=navy)
        for floor in floors[:-1]:
            y_top = y0 + 60 + floors.index(floor) * 95
            y_bottom = y_top + 95
            is_removed = column in removed[str(floor)]
            draw.line((x, y_top + 5, x, y_bottom - 5), fill=red if is_removed else green, width=11)
    draw.text((x0 + 110, y0 + h - 24), "vert : segment survivant", font=font(18, True), fill=green)
    draw.text((x0 + 390, y0 + h - 24), "rouge : retire", font=font(18, True), fill=red)

    # Right panel: pass matrix at full demand.
    rx, ry, rw, rh = 845, 150, 965, 760
    draw.text((rx + rw / 2, ry - 35), "Equilibre a 34 429 kip", anchor="mm", font=font(27, True), fill=navy)
    rows = payload["case_rows"]
    grouped: dict[str, list[dict[str, object]]] = {}
    for row in rows:
        key = f"{row['topology']} | {row['beam_damage_case']}"
        grouped.setdefault(key, []).append(row)
    labels = list(grouped)
    profiles = ["12WF65 x0.5", "12WF65 x1.0", "14WF136 x0.5", "14WF136 x1.0", "14WF228 x0.5", "14WF228 x1.0"]
    label_w = 420
    cell_w = (rw - label_w) / len(profiles)
    cell_h = rh / len(labels)
    for index, label in enumerate(labels):
        cy = ry + (index + 0.5) * cell_h
        short = label.replace("orthogonal_floor96_reconstruction", "orthogonal").replace("nist_moment_only", "moment NIST").replace("no_beam_damage_upper_bound", "sans dommage poutres").replace("floor96_figure_damage", "dommage F96").replace("repeat_floor96_damage_floors94_98", "dommage repete 94-98")
        draw.text((rx + label_w - 15, cy), short, anchor="rm", font=font(15, True), fill=navy)
        case_lookup = {(row["beam_profile"], float(row["connection_factor"])): row for row in grouped[label]}
        for pi, profile_label in enumerate(profiles):
            profile, factor = profile_label.split(" x")
            row = case_lookup[(profile, float(factor))]
            x1 = rx + label_w + pi * cell_w
            color = green if row["equilibrium"] else red
            draw.rounded_rectangle((x1 + 4, cy - cell_h * 0.34, x1 + cell_w - 4, cy + cell_h * 0.34), radius=8, fill=color)
            draw.text((x1 + cell_w / 2, cy), "OK" if row["equilibrium"] else f"{100*float(row['maximum_stable_load_factor']):.0f}%", anchor="mm", font=font(16, True), fill="white")
    for pi, profile in enumerate(profiles):
        x = rx + label_w + (pi + 0.5) * cell_w
        draw.text((x, ry + rh + 28), profile.replace(" x", "\nx"), anchor="ma", font=font(15, True), fill=navy, spacing=2)

    summary = payload["summary"]
    fill = (226, 242, 232) if summary["any_official_topology_pass"] else (249, 229, 229)
    color = green if summary["any_official_topology_pass"] else red
    draw.rounded_rectangle((90, 985, 1810, 1070), radius=18, fill=fill)
    draw.text((950, 1012), summary["gate_label"], anchor="mm", font=font(29, True), fill=color)
    draw.text((950, 1048), summary["gate_explanation"], anchor="mm", font=font(19, True), fill=navy)
    canvas.save(OUT_PNG)


def write_report(payload: dict[str, object]) -> None:
    summary = payload["summary"]
    best = summary["best_reconstructed_case"]
    stable_load_kip = (
        float(summary["best_reconstructed_maximum_stable_load_factor"])
        * float(payload["post_impact_core_demand_kip"])
    )
    disconnected_load_kip = sum(
        float(component["load_kip"])
        for component in best["loaded_disconnected_components"]
    )
    stable_load_label = f"{stable_load_kip:,.0f}".replace(",", " ")
    disconnected_load_label = f"{disconnected_load_kip:,.0f}".replace(",", " ")
    rows = [
        "# WTC 1 - V8L : redistribution froide multi-etages 94-99",
        "",
        "## Resultat principal",
        "",
        summary["report_conclusion"],
        "",
        (
            "Le cas reconstruit le plus resistant (aucun dommage initial de poutre, "
            f"14WF228, facteur d'assemblage 1,0) reste stable jusqu'a "
            f"{summary['best_reconstructed_maximum_stable_load_factor']:.0%}, soit "
            f"environ {stable_load_label} kip sur les 34 429 kip demandes, puis "
            f"perd un composant encore charge a {best['failure_load_factor']:.0%}. "
            f"A ce pas, {best['additional_fractured_beam_count']} poutres et "
            f"{best['additional_failed_column_count']} segments de poteaux additionnels "
            f"ont atteint leurs criteres; le composant deconnecte porte "
            f"{disconnected_load_label} kip. La resolution de charge est de 1 point "
            "de pourcentage; 78 % est un seuil numerique de ce modele, pas une "
            "probabilite de l'evenement reel."
        ),
        "",
        "La V8L corrige une faiblesse structurelle de V8J/V8K : une charge arrivant sur un poteau coupe au niveau 96 peut maintenant se redistribuer par les poutres du niveau 97 avant d'atteindre la coupure. Les six niveaux sont resolus simultanement; les segments Case B 94-96 sont absents des le debut et les nouvelles surcharges peuvent provoquer plastification des poutres ou perte de segments voisins.",
        "",
        "## Faits et resultats officiels",
        "",
        "- La Figure 2-17 de NIST fournit les segments du noyau severes ou lourdement endommages en Case B.",
        "- Le noyau isole NIST comprenait poteaux, poutres et dalles des niveaux 89-106. Le cas structurel B ne convergait pas, meme avec appuis lateraux; ce sous-modele ne comprenait ni transfert par les planchers vers les facades ni hat truss.",
        "- Dans le modele global, seules les poutres du noyau a assemblage rigide etaient explicites. La rigidite axiale des autres poutres etait integree a la dalle equivalente, dont NIST dit qu'elle redistribuait localement les charges entre poteaux voisins.",
        "- Le modele global stable rapporte environ +1 % de charge totale du noyau apres impact, avec redistribution surtout vers les poteaux voisins; 705 flambait et 605/804 montraient un flambement mineur.",
        "",
        "## Resultats des enveloppes",
        "",
        "| Topologie | Dommage poutres | Profil | Facteur assemblage | Equilibre | Facteur de charge atteint | Deplacement max | DCR poteau max |",
        "|---|---|---|---:|---|---:|---:|---:|",
    ]
    for row in payload["case_rows"]:
        rows.append(
            "| {topology} | {damage} | {profile} | {factor:.1f} | {status} | {load:.1%} | {disp} | {dcr} |".format(
                topology=row["topology"],
                damage=row["beam_damage_case"],
                profile=row["beam_profile"],
                factor=float(row["connection_factor"]),
                status="oui" if row["equilibrium"] else "non",
                load=float(row["maximum_stable_load_factor"]),
                disp=(f"{float(row['maximum_abs_displacement_in']):.3f} in" if row.get("maximum_abs_displacement_in") is not None else "n/a"),
                dcr=(f"{float(row['maximum_column_dcr']):.3f}" if row.get("maximum_column_dcr") is not None else "n/a"),
            )
        )
    rows.extend(
        [
            "",
            "## Hypotheses propres a V8L",
            "",
            "- Les charges sont appliquees au niveau 99 proportionnellement aux capacites froides V8B; NIST ne publie pas ici les 47 charges nodales exactes reutilisables.",
            "- Le reseau `nist_moment_only` reprend les 17 liaisons a assemblage rigide deja transcrites en V8H. Son absence de liaisons dans la rangee 500 est une propriete du sous-reseau explicite, pas la preuve d'une absence de plancher.",
            "- Le reseau orthogonal relie les voisins de rangee et les memes terminaisons entre rangees, sans diagonales nearest-four. Il represente une enveloppe poutres+dalle omise, pas un plan as-built.",
            "- Les profils 12WF65, 14WF136 et 14WF228 et les facteurs d'assemblage 0,5/1,0 sont des bornes. Les vrais Books 5/6 restent manquants.",
            "- Les poteaux sont des ressorts axiaux scalaires; la flexion biaxiale, les rotations de noeuds, P-delta, la fissuration de dalle et la dynamique ne sont pas resolus.",
            "",
            "## Contradictions et incertitudes",
            "",
            "- Un echec du reseau moment-only est coherent avec le non-convergence du noyau isole Case B de NIST; il ne contredit pas le modele global, qui contient les facades, planchers de bureau et le hat truss.",
            "- Un passage du reseau orthogonal montrerait seulement qu'un chemin composite suffisamment rigide peut fermer le cut-set. Sans module equivalent de dalle, sections et assemblages publies, ce serait une possibilite de modele, pas une validation independante.",
            "- Le dommage de poutres raffine Case B etage par etage n'est pas disponible. Les trois cartes testees encadrent cette lacune mais ne la resolvent pas.",
            "",
            "## Decision du gate",
            "",
            summary["gate_decision"],
            "",
            f"Temps d'execution : {payload['runtime_seconds']:.2f} s. Les 36 cas, les retraits de segments et les sorties critiques sont conserves dans le JSON V8L.",
        ]
    )
    OUT_REPORT.write_text("\n".join(rows) + "\n", encoding="utf-8")


def main() -> None:
    started = time.perf_counter()
    inputs = load_inputs()
    floor_data, coords = prepared(inputs)
    topologies = topology_edges(inputs)
    config_cases = inputs["config"]["model_cases"]
    rows: list[dict[str, object]] = []
    for topology_name in config_cases["topologies"]:
        for damage_case in config_cases["beam_damage_cases"]:
            for profile in config_cases["beam_profiles"]:
                for connection_factor in config_cases["connection_factors"]:
                    result = solve_case(
                        inputs,
                        floor_data,
                        coords,
                        topologies[topology_name],
                        str(profile),
                        float(connection_factor),
                        str(damage_case),
                        float(config_cases["post_impact_core_demand_kip"]),
                    )
                    rows.append(
                        {
                            "topology": topology_name,
                            "beam_damage_case": damage_case,
                            "beam_profile": profile,
                            "connection_factor": float(connection_factor),
                            **result,
                        }
                    )

    official_rows = [row for row in rows if row["topology"] == "nist_moment_only"]
    reconstructed_rows = [
        row for row in rows if row["topology"] == "orthogonal_floor96_reconstruction"
    ]
    any_official = any(bool(row["equilibrium"]) for row in official_rows)
    any_reconstructed = any(bool(row["equilibrium"]) for row in reconstructed_rows)
    best_official = max(
        official_rows, key=lambda row: float(row["maximum_stable_load_factor"])
    )
    best_reconstructed = max(
        reconstructed_rows,
        key=lambda row: float(row["maximum_stable_load_factor"]),
    )
    if any_official:
        gate_label = "GATE FROID PARTIEL : topologie officielle explicite stable"
        gate_explanation = "Une verification as-built des sections et assemblages reste necessaire avant la thermique."
        report_conclusion = "Au moins un cas du reseau moment-connected explicite atteint la demande froide. Ce resultat doit encore etre verifie avec les sections et assemblages as-built avant de valider le gate."
        gate_decision = "**PARTIELLEMENT FRANCHI.** Une topologie officiellement explicite ferme le chemin, mais les affectations de sections et d'assemblages restent des proxies; la thermique reste suspendue."
    elif any_reconstructed:
        gate_label = "GATE FROID NON VALIDE : seule l'enveloppe reconstruite passe"
        gate_explanation = "Le noyau moment-only echoue; le chemin composite manquant doit etre source ou couple au perimetre."
        report_conclusion = "Aucun cas du sous-reseau NIST des poutres a assemblage rigide n'atteint la demande froide. Des cas de l'enveloppe orthogonale reconstruite y parviennent, ce qui montre qu'une redistribution multi-etages composite peut fermer le cut-set, sans prouver que les sections, assemblages et dommages reels fournissaient ce chemin."
        gate_decision = "**NON VALIDE.** La fermeture du cut-set depend d'une enveloppe reconstruite. La prochaine iteration doit introduire le chemin core-plancher de bureau-facade ou recuperer le module equivalent et les Books 5/6; aucune thermique/Blender dynamique n'est autorisee."
    else:
        gate_label = "GATE FROID NON VALIDE : noyau multi-etages insuffisant"
        gate_explanation = "Comme le noyau isole Case B de NIST, toutes les enveloppes perdent l'equilibre."
        report_conclusion = "Les deux topologies multi-etages perdent l'equilibre avant la demande froide complete. Ce resultat est qualitativement coherent avec la non-convergence du noyau isole Case B de NIST et indique que le prochain chemin a introduire est le couplage vers les facades et le hat truss, pas une resistance locale arbitrairement augmentee."
        gate_decision = "**NON VALIDE.** Le noyau reduit multi-etages ne suffit pas. La prochaine iteration doit ajouter les planchers de bureau, facades et/ou le hat truss froid avant toute thermique ou Blender dynamique."

    runtime_seconds = time.perf_counter() - started
    payload = {
        "model": "WTC1_V8L_MULTISTORY_COLD_FRAME",
        "version": "8.11.0",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "runtime_seconds": runtime_seconds,
        "configuration_file": str(CONFIG.relative_to(ROOT)).replace("\\", "/"),
        "facts_transferred": inputs["config"]["official_facts"],
        "model_assumptions": inputs["config"]["mechanical_laws"],
        "gate_definition": inputs["config"]["gate"],
        "post_impact_core_demand_kip": float(
            config_cases["post_impact_core_demand_kip"]
        ),
        "topology_summary": {
            name: {
                "edge_count_per_floor": len(edges),
                "connected_column_count": len({node for edge in edges for node in edge}),
            }
            for name, edges in topologies.items()
        },
        "case_b_removed_segments": {
            str(floor): sorted(floor_data[floor]["removed"])
            for floor in sorted(floor_data, reverse=True)
        },
        "case_rows": rows,
        "summary": {
            "case_count": len(rows),
            "official_topology_pass_count": sum(bool(row["equilibrium"]) for row in official_rows),
            "reconstructed_topology_pass_count": sum(bool(row["equilibrium"]) for row in reconstructed_rows),
            "any_official_topology_pass": any_official,
            "any_reconstructed_topology_pass": any_reconstructed,
            "best_official_maximum_stable_load_factor": float(
                best_official["maximum_stable_load_factor"]
            ),
            "best_reconstructed_maximum_stable_load_factor": float(
                best_reconstructed["maximum_stable_load_factor"]
            ),
            "best_reconstructed_case": {
                "beam_damage_case": best_reconstructed["beam_damage_case"],
                "beam_profile": best_reconstructed["beam_profile"],
                "connection_factor": best_reconstructed["connection_factor"],
                "reason": best_reconstructed["reason"],
                "failure_load_factor": best_reconstructed["final_load_factor"],
                "additional_fractured_beam_count": best_reconstructed.get(
                    "additional_fractured_beam_count", 0
                ),
                "additional_failed_column_count": best_reconstructed.get(
                    "additional_failed_column_count", 0
                ),
                "loaded_disconnected_components": best_reconstructed.get(
                    "loaded_disconnected_components", []
                ),
            },
            "gate_label": gate_label,
            "gate_explanation": gate_explanation,
            "report_conclusion": report_conclusion,
            "gate_decision": gate_decision,
            "thermal_runs_authorized": False,
            "blender_coupling_authorized": False,
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
                "official_passes": payload["summary"]["official_topology_pass_count"],
                "reconstructed_passes": payload["summary"]["reconstructed_topology_pass_count"],
                "runtime_seconds": runtime_seconds,
                "outputs": [str(OUT_JSON), str(OUT_REPORT), str(OUT_PNG)],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
