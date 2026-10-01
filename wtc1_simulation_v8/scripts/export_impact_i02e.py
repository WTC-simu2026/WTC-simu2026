"""Export native R9 solver animations and audit their coordinates/topology."""

from __future__ import annotations

import csv
import json
import re
import subprocess
from pathlib import Path

import numpy as np

from export_impact_i02a import parse_vtk
from run_impact_i02c import ROOT, RUNTIME, dump, sha


OUT = ROOT / "wtc1_simulation_v8/output/impact_i02e_skin_stringer_zone"
VIEW = ROOT / "wtc1_3d_v4/output/impact_i02e"
CASES = (
    "CONTACT_MERGED_H127_R9",
    "CONTACT_UNBREAKABLE_H127_R9",
    "CONTACT_RUPTURABLE_H127_R9",
)


def load_joint_history(directory: Path, meta: dict):
    path = directory / f"{meta['name']}T01.csv"
    with path.open(encoding="utf-8-sig", newline="") as stream:
        headers = next(csv.reader(stream))
    data = np.loadtxt(path, delimiter=",", skiprows=1)
    columns = [index for index, header in enumerate(headers) if "JOINT_NODE_HISTORY" in header]
    raw = data[:, columns].reshape(len(data), len(columns) // 6, 6)
    ids = []
    for local in range(len(columns) // 6):
        match = re.search(r"JOINT_NODE_HISTORY\s+(\d+)", headers[columns[6 * local]])
        if not match:
            raise RuntimeError("Cannot recover joint node IDs")
        ids.append(int(match.group(1)))
    return data[:, 0], ids, raw


def main() -> None:
    VIEW.mkdir(parents=True, exist_ok=True)
    all_cases = {}
    for case_id in CASES:
        directory = OUT / case_id
        meta = json.loads((directory / "generation.json").read_text(encoding="utf-8"))
        results = json.loads((directory / "results.json").read_text(encoding="utf-8"))
        if results["status"] != "PASS":
            raise RuntimeError(f"Unaccepted case: {case_id}")
        case_view = VIEW / case_id
        case_view.mkdir(parents=True, exist_ok=True)
        files = sorted(path for path in directory.glob(meta["name"] + "A*") if re.fullmatch(r".*A\d{3}", path.name))
        initial = np.asarray(meta["nodes_mm"], dtype=float)
        th_time, th_node_ids, th_joint = load_joint_history(directory, meta)
        th_order = {node_id: index for index, node_id in enumerate(th_node_ids)}
        records = []
        frame_points = []
        frame_times = []
        frame_active = []
        frame_damage = []
        max_epsp_by_part = {str(part): 0.0 for part in range(1, 8)}
        vtk_files = []
        for state, source in enumerate(files):
            process = subprocess.run(
                [str(RUNTIME / "anim_to_vtk_win64.exe"), str(source)],
                capture_output=True,
                text=True,
                timeout=60,
            )
            if process.returncode:
                raise RuntimeError(source.name)
            vtk = parse_vtk(process.stdout)
            node_ids = vtk["NODE_ID"].astype(int)
            points = vtk["points"].reshape(-1, 3)
            displacement = vtk["Displacement"].reshape(-1, 3)
            global_points = np.empty_like(initial)
            global_points[node_ids - 1] = points
            frame_points.append(global_points)
            frame_times.append(float(vtk["time"]))

            identity = abs(points - initial[node_ids - 1] - displacement)
            quant = lambda value: 0.500001 * 10.0 ** (np.floor(np.log10(np.maximum(abs(value), 1.0e-30))) - 5)
            identity_bound = quant(points) + quant(displacement) + np.finfo(np.float32).eps * abs(initial[node_ids - 1]) + 1.0e-10

            joint_ids = [node for node in meta["joint_history_nodes"] if node in set(node_ids)]
            joint_native = np.asarray([displacement[np.flatnonzero(node_ids == node)[0]] for node in joint_ids])
            joint_expected = np.asarray(
                [
                    [np.interp(vtk["time"], th_time, th_joint[:, th_order[node], axis]) for axis in range(3)]
                    for node in joint_ids
                ]
            )
            max_joint_velocity = float(np.max(abs(th_joint[:, :, 3:6])))
            cross_bound = 0.0001 + max_joint_velocity * 0.00051
            joint_cross = float(np.max(abs(joint_native - joint_expected))) if len(joint_ids) else 0.0

            cells = vtk["cells"].astype(int)
            element_ids = vtk["ELEMENT_ID"].astype(int)
            part_ids = vtk["PART_ID"].astype(int)
            offset = 0
            topology_ok = True
            shell_count = 0
            brick_count = 0
            for cell_index, element_id in enumerate(element_ids):
                count = cells[offset]
                local_nodes = cells[offset + 1 : offset + 1 + count]
                actual = set(node_ids[local_nodes])
                offset += count + 1
                if element_id <= len(meta["quads"]):
                    topology_ok &= count == 4 and actual == set(meta["quads"][element_id - 1])
                    shell_count += 1
                else:
                    position = meta["brick_ids"].index(int(element_id)) if int(element_id) in meta["brick_ids"] else -1
                    topology_ok &= position >= 0 and count == 8 and actual == set(meta["bricks"][position])
                    brick_count += 1

            epsp_fields = [
                key
                for key in vtk
                if key.startswith("2DELEM_Plastic_Strain") or key.startswith("2DELEM_Plast_Strn")
            ]
            for part in range(1, 8):
                mask = part_ids == part
                if np.any(mask):
                    max_epsp_by_part[str(part)] = max(
                        max_epsp_by_part[str(part)],
                        max(float(np.max(vtk[key][mask])) for key in epsp_fields),
                    )
            brick_mask = part_ids == 8
            active = vtk["EROSION_STATUS"][brick_mask] if np.any(brick_mask) else np.empty(0)
            damage = vtk["3DELEM_MAX_DAMAGE_ELEMENT"][brick_mask] if np.any(brick_mask) else np.empty(0)
            frame_active.append(active)
            frame_damage.append(damage)

            target = case_view / f"state_{state:03d}.vtk"
            target.write_text(process.stdout, encoding="utf-8")
            vtk_files.append(target)
            checks = {
                "all_nodes_exported": len(node_ids) == len(initial) and len(set(node_ids)) == len(initial),
                "displacement_identity": bool(np.all(identity <= identity_bound)),
                "joint_coordinates_cross_history": joint_cross <= cross_bound,
                "element_topology": topology_ok and shell_count == len(meta["quads"]) and brick_count == len(meta["bricks"]),
            }
            records.append(
                {
                    "state": state,
                    "time_ms": float(vtk["time"]),
                    "source": str(source.relative_to(ROOT)).replace("\\", "/"),
                    "source_sha256": sha(source),
                    "vtk": str(target.relative_to(ROOT)).replace("\\", "/"),
                    "vtk_sha256": sha(target),
                    "max_displacement_identity_error_mm": float(np.max(identity)),
                    "max_displacement_identity_bound_mm": float(np.max(identity_bound)),
                    "joint_history_cross_error_mm": joint_cross,
                    "joint_history_cross_bound_mm": cross_bound,
                    "minimum_erosion_status": float(np.min(vtk["EROSION_STATUS"])),
                    "maximum_erosion_status": float(np.max(vtk["EROSION_STATUS"])),
                    "maximum_reported_cohesive_damage": float(np.max(damage)) if len(damage) else None,
                    "checks": checks,
                }
            )

        npz = directory / "native_frames_r10.npz"
        max_bricks = max((len(values) for values in frame_active), default=0)
        active_array = np.asarray(frame_active) if max_bricks else np.empty((len(frame_active), 0))
        damage_array = np.asarray(frame_damage) if max_bricks else np.empty((len(frame_damage), 0))
        np.savez_compressed(
            npz,
            points_mm=np.asarray(frame_points),
            times_ms=np.asarray(frame_times),
            quads=np.asarray(meta["quads"], dtype=int) - 1,
            parts=np.asarray(meta["quad_parts"], dtype=int),
            bricks=np.asarray(meta["bricks"], dtype=int) - 1 if meta["bricks"] else np.empty((0, 8), dtype=int),
            active=active_array,
            damage=damage_array,
        )
        pvd = case_view / f"{case_id}_solver_states_ms.pvd"
        pvd.write_text(
            "<?xml version=\"1.0\"?>\n<VTKFile type=\"Collection\" version=\"0.1\" byte_order=\"LittleEndian\">\n  <Collection>\n"
            + "".join(
                f"    <DataSet timestep=\"{record['time_ms']:.12g}\" group=\"\" part=\"0\" file=\"{Path(record['vtk']).name}\"/>\n"
                for record in records
            )
            + "  </Collection>\n</VTKFile>\n",
            encoding="utf-8",
        )
        case_checks = {
            "native_states": len(records) == 30,
            "all_state_checks": all(all(record["checks"].values()) for record in records),
            "strictly_increasing_times": all(b > a for a, b in zip(frame_times, frame_times[1:])),
            "all_shells_active": all(record["minimum_erosion_status"] == 1.0 for record in records),
            "pvd_exists": pvd.exists(),
            "npz_exists": npz.exists(),
        }
        all_cases[case_id] = {
            "status": "PASS" if all(case_checks.values()) else "FAIL",
            "checks": case_checks,
            "states": records,
            "max_effective_plastic_strain_by_part": max_epsp_by_part,
            "maximum_reported_cohesive_damage": max(
                (record["maximum_reported_cohesive_damage"] or 0.0 for record in records),
                default=0.0,
            ),
            "npz": str(npz.relative_to(ROOT)).replace("\\", "/"),
            "npz_sha256": sha(npz),
            "pvd": str(pvd.relative_to(ROOT)).replace("\\", "/"),
            "pvd_sha256": sha(pvd),
        }

    audit = {
        "status": "PASS" if all(case["status"] == "PASS" for case in all_cases.values()) else "FAIL",
        "cases": all_cases,
        "converter": str((RUNTIME / "anim_to_vtk_win64.exe").relative_to(ROOT)).replace("\\", "/"),
        "converter_sha256": sha(RUNTIME / "anim_to_vtk_win64.exe"),
        "scope": "Direct export of native solver states. No mechanical interpolation, displacement amplification or Blender physics. The LAW117 damage animation field is reported but not treated as qualified unless independently reconciled with constitutive history.",
    }
    dump(VIEW / "native_export_audit_r10.json", audit)
    print(
        json.dumps(
            {
                "status": audit["status"],
                "cases": {
                    case_id: {
                        "states": len(case["states"]),
                        "max_epsp": case["max_effective_plastic_strain_by_part"],
                        "max_reported_damage": case["maximum_reported_cohesive_damage"],
                    }
                    for case_id, case in all_cases.items()
                },
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
