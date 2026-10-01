"""Generate and run immutable IMPACT-I02H locally refined M(T) coupons."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import subprocess
import time
from pathlib import Path

import run_impact_i02g as i02g


ROOT = Path(__file__).resolve().parents[2]
CFG = ROOT / "wtc1_simulation_v8/data/impact_i02h_local_cohesive.json"
RUNTIME = ROOT / "wtc1_simulation_v8/openradioss_runtime/v20260728-win64"
OUTPUT = ROOT / "wtc1_simulation_v8/output/impact_i02h_local_cohesive"


def dump(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def subdivide(start: float, stop: float, target_step: float) -> list[float]:
    count = max(1, round((stop - start) / target_step))
    return [start + (stop - start) * index / count for index in range(count + 1)]


def join_segments(segments: list[list[float]]) -> list[float]:
    values: list[float] = []
    for segment in segments:
        if values and math.isclose(values[-1], segment[0], rel_tol=0, abs_tol=1.0e-12):
            values.extend(segment[1:])
        else:
            values.extend(segment)
    return values


def clipped_tributary_width(xs: list[float], index: int, width: float, crack_half: float) -> float:
    x = xs[index]
    left = -width / 2.0 if index == 0 else 0.5 * (xs[index - 1] + x)
    right = width / 2.0 if index == len(xs) - 1 else 0.5 * (x + xs[index + 1])
    intact = ((-width / 2.0, -crack_half), (crack_half, width / 2.0))
    return sum(max(0.0, min(right, stop) - max(left, start)) for start, stop in intact)


def tabulated_material_lines(material: dict) -> list[str]:
    lines = [
        "/MAT/PLAS_TAB/1",
        "AA2024_T3_NASA_LT_LAW36_FRESH_STATE",
        i02g.ff(material["density_g_per_mm3"], 0),
        i02g.ff(material["young_modulus_mpa"], material["poisson_ratio"], 0, 0, 0),
        f"{1:10d}{0:10d}{0:20g}{0:20g}{0:20g}{'':10s}{0:10d}",
        f"{0:10d}{0:20g}{0:10d}{0:20g}{0:20g}",
        i02g.ii(200),
        i02g.ff(1),
        i02g.ff(0),
        "/FUNCT/200",
        "NASA_2024_T3_TRUE_STRESS_PLASTIC_STRAIN",
    ]
    lines += [i02g.ff(strain, stress) for strain, stress in zip(material["law36_plastic_true_strain"], material["law36_true_stress_mpa"])]
    return lines


def generate(cfg: dict, case: dict, directory: Path) -> dict:
    geometry = cfg["geometry"]
    material_variant = case.get("material_variant", "epp_i02g")
    material = cfg["material_tabulated_radioss"] if material_variant == "nasa_law36" else cfg["material_baseline_applied"]
    mesh_cfg = cfg["mesh"]
    seam = cfg["seam"]
    execution = cfg["execution"]
    width = float(geometry["width_mm"])
    length = float(geometry["length_mm"])
    half_length = length / 2.0
    thickness = float(geometry["thickness_mm"])
    crack_half = float(geometry["initial_total_crack_length_mm"]) / 2.0
    local_step = float(case["local_step_mm"])
    outer_break = float(mesh_cfg["outer_x_break_mm"])
    far_step = float(mesh_cfg["far_field_target_step_mm"])
    near_height = float(mesh_cfg["near_seam_half_height_mm"])

    xs = join_segments([
        subdivide(-width / 2.0, -outer_break, far_step),
        subdivide(-outer_break, outer_break, local_step),
        subdivide(outer_break, width / 2.0, far_step),
    ])
    y_positive = join_segments([
        subdivide(0.0, near_height, local_step),
        subdivide(near_height, half_length, far_step),
    ])
    y_lower = [-value for value in reversed(y_positive)]
    y_upper = y_positive

    nodes: list[tuple[float, float, float]] = []
    grids: list[list[list[int]]] = []
    for ys in (y_lower, y_upper):
        grid: list[list[int]] = []
        for y in ys:
            row = []
            for x in xs:
                row.append(len(nodes) + 1)
                nodes.append((x, y, 0.0))
            grid.append(row)
        grids.append(grid)

    shells: list[tuple[int, int, int, int]] = []
    for grid in grids:
        for iy in range(len(grid) - 1):
            for ix in range(len(xs) - 1):
                shells.append((grid[iy][ix], grid[iy][ix + 1], grid[iy + 1][ix + 1], grid[iy + 1][ix]))

    edge_lengths: list[float] = []
    signed_areas: list[float] = []
    for quad in shells:
        points = [nodes[node_id - 1] for node_id in quad]
        edge_lengths.extend(
            math.hypot(points[(index + 1) % 4][0] - points[index][0], points[(index + 1) % 4][1] - points[index][1])
            for index in range(4)
        )
        signed_areas.append(
            0.5
            * sum(
                points[index][0] * points[(index + 1) % 4][1]
                - points[(index + 1) % 4][0] * points[index][1]
                for index in range(4)
            )
        )

    lower_seam = grids[0][-1]
    upper_seam = grids[1][0]
    lower_grip = grids[0][0]
    upper_grip = grids[1][-1]
    all_nodes = list(range(1, len(nodes) + 1))
    anchor_node = min(lower_grip, key=lambda node_id: abs(nodes[node_id - 1][0]))
    seam_pairs: list[dict] = []
    for index, x in enumerate(xs):
        tributary_width = clipped_tributary_width(xs, index, width, crack_half)
        if tributary_width <= 1.0e-12:
            continue
        seam_pairs.append({
            "x_mm": x,
            "side": "left" if x < 0 else "right",
            "lower_node": lower_seam[index],
            "upper_node": upper_seam[index],
            "tributary_width_mm": tributary_width,
        })
    expected_ligament_width = width - 2.0 * crack_half
    if not math.isclose(sum(pair["tributary_width_mm"] for pair in seam_pairs), expected_ligament_width, rel_tol=1.0e-12, abs_tol=1.0e-12):
        raise ValueError("Cohesive tributary widths do not equal the intact ligament width")

    mode = case["mode"]
    non_failing = mode in ("elastic", "no_propagation")
    if mode == "elastic":
        loading_end_ms = float(case.get("loading_end_ms", execution["elastic_end_ms"]))
        target_displacement = float(case.get("target_displacement_mm", execution["elastic_target_displacement_mm"]))
    else:
        loading_end_ms = float(case.get("loading_end_ms", execution["fracture_end_ms"]))
        target_displacement = float(case.get("target_displacement_mm", execution["fracture_target_displacement_mm"]))
    run_end_ms = float(case.get("run_end_ms", loading_end_ms))
    if run_end_ms > loading_end_ms:
        raise ValueError("run_end_ms cannot exceed loading_end_ms")
    gf = case.get("Gf_N_per_mm")
    deltaf = None if gf is None else 2.0 * float(gf) / float(seam["peak_normal_traction_mpa"])
    name = "I02H_" + case["id"]

    lines = [
        "#RADIOSS STARTER",
        "# NASA-size M(T), local crack-tip refinement, prescribed cohesive path; not calibrated 3D tearing",
        "/BEGIN",
        name,
        i02g.ii(2026, 0),
        i02g.ff("g", "mm", "ms"),
        i02g.ff("g", "mm", "ms"),
        "/TITLE",
        name,
        "/ANALY",
        i02g.ii(0, "", 0, 0),
        "/SPMD",
        i02g.ii(0, 0) + i02g.ff(0, 1),
    ]
    lines += tabulated_material_lines(material) if material_variant == "nasa_law36" else i02g.material_lines(material)
    lines += ["/SKEW/FIX/1", "GLOBAL_XY_SEAM_AXES", i02g.ff(0, 0, 0), i02g.ff(0, 1, 0), i02g.ff(0, 0, 1), "/NODE"]
    lines += [i02g.ii(node_id) + i02g.ff(*xyz) for node_id, xyz in enumerate(nodes, 1)]
    lines += ["/PART/1", "AA2024_T3_MIDDLE_CRACK_SHEET", i02g.ii(1, 1, 0), "/SHELL/1"]
    lines += [i02g.ii(element_id, *quad) for element_id, quad in enumerate(shells, 1)]
    lines += i02g.shell_property_lines(thickness)

    shear_modulus = material["young_modulus_mpa"] / (2.0 * (1.0 + material["poisson_ratio"]))
    spring_ids: list[int] = []
    for index, pair in enumerate(seam_pairs):
        property_id = 1000 + index
        element_id = len(shells) + index + 1
        function_x = 3000 + 2 * index
        function_y = function_x + 1
        area = thickness * pair["tributary_width_mm"]
        normal_stiffness = material["young_modulus_mpa"] / local_step * area
        tangent_stiffness = shear_modulus / local_step * area
        peak_force = seam["peak_normal_traction_mpa"] * area
        delta0 = peak_force / normal_stiffness
        i02g.add_spring_property(lines, property_id, function_x, function_y, tangent_stiffness, normal_stiffness, peak_force, delta0, deltaf, non_failing)
        lines += [
            f"/PART/{property_id}",
            f"SEAM_CONNECTION_{index}",
            i02g.ii(property_id, 0, 0),
            f"/SPRING/{property_id}",
            i02g.ii(element_id, pair["lower_node"], pair["upper_node"], 0, 0, 0, 0, "", "", 1),
        ]
        pair.update({
            "element_id": element_id,
            "property_id": property_id,
            "area_mm2": area,
            "normal_stiffness_N_per_mm": normal_stiffness,
            "tangent_stiffness_N_per_mm": tangent_stiffness,
            "peak_force_N": peak_force,
            "delta0_mm": delta0,
            "deltaf_mm": deltaf,
        })
        spring_ids.append(element_id)

    groups = {
        1: ("ALL_SHEET_NODES", all_nodes),
        2: ("LOWER_GRIP", lower_grip),
        3: ("UPPER_GRIP", upper_grip),
        4: ("X_ANCHOR", [anchor_node]),
        5: ("SEAM_NODES", lower_seam + upper_seam),
    }
    for group_id, (title, group_nodes) in groups.items():
        lines += [f"/GRNOD/NODE/{group_id}", title]
        lines += [i02g.ii(*group) for group in i02g.chunks(group_nodes)]
    lines += [
        "/BCS/1", "IN_PLANE_SHELL_MOTION_ONLY", f"{'001':>6}{'111':>4}" + i02g.ii(0, 1),
        "/BCS/2", "FIX_LOWER_GRIP_Y", f"{'010':>6}{'000':>4}" + i02g.ii(0, 2),
        "/BCS/3", "REMOVE_RIGID_X_TRANSLATION", f"{'100':>6}{'000':>4}" + i02g.ii(0, 4),
    ]
    path = []
    for index in range(401):
        u = index / 400.0
        smooth = 3.0 * u * u - 2.0 * u * u * u
        path.append((u * loading_end_ms, smooth * target_displacement))
    lines += ["/FUNCT/90", "SMOOTH_UPPER_GRIP_DISPLACEMENT"]
    lines += [i02g.ff(t, displacement) for t, displacement in path]
    lines += [
        "/IMPDISP/1", "UPPER_GRIP_Y_DISPLACEMENT", i02g.ii(90, "Y", 0, 0, 3, "", 0), i02g.ff(1, 1, 0, 1.0e30),
        "/TH/PART/1", "SHEET_ENERGY_MASS", i02g.ii("IE", "KE", "MASS", "HE"), i02g.ii(1),
        "/TH/SPRING/2", "SEAM_HISTORY", i02g.ii("OFF", "FX", "FY", "LX", "LY", "IE"),
    ]
    lines += [i02g.ii(element_id, "") + f"SEAM_{index}" for index, element_id in enumerate(spring_ids)]
    lines += ["/TH/NODE/3", "UPPER_GRIP_HISTORY", i02g.ii("DY", "VY", "REACY")]
    lines += [i02g.ii(node_id, 0) for node_id in upper_grip]
    lines += ["/TH/NODE/4", "SEAM_NODE_HISTORY", i02g.ii("DX", "DY")]
    lines += [i02g.ii(node_id, 0) for node_id in lower_seam + upper_seam]
    lines += ["/UNIT/1", "I02H_G_MM_MS", i02g.ff("g", "mm", "ms"), "/END"]
    starter = directory / f"{name}_0000.rad"
    starter.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")

    dt_scale = float(case.get("dt_scale", execution["dt_scale"]))
    animation_dt = run_end_ms / (int(execution["animation_states"]) - 1)
    engine = [
        "/ANIM/DT", i02g.ff(0, animation_dt), "/ANIM/VECT/DISP", "/ANIM/VECT/VEL", "/ANIM/ELEM/ENER",
        "/DT", i02g.ff(dt_scale, 0), "/MON/ON", "/PRINT/-100/100", f"/RUN/{name}/1", i02g.ff(run_end_ms),
        "/TFILE/4", i02g.ff(execution["history_dt_ms"]), "/VERS/2026",
    ]
    engine_file = directory / f"{name}_0001.rad"
    engine_file.write_text("\n".join(engine) + "\n", encoding="utf-8", newline="\n")

    expected_mass = width * length * thickness * material["density_g_per_mm3"]
    expected_fracture_energy = None if gf is None else float(gf) * expected_ligament_width * thickness * 0.001
    x_steps = [b - a for a, b in zip(xs[:-1], xs[1:])]
    y_steps = [b - a for a, b in zip(y_positive[:-1], y_positive[1:])]
    metadata = {
        "name": name,
        "case": case,
        "nodes_mm": nodes,
        "shells": [{"id": element_id, "nodes": quad} for element_id, quad in enumerate(shells, 1)],
        "mesh": {
            "nx": len(xs) - 1,
            "ny_half": len(y_positive) - 1,
            "x_coordinates_mm": xs,
            "y_positive_coordinates_mm": y_positive,
            "minimum_x_step_mm": min(x_steps),
            "maximum_x_step_mm": max(x_steps),
            "minimum_y_step_mm": min(y_steps),
            "maximum_y_step_mm": max(y_steps),
            "minimum_edge_mm": min(edge_lengths),
            "maximum_edge_mm": max(edge_lengths),
            "minimum_signed_area_mm2": min(signed_areas),
            "maximum_signed_area_mm2": max(signed_areas),
        },
        "seam_pairs": seam_pairs,
        "lower_seam_nodes": lower_seam,
        "upper_seam_nodes": upper_seam,
        "lower_grip_nodes": lower_grip,
        "upper_grip_nodes": upper_grip,
        "anchor_node": anchor_node,
        "loading_end_ms": loading_end_ms,
        "run_end_ms": run_end_ms,
        "target_displacement_mm": target_displacement,
        "loading_path_ms_mm": path,
        "expected_mass_g": expected_mass,
        "expected_intact_ligament_width_mm": expected_ligament_width,
        "cohesive_tributary_width_sum_mm": sum(pair["tributary_width_mm"] for pair in seam_pairs),
        "expected_full_ligament_fracture_energy_J": expected_fracture_energy,
        "deltaf_mm": deltaf,
        "material_applied": material,
        "material_variant": material_variant,
        "identified_material_curve_not_applied": cfg["identified_material_curve_not_applied"],
        "generator_sha256": sha(Path(__file__)),
        "config_sha256": sha(CFG),
        "source_sha256": {source["path"]: source["sha256"] for source in cfg["sources"] if "path" in source},
    }
    dump(directory / "generation.json", metadata)
    return metadata


def execute(executable: Path, arguments: list[str], directory: Path, environment: dict, log_name: str, timeout: int) -> dict:
    start = time.perf_counter()
    process = subprocess.run([str(executable), *arguments], cwd=directory, env=environment, capture_output=True, timeout=timeout)
    (directory / log_name).write_bytes(process.stdout + process.stderr)
    record = {
        "command": [str(executable), *arguments],
        "returncode": process.returncode,
        "seconds": time.perf_counter() - start,
        "executable_sha256": sha(executable),
    }
    if process.returncode:
        raise RuntimeError(f"{log_name} failed in {directory}")
    return record


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", required=True)
    parser.add_argument("--revision", default="R0")
    parser.add_argument("--generate-only", action="store_true")
    args = parser.parse_args()
    cfg = json.loads(CFG.read_text(encoding="utf-8"))
    case = next(item for item in cfg["cases"] if item["id"] == args.case).copy()
    case["id"] = case["id"].replace("_R0", "_" + args.revision)
    directory = OUTPUT / case["id"]
    if directory.exists():
        raise RuntimeError("Existing case preserved: " + str(directory))
    directory.mkdir(parents=True)
    metadata = generate(cfg, case, directory)
    if args.generate_only:
        print(json.dumps({"case": case["id"], "generated_only": True, "nodes": len(metadata["nodes_mm"]), "shells": len(metadata["shells"]), "seam_springs": len(metadata["seam_pairs"])}))
        return

    environment = os.environ.copy()
    environment.update(
        RAD_CFG_PATH="C:/OpenRadioss/hm_cfg_files",
        RAD_H3D_PATH="C:/OpenRadioss/extlib/h3d/lib/win64",
        OPENRADIOSS_PATH="C:/OpenRadioss",
        OMP_NUM_THREADS=str(cfg["execution"]["threads"]),
        KMP_STACKSIZE="400m",
    )
    records = []
    jobs = [
        ("starter_win64.exe", ["-i", metadata["name"] + "_0000.rad", "-np", "1"], "starter.log"),
        ("engine_win64.exe", ["-i", metadata["name"] + "_0001.rad"], "engine.log"),
        ("th_to_csv_win64.exe", [metadata["name"] + "T01"], "converter.log"),
    ]
    for executable, arguments, log_name in jobs:
        records.append(execute(RUNTIME / executable, arguments, directory, environment, log_name, cfg["execution"]["maximum_case_wall_seconds"]))
        dump(directory / "execution.json", records)
    print(json.dumps({
        "case": case["id"],
        "seconds": sum(record["seconds"] for record in records),
        "nodes": len(metadata["nodes_mm"]),
        "shells": len(metadata["shells"]),
        "seam_springs": len(metadata["seam_pairs"]),
        "minimum_edge_mm": metadata["mesh"]["minimum_edge_mm"],
        "expected_mass_g": metadata["expected_mass_g"],
        "deltaf_mm": metadata["deltaf_mm"],
    }))


if __name__ == "__main__":
    main()
