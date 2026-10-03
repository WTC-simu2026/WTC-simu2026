"""Fresh I02I-B coupon generator, derived from preserved I02H geometry; explicit finite shell and fixed initial-area penalty."""

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
import run_impact_i02i_material as unit
import re
from datetime import datetime, timezone


ROOT = Path(__file__).resolve().parents[2]
CFG = ROOT / "wtc1_simulation_v8/data/impact_i02i_fixed_penalty_predeclaration.json"
RUNTIME = ROOT / "wtc1_simulation_v8/openradioss_runtime/v20260728-win64"
OUTPUT = ROOT / "wtc1_simulation_v8/output/impact_i02i_fixed_penalty"


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
    points, ledger = unit.curve(cfg, case["interpretation"])
    material = dict(cfg["material"], law36_plastic_true_strain=[p[0] for p in points], law36_true_stress_mpa=[p[1] for p in points])
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
    name = "I02IB_" + case["id"]

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
    lines += ["/PROP/SHELL/1", "QEPH_EXPLICIT_FINITE_FRESH", f'{24:10d}{4:10d}{0:10d}{0:10d}{0:10d}{"":10s}{0:20g}', i02g.ff(0,0,0,0,0), i02g.ii(5,"")+i02g.ff(thickness,0)+i02g.ii("",1,1,0)]

    shear_modulus = material["young_modulus_mpa"] / (2.0 * (1.0 + material["poisson_ratio"]))
    spring_ids: list[int] = []
    for index, pair in enumerate(seam_pairs):
        property_id = 1000 + index
        element_id = len(shells) + index + 1
        function_x = 3000 + 2 * index
        function_y = function_x + 1
        area = thickness * pair["tributary_width_mm"]
        normal_stiffness = seam["normal_penalty_N_per_mm3"] * area
        tangent_stiffness = seam["tangent_penalty_N_per_mm3"] * area
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
    for index in range(801):
        u = index / 800.0
        smooth = u*u*u*(10+u*(-15+6*u))
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
    lines += ["/TH/NODE/5", "LOWER_GRIP_HISTORY", i02g.ii("DY", "VY", "REACY")]
    lines += [i02g.ii(node_id, 0) for node_id in lower_grip]
    plastic_ids=[]
    for eid,quad in enumerate(shells,1):
        cx=sum(nodes[n-1][0] for n in quad)/4; cy=sum(nodes[n-1][1] for n in quad)/4
        if crack_half-local_step <= abs(cx) <= outer_break and abs(cy) <= 2*local_step:
            plastic_ids.append(eid)
    lines += ["/TH/SHEL/7", "TIP_PLASTIC_HISTORY", i02g.ii("EMAX")]
    lines += [i02g.ii(eid,0) for eid in plastic_ids]
    guards=[]
    if mode == "fracture":
        for sid,x in [(501,-outer_break),(502,outer_break)]:
            j=min(range(len(xs)),key=lambda k:abs(xs[k]-x))
            assert abs(xs[j]-x)<1e-9
            guards.append(dict(sensor_id=sid,x_mm=x,lower_node=lower_seam[j],upper_node=upper_seam[j],threshold_mm=seam["domain_stop_gap_fraction_of_deltaf"]*deltaf))
            lines += [f"/SENSOR/DIST/{sid}/1", "REFINED_DOMAIN_GUARD", i02g.ff(0), i02g.ii(lower_seam[j],upper_seam[j])+i02g.ff(-1e30,guards[-1]["threshold_mm"],0)+i02g.ii(0)]
        lines += ["/TH/SENSOR/6", "DOMAIN_STOP_STATUS", i02g.ii("STATUS"), i02g.ii(501,502)]
    lines += ["/UNIT/1", "I02IB_G_MM_MS", i02g.ff("g", "mm", "ms"), "/END"]
    starter = directory / f"{name}_0000.rad"
    starter.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")

    dt_scale = float(case.get("dt_scale", execution["dt_scale"]))
    history_dt = execution["history_dt_ms"] * loading_end_ms / (6. if mode=="elastic" else 12.)
    engine = [
        "/DT", i02g.ff(dt_scale, 0), "/MON/ON", "/PRINT/-100/100", f"/RUN/{name}/1", i02g.ff(run_end_ms),
        "/TFILE/4", i02g.ff(history_dt), "/VERS/2026",
    ]
    if guards: engine += ["/STOP/LSENSOR",i02g.ii(501,502),i02g.ii(0,1,0,0,0,0,0)]
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
        "shell_options": cfg["shell_options"], "conversion_ledger": ledger, "guards":guards, "plastic_history_shell_ids":plastic_ids,
        "dependency_sha256":{Path(mod.__file__).name:sha(Path(mod.__file__)) for mod in [i02g,unit]},
        "config_sha256": sha(CFG),
        "source_sha256": {source["path"]: source["sha256"] for source in cfg["sources"] if "path" in source},
    }
    dump(directory / "generation.json", metadata)
    return metadata


def snapshot():
    OUTPUT.mkdir(parents=True,exist_ok=False)
    old=ROOT/'wtc1_simulation_v8/output/impact_i02i_material'
    entries={}
    for name in ['preservation_before.json','artifact_manifest.json']:
        for entry in json.loads((old/name).read_text())['files']:
            assert sha(ROOT/entry['path'])==entry['sha256'],entry['path']
            entries[entry['path']]=entry
    for p in [old/'publication_verification.json',old/'artifact_manifest.json',old/'preservation_before.json',ROOT/'harness/handoffs/WTC1_IMPACT_I02I_A_HANDOFF.md']:
        entries[p.relative_to(ROOT).as_posix()]={'path':p.relative_to(ROOT).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)}
    dump(OUTPUT/'preservation_before.json',{'created_utc':datetime.now(timezone.utc).isoformat(),'files':list(entries.values()),'scope':'Only previously pinned manifests; no archive scan or historical solver rerun.'})
    for name in ['state.json','experiments/registry.jsonl']:
        (OUTPUT/('before_'+Path(name).name)).write_bytes((ROOT/'harness'/name).read_bytes())
    print(json.dumps({'protected_files':len(entries)}),flush=True)


def sensor_generate(cfg,folder):
    unit_cfg=json.loads(unit.CFG.read_text())
    case={'id':'SENSOR_STOP_R1','interpretation':'engineering','shell':'finite','path':'elastic'}
    meta=unit.generate(unit_cfg,case,folder)
    name=meta['name']; starter=folder/(name+'_0000.rad'); engine=folder/(name+'_0001.rad')
    extra=['/SENSOR/DIST/501/1','FRESH_ELASTIC_SENSOR_STOP',i02g.ff(0),i02g.ii(1,2)+i02g.ff(-1e30,10.01,0)+i02g.ii(0),'/TH/SENSOR/6','DOMAIN_STOP_STATUS',i02g.ii('STATUS'),i02g.ii(501)]
    starter.write_text(starter.read_text().replace('/END','\n'.join(extra)+'\n/END'),encoding='utf-8',newline='\n')
    with engine.open('a',encoding='utf-8',newline='\n') as f: f.write('/STOP/LSENSOR\n'+i02g.ii(501)+'\n'+i02g.ii(0,1,0,0,0,0,0)+'\n')
    meta.update(sensor_threshold_distance_mm=10.01,configured_end_ms=meta['end_ms'],purpose='Verify actual engine stopping and ended T01 with fresh homogeneous elastic patch.',campaign_config_sha256=sha(CFG),campaign_generator_sha256=sha(__file__))
    dump(folder/'generation.json',meta); return meta


def execute_case(cfg,case,sensor=False):
    folder=OUTPUT/case['id']; folder.mkdir(exist_ok=False)
    meta=sensor_generate(cfg,folder) if sensor else generate(cfg,case,folder)
    env=os.environ.copy(); env.update(RAD_CFG_PATH='C:/OpenRadioss/hm_cfg_files',RAD_H3D_PATH='C:/OpenRadioss/extlib/h3d/lib/win64',OPENRADIOSS_PATH='C:/OpenRadioss',OMP_NUM_THREADS='1',KMP_STACKSIZE='400m',PYTHONDONTWRITEBYTECODE='1')
    records=[]
    jobs=[('starter_win64.exe',['-i',meta['name']+'_0000.rad','-np','1'],'starter.log'),('engine_win64.exe',['-i',meta['name']+'_0001.rad'],'engine.log'),('th_to_csv_win64.exe',[meta['name']+'T01'],'converter.log')]
    for exe,args,log in jobs:
        start=time.perf_counter(); limit=120 if sensor else cfg['execution']['maximum_case_wall_seconds']
        try:
            p=subprocess.run([str(RUNTIME/exe),*args],cwd=folder,env=env,capture_output=True,timeout=limit)
        except subprocess.TimeoutExpired as exc:
            (folder/log).write_bytes((exc.stdout or b'')+(exc.stderr or b''))
            dump(folder/'timeout.json',{'job':exe,'limit_seconds':limit,'status':'diagnostic_incomplete'}); raise
        (folder/log).write_bytes(p.stdout+p.stderr)
        records.append({'command':[str(RUNTIME/exe),*args],'returncode':p.returncode,'seconds':time.perf_counter()-start,'executable_sha256':sha(RUNTIME/exe)})
        dump(folder/'execution.json',records)
        if p.returncode: raise RuntimeError(log+' failed')
        if exe.startswith('starter'):
            listing=(folder/(meta['name']+'_0000.out')).read_text(errors='replace')
            if re.search(r'(?:WARNING|ERROR) ID',listing) or 'unsupported field' in listing.lower(): raise RuntimeError('Preflight gate failed; engine not launched')
    print(json.dumps({'case':case['id'],'seconds':sum(r['seconds'] for r in records)}),flush=True)


def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--snapshot',action='store_true'); parser.add_argument('--sensor',action='store_true'); parser.add_argument('--case'); parser.add_argument('--campaign',action='store_true'); args=parser.parse_args()
    if args.snapshot: snapshot(); return
    cfg=json.loads(CFG.read_text())
    assert (OUTPUT/'preservation_before.json').exists(),'Snapshot required'
    if args.sensor: execute_case(cfg,{'id':'SENSOR_STOP_R1'},True); return
    cases=cfg['cases'] if args.campaign else [c for c in cfg['cases'] if c['id']==args.case]
    assert cases,'Unknown case'
    if args.campaign:
        control=json.loads((OUTPUT/'control_checks.json').read_text()); assert control['pass'],'Controls required before fracture campaign'
    for case in cases:
        folder=OUTPUT/case['id']
        if folder.exists():
            records=json.loads((folder/'execution.json').read_text())
            assert len(records)==3 and all(r['returncode']==0 for r in records),'Incomplete case retained; do not overwrite'
            print(json.dumps({'cached':case['id'],'no_rerun':True}),flush=True); continue
        seconds=sum(r['seconds'] for p in OUTPUT.glob('*/execution.json') for r in json.loads(p.read_text()))
        assert seconds < cfg['execution']['maximum_campaign_wall_seconds'],'Campaign cost gate reached'
        execute_case(cfg,case)


if __name__=='__main__': main()
