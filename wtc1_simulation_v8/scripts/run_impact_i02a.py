"""Run the IMPACT-I02A structured wing-section references.

This is an early, non-eroding component model.  It deliberately does not turn
the graphics-only B762 mesh into structure and does not identify real wing
fracture.  Solver units are g, mm, ms and MPa.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import re
import subprocess
import time
from pathlib import Path

from generate_v8v_deformable_projectile import (
    ShellMesh,
    add_facade,
    chunks,
    fixed_fields as ff,
    material_lines,
    type7_lines,
)


ROOT = Path(__file__).resolve().parents[2]
CFG = ROOT / "wtc1_simulation_v8/data/impact_i02a_structured_wing.json"
I01_CFG = ROOT / "wtc1_simulation_v8/data/impact_i01_first_contact.json"

PARTS = {
    1: ("COLUMNS", 1, "column_shell_thickness_mm"),
    2: ("SPANDREL", 1, "spandrel_shell_thickness_mm"),
    3: ("WING_SKINS", 2, "skin_thickness_mm"),
    4: ("WING_SPARS", 3, "spar_thickness_mm"),
    5: ("WING_RIBS", 3, "rib_thickness_mm"),
    6: ("WING_STRINGER_WEBS", 3, "stringer_thickness_mm"),
    7: ("WING_STRINGER_FLANGES", 3, "stringer_thickness_mm"),
}
WING_PART_IDS = (3, 4, 5, 6, 7)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def uniform_coordinates(start: float, stop: float, target: float) -> list[float]:
    count = max(1, math.ceil(abs(stop - start) / target))
    return [start + (stop - start) * i / count for i in range(count + 1)]


def merged_coordinates(base: list[float], extra: list[float]) -> list[float]:
    return sorted({round(value, 6) for value in [*base, *extra]})


def add_grid_xz(mesh: ShellMesh, y: float, xs: list[float], zs: list[float], part: int) -> None:
    nodes = [[mesh.node((x, y, z)) for x in xs] for z in zs]
    for j in range(len(zs) - 1):
        for i in range(len(xs) - 1):
            mesh.shells[part].append((nodes[j][i], nodes[j][i + 1], nodes[j + 1][i + 1], nodes[j + 1][i]))


def add_grid_xy(mesh: ShellMesh, z: float, xs: list[float], ys: list[float], part: int) -> None:
    nodes = [[mesh.node((x, y, z)) for x in xs] for y in ys]
    for j in range(len(ys) - 1):
        for i in range(len(xs) - 1):
            mesh.shells[part].append((nodes[j][i], nodes[j][i + 1], nodes[j + 1][i + 1], nodes[j + 1][i]))


def add_grid_yz(mesh: ShellMesh, x: float, ys: list[float], zs: list[float], part: int) -> None:
    nodes = [[mesh.node((x, y, z)) for y in ys] for z in zs]
    for j in range(len(zs) - 1):
        for i in range(len(ys) - 1):
            mesh.shells[part].append((nodes[j][i], nodes[j][i + 1], nodes[j + 1][i + 1], nodes[j + 1][i]))


def add_structured_wing(mesh: ShellMesh, geometry: dict, target: float) -> dict:
    for part_id in WING_PART_IDS:
        mesh.shells.setdefault(part_id, [])

    half_span = geometry["span_width_mm"] / 2.0
    half_height = geometry["height_mm"] / 2.0
    x0, x1 = -half_span, half_span
    y0 = geometry["center_y_mm"] - half_height
    y1 = geometry["center_y_mm"] + half_height
    z0 = geometry["front_z_mm"]
    z1 = z0 + geometry["chord_length_mm"]

    rib_x = [x0 + (x1 - x0) * i / (geometry["rib_count"] - 1) for i in range(geometry["rib_count"])]
    stringer_z = [z0 + geometry["chord_length_mm"] * (i + 0.5) / geometry["stringers_per_skin"] for i in range(geometry["stringers_per_skin"])]
    flange = geometry["stringer_free_flange_width_mm"]
    web = geometry["stringer_web_height_mm"]

    xs = merged_coordinates(uniform_coordinates(x0, x1, target), rib_x)
    zs = merged_coordinates(
        uniform_coordinates(z0, z1, target),
        [value for z in stringer_z for value in (z - flange, z, z + flange)],
    )
    ys = merged_coordinates(uniform_coordinates(y0, y1, target), [y0 + web, y1 - web])

    add_grid_xz(mesh, y0, xs, zs, 3)
    add_grid_xz(mesh, y1, xs, zs, 3)
    add_grid_xy(mesh, z0, xs, ys, 4)
    add_grid_xy(mesh, z1, xs, ys, 4)
    for x in rib_x:
        add_grid_yz(mesh, x, ys, zs, 5)

    for z in stringer_z:
        add_grid_xy(mesh, z, xs, [y1 - web, y1], 6)
        add_grid_xy(mesh, z, xs, [y0, y0 + web], 6)
        add_grid_xz(mesh, y1 - web, xs, [z, z + flange], 7)
        add_grid_xz(mesh, y0 + web, xs, [z - flange, z], 7)

    return {
        "bounds_mm": {"x": [x0, x1], "y": [y0, y1], "z": [z0, z1]},
        "rib_x_mm": rib_x,
        "stringer_z_mm": stringer_z,
        "grid_counts": {"x": len(xs), "y": len(ys), "z": len(zs)},
        "stringer_interpretation": f"{geometry['stringers_per_skin']} per skin",
    }


def johnson_reference_lines(material_id: int, title: str, material: dict) -> list[str]:
    return [
        f"/MAT/PLAS_JOHNS/{material_id}",
        title,
        ff(material["density_g_per_mm3"], 0),
        f"{material['young_modulus_mpa']:20.12g}{material['poisson_ratio']:20.12g}{1:10d}",
        ff(
            material["yield_strength_mpa"],
            material["hardening_B_mpa"],
            material["hardening_exponent_n"],
            1.0e30,
            0,
        ),
        ff(0, 0.001, 1, 1, 0, 0),
        ff(0, 0, 0, 0),
    ]


def shell_property_lines_clean(property_id: int, title: str, thickness: float) -> list[str]:
    # Stop the last record after Thick.  Empty optional Ashear/Ithick/Iplas fields
    # avoid the unsupported-field warnings retained in the immutable I01 decks.
    return [
        f"/PROP/SHELL/{property_id}",
        title,
        f"{24:10d}{-1:10d}{0:10d}{0:10d}{0:10d}{'':10s}{0.0:20g}",
        ff(0, 0, 0, 0, 0),
        f"{5:10d}{'':10s}{thickness:20.12g}",
    ]


def generate(cfg: dict, case: dict, directory: Path) -> dict:
    i01 = json.loads(I01_CFG.read_text(encoding="utf-8"))
    inherited = json.loads((ROOT / i01["inherited_config"]).read_text(encoding="utf-8"))
    mesh = ShellMesh()
    for part_id in range(1, 8):
        mesh.shells.setdefault(part_id, [])

    fixed = add_facade(mesh, cfg["facade"], case["mesh_mm"])
    facade_node_count = len(mesh.nodes)
    topology = add_structured_wing(mesh, cfg["wing_section"], case["mesh_mm"])
    wing_nodes = set(range(facade_node_count + 1, len(mesh.nodes) + 1))

    name = "I02A_" + case["id"]
    lines = [
        "#RADIOSS STARTER",
        "# Structured wing-section topology; non-eroding reference; not a Boeing fracture result",
        "/BEGIN",
        f"{name:<80}",
        f"{2026:10d}{0:10d}",
        ff("g", "mm", "ms"),
        ff("g", "mm", "ms"),
        "/TITLE",
        name,
        "/ANALY",
        f"{0:10d}{'':10s}{0:10d}{0:10d}",
        "/SPMD",
        f"{0:10d}{0:10d}{0:20d}{1:20d}",
    ]
    lines += material_lines(1, "Representative facade steel from I01; no failure", inherited["facade_material"], 1.0e30)
    lines += johnson_reference_lines(2, "2024-T3 clad-sheet static EPP reference; no failure", cfg["materials"]["skin_2024_t3_clad_reference"])
    lines += johnson_reference_lines(3, "7075-T6 static EPP internal reference; no failure", cfg["materials"]["internal_7075_t6_reference"])
    lines += ["/NODE"]
    for node_id, (x, y, z) in enumerate(mesh.nodes, 1):
        lines.append(f"{node_id:10d}{x:20.12g}{y:20.12g}{z:20.12g}")

    lines += [
        "/BCS/1",
        "FIXED_COLUMN_ENDS",
        f"{'111':>6}{'111':>4}{0:10d}{10:10d}",
        "/GRNOD/NODE/10",
        "FIXED_COLUMN_ENDS",
    ]
    for group in chunks(sorted(fixed)):
        lines.append("".join(f"{value:10d}" for value in group))

    element_id = 1
    element_ranges = {}
    cells = []
    cell_parts = []
    for part_id in range(1, 8):
        title, material_id, _ = PARTS[part_id]
        lines += [f"/PART/{part_id}", title, f"{part_id:10d}{material_id:10d}{0:10d}", f"/SHELL/{part_id}"]
        first = element_id
        for shell in mesh.shells[part_id]:
            lines.append(f"{element_id:10d}" + "".join(f"{node:10d}" for node in shell))
            cells.append([node - 1 for node in shell])
            cell_parts.append(part_id)
            element_id += 1
        element_ranges[str(part_id)] = [first, element_id - 1]

    for part_id in range(1, 8):
        title, _, thickness_key = PARTS[part_id]
        source = cfg["facade"] if part_id < 3 else cfg["wing_section"]
        lines += shell_property_lines_clean(part_id, title + "_PROPERTY", source[thickness_key])

    lines += ["/GRNOD/PART/20", "ALL_WING_SECTION_NODES"]
    for group in chunks(list(WING_PART_IDS)):
        lines.append("".join(f"{value:10d}" for value in group))
    lines += ["/SURF/PART/30", "FACADE_SURFACE", f"{1:10d}{2:10d}"]
    speed = cfg["speed"]["m_per_s"]
    lines += [
        "/INIVEL/TRA/1",
        "WING_SECTION_INITIAL_SPEED",
        f"{0:20.12g}{0:20.12g}{-speed:20.12g}{20:10d}{0:10d}",
        f"{0:20.12g}{0:10d}",
    ]
    if case["contact"]:
        lines += type7_lines(1, "STRUCTURED_WING_TO_FACADE", 20, 30)
        lines += ["/TH/INTER/1", "CONTACT_IMPULSE", f"{'FNZ':>10}", f"{1:10d}"]

    lines += [
        "/TH/PART/2",
        "PART_STATES",
        "".join(f"{value:>10}" for value in ("IE", "KE", "ZMOM", "MASS", "HE", "ERODED", "VZ")),
    ]
    for group in chunks(list(range(1, 8)), 3):
        lines.append("".join(f"{value:10d}" for value in group))
    lines += ["/TH/NODE/3", "FIXED_SUPPORT_REACTIONS", f"{'REACZ':>10}"]
    for node_id in sorted(fixed):
        lines.append(f"{node_id:10d}{0:10d}")
    lines += ["/END"]

    starter = directory / f"{name}_0000.rad"
    starter.write_text("\n".join(lines) + "\n", encoding="utf-8")
    execution = cfg["execution"]
    engine = [
        "/ANIM/DT",
        ff(0, execution["animation_dt_ms"]),
        "/ANIM/SHELL/EPSP/ALL",
        "/ANIM/ELEM/ENER",
        "/ANIM/VECT/VEL",
        "/ANIM/VECT/DISP",
        "/DT",
        ff(case["dt_scale"], 0),
        "/MON/ON",
        "/PRINT/-100/100",
        f"/RUN/{name}/1",
        ff(execution["end_ms"]),
        "/TFILE/4",
        ff(execution["history_dt_ms"]),
        "/VERS/2026",
    ]
    engine_file = directory / f"{name}_0001.rad"
    engine_file.write_text("\n".join(engine) + "\n", encoding="utf-8")

    thickness = {
        1: cfg["facade"]["column_shell_thickness_mm"],
        2: cfg["facade"]["spandrel_shell_thickness_mm"],
        3: cfg["wing_section"]["skin_thickness_mm"],
        4: cfg["wing_section"]["spar_thickness_mm"],
        5: cfg["wing_section"]["rib_thickness_mm"],
        6: cfg["wing_section"]["stringer_thickness_mm"],
        7: cfg["wing_section"]["stringer_thickness_mm"],
    }
    density = {1: inherited["facade_material"]["density_g_per_mm3"], 2: inherited["facade_material"]["density_g_per_mm3"]}
    density.update({3: cfg["materials"]["skin_2024_t3_clad_reference"]["density_g_per_mm3"]})
    density.update({part_id: cfg["materials"]["internal_7075_t6_reference"]["density_g_per_mm3"] for part_id in (4, 5, 6, 7)})
    expected_mass_g = {str(part_id): mesh.part_area(part_id) * thickness[part_id] * density[part_id] for part_id in range(1, 8)}
    wing_mass_g = sum(expected_mass_g[str(part_id)] for part_id in WING_PART_IDS)
    meta = {
        "name": name,
        "case": case,
        "nodes": len(mesh.nodes),
        "shells": len(cells),
        "shells_by_part": {str(part_id): len(mesh.shells[part_id]) for part_id in range(1, 8)},
        "fixed_nodes": len(fixed),
        "wing_nodes": len(wing_nodes),
        "topology": topology,
        "element_ranges": element_ranges,
        "expected_mass_g_by_part": expected_mass_g,
        "expected_wing_mass_g": wing_mass_g,
        "expected_initial_wing_ke_J": 0.5 * wing_mass_g * speed * speed * 0.001,
        "initial_gap_to_facade_midsurface_mm": cfg["wing_section"]["front_z_mm"],
        "source_sha256": {
            "wtc1_simulation_v8/data/impact_i02a_structured_wing.json": sha256(CFG),
            "wtc1_simulation_v8/data/impact_i01_first_contact.json": sha256(I01_CFG),
            "work/official_sources/ncstar1-2bv1.pdf": sha256(ROOT / "work/official_sources/ncstar1-2bv1.pdf"),
        },
    }
    write_json(directory / "mesh.json", {"nodes_mm": mesh.nodes, "quads": cells, "parts": cell_parts, "fixed_nodes_zero_based": [node - 1 for node in sorted(fixed)]})
    write_json(directory / "generation.json", meta)
    return meta


def execute(executable: Path, arguments: list[str], directory: Path, environment: dict, log_name: str, timeout: int) -> dict:
    start = time.perf_counter()
    with (directory / log_name).open("w", encoding="utf-8") as stream:
        try:
            result = subprocess.run([str(executable), *arguments], cwd=directory, env=environment, stdout=stream, stderr=subprocess.STDOUT, timeout=timeout)
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError("Case exceeded declared wall limit; incomplete") from exc
    if result.returncode:
        raise RuntimeError(f"{log_name} failed, exit {result.returncode}")
    return {"exit_code": result.returncode, "seconds": time.perf_counter() - start, "exe": str(executable), "sha256": sha256(executable), "args": arguments}


def find_column(headers: list[str], title: str, variable: str) -> str:
    hits = [header for header in headers if title in header and re.search(r"\b" + re.escape(variable) + r"\b", header)]
    if len(hits) != 1:
        raise RuntimeError(f"Ambiguous column {title}/{variable}: {hits}")
    return hits[0]


def parse(cfg: dict, case: dict, directory: Path, meta: dict) -> dict:
    name = meta["name"]
    csv_path = directory / f"{name}T01.csv"
    with csv_path.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    if not rows:
        raise RuntimeError("Empty time-history conversion")
    headers = list(rows[0])
    write_json(directory / "history_headers.json", headers)

    titles = {part_id: PARTS[part_id][0] for part_id in range(1, 8)}
    part_columns = {
        part_id: {variable: find_column(headers, title, variable) for variable in ("MASS", "ZMOM", "KE", "IE", "HE", "ERODED", "VZ")}
        for part_id, title in titles.items()
    }
    contact_column = next((header for header in headers if "CONTACT_IMPULSE" in header), None)
    # th_to_csv preserves one column per requested node but labels the binary
    # variable generically.  This group requests REACZ only, so every column
    # bearing the unique group title is a Z-reaction cumulative impulse.
    reaction_columns = [header for header in headers if "FIXED_SUPPORT_REACTIONS" in header]
    first = rows[0]
    initial_energy = float(first["KINETIC ENERGY"]) + float(first["ROTATION ENERGY"]) + float(first["INTERNAL ENERGY"])
    initial_total_pz = float(first["Z-MOMENTUM"])
    initial_contact = float(first[contact_column]) if contact_column else 0.0
    initial_reactions = {column: float(first[column]) for column in reaction_columns}
    initial_wing_pz = sum(float(first[part_columns[part_id]["ZMOM"]]) for part_id in WING_PART_IDS)

    history = []
    for row in rows:
        total_energy = float(row["KINETIC ENERGY"]) + float(row["ROTATION ENERGY"]) + float(row["INTERNAL ENERGY"])
        external_work = float(row["EXTERNAL WORK"])
        contact_impulse = (float(row[contact_column]) - initial_contact) if contact_column else 0.0
        reaction_impulse = sum(float(row[column]) - initial_reactions[column] for column in reaction_columns)
        wing_pz = sum(float(row[part_columns[part_id]["ZMOM"]]) for part_id in WING_PART_IDS)
        wing_mass = sum(float(row[part_columns[part_id]["MASS"]]) for part_id in WING_PART_IDS)
        wing_ke = sum(float(row[part_columns[part_id]["KE"]]) for part_id in WING_PART_IDS)
        wing_ie = sum(float(row[part_columns[part_id]["IE"]]) for part_id in WING_PART_IDS)
        wing_he = sum(float(row[part_columns[part_id]["HE"]]) for part_id in WING_PART_IDS)
        part_he_total = sum(float(row[part_columns[part_id]["HE"]]) for part_id in range(1, 8))
        history.append(
            {
                "t_ms": float(row["time"]),
                "global_ke_J": float(row["KINETIC ENERGY"]) * 0.001,
                "global_ie_J": float(row["INTERNAL ENERGY"]) * 0.001,
                "global_hourglass_J": float(row["HOURGLASS ENERGY"]) * 0.001,
                "global_elastic_contact_J": float(row["ELASTIC CONTACT ENERGY"]) * 0.001,
                "global_added_mass_g": float(row["ADDED MASS"]),
                "energy_error_fraction": (total_energy - initial_energy - external_work) / max(abs(initial_energy), 1.0e-30),
                "total_delta_pz_Ns": (float(row["Z-MOMENTUM"]) - initial_total_pz) * 0.001,
                "wing_delta_pz_Ns": (wing_pz - initial_wing_pz) * 0.001,
                "contact_impulse_Ns": contact_impulse * 0.001,
                "support_reaction_impulse_Ns": reaction_impulse * 0.001,
                "wing_mass_kg": wing_mass * 0.001,
                "wing_ke_J": wing_ke * 0.001,
                "wing_ie_J": wing_ie * 0.001,
                "wing_hourglass_J": wing_he * 0.001,
                "part_hourglass_total_J": part_he_total * 0.001,
            }
        )
    write_json(directory / "history_si.json", history)

    starter_text = (directory / "starter.log").read_text(encoding="utf-8", errors="replace")
    engine_text = (directory / "engine.log").read_text(encoding="utf-8", errors="replace")
    last = history[-1]
    initial_wing_mass_g = sum(float(first[part_columns[part_id]["MASS"]]) for part_id in WING_PART_IDS)
    expected_mass_g = meta["expected_wing_mass_g"]
    initial_ke_J = float(first["KINETIC ENERGY"]) * 0.001
    contact_abs = abs(last["contact_impulse_Ns"])
    wing_dp_abs = abs(last["wing_delta_pz_Ns"])
    reaction_abs = abs(last["support_reaction_impulse_Ns"])
    total_dp_abs = abs(last["total_delta_pz_Ns"])
    warnings = len(re.findall(r"WARNING ID\s*:", starter_text, flags=re.IGNORECASE))
    penetration_counts = [int(value) for value in re.findall(r"THERE ARE\s+(\d+)\s+INITIAL PENETRATIONS", starter_text)]
    eroded = max(sum(float(row[part_columns[part_id]["ERODED"]]) for part_id in WING_PART_IDS) for row in rows)
    wing_speed_final = sum(float(rows[-1][part_columns[part_id]["VZ"]]) * float(rows[-1][part_columns[part_id]["MASS"]]) for part_id in WING_PART_IDS) / max(sum(float(rows[-1][part_columns[part_id]["MASS"]]) for part_id in WING_PART_IDS), 1.0e-30)
    result = {
        "case": case["id"],
        "normal_termination": "NORMAL TERMINATION" in engine_text.upper(),
        "starter_warnings": warnings,
        "history_rows": len(rows),
        "end_ms": last["t_ms"],
        "nodes": meta["nodes"],
        "shells": meta["shells"],
        "shells_by_part": meta["shells_by_part"],
        "fixed_nodes": meta["fixed_nodes"],
        "reaction_history_columns": len(reaction_columns),
        "initial_ke_J": initial_ke_J,
        "expected_initial_wing_ke_J": meta["expected_initial_wing_ke_J"],
        "initial_wing_mass_kg": initial_wing_mass_g * 0.001,
        "expected_wing_mass_kg": expected_mass_g * 0.001,
        "mass_error_fraction": abs(initial_wing_mass_g - expected_mass_g) / expected_mass_g,
        "max_abs_energy_error_fraction": max(abs(item["energy_error_fraction"]) for item in history),
        "max_hourglass_over_initial_ke": max(abs(item["part_hourglass_total_J"]) for item in history) / max(initial_ke_J, 1.0e-30),
        "max_added_mass_fraction": max(abs(item["global_added_mass_g"]) for item in history) / max(sum(float(first[part_columns[part_id]["MASS"]]) for part_id in range(1, 8)), 1.0e-30),
        "final_contact_impulse_abs_Ns": contact_abs,
        "final_wing_momentum_change_abs_Ns": wing_dp_abs,
        "contact_wing_momentum_error_fraction": abs(contact_abs - wing_dp_abs) / max(contact_abs, wing_dp_abs, 1.0),
        "final_support_reaction_impulse_abs_Ns": reaction_abs,
        "final_total_momentum_change_abs_Ns": total_dp_abs,
        "support_total_momentum_error_fraction": abs(reaction_abs - total_dp_abs) / max(reaction_abs, total_dp_abs, 1.0),
        "initial_penetration_counts": penetration_counts,
        "max_wing_eroded_elements": eroded,
        "final_wing_mass_weighted_vz_m_per_s": wing_speed_final,
        "free_flight_speed_error_fraction": abs(wing_speed_final + cfg["speed"]["m_per_s"]) / cfg["speed"]["m_per_s"] if not case["contact"] else None,
        "final": last,
        "raw_time_history_note": "T01 ASCII conversion is treated as cumulative impulse for contact and nodal reaction histories; no engine title was added to request converter differentiation.",
        "scope": "Non-eroding merged-connectivity structured wing-section reference, not a Boeing 767 fracture or WTC1 impact validation.",
    }
    write_json(directory / "results.json", result)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", required=True)
    parser.add_argument("--parse-only", action="store_true")
    args = parser.parse_args()
    cfg = json.loads(CFG.read_text(encoding="utf-8"))
    case = next(item for item in cfg["cases"] if item["id"] == args.case)
    directory = ROOT / cfg["output_root"] / case["id"]
    runtime = ROOT / "wtc1_simulation_v8/openradioss_runtime/v20260728-win64"
    environment = os.environ.copy()
    environment.update(
        {
            "RAD_CFG_PATH": "C:/OpenRadioss/hm_cfg_files",
            "RAD_H3D_PATH": "C:/OpenRadioss/extlib/h3d/lib/win64",
            "OPENRADIOSS_PATH": "C:/OpenRadioss",
            "OMP_NUM_THREADS": str(cfg["execution"]["threads"]),
            "KMP_STACKSIZE": "400m",
        }
    )
    if args.parse_only:
        meta = json.loads((directory / "generation.json").read_text(encoding="utf-8"))
    else:
        if directory.exists():
            raise RuntimeError("Refuse to overwrite an existing case")
        directory.mkdir(parents=True)
        meta = generate(cfg, case, directory)
        runs = []
        jobs = [
            ("starter_win64.exe", ["-i", meta["name"] + "_0000.rad", "-np", "1"], "starter.log"),
            ("engine_win64.exe", ["-i", meta["name"] + "_0001.rad"], "engine.log"),
            ("th_to_csv_win64.exe", [meta["name"] + "T01"], "converter.log"),
        ]
        for executable, arguments, log_name in jobs:
            runs.append(execute(runtime / executable, arguments, directory, environment, log_name, cfg["execution"]["maximum_case_wall_seconds"]))
        write_json(directory / "execution.json", runs)
    print(json.dumps(parse(cfg, case, directory, meta), ensure_ascii=False))


if __name__ == "__main__":
    main()
