"""Reaudit cached I02H histories, never overwrite a solver case; publish bounded findings."""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import math
import re
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
import run_impact_i02h as base
import audit_impact_i02h as auditor
import audit_impact_i02g as util

ROOT, OUT = base.ROOT, base.OUTPUT
CONFIG = ROOT / "wtc1_simulation_v8/data/impact_i02h_completion_r1.json"
NAMES = ["G30_L127_DT90_R1", "G30_L254_TAB_DT90_R1", "G30_L127_TAB_DT90_R2", "G30_L0635_TAB_DT90_R1", "G30_L127_TAB_DT45_R1", "ELASTIC_L127_TAB_CHECK_R1", "NOPROP_L127_TAB_CHECK_R1"]
STATUS = "completed_bounded_coupon_onset_checks_with_unqualified_propagation_and_material_convention"


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def difference(a, b):
    return abs(a - b) / max(abs(a), abs(b), 1e-12)


def preserved():
    entries = read(OUT / "preservation_before_finalization.json")["files"]
    failures = [e["path"] for e in entries if not (ROOT / e["path"]).is_file() or base.sha(ROOT / e["path"]) != e["sha256"]]
    return {"files_checked": len(entries), "failures": failures, "pass": not failures}


def history(directory, metadata):
    states = []
    with next(directory.glob("*.csv")).open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        seam = util.entity_columns(reader.fieldnames, "SEAM_HISTORY", 6)
        grip = util.entity_columns(reader.fieldnames, "UPPER_GRIP_HISTORY", 3)
        sides = [[p for p in metadata["seam_pairs"] if p["side"] == s] for s in ("left", "right")]
        for row in reader:
            off = {i: float(row[c[0]]) for i, c in seam.items()}
            extension = sum(auditor.contiguous_extension(p, off) for p in sides) / 2
            states.append({"time_ms": float(row["time"]), "displacement_mm": sum(float(row[c[0]]) for c in grip.values()) / len(grip), "force_N": abs(sum(float(row[c[2]]) for c in seam.values())), "extension_mm": extension, "internal_J": float(row["INTERNAL ENERGY"]) * .001, "kinetic_J": float(row["KINETIC ENERGY"]) * .001, "external_J": float(row["EXTERNAL WORK"]) * .001})
    return states


def font(n, bold=False):
    return ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf", n)


def figure(histories, comparisons):
    im = Image.new("RGB", (1500, 1030), "#f5f3ee")
    d = ImageDraw.Draw(im)
    ink, gray = "#19364b", "#5d6871"
    d.text((45, 28), "I02H | Le début de rupture se stabilise, pas toute la propagation", font=font(31, True), fill=ink)
    d.text((45, 77), "Éprouvette 76,2 × 300 × 2,3 mm — trajet de fissure imposé — matériau et rupture non calibrés", font=font(22), fill=gray)
    series = [(NAMES[1], "h = 2,54 mm", "#b87419"), (NAMES[2], "h = 1,27 mm", "#276cad"), (NAMES[3], "h = 0,635 mm", "#298565"), (NAMES[4], "h = 1,27 ; pas / 2", "#9259a2")]
    for i, (_, label, color) in enumerate(series):
        x = 65 + i * 360
        d.line((x, 133, x + 30, 133), fill=color, width=5)
        d.text((x + 40, 119), label, font=font(21), fill=ink)
    for column, key, title, ymax in [(0, "force_N", "Force dans la section cohésive (kN)", 50), (1, "extension_mm", "Avance moyenne de fissure (mm)", 14)]:
        left, top, right, bottom = 100 + column * 720, 225, 690 + column * 720, 690
        d.rounded_rectangle((left - 65, 173, right + 40, 792), radius=12, fill="white")
        d.text((left - 30, 184), title, font=font(23, True), fill=ink)
        def xy(x, y):
            return left + x / 1.6 * (right - left), bottom - y / ymax * (bottom - top)
        for j in range(6):
            y = ymax * j / 5
            ypx = xy(0, y)[1]
            d.line((left, ypx, right, ypx), fill="#dde2e5", width=1)
            d.text((left - 52, ypx - 12), f"{y:g}", font=font(18), fill=gray)
        for j in range(5):
            x = .4 * j
            xpx = xy(x, 0)[0]
            d.line((xpx, top, xpx, bottom), fill="#e8ecee", width=1)
            d.text((xpx - 10, bottom + 15), f"{x:g}", font=font(18), fill=gray)
        d.line((left, top, left, bottom, right, bottom), fill=ink, width=2)
        if key == "extension_mm":
            y = xy(0, 10.16)[1]
            for x in range(left, right, 18):
                d.line((x, y, min(x + 9, right), y), fill="#9a4c47", width=2)
            d.text((left + 12, y - 29), "Limite du domaine local raffiné", font=font(18), fill="#9a4c47")
        for name, _, color in series:
            values = histories[name]
            coords = [xy(s["displacement_mm"], s[key] / (1000 if key == "force_N" else 1)) for s in values]
            if name == NAMES[4]:
                for j in range(0, len(coords) - 2, 9):
                    d.line(coords[j:j + 5], fill=color, width=3)
            else:
                d.line(coords, fill=color, width=3)
        d.text((left + 55, bottom + 58), "Déplacement imposé du mors (mm)", font=font(21), fill=ink)
    d.text((60, 831), f"Première séparation : écart moyen/fin = {100*comparisons['medium_fine_onset_difference_fraction']:.2f} % ; pas / 2 = {100*comparisons['half_dt_onset_difference_fraction']:.5f} %", font=font(25, True), fill=ink)
    d.text((60, 880), f"Grossier/moyen : {100*comparisons['coarse_medium_onset_difference_fraction']:.2f} % > 10 % ; la séquence de déchirure reste dépendante du maillage.", font=font(23), fill="#9a4c47")
    d.text((60, 930), "Aucune aile ni façade simulée ici. Courbes issues des états calculés, sans trajectoire graphique imposée.", font=font(23), fill=gray)
    im.save(OUT / "synthese_impact_i02h.png")


def build():
    if (OUT / "summary_i02h.json").exists():
        raise RuntimeError("Synthesis already exists: preserve it, use a new revision")
    cfg = read(base.CFG)
    verification = OUT / "verification_r1"
    verification.mkdir(exist_ok=False)
    results, histories, diagnostics = {}, {}, {}
    saved_dump = auditor.dump
    auditor.dump = lambda *args: None  # Recompute into new files, preserve every original case audit.
    try:
        for name in NAMES:
            directory = OUT / name
            metadata = read(directory / "generation.json")
            result = auditor.audit_case(directory, cfg)
            base.dump(verification / (name + ".json"), result)
            results[name] = result
            states = history(directory, metadata)
            histories[name] = states
            work_scale = max(abs(s["external_J"]) for s in states)
            significant = [s for s in states if abs(s["external_J"]) > max(work_scale * .01, 1e-12)]
            largest = max(significant, key=lambda s: s["kinetic_J"] / max(s["internal_J"], 1e-12))
            refinement_limit = cfg["mesh"]["outer_x_break_mm"] - cfg["geometry"]["initial_total_crack_length_mm"] / 2
            ctoa_eligible = [s for s in result["advance_ctoa_states_after_2p3mm"] if max(s["left_extension_mm"], s["right_extension_mm"]) <= refinement_limit + 1e-9]
            starter = next(directory.glob("*_0000.out")).read_text(encoding="utf-8", errors="replace")
            warning_ids = re.findall(r"^WARNING ID\s*:\s*(\d+)", starter, re.M)
            old = read(directory / "case_audit.json")
            repeated = {k: difference(result[k], old[k]) for k in ("peak_remote_stress_mpa", "maximum_mass_error_fraction", "maximum_global_energy_residual_fraction", "section_work_to_external_error_fraction")}
            final = states[-1]
            diagnostics[name] = {
                "cached_numeric_metrics_reproduced": all(v < 1e-12 for v in repeated.values()),
                "cached_audit_relative_differences": repeated,
                "nodes": len(metadata["nodes_mm"]), "shells": len(metadata["shells"]), "springs": len(metadata["seam_pairs"]),
                "actual_starter_warning_ids": warning_ids,
                "maximum_KE_IE_significant_work_window": largest["kinetic_J"] / max(largest["internal_J"], 1e-12),
                "maximum_KE_IE_time_ms": largest["time_ms"],
                "ctoa_advance_states_inside_refined_domain": ctoa_eligible,
                "maximum_refined_tip_extension_mm": refinement_limit,
                "stored_generator_hash_matches_current": metadata["generator_sha256"] == base.sha(Path(base.__file__)),
                "stored_config_hash_matches_current_base": metadata["config_sha256"] == base.sha(base.CFG),
                "final_simplified_balance_J": final["external_J"] - final["internal_J"] - final["kinetic_J"],
                "elastic_half_force_displacement_J": .5 * final["force_N"] * final["displacement_mm"] * .001 if metadata["case"]["mode"] == "elastic" else None,
                "elastic_half_force_displacement_relative_error": difference(.5 * final["force_N"] * final["displacement_mm"] * .001, final["internal_J"]) if metadata["case"]["mode"] == "elastic" else None,
                "scope": "Additional post hoc diagnostics, not retrospective preregistration or independent material calibration"
            }
    finally:
        auditor.dump = saved_dump
    ep, coarse, medium, fine, half, elastic, noprop = [results[n] for n in NAMES]
    onset = lambda r: r["complete_separation_onset"]["remote_stress_mpa"]
    matched = []
    for a in medium["advance_states"]:
        for b in half["advance_states"]:
            if math.isclose(a["mean_extension_mm"], b["mean_extension_mm"], abs_tol=1e-9):
                matched.append({"extension_mm": a["mean_extension_mm"], "time_ms_full": a["time_ms"], "time_ms_half": b["time_ms"], "ctoa_B_full_deg": a["ctoa_B_deg"], "ctoa_B_half_deg": b["ctoa_B_deg"], "ctoa_B_difference_fraction": difference(a["ctoa_B_deg"], b["ctoa_B_deg"]), "ctoa_2B_full_deg": a["ctoa_2B_deg"], "ctoa_2B_half_deg": b["ctoa_2B_deg"], "inside_refined_domain": a["mean_extension_mm"] <= 10.16})
    comparisons = {
        "relative_difference_definition": "abs(a-b)/max(abs(a),abs(b))",
        "coarse_medium_onset_difference_fraction": difference(onset(coarse), onset(medium)),
        "medium_fine_onset_difference_fraction": difference(onset(medium), onset(fine)),
        "half_dt_onset_difference_fraction": difference(onset(medium), onset(half)),
        "medium_fine_peak_force_difference_fraction": difference(medium["peak_remote_stress_mpa"], fine["peak_remote_stress_mpa"]),
        "half_dt_ctoa_matched_extensions": matched,
        "fine_ctoa_states_in_refined_domain_count": len(diagnostics[NAMES[3]]["ctoa_advance_states_inside_refined_domain"]),
        "material_comparison_is_multifactor": True,
        "mesh_comparison_also_changes_seam_stiffness": True,
        "stress_measure": "Total seam FY divided by initial gross section 76.2*2.3 mm2; not tip stress or maximum element stress",
    }
    checks = {"all_seven_case_integrity_checks": all(r["all_case_gates_pass"] for r in results.values()), "cached_numeric_metrics_reproduced": all(d["cached_numeric_metrics_reproduced"] for d in diagnostics.values()), "controls_no_propagation": elastic["final_state"]["mean_extension_mm"] == 0 and noprop["final_state"]["mean_extension_mm"] == 0, "three_local_resolutions": True, "coarse_medium_onset_within_10_percent": comparisons["coarse_medium_onset_difference_fraction"] <= .10, "medium_fine_onset_within_10_percent": comparisons["medium_fine_onset_difference_fraction"] <= .10, "half_dt_onset_within_5_percent": comparisons["half_dt_onset_difference_fraction"] <= .05, "fine_two_distinct_ctoa_advances_after_2p3mm": len(fine["advance_ctoa_states_after_2p3mm"]) >= 2, "fine_two_ctoa_advances_inside_refined_domain_posthoc": comparisons["fine_ctoa_states_in_refined_domain_count"] >= 2, "original_files_preserved": preserved()["pass"]}
    campaign = {"checks": checks, "passed": sum(checks.values()), "total": len(checks), "all_campaign_checks_pass": all(checks.values()), "interpretation": "Engineering checks only; physical qualification remains false even if these checks pass.", "physical_material_convention_verified": False, "full_propagation_converged": False, "physical_metal_tearing_calibrated": False, "aircraft_or_facade_qualified": False, "historical_conclusion_authorized": False}
    compact_cases = []
    for name, r in results.items():
        compact_cases.append({"id": name, "mesh_h_mm": r["case"]["local_step_mm"], "material_variant": r["case"].get("material_variant", "epp_i02g"), "mode": r["case"]["mode"], "all_case_gates_pass": r["all_case_gates_pass"], "peak_stress_MPa": r["peak_remote_stress_mpa"], "first_separation": r["complete_separation_onset"], "final_extension_mm": r["final_state"]["mean_extension_mm"], "distinct_advance_count": len(r["advance_states"]), "execution_seconds": r["execution_seconds_recorded"], "mass_error_fraction": r["maximum_mass_error_fraction"], "energy_residual_fraction": r["maximum_global_energy_residual_fraction"], "work_error_fraction": r["section_work_to_external_error_fraction"], "KE_IE_at_peak": r["kinetic_to_internal_at_peak_stress"], "KE_IE_max_significant_window": diagnostics[name]["maximum_KE_IE_significant_work_window"], "final_state": r["final_state"]})
    summary = {"iteration": "IMPACT-I02H", "created_utc": dt.datetime.now(dt.timezone.utc).isoformat(), "status": STATUS, "next_iteration": "IMPACT-I02I", "cases": compact_cases, "accepted_execution_seconds": sum(c["execution_seconds"] for c in compact_cases), "comparisons": comparisons, "campaign": campaign, "preservation": preserved(), "length_scale_corrected_mm": {"EPP": 73100 * 30 / 495**2, "TAB": 71400 * 30 / 495**2}, "rejected_or_partial": ["G30_L127_TAB_DT90_PREFLIGHT: misplaced VP field, corrected in fresh PREFLIGHT2", "G30_L127_TAB_DT90_R1: interrupted extended run, diagnostic only; total elapsed duration not recorded"], "not_executed": ["fine EPP: cost gate after stalled medium EPP", "Gf15/60 local TAB sensitivity", "full aircraft/facade", "thermal branch V11S"], "warnings": ["NASA table 15 contains 0.15/0.4 while its deck contains 0.015/0.04", "NASA stress/strain convention not established in reviewed pages", "EPP/TAB change E, nu, yield and hardening, hence also seam stiffness", "K=E/h changes physical penalty compliance across mesh resolutions", "12 ms TAB window chosen after extended-run distortion, not predeclared physical endpoint", "final 12.7 mm extension is outside locally refined domain", "old FULLY_INTEGRATED label is incorrect: Ishell=24 means QEPH", "older generator/config hashes differ for some cached cases; the saved decks and histories are authoritative"]}
    source_manifest = {"created_utc": summary["created_utc"], "local_sources": [{"path": p.relative_to(ROOT).as_posix(), "sha256": base.sha(p), "bytes": p.stat().st_size} for p in (ROOT / "wtc1_simulation_v8/input/impact_i02f_sources/NASA_CR_191523_2024T3_CTOA.pdf", ROOT / "wtc1_simulation_v8/input/impact_i02h_sources/NASA_CR_2006_214281_STAGS.pdf")], "primary_urls": ["https://ntrs.nasa.gov/citations/20060008654", "https://help.altair.com/hwsolvers/rad/topics/solvers/rad/mat_law36_plas_tab_starter_r.htm", "https://help.altair.com/hwsolvers/rad/topics/solvers/rad/prop_type1_shell_starter_r.htm"], "visual_pdf_inspection": {"source": "NASA_CR_2006_214281_STAGS.pdf", "pdf_pages_1_based": [181, 196], "printed_pages": [177, 192], "rendered_views": ["tmp/i02h_nasa_table15.png", "tmp/i02h_nasa_deck.png"], "table_strains": [0, .00483, .15, .4, .1, .16], "deck_strains": [.00483, .015, .04, .1, .16], "deck_stresses_psi": [50000, 56600, 62400, 68200, 71100], "table_stresses_MPa": [0, 345, 390, 430, 470, 491], "conclusion": "Decimal discrepancy verified visually; deck supports .015/.04. Small table/deck psi inconsistencies also retained. Engineering/true convention remains unidentified."}, "NASA_19990021015": "Previously listed in base config; not relied on for current closure because this fetch failed.", "source_archive_modified": False}
    for name, value in [("summary_i02h.json", summary), ("comparisons.json", comparisons), ("campaign_audit.json", campaign), ("additional_diagnostics.json", diagnostics), ("source_manifest.json", source_manifest)]:
        base.dump(OUT / name, value)
    figure(histories, comparisons)
    print(json.dumps({"case_checks_pass": campaign["checks"]["all_seven_case_integrity_checks"], "campaign": f"{campaign['passed']}/{campaign['total']}", "preserved": preserved(), "comparisons": comparisons, "cases": compact_cases}, ensure_ascii=False, indent=2))


def release():
    # Publication audit is intentionally separate from scientific acceptance.
    warning_audit = {}
    for name in NAMES:
        log = next((OUT / name).glob("*_0000.out")).read_text(encoding="utf-8", errors="replace")
        ids = re.findall(r"^WARNING ID\s*:\s*(\d+)", log, re.M)
        slopes = re.findall(r"STIFFNESS VALUE\s+([\d.E+\-]+)\s+IS NOT CONSISTENT WITH THE MAXIMUM SLOPE\s*\(([\d.E+\-]+)", log)
        warning_audit[name] = {"warning_ids": ids, "known_ids_only": set(ids) <= ({"445", "506"} if name == NAMES[0] else {"445"}), "slope_corrections_reported": len(slopes), "maximum_relative_slope_correction_at_printed_precision": max((difference(float(a), float(b)) for a, b in slopes), default=0), "meaning": "445: massless springs, inertia floor printed as 1e-20; 506 in EPP: tiny printed slope consistency corrections, not omitted."}
    base.dump(OUT / "warning_audit.json", warning_audit)
    expected = ["summary_i02h.json", "comparisons.json", "campaign_audit.json", "additional_diagnostics.json", "source_manifest.json", "rapport_impact_i02h.md", "synthese_impact_i02h.png", "warning_audit.json", "preservation_before_finalization.json"]
    paths = [OUT / s for s in expected] + [CONFIG, Path(__file__), ROOT / "wtc1_simulation_v8/scripts/complete_impact_i02h.py", ROOT / "harness/handoffs/WTC1_IMPACT_I02H_HANDOFF.md"]
    for name in NAMES:
        paths += [OUT / "verification_r1" / (name + ".json")]
        paths += [p for p in (OUT / name).iterdir() if p.is_file() and (p.suffix in (".json", ".rad", ".csv", ".out", ".log") or p.name.endswith("T01"))]
    paths += [ROOT / e["path"] for e in read(OUT / "source_manifest.json")["local_sources"]]
    checks = {"required_artifacts_exist": all(p.is_file() for p in paths), "preserved_files_unchanged": preserved()["pass"], "case_audits_pass": read(OUT / "campaign_audit.json")["checks"]["all_seven_case_integrity_checks"], "scientific_failures_disclosed": not read(OUT / "campaign_audit.json")["all_campaign_checks_pass"], "physical_claim_gate_closed": not read(OUT / "campaign_audit.json")["historical_conclusion_authorized"], "NASA_download_hash": base.sha(ROOT / "wtc1_simulation_v8/input/impact_i02h_sources/NASA_CR_2006_214281_STAGS.pdf") == "aef6bef6327dd7038ea4bd78e232403bc2cffda94e8012df15e1fc10369abb80"}
    result = subprocess.run(["C:/Program Files/PowerShell/7/pwsh.exe", "-NoProfile", "-Command", "& harness/tools/Test-WtcHarness.ps1 | ConvertTo-Json"], cwd=ROOT, capture_output=True, text=True, encoding="utf-8", check=True)
    harness = json.loads(result.stdout)
    checks["harness_prepublication_pass"] = harness["Status"] == "PASS"
    base.dump(OUT / "harness_prepublication.json", harness)
    checks["all_cached_audits_reproduced"] = read(OUT / "campaign_audit.json")["checks"]["cached_numeric_metrics_reproduced"]
    checks["only_documented_starter_warnings"] = all(w["known_ids_only"] and w["maximum_relative_slope_correction_at_printed_precision"] < 1e-9 for w in warning_audit.values())
    checks["new_controls_effective_configuration_hashes"] = all(read(OUT / n / "generation.json")["config_sha256"] == base.sha(OUT / n / "effective_configuration.json") for n in NAMES[-2:])
    checks["solver_executables_unchanged"] = all(base.sha(Path(r["command"][0])) == r["executable_sha256"] for n in NAMES for r in read(OUT / n / "execution.json"))
    manifest = {"created_utc": dt.datetime.now(dt.timezone.utc).isoformat(), "files": [{"path": p.relative_to(ROOT).as_posix(), "bytes": p.stat().st_size, "sha256": base.sha(p)} for p in sorted(set(paths)) if p.is_file()], "scope": "Publication inputs, source PDFs, completed case decks/logs/histories/audits and report/handoff. Immutable older case animations/rejected trials covered by preservation snapshot."}
    base.dump(OUT / "artifact_manifest.json", manifest)
    base.dump(OUT / "release_audit.json", {"checks": checks, "passed": sum(checks.values()), "total": len(checks), "pass": all(checks.values()), "preservation": preserved(), "physical_validation": False})
    print(json.dumps({"checks": checks, "all_pass": all(checks.values()), "manifest_files": len(manifest["files"])}))
    if not all(checks.values()):
        raise RuntimeError("Publication audit failed; do not register")


def verify_publication():
    manifest = read(OUT / "artifact_manifest.json")
    failures = [e["path"] for e in manifest["files"] if not (ROOT / e["path"]).is_file() or base.sha(ROOT / e["path"]) != e["sha256"]]
    state = read(ROOT / "harness/state.json")
    registry = [json.loads(s) for s in (ROOT / "harness/experiments/registry.jsonl").read_text(encoding="utf-8-sig").splitlines() if s.strip()]
    records = [r for r in registry if r.get("experiment_id") == "WTC1-IMPACT-I02H"]
    run = subprocess.run(["C:/Program Files/PowerShell/7/pwsh.exe", "-NoProfile", "-Command", "& harness/tools/Test-WtcHarness.ps1 | ConvertTo-Json"], cwd=ROOT, capture_output=True, text=True, encoding="utf-8", check=True)
    harness = json.loads(run.stdout)
    checks = {"manifest_hashes": not failures, "previous_files_preserved": preserved()["pass"], "single_registry_record": len(records) == 1, "correct_current_state": state["current_iteration"] == "IMPACT-I02H" and state["next_iteration"] == "IMPACT-I02I", "harness_pass": harness["Status"] == "PASS", "release_audit_pass": read(OUT / "release_audit.json")["pass"], "report_and_handoff_present": (OUT / "rapport_impact_i02h.md").is_file() and (ROOT / "harness/handoffs/WTC1_IMPACT_I02H_HANDOFF.md").is_file(), "registry_artifacts_present": len(records) == 1 and all((ROOT / records[0][k]).is_file() for k in ("report", "configuration", "summary", "results", "comparisons", "artifact_manifest", "release_audit", "handoff"))}
    result = {"created_utc": dt.datetime.now(dt.timezone.utc).isoformat(), "checks": checks, "pass": all(checks.values()), "harness": harness, "manifest_files_checked": len(manifest["files"]), "manifest_failures": failures, "preservation": preserved(), "scientific_campaign_checks": "9/10; not physical validation"}
    target = OUT / "publication_verification.json"
    if target.exists():
        target = OUT / ("publication_verification_" + dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ") + ".json")
    base.dump(target, result)
    print(json.dumps(result, indent=2))
    if not result["pass"]:
        raise RuntimeError("Publication coherence verification failed")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--release", action="store_true")
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    verify_publication() if args.verify else release() if args.release else build()
