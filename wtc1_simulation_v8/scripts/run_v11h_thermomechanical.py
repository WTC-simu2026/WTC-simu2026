"""Run the bounded V11H linear-thermoelastic section qualification."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import platform
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont, __version__ as pillow_version

import test_v11h_thermomechanical
import v11h_thermomechanical_model as physics


ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "wtc1_simulation_v8/data/v11h_thermomechanical_predeclaration.json"


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def digest(value):
    data = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def write_json(path, value):
    Path(path).write_text(
        json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def manifest_hashes(directory):
    manifest = read(directory / "offline_manifest.json")
    hashes = dict(manifest["input_sha256"])
    for name, expected in manifest["output_sha256"].items():
        hashes[(directory / name).relative_to(ROOT).as_posix()] = expected
    return manifest, hashes


def build_cold_control(cfg):
    directory = ROOT / cfg["cold_panel_directory"]
    manifest, expected = manifest_hashes(directory)
    checks = {name: sha(ROOT / name) == value for name, value in expected.items()}
    results = read(directory / "results_v11f.json")
    release = read(directory / "release_audit.json")
    wanted = cfg["cold_control"]
    identity = {
        "iteration": results["iteration"] == wanted["expected_iteration"],
        "results_status": results["status"] == wanted["expected_status"],
        "release_status": release["status"] == wanted["expected_status"],
        "test_count": results["test_count"] == results["tests_passed"] == wanted["expected_test_count"],
        "case_count": results["case_count"] == wanted["expected_case_count"],
        "numerical_digest": results["numerical_digest_sha256"] == wanted["expected_numerical_digest_sha256"],
        "manifest_status": manifest["implementation_status"] == wanted["expected_status"],
    }
    return {
        "iteration": "V11F",
        "status": "PASS" if all(checks.values()) and all(identity.values()) else "FAIL",
        "hash_checks": checks,
        "identity_checks": identity,
        "results_sha256": sha(directory / "results_v11f.json"),
        "offline_manifest_sha256": sha(directory / "offline_manifest.json"),
        "release_audit_sha256": sha(directory / "release_audit.json"),
        "test_count": results["test_count"],
        "case_count": results["case_count"],
        "state_count": results["state_count"],
        "numerical_digest_sha256": results["numerical_digest_sha256"],
        "policy": "V11F is read and hashed only; no cold state is recomputed or modified.",
    }


def solve_cases(cfg, section_cfg, fibers, steps):
    return [
        physics.ElasticThermoSection(section_cfg, cfg, case, fibers).trace(steps)
        for case in cfg["cases"]
    ]


def write_csvs(directory, reference, mesh_runs):
    history_fields = [
        "case_id", "mode", "step", "segment", "temperature_scale",
        "temperature_bottom_c", "temperature_top_c", "eps0", "kappa_per_m",
        "minimum_material_temperature_c", "maximum_material_temperature_c",
        "N_N", "M_Nm", "support_reaction_N", "support_reaction_Nm",
        "centroid_extension_m", "simply_supported_free_bow_midspan_m",
        "stored_mechanical_J_per_m", "cumulative_thermoelastic_work_J_per_m",
        "cumulative_external_mechanical_work_J_per_m", "mechanical_energy_residual_relative",
        "sensible_enthalpy_change_J_per_m", "maximum_absolute_stress_Pa",
        "minimum_stress_Pa", "maximum_stress_Pa", "free_axial_residual_relative",
        "free_moment_residual_relative",
        "concrete_tension_ratio_ft20", "concrete_compression_ratio_fc20",
        "steel_stress_ratio_fy20", "dissipated_J_per_m", "global_energy_credit_J",
    ]
    with (directory / "section_paths.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=history_fields)
        writer.writeheader()
        for run in reference:
            for row in run["history"]:
                writer.writerow({**row, "case_id": run["summary"]["id"], "mode": run["summary"]["mode"]})

    fiber_fields = [
        "case_id", "fiber", "kind", "y_m", "area_m2", "E_Pa", "alpha_per_K",
        "density_kg_m3", "specific_heat_J_kg_K", "delta_temperature_C",
        "thermal_strain", "total_strain", "mechanical_strain", "stress_Pa",
        "stored_mechanical_J_per_m_contribution", "sensible_enthalpy_J_per_m_contribution",
    ]
    with (directory / "section_fiber_states.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fiber_fields)
        writer.writeheader()
        for run in reference:
            for row in run["peak_fibers"]:
                writer.writerow({**row, "case_id": run["summary"]["id"]})

    energy_fields = [
        "case_id", "mode", "location", "temperature_bottom_c", "temperature_top_c",
        "stored_mechanical_J_per_m", "thermoelastic_work_J_per_m",
        "external_mechanical_work_J_per_m", "sensible_enthalpy_change_J_per_m",
        "dissipated_J_per_m", "mechanical_energy_residual_relative", "global_energy_credit_J",
    ]
    with (directory / "energy_ledger.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=energy_fields)
        writer.writeheader()
        for run in reference:
            for location in ("peak", "final"):
                row = run["summary"][location]
                writer.writerow({
                    "case_id": run["summary"]["id"], "mode": run["summary"]["mode"], "location": location,
                    "temperature_bottom_c": row["temperature_bottom_c"], "temperature_top_c": row["temperature_top_c"],
                    "stored_mechanical_J_per_m": row["stored_mechanical_J_per_m"],
                    "thermoelastic_work_J_per_m": row["cumulative_thermoelastic_work_J_per_m"],
                    "external_mechanical_work_J_per_m": row["cumulative_external_mechanical_work_J_per_m"],
                    "sensible_enthalpy_change_J_per_m": row["sensible_enthalpy_change_J_per_m"],
                    "dissipated_J_per_m": row["dissipated_J_per_m"],
                    "mechanical_energy_residual_relative": row["mechanical_energy_residual_relative"],
                    "global_energy_credit_J": row["global_energy_credit_J"],
                })

    rows = []
    for fibers, cases in mesh_runs.items():
        for case_id, run in cases.items():
            peak = run["summary"]["peak"]
            rows.append({
                "concrete_fibers": int(fibers), "case_id": case_id,
                "eps0": peak["eps0"], "kappa_per_m": peak["kappa_per_m"],
                "N_N": peak["N_N"], "M_Nm": peak["M_Nm"],
                "stored_mechanical_J_per_m": peak["stored_mechanical_J_per_m"],
                "sensible_enthalpy_change_J_per_m": peak["sensible_enthalpy_change_J_per_m"],
            })
    fields = list(rows[0])
    with (directory / "section_mesh_comparison.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def font(size, bold=False):
    path = "C:/Windows/Fonts/segoeui" + ("b" if bold else "") + ".ttf"
    try:
        return ImageFont.truetype(path, size)
    except OSError:
        return ImageFont.load_default()


def figure(path, result, reference):
    by_id = {row["summary"]["id"]: row for row in reference}
    image = Image.new("RGB", (1600, 1120), "#eef3f6")
    draw = ImageDraw.Draw(image)

    def text(x, y, value, size=20, color="#253b4a", bold=False):
        draw.text((x, y), value, font=font(size, bold), fill=color)

    def card(box):
        draw.rounded_rectangle(box, radius=18, fill="white", outline="#d5e0e6", width=2)

    text(42, 24, "WTC 1 / V11H — références thermomécaniques élastiques", 34, bold=True)
    text(43, 75, "Températures imposées de 20 à 120 °C ; aucune simulation d'incendie ni loi fissurée à chaud.", 23)

    card((35, 124, 1565, 290))
    text(60, 144, f"{result['tests_passed']}/{result['test_count']} contrôles numériques réussis", 29, bold=True)
    text(60, 193, "V11F froid : empreintes, 132 contrôles et 14 cas préservés sans recalcul.", 23)
    text(60, 235, "Énergie mécanique et enthalpie sensible sont comptées séparément en J/m.", 22)

    panels = [(55, 335, 750, 830), (850, 335, 1545, 830)]
    for box in panels:
        card(box)

    text(80, 355, "Dilatation uniforme", 25, bold=True)
    uniform_free = by_id["R02_UNIFORM_FREE"]["summary"]["peak"]
    uniform_fixed = by_id["R02_UNIFORM_AXIAL_RESTRAINED"]["summary"]["peak"]
    text(85, 414, f"Libre : allongement au centroïde = {1000*uniform_free['centroid_extension_m']:.2f} mm", 22)
    text(85, 458, f"Axialement empêchée : réaction = {uniform_fixed['support_reaction_N']/1000:.1f} kN", 22)
    text(85, 502, f"Énergie stockée = {uniform_fixed['stored_mechanical_J_per_m']/1000:.2f} kJ/m", 22)
    text(85, 565, "Le travail mécanique des appuis est nul :", 21, bold=True)
    text(85, 605, "déplacement nul aux coordonnées bloquées ;", 20)
    text(85, 640, "résultante nulle aux coordonnées libres.", 20)
    text(85, 704, "Réactions ≠ travail d'appui non nul.", 21, color="#9a5c18", bold=True)

    text(875, 355, "Gradient dans l'épaisseur", 25, bold=True)
    grad_free = by_id["R02_GRADIENT_FREE"]["summary"]["peak"]
    grad_fixed = by_id["R02_GRADIENT_FULLY_RESTRAINED"]["summary"]["peak"]
    text(880, 414, f"Face basse / haute : 20 / 120 °C", 22)
    text(880, 458, f"Libre : courbure = {grad_free['kappa_per_m']:.5e} m⁻¹", 22)
    text(880, 502, f"Flèche cinématique libre = {grad_free['simply_supported_free_bow_midspan_m']:.3f} m", 22)
    text(880, 559, f"Blocage complet : R_N = {grad_fixed['support_reaction_N']/1000:.1f} kN", 21)
    text(880, 599, f"Blocage complet : R_M = {grad_fixed['support_reaction_Nm']/1000:.1f} kN·m", 21)
    text(880, 671, "La flèche est une référence petites pentes,", 20, color="#9a5c18", bold=True)
    text(880, 706, "pas la réponse du panneau V11F.", 20, color="#9a5c18", bold=True)

    card((35, 870, 1565, 1085))
    text(60, 892, "Portée des résultats", 25, bold=True)
    text(60, 939, "Propriétés constantes et génériques ; dilatation libre/empêchée et gradient seulement.", 21)
    text(60, 978, "Pas de conduction, convection, rayonnement, incendie, fluage, endommagement chauffé ou effondrement.", 21)
    text(60, 1017, "Les écrans de résistance à 20 °C signalent une limite de domaine ; ils ne créent aucune résistance à chaud.", 21)
    image.save(path)


def report(path, cfg, result, reference):
    by_id = {row["summary"]["id"]: row for row in reference}
    material = cfg["thermal_properties"]
    lines = [
        "# V11H — socle thermomécanique élastique borné",
        "",
        "## Résultat",
        "",
        f"V11H passe {result['tests_passed']}/{result['test_count']} contrôles. Elle qualifie une section élastique à température prescrite pour dilatation libre, dilatation empêchée et gradient linéaire dans l'épaisseur. Les propriétés, unités, déformations thermiques, réactions, travail thermoélastique, énergie stockée et enthalpie sensible sont enregistrés à chaque état.",
        "",
        "Le contrôle froid V11F est conservé octet par octet : 132/132 contrôles, 14 cas et son empreinte numérique antérieure sont retrouvés. Aucun état V11F n'est recalculé ou modifié. V11H ne couple pas encore le champ thermique au panneau V11F et n'introduit aucune loi de fissuration à chaud.",
        "",
        "## 1. Faits directement observés ou transcrits",
        "",
        "Le dossier local vérifié indiquait V11G terminée et V11H suivante. Les fichiers V11F/V11G déclarés par leurs manifestes ont été relus par empreinte, sans rescanner l'archive source. La géométrie de section reprend le ruban équivalent V11E/V11F : largeur 2,032 m, épaisseur équivalente 0,11049 m et portée de référence 18,1102 m.",
        "",
        "## 2. Résultats d'un modèle officiel",
        "",
        "Aucun nouveau résultat officiel n'est utilisé. Les résultats historiques déjà transcrits dans les étapes antérieures ne sont ni étendus ni réinterprétés ici.",
        "",
        "## 3. Affirmations provenant des archives locales",
        "",
        "Aucune nouvelle affirmation d'archive, mesure de température, séquence d'incendie ou identification de mécanisme n'entre dans V11H.",
        "",
        "## 4. Hypothèses propres au modèle",
        "",
        "Petites déformations et sections planes : ε(y)=ε₀−yκ. La déformation thermique est εth=α(T−20 °C), la déformation mécanique εm=ε−εth et la contrainte σ=Eεm. Les résultantes sont N=ΣAσ et M=−ΣAyσ.",
        "",
        f"Les coefficients constants sont αc={material['concrete']['thermal_expansion_per_k']:.3e} K⁻¹ et αs={material['reinforcement']['thermal_expansion_per_k']:.3e} K⁻¹. Les propriétés calorifiques constantes sont ρc={material['concrete']['density_kg_m3']:.0f} kg/m³, cp,c={material['concrete']['specific_heat_j_kg_k']:.0f} J/(kg·K), ρs={material['reinforcement']['density_kg_m3']:.0f} kg/m³ et cp,s={material['reinforcement']['specific_heat_j_kg_k']:.0f} J/(kg·K). Ce sont des hypothèses génériques, pas des propriétés mesurées du béton ou des armatures du WTC1.",
        "",
        "E et les résistances à 20 °C sont hérités sans dégradation. Il n'y a ni conduction, convection, rayonnement, flux incident, protection projetée calculée, fluage, plasticité, fissuration, écrasement, glissement d'adhérence, non-linéarité géométrique ou contact. Le gradient est imposé, non calculé. La température maximale de 120 °C est un palier numérique de qualification, pas une reconstitution d'incendie.",
        "",
        "L'énergie mécanique par mètre longitudinal est U=1/2 ΣAE εm². Le travail thermoélastique conjugué est −∫ΣAσ dεth. Le travail mécanique généralisé est ∫(N dε₀+M dκ). Pour les appuis idéaux présents, les coordonnées bloquées ne bougent pas et les coordonnées libres ont une résultante nulle : le travail mécanique d'appui vaut donc zéro même si les réactions ne sont pas nulles. L'enthalpie sensible H=ΣρcpAΔT est inventoriée séparément ; aucune équation de chaleur n'est résolue.",
        "",
        "## 5. Résultats dérivés",
        "",
        "| Cas | Cinématique | T basse/haute au pic (°C) | ε₀ | κ (m⁻¹) | Réaction N (kN) | Réaction M (kN·m) | U (kJ/m) | H sensible (MJ/m) |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for run in reference:
        peak = run["summary"]["peak"]
        lines.append(
            f"| {run['summary']['id']} | {run['summary']['mode']} | {peak['temperature_bottom_c']:.1f}/{peak['temperature_top_c']:.1f} | {peak['eps0']:.6e} | {peak['kappa_per_m']:.6e} | {peak['support_reaction_N']/1000:.6f} | {peak['support_reaction_Nm']/1000:.6f} | {peak['stored_mechanical_J_per_m']/1000:.6f} | {peak['sensible_enthalpy_change_J_per_m']/1e6:.6f} |"
        )
    uniform_free = by_id["R02_UNIFORM_FREE"]["summary"]["peak"]
    uniform_fixed = by_id["R02_UNIFORM_AXIAL_RESTRAINED"]["summary"]["peak"]
    gradient_free = by_id["R02_GRADIENT_FREE"]["summary"]["peak"]
    gradient_fixed = by_id["R02_GRADIENT_FULLY_RESTRAINED"]["summary"]["peak"]
    lines += [
        "",
        f"À +100 K uniforme, le cas composite libre donne un allongement au centroïde de {1000*uniform_free['centroid_extension_m']:.6f} mm. Le même cas axialement empêché donne une réaction de {uniform_fixed['support_reaction_N']/1000:.6f} kN et stocke {uniform_fixed['stored_mechanical_J_per_m']/1000:.6f} kJ/m.",
        "",
        f"Pour un gradient imposé de 20 à 120 °C, le cas composite libre donne κ={gradient_free['kappa_per_m']:.9e} m⁻¹ et une flèche cinématique petites pentes de {gradient_free['simply_supported_free_bow_midspan_m']:.6f} m. Le blocage complet donne des réactions de {gradient_fixed['support_reaction_N']/1000:.6f} kN et {gradient_fixed['support_reaction_Nm']/1000:.6f} kN·m. Cette flèche n'est pas un calcul du panneau V11F.",
        "",
        f"Le résidu relatif maximal de l'identité énergétique est {result['maxima']['energy_residual_relative']:.3e}; le résidu maximal des résultantes libres est {result['maxima']['free_resultant_residual_relative']:.3e}. Les deux cycles reviennent à l'état de référence sans dissipation. Le passage de 160 à 320 fibres donne un écart maximal de {result['maxima']['mesh_160_to_320_relative']:.3e}, et le demi-pas conserve les états terminaux à {result['maxima']['half_step_relative']:.3e}.",
        "",
        "Les rapports aux résistances froides ft, fc et fy sont uniquement des écrans de domaine. Un dépassement n'autoriserait pas l'emploi de l'élasticité : il indiquerait au contraire que ce cas doit s'arrêter avant une interprétation physique ou être repris avec une loi thermodynamique complète et un historique cohérent.",
        "",
        "## 6. Contradictions, limites et informations manquantes",
        "",
        "Une température imposée n'est pas un incendie calculé. Il manque les flux thermiques, échanges de surface, propriétés variables, humidité, état de la protection, températures spatiales et leur validation. Il manque aussi une énergie libre dépendant de T et de l'endommagement, les forces thermodynamiques, l'irréversibilité et une loi de fissuration/écrasement/plasticité à chaud avant de modifier E, ft, fc ou fy.",
        "",
        "La localisation en flexion après fracture complète reste non validée. Le succès de ces coupons numériques ne valide ni le panneau chauffé, ni la tour, ni l'impact, ni l'incendie, ni l'initiation ou la propagation d'un effondrement réel. Blender reste inchangé et sans crédit mécanique.",
        "",
        "## Suite bornée",
        "",
        result["next_objective"],
        "",
        f"Exécution finale : {result['runtime']['seconds']:.3f} s sur CPU ; Python {result['runtime']['python']}, NumPy {result['runtime']['numpy']}, Pillow {result['runtime']['Pillow']}. Graine {cfg['random_seed']}, sans tirage aléatoire. Empreinte numérique : {result['numerical_digest_sha256']}. Aucune installation, analyse vidéo, relecture d'archive, solveur externe, GPU ou modification Blender.",
        "",
        "## Livrables",
        "",
        "results_v11h.json, section_paths.json, section_paths.csv, section_fiber_states.csv, section_mesh_comparison.csv, mesh_convergence.json, energy_ledger.csv, thermal_material_ledger.json, cold_v11f_control.json, v10w_bar_replay.json, numerical_audit.json, source_manifest.json, offline_manifest.json et synthese_v11h_thermomecanique.png. L'audit de relecture séparé est ajouté dans release_audit.json avant publication locale.",
        "",
    ]
    Path(path).write_text("\n".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    cfg = read(CONFIG)
    section_cfg = read(ROOT / cfg["section_configuration"])
    directory = (ROOT / args.output).resolve()
    roots = [(ROOT / cfg[key]).resolve() for key in ("output_directory", "scratch_directory")]
    if not any(directory == root or root in directory.parents for root in roots):
        raise ValueError("Outside V11H output roots")
    if directory.exists():
        raise FileExistsError("Preserve previous output; choose a new directory")

    v11f_manifest, v11f_hashes = manifest_hashes(ROOT / cfg["cold_panel_directory"])
    v11g_manifest, v11g_hashes = manifest_hashes(ROOT / cfg["previous_iteration_directory"])
    inherited = {**v11f_hashes, **v11g_hashes}
    inherited_checks = {name: sha(ROOT / name) == value for name, value in inherited.items()}
    if not all(inherited_checks.values()):
        raise ValueError("V11F/V11G inherited hash mismatch")

    code = [
        "wtc1_simulation_v8/scripts/v11h_thermomechanical_model.py",
        "wtc1_simulation_v8/scripts/test_v11h_thermomechanical.py",
        "wtc1_simulation_v8/scripts/run_v11h_thermomechanical.py",
        "wtc1_simulation_v8/scripts/audit_v11h_release.py",
    ]
    paths = list(dict.fromkeys([
        CONFIG.relative_to(ROOT).as_posix(), cfg["section_configuration"],
        cfg["cold_panel_configuration"], cfg["cached_bar_reference"],
        *cfg["protected_files"], *code,
    ]))
    missing = [name for name in paths if not (ROOT / name).is_file()]
    if missing:
        raise FileNotFoundError(f"Missing declared input(s): {missing}")
    before = {name: sha(ROOT / name) for name in paths}

    directory.mkdir(parents=True)
    started = datetime.now(timezone.utc).isoformat()
    start = time.perf_counter()
    reference_n = cfg["discretization"]["reference_concrete_fibers"]
    steps = cfg["discretization"]["temperature_steps_per_segment"]
    reference = solve_cases(cfg, section_cfg, reference_n, steps)
    print(f"{len(reference)} bounded reference cases computed", flush=True)
    replay = solve_cases(cfg, section_cfg, reference_n, steps)
    half_step = solve_cases(cfg, section_cfg, reference_n, cfg["discretization"]["half_step_temperature_steps_per_segment"])
    mesh_runs = {}
    for fibers in cfg["discretization"]["comparison_concrete_fibers"]:
        mesh_runs[str(fibers)] = {
            run["summary"]["id"]: run for run in solve_cases(cfg, section_cfg, fibers, steps)
        }
    print("Replay, half-step and three mesh checks computed", flush=True)

    cached_bar = read(ROOT / cfg["cached_bar_reference"])
    bar = physics.cached_v10w_bar_replay(cached_bar)
    cold_control = build_cold_control(cfg)
    tests, comparisons = test_v11h_thermomechanical.run(
        cfg, section_cfg, reference, replay, half_step, mesh_runs, bar, cached_bar, cold_control
    )
    tests.append({
        "test": "reference_serialization_exact_replay_digest",
        "pass": digest(reference) == digest(replay),
        "evidence": digest(reference),
    })

    half_max = max(comparisons["half_step"].values())
    mesh_max = max(comparisons["mesh_160_to_320"].values())
    energy_max = max(run["summary"]["maximum_energy_residual_relative"] for run in reference + half_step)
    free_max = max(run["summary"]["maximum_free_resultant_residual_relative"] for run in reference + half_step)
    state_count = sum(len(run["history"]) for run in reference)
    peak_screen = max(run["summary"]["maximum_elastic_screen_ratio"] for run in reference)
    next_objective = (
        "V11I : injecter les pré-déformations et courbures thermiques élastiques qualifiées dans un seul panneau V11F borné, avec contrôle ΔT=0, température uniforme puis gradient imposé, réactions et travail des appuis ; arrêter avant toute fissuration chauffée ou limite de domaine. Formuler ensuite l'énergie libre et l'historique du matériau endommagé avant d'autoriser une loi fissurée à chaud."
    )
    runtime = {
        "started_utc": started,
        "finished_utc": datetime.now(timezone.utc).isoformat(),
        "seconds": time.perf_counter() - start,
        "python": platform.python_version(),
        "numpy": np.__version__,
        "Pillow": pillow_version,
        "executable": sys.executable,
        "OPENBLAS_NUM_THREADS": os.environ.get("OPENBLAS_NUM_THREADS"),
        "scope": "Reference/replay/half-step/mesh/cold-control/tests before report rendering",
    }
    status = "PASS" if all(test["pass"] for test in tests) else "FAIL"
    result = {
        "iteration": "V11H", "status": status,
        "test_count": len(tests), "tests_passed": sum(test["pass"] for test in tests),
        "case_count": len(reference), "state_count": state_count,
        "temperature_reference_c": cfg["thermal_properties"]["reference_temperature_c"],
        "maximum_prescribed_temperature_c": max(
            max(run["summary"]["peak"]["temperature_bottom_c"], run["summary"]["peak"]["temperature_top_c"])
            for run in reference
        ),
        "case_summaries": [run["summary"] for run in reference],
        "maxima": {
            "energy_residual_relative": energy_max,
            "free_resultant_residual_relative": free_max,
            "half_step_relative": half_max,
            "mesh_160_to_320_relative": mesh_max,
            "elastic_screen_ratio_cold_properties": peak_screen,
        },
        "cold_v11f_control_status": cold_control["status"],
        "cold_v11f_results_sha256": cold_control["results_sha256"],
        "runtime": runtime,
        "numerical_digest_sha256": digest({
            "reference": reference, "half_step": half_step,
            "mesh_summaries": {key: {case: value["summary"] for case, value in runs.items()} for key, runs in mesh_runs.items()},
            "bar": bar,
        }),
        "elastic_thermomechanical_section_references_validated": status == "PASS",
        "prescribed_temperature_only": True,
        "cold_panel_mechanics_changed": False,
        "heated_fracture_solved": False,
        "full_panel_thermomechanical_coupling_solved": False,
        "heat_transfer_solved": False,
        "fire_solved": False,
        "aircraft_impact_computed": False,
        "collapse_validated": False,
        "blender_changed": False,
        "global_energy_credit_J": 0.0,
        "next_iteration": "V11I", "next_objective": next_objective,
    }

    write_json(directory / "results_v11h.json", result)
    write_json(directory / "section_paths.json", reference)
    mesh_saved = {
        key: {case: {"summary": run["summary"], "inventory": run["inventory"]} for case, run in runs.items()}
        for key, runs in mesh_runs.items()
    }
    write_json(directory / "mesh_convergence.json", mesh_saved)
    write_csvs(directory, reference, mesh_runs)
    write_json(directory / "thermal_material_ledger.json", {
        "iteration": "V11H",
        "reference_temperature_c": cfg["thermal_properties"]["reference_temperature_c"],
        "thermal_properties": cfg["thermal_properties"],
        "section_materials": {
            "concrete": section_cfg["concrete"], "reinforcement": section_cfg["reinforcement"]
        },
        "formulas": {
            "thermal_strain": "eps_th=alpha*(T-T_ref)",
            "mechanical_strain": "eps_m=eps0-y*kappa-eps_th",
            "stress": "sigma=E*eps_m",
            "resultants": "N=sum(A*sigma); M=-sum(A*y*sigma)",
            "stored_mechanical_energy": "U=0.5*sum(A*E*eps_m^2), J/m",
            "thermoelastic_work": "W_th=-integral sum(A*sigma*d_eps_th), J/m",
            "mechanical_work": "W_mech=integral(N*d_eps0+M*d_kappa), J/m",
            "sensible_enthalpy": "H=sum(rho*cp*A*DeltaT), J/m, separate from mechanical balance",
        },
        "constitutive_exclusions": cfg["scope"],
        "temperature_field_is_fire_calculation": False,
        "global_energy_credit_J": 0.0,
    })
    write_json(directory / "cold_v11f_control.json", cold_control)
    write_json(directory / "v10w_bar_replay.json", bar)
    write_json(directory / "numerical_audit.json", {
        "iteration": "V11H", "status": status,
        "test_count": len(tests), "tests": tests, "comparisons": comparisons,
    })
    write_json(directory / "source_manifest.json", {
        "iteration": "V11H",
        "input_and_protected_sha256": before,
        "inherited_v11f_manifest_sha256": sha(ROOT / cfg["cold_panel_directory"] / "offline_manifest.json"),
        "inherited_v11g_manifest_sha256": sha(ROOT / cfg["previous_iteration_directory"] / "offline_manifest.json"),
        "inherited_manifest_checks": inherited_checks,
        "source_scope": "Saved local V10W/V11E/V11F/V11G artifacts only; no source archive rescan and no new web source required for explicitly generic hypotheses.",
        "new_archive_pdf_photo_or_video_analysis": False,
        "internet_source_used": False,
        "external_solver_or_multiagent_validation": False,
    })
    figure(directory / "synthese_v11h_thermomecanique.png", result, reference)
    report(directory / "rapport_v11h_thermomecanique.md", cfg, result, reference)

    after = {name: sha(ROOT / name) for name in paths}
    output_hashes = {path.name: sha(path) for path in sorted(directory.iterdir()) if path.is_file()}
    write_json(directory / "offline_manifest.json", {
        "iteration": "V11H", "implementation_status": status,
        "input_sha256": after, "input_and_protected_unchanged": before == after,
        "cold_v11f_control_status": cold_control["status"],
        "output_sha256": output_hashes, "manifest_excludes_itself": True,
    })
    summary = {
        "status": status, "tests": len(tests), "states": state_count,
        "runtime_seconds": runtime["seconds"], "maxima": result["maxima"],
        "cold_v11f": cold_control["status"], "inputs_unchanged": before == after,
        "failed_tests": [test for test in tests if not test["pass"]],
    }
    print(json.dumps(summary, ensure_ascii=False), flush=True)
    if status != "PASS" or cold_control["status"] != "PASS" or before != after:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
