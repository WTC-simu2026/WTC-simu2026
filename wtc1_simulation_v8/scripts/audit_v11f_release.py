"""Read saved V11F artifacts without importing or invoking the mechanics kernel.

Reconstruct terminal strains, section/spring energy and global static balance.
This is a second calculation path, not external/experimental certification.
"""
import argparse
import csv
import hashlib
import json
import math
import platform
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def grouped_csv(path):
    grouped = defaultdict(list)
    with Path(path).open(encoding="utf-8-sig", newline="") as stream:
        for row in csv.DictReader(stream):
            grouped[row["case_id"]].append(row)
    return grouped


def relative(a, b, floor=1.):
    return abs(a - b) / max(floor, abs(a), abs(b))


def audit(directory):
    checks = []

    def check(name, condition, evidence):
        checks.append({"test": name, "pass": bool(condition), "evidence": evidence})

    manifest = read(directory / "offline_manifest.json")
    result = read(directory / "results_v11f.json")
    cfg = read(ROOT / "wtc1_simulation_v8/data/v11f_panel_coupling_predeclaration.json")
    inputs = {p: sha(ROOT / p) == h for p, h in manifest["input_sha256"].items()}
    outputs = {p: sha(directory / p) == h for p, h in manifest["output_sha256"].items()}
    check("output_hashes", all(outputs.values()), outputs)
    check("input_and_protected_hashes", all(inputs.values()), inputs)
    historical_counts = {}
    for iteration, folder in (("V11E", "v11e_cracked_section"), ("V11D", "v11d_slab_contact")):
        old = ROOT / "wtc1_simulation_v8/output" / folder
        old_manifest = read(old / "offline_manifest.json")
        if iteration == "V11E":
            old_outputs = old_manifest["output_sha256"]
            old_inputs = old_manifest["input_sha256"]
        else:
            old_outputs = {r["path"]: r["sha256"] for r in old_manifest["files"]}
            old_inputs = {r["path"]: r["sha256_after"] for r in read(old / "source_manifest.json")["input_and_protected_files"]}
        output_ok = {p: sha(old / p) == h for p, h in old_outputs.items()}
        input_ok = {p: sha(ROOT / p) == h for p, h in old_inputs.items()}
        check(iteration + "_all_output_hashes", all(output_ok.values()), output_ok)
        check(iteration + "_all_input_hashes", all(input_ok.values()), input_ok)
        historical_counts[iteration] = {"outputs": len(old_outputs), "inputs": len(old_inputs)}

    inventory = {r["case"]["id"]: r for r in read(directory / "panel_inventory.json")}
    history = grouped_csv(directory / "path_history.csv")
    sections = grouped_csv(directory / "section_states.csv")
    terms = grouped_csv(directory / "physical_component_forces.csv")
    nodes = grouped_csv(directory / "slab_displacements.csv")
    reference = [{"summary": r, "history": history[r["id"]], "sections": sections[r["id"]],
                  "terms": terms[r["id"]], "slab_nodes": nodes[r["id"]], "inventory": inventory[r["id"]]}
                 for r in result["summaries"]]
    check("saved_reference_case_state_inventory_counts",
          len(reference) == len(history) == len(inventory) == result["case_count"] == 14
          and sum(map(len, history.values())) == result["state_count"] == 713,
          {"cases": len(reference), "states": sum(map(len, history.values()))})
    numerical = read(directory / "numerical_audit.json")
    check("saved_132_implementation_checks", numerical["tests_passed"] == numerical["test_count"]
          == result["tests_passed"] == result["test_count"] == len(numerical["tests"]) == 132
          and all(r["pass"] for r in numerical["tests"]), result["test_count"])
    comparisons = read(directory / "convergence_comparison.json")
    fine = [r for r in comparisons["mesh"] if r["comparison"] == "SUBDIVISIONS_4_TO_8"]
    check("saved_mesh_and_half_step_gates",
          len(fine) == len(comparisons["half_step"]) == 14
          and all(r["response_gate_pass"] for r in fine + comparisons["half_step"]),
          {"fine_mesh": len(fine), "half_step": len(comparisons["half_step"])})
    verification = read(directory / "verification_runs.json")
    runs = {"reference": reference, "half_step": verification["half_step"],
            **{"mesh_" + k: v for k, v in verification["mesh_runs"].items()}}
    maxima = {k: 0. for k in ("energy", "axial_strain", "curvature", "face_compression", "vertical", "horizontal", "moment", "crack_length")}
    balances = []
    shape_counts = []
    for label, run in runs.items():
        for data in run:
            s = data["summary"]
            inv = data["inventory"]
            sr = data["sections"]
            tr = data["terms"]
            nd = data["slab_nodes"]
            sec = inv["section"]
            component = {r["id"]: r for r in tr}
            lengths = math.fsum(float(r["weight_m"]) for r in sr)
            shape_counts.append(len(sr) == inv["gauss_sections"] and len(nd) == inv["slab_nodes"]
                                and len(tr) == inv["steel_members"] + 3 + 3 * inv["contact_stations"]
                                and abs(lengths - inv["span_m"]) < 1e-10
                                and all(float(r["weight_m"]) == float(r["Lch_m"]) for r in sr))
            spring_U = .5 * math.fsum(float(r["force_N"]) * float(r["extension_or_gap_m"]) for r in tr)
            recovered = {"spring_stored_J": spring_U}
            for key, target in (("stored_J_per_m", "slab_stored_J"),
                                ("dissipated_J_per_m", "dissipated_J"),
                                ("concrete_dissipated_J_per_m", "concrete_dissipated_J"),
                                ("steel_dissipated_J_per_m", "steel_dissipated_J"),
                                ("work_J_per_m", "exact_internal_work_J")):
                recovered[target] = math.fsum(float(r[key]) * float(r["weight_m"]) for r in sr)
            recovered["exact_internal_work_J"] += spring_U
            recovered["stored_J"] = recovered["slab_stored_J"] + spring_U
            for key, value in recovered.items():
                maxima["energy"] = max(maxima["energy"], relative(value, float(s[key])))
            maxima["energy"] = max(maxima["energy"], relative(recovered["exact_internal_work_J"], recovered["stored_J"] + recovered["dissipated_J"]))
            cracked_length = math.fsum(float(r["weight_m"]) for r in sr if float(r["max_damage"]) > 1e-10)
            maxima["crack_length"] = max(maxima["crack_length"], abs(cracked_length - float(s["cracked_quadrature_length_m"])))

            def strain(element, x):
                a, b = nd[element], nd[element + 1]
                dx = float(b["x_m"]) - float(a["x_m"])
                t = (x - float(a["x_m"])) / dx
                eps = (float(b["axial_m"]) - float(a["axial_m"])) / dx
                curvature = ((12*t-6) * float(a["vertical_m"]) + (6-12*t) * float(b["vertical_m"])) / dx**2
                curvature += ((6*t-4) * float(a["rotation_rad"]) + (6*t-2) * float(b["rotation_rad"])) / dx
                return eps, curvature

            for row in sr:
                eps, curvature = strain(int(row["element"]), float(row["x_m"]))
                maxima["axial_strain"] = max(maxima["axial_strain"], abs(eps - float(row["eps0"])))
                maxima["curvature"] = max(maxima["curvature"], abs(curvature - float(row["kappa_per_m"])))
            compression = 0.
            for el in range(len(nd) - 1):
                for node in (nd[el], nd[el + 1]):
                    eps, curvature = strain(el, float(node["x_m"]))
                    compression = max(compression, -sec["E_concrete_Pa"] * (eps - abs(curvature) * sec["equivalent_thickness_m"] / 2) / sec["fc_Pa"])
            maxima["face_compression"] = max(maxima["face_compression"], abs(compression - float(s["compression_ratio"])))
            # Undeformed coordinates, consistent with the small-strain V11F equations.
            # Both steel seats lie at y=0. The sole horizontal seat thus has zero moment about the exterior seat.
            L = inv["span_m"]
            x_act = cfg["loading"]["truss_actuator_station"] * L / 16 if s["kind"].startswith("truss_") else inv["slab_actuator_x_m"]
            V = -math.fsum(float(r["force_N"]) for r in tr if r["kind"] == "seat_v")
            H = -math.fsum(float(r["force_N"]) for r in tr if r["kind"] == "seat_h")
            act = float(s["actuator_reaction_N"])
            gravity = float(s["gravity_load_N"])
            M = -float(component["SEAT-V-interior"]["force_N"]) * L + act * x_act - gravity * L / 2
            maxima["vertical"] = max(maxima["vertical"], abs(V + act - gravity) / max(1., gravity, abs(act)))
            maxima["horizontal"] = max(maxima["horizontal"], abs(H) / max(1., gravity, abs(act)))
            maxima["moment"] = max(maxima["moment"], abs(M) / max(1., gravity * L, abs(act * x_act)))
            balances.append({"run": label, "case": s["id"], "vertical_error_N": V + act - gravity, "horizontal_error_N": H, "moment_error_Nm": M})
            for row in data["history"]:
                v, a, g = (float(row[key]) for key in ("seat_reaction_N", "actuator_reaction_N", "gravity_load_N"))
                maxima["vertical"] = max(maxima["vertical"], abs(v + a - g) / max(1., g, abs(a)))

    check("saved_shapes_weights_and_component_counts", all(shape_counts), {"terminal_panels_checked": len(shape_counts)})
    check("saved_J_per_m_and_spring_work_recover_panel_energy", maxima["energy"] < 1e-9, maxima["energy"])
    check("saved_displacements_recover_axial_and_curvature_fields", maxima["axial_strain"] < 1e-10 and maxima["curvature"] < 1e-9,
          {k: maxima[k] for k in ("axial_strain", "curvature")})
    check("saved_face_compression_screen", maxima["face_compression"] < 1e-8, maxima["face_compression"])
    check("saved_damaged_quadrature_length", maxima["crack_length"] < 1e-10, maxima["crack_length"])
    check("saved_global_force_and_moment_balance", max(maxima[k] for k in ("vertical", "horizontal", "moment")) < 1e-8,
          {"maxima": {k: maxima[k] for k in ("vertical", "horizontal", "moment")}, "terminal_balances": balances})
    check("global_blender_fire_impact_flags_unchanged", result["global_energy_credit_J"] == 0
          and not any(result[k] for k in ("fire_solved", "aircraft_impact_computed", "blender_changed", "geometrically_nonlinear", "as_built_reinforcement_known", "counts_are_probabilities")),
          "No global mechanics credit, new historical identification, aircraft, heat or animation inferred from this panel.")
    previous_attempt = ROOT / "tmp/v11f_panel_coupling/attempt01/results_v11f.json"
    if previous_attempt.exists():
        check("numerics_unchanged_after_editorial_clarifications",
              read(previous_attempt)["numerical_digest_sha256"] == result["numerical_digest_sha256"], result["numerical_digest_sha256"])
    ref_by_id = {r["id"]: r for r in result["summaries"]}
    diagnostic = []
    for row in fine:
        a = ref_by_id[row["case_id"]]["concrete_dissipated_J"]
        b = row["other_concrete_dissipated_J"]
        diagnostic.append({"case_id": row["case_id"], "reference_final_D_J": a, "fine_final_D_J": b,
                           "final_absolute_difference_J": abs(a-b), "final_true_relative_difference": abs(a-b)/a if a > 0 else None,
                           "declared_common_curve_normalized_difference_with_1J_floor": row["concrete_dissipation_relative_difference"]})
    code = Path(__file__).resolve()
    return {"iteration": "V11F", "status": "PASS" if all(r["pass"] for r in checks) else "FAIL",
            "checked_at_utc": datetime.now(timezone.utc).isoformat(), "check_count": len(checks), "checks": checks,
            "output_hash_count": len(outputs), "input_hash_count": len(inputs), "previous_iteration_hash_counts": historical_counts,
            "readback_maxima": maxima, "terminal_panel_count": len(shape_counts), "dissipation_mesh_diagnostics": diagnostic,
            "dissipation_diagnostic_note": "True final relative differences compare each mesh's own terminal state. They supplement, do not change, the pre-existing common-parameter gate with its 1 J normalization floor.",
            "audit_scope": "Read-back checks without importing the mechanics kernel. Global static moments at terminal states; vertical balance at all saved states; terminal strain/energy reconstruction. Not external solver or experimental validation.",
            "work_limit": "Full external work history is checked inside the solver; saved histories omit full nodal displacement vectors, so this read-back does NOT independently reconstruct that entire vector-work history.",
            "attempt_policy": "attempt01 retained as computation before report/plot clarification. Final attempt02 has identical numerical digest, revised report/plot and pinned read-back audit script; original numerical kernels/configuration unchanged.",
            "audit_script": code.relative_to(ROOT).as_posix(), "audit_script_sha256": sha(code),
            "python": platform.python_version(), "global_energy_credit_J": 0., "blender_changed": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", required=True)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    directory = (ROOT / args.directory).resolve()
    roots = [(ROOT / "tmp/v11f_panel_coupling").resolve(), (ROOT / "wtc1_simulation_v8/output/v11f_panel_coupling").resolve()]
    if not any(directory == root or root in directory.parents for root in roots):
        raise ValueError("Outside declared V11F output roots")
    result = audit(directory)
    if args.write:
        target = directory / "release_audit.json"
        if target.exists():
            raise FileExistsError("Existing release audit is preserved")
        target.write_text(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf8")
    print(json.dumps({k: v for k, v in result.items() if k not in ("checks", "dissipation_mesh_diagnostics")}, indent=2, ensure_ascii=False))
    if result["status"] != "PASS":
        print(json.dumps([r for r in result["checks"] if not r["pass"]], indent=2))
        raise SystemExit(1)
