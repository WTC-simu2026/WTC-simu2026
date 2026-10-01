"""Generate and run immutable IMPACT-I02F crack-band shell coupon cases."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import subprocess
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CFG = ROOT / "wtc1_simulation_v8/data/impact_i02f_tear_coupon.json"
RUNTIME = ROOT / "wtc1_simulation_v8/openradioss_runtime/v20260728-win64"


def dump(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ff(*values: object) -> str:
    return "".join(f"{value:20.12g}" if isinstance(value, (int, float)) else f"{value:>20}" for value in values)


def ii(*values: object) -> str:
    return "".join(f"{value:10d}" if isinstance(value, int) else f"{value:>10}" for value in values)


def chunks(values: list[int], width: int = 10) -> list[list[int]]:
    return [values[start : start + width] for start in range(0, len(values), width)]


def material_lines(material_id: int, title: str, material: dict) -> list[str]:
    return [
        f"/MAT/PLAS_JOHNS/{material_id}",
        title,
        ff(material["density_g_per_mm3"], 0),
        ff(material["young_modulus_mpa"], material["poisson_ratio"]) + ii(0),
        ff(material["yield_strength_mpa"], 0, 1, 0, 0),
        ff(0, 0, 0, 0, 0, 0),
        ff(0, 0, 0, 0),
    ]


def property_lines(property_id: int, title: str, thickness: float) -> list[str]:
    return [
        f"/PROP/SHELL/{property_id}",
        title,
        f"{24:10d}{-1:10d}{0:10d}{0:10d}{0:10d}{'':10s}{0.0:20g}",
        ff(0, 0, 0, 0, 0),
        f"{5:10d}{'':10s}{thickness:20.12g}",
    ]


def failure_lines(material_id: int, table_id: int, failure_plastic_strain: float) -> list[str]:
    return [
        f"/FAIL/TAB1/{material_id}/1",
        f"{1:10d}{0:10d}{'':20s}{0:20g}{0:20g}{'':10s}{0:10d}",
        ff(0, 0, 0, 0) + ii(0),
        ii(table_id) + ff(1, 1) + ii(0) + ff(0, 0),
        ii(0) + ff(0, 0, 0, 0) + ii(0),
        ii(0) + ff(0),
        f"/TABLE/1/{table_id}",
        "CONSTANT_FAILURE_PLASTIC_STRAIN_CRACK_BAND",
        ii(1),
        ff(-10, failure_plastic_strain),
        ff(10, failure_plastic_strain),
    ]


def generate(cfg: dict, case: dict, directory: Path) -> dict:
    geometry = cfg["geometry"]
    material = cfg["materials"][case["material"]]
    h = float(case["h_mm"])
    width = float(geometry["width_mm"])
    thickness = float(geometry["thickness_mm"])
    length = h
    nx = 1
    ny = round(width / h)
    if not math.isclose(ny * h, width):
        raise ValueError("Coupon dimensions must be integer multiples of h")
    xs = [-length / 2, length / 2]
    ys = [-width / 2 + index * h for index in range(ny + 1)]
    nodes: list[tuple[float, float, float]] = []
    grid: list[list[int]] = []
    for x in xs:
        row = []
        for y in ys:
            row.append(len(nodes) + 1)
            nodes.append((x, y, 0.0))
        grid.append(row)
    shells: list[tuple[int, tuple[int, int, int, int], int]] = []
    band_ix = 0
    band_elements: list[int] = []
    for ix in range(nx):
        for iy in range(ny):
            element_id = len(shells) + 1
            part_id = 2
            quad = (grid[ix][iy], grid[ix + 1][iy], grid[ix + 1][iy + 1], grid[ix][iy + 1])
            shells.append((element_id, quad, part_id))
            if part_id == 2:
                band_elements.append(element_id)
    all_nodes = list(range(1, len(nodes) + 1))
    left_nodes = list(grid[0])
    right_nodes = list(grid[-1])
    anchor_node = grid[0][0]
    name = "I02F_" + case["id"]
    lines = [
        "#RADIOSS STARTER",
        "# Prescribed crack-band energy coupon; not a physical aircraft coupon",
        "/BEGIN",
        name,
        ii(2026, 0),
        ff("g", "mm", "ms"),
        ff("g", "mm", "ms"),
        "/TITLE",
        name,
        "/ANALY",
        ii(0, "", 0, 0),
        "/SPMD",
        ii(0, 0) + ff(0, 1),
    ]
    lines += material_lines(2, case["material"] + "_EPP_LOCAL_BAND", material)
    failure_plastic_strain = None
    target_plastic_work_J = None
    if case["failure"]:
        target_gf = float(case["Gf_N_per_mm"])
        failure_plastic_strain = target_gf / (float(material["yield_strength_mpa"]) * h)
        target_plastic_work_J = target_gf * width * thickness * 0.001
        lines += failure_lines(2, 1001, failure_plastic_strain)
    lines += ["/NODE"]
    lines += [ii(node_id) + ff(*xyz) for node_id, xyz in enumerate(nodes, 1)]
    for group_id, title, group_nodes in [
        (1, "ALL_COUPON_NODES", all_nodes),
        (2, "FIXED_LEFT_EDGE", left_nodes),
        (3, "MOVING_RIGHT_EDGE", right_nodes),
        (4, "TRANSVERSE_ANCHOR", [anchor_node]),
    ]:
        lines += [f"/GRNOD/NODE/{group_id}", title]
        lines += [ii(*group) for group in chunks(group_nodes)]
    lines += [
        "/BCS/1",
        "SHELL_PLANE_AND_ROTATIONS",
        f"{'001':>6}{'111':>4}" + ii(0, 1),
        "/BCS/2",
        "FIXED_LEFT_X",
        f"{'100':>6}{'000':>4}" + ii(0, 2),
        "/BCS/3",
        "REMOVE_RIGID_TRANSVERSE_Y",
        f"{'010':>6}{'000':>4}" + ii(0, 4),
    ]
    part_id = 2
    title = "PRESCRIBED_LOCALIZATION_BAND"
    lines += [f"/PART/{part_id}", title, ii(part_id, part_id, 0), f"/SHELL/{part_id}"]
    lines += [ii(element_id, *quad) for element_id, quad, shell_part in shells]
    lines += property_lines(part_id, title + "_PROPERTY", thickness)
    end_ms = float(cfg["execution"]["end_ms"])
    elastic_yield_extension = h * float(material["yield_strength_mpa"]) / float(material["young_modulus_mpa"])
    if case["failure"]:
        target_displacement = float(cfg["execution"]["post_failure_displacement_factor"]) * (
            elastic_yield_extension + float(case["Gf_N_per_mm"]) / float(material["yield_strength_mpa"])
        )
    else:
        target_displacement = h * (
            float(material["yield_strength_mpa"]) / float(material["young_modulus_mpa"])
            + float(cfg["execution"]["non_eroding_control_plastic_strain"])
        )
    path = []
    for index in range(101):
        u = index / 100
        smooth = 3 * u * u - 2 * u * u * u
        path.append((u * end_ms, smooth * target_displacement))
    lines += ["/FUNCT/90", "SMOOTH_RIGHT_GRIP_DISPLACEMENT"]
    lines += [ff(t, d) for t, d in path]
    lines += [
        "/IMPDISP/1",
        "RIGHT_GRIP_X",
        ii(90, "X", 0, 0, 3, "", 0),
        ff(1, 1, 0, 1.0e30),
        "/TH/PART/2",
        "PRESCRIBED_LOCALIZATION_BAND",
        ii("IE", "KE", "MASS", "HE", "ERODED"),
        ii(2),
        "/TH/NODE/3",
        "BOUNDARY_X_HISTORY",
        ii("DX", "VX", "REACX"),
    ]
    for node_id in left_nodes + right_nodes:
        lines.append(ii(node_id, 0))
    lines += ["/TH/SHEL/4", "LOCALIZATION_BAND_ELEMENT_HISTORY", ii("OFF", "PLAS", "EMAX")]
    lines += [ii(element_id, 0) for element_id in band_elements]
    lines += [
        "/UNIT/1",
        "I02F_G_MM_MS",
        ff("g", "mm", "ms"),
        "/END",
    ]
    starter = directory / f"{name}_0000.rad"
    starter.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    dt_scale = float(case.get("dt_scale", cfg["execution"]["dt_scale"]))
    animation_dt = end_ms / (int(cfg["execution"]["animation_states"]) - 1)
    engine = [
        "/ANIM/DT",
        ff(0, animation_dt),
        "/ANIM/SHELL/EPSP/ALL",
        "/ANIM/SHELL/DAMA",
        "/ANIM/ELEM/ENER",
        "/ANIM/VECT/DISP",
        "/ANIM/VECT/VEL",
        "/DT",
        ff(dt_scale, 0),
        "/MON/ON",
        "/PRINT/-100/100",
        f"/RUN/{name}/1",
        ff(end_ms),
        "/TFILE/4",
        ff(cfg["execution"]["history_dt_ms"]),
        "/VERS/2026",
    ]
    engine_file = directory / f"{name}_0001.rad"
    engine_file.write_text("\n".join(engine) + "\n", encoding="utf-8", newline="\n")
    metadata = {
        "name": name,
        "case": case,
        "nodes_mm": nodes,
        "shells": [{"id": element_id, "nodes": quad, "part": part_id} for element_id, quad, part_id in shells],
        "band_elements": band_elements,
        "all_nodes": all_nodes,
        "left_nodes": left_nodes,
        "right_nodes": right_nodes,
        "mesh": {"nx": nx, "ny": ny, "h_mm": h},
        "material": material,
        "target_displacement_mm": target_displacement,
        "elastic_yield_extension_mm": elastic_yield_extension,
        "failure_plastic_strain": failure_plastic_strain,
        "target_plastic_work_J": target_plastic_work_J,
        "crack_area_mm2": width * thickness,
        "expected_mass_g": length * width * thickness * material["density_g_per_mm3"],
        "loading_path_ms_mm": path,
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
    args = parser.parse_args()
    cfg = json.loads(CFG.read_text(encoding="utf-8"))
    case = next(item for item in cfg["cases"] if item["id"] == args.case).copy()
    case["id"] = case["id"].replace("_R0", "_" + args.revision)
    directory = ROOT / "wtc1_simulation_v8/output/impact_i02f_tear_coupon" / case["id"]
    if directory.exists():
        raise RuntimeError("Existing case preserved: " + str(directory))
    directory.mkdir(parents=True)
    metadata = generate(cfg, case, directory)
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
    print(json.dumps({"case": case["id"], "seconds": sum(record["seconds"] for record in records), "nodes": len(metadata["nodes_mm"]), "shells": len(metadata["shells"]), "failure_plastic_strain": metadata["failure_plastic_strain"]}))


if __name__ == "__main__":
    main()
