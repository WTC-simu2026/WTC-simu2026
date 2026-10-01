"""Run and package the bounded V11I thermoelastic panel experiment."""
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

import test_v11i_thermoelastic_panel
import v11i_thermoelastic_panel_model as physics


ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "wtc1_simulation_v8/data/v11i_thermoelastic_panel_predeclaration.json"


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def digest(value):
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def write_json(path, value):
    Path(path).write_text(
        json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def write_csv(path, rows):
    rows = list(rows)
    fields = list(dict.fromkeys(key for row in rows for key in row))
    with Path(path).open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def load_inputs(cold_cfg):
    paths = {"d": cold_cfg["panel_configuration"], "e": cold_cfg["section_configuration"]}
    inputs = {key: read(ROOT / path) for key, path in paths.items()}
    paths["c"] = inputs["d"]["base_configuration"]
    inputs["c"] = read(ROOT / paths["c"])
    paths.update({
        "a": inputs["c"]["base_configuration"],
        "transfer": inputs["c"]["transfer"],
        "seats": inputs["c"]["seats"],
    })
    for key in ("a", "transfer", "seats"):
        inputs[key] = read(ROOT / paths[key])
    inputs["seats"] = inputs["seats"]["floor_truss_seats"]
    return inputs, paths


def manifest_hashes(directory):
    manifest = read(directory / "offline_manifest.json")
    expected = dict(manifest["input_sha256"])
    for name, value in manifest["output_sha256"].items():
        expected[(directory / name).relative_to(ROOT).as_posix()] = value
    return manifest, expected


def saved_control(directory, expected_iteration, expected_tests, expected_cases, expected_digest):
    manifest, expected = manifest_hashes(directory)
    hashes = {name: sha(ROOT / name) == value for name, value in expected.items()}
    results_name = "results_" + expected_iteration.lower() + ".json"
    results = read(directory / results_name)
    release = read(directory / "release_audit.json")
    identity = {
        "iteration": results["iteration"] == expected_iteration,
        "results_status": results["status"] == "PASS",
        "release_status": release["status"] == "PASS",
        "tests": results["test_count"] == results["tests_passed"] == expected_tests,
        "cases": results["case_count"] == expected_cases,
        "digest": results["numerical_digest_sha256"] == expected_digest,
        "manifest": manifest["implementation_status"] == "PASS",
    }
    return {
        "iteration": expected_iteration,
        "status": "PASS" if all(hashes.values()) and all(identity.values()) else "FAIL",
        "hash_checks": hashes,
        "identity_checks": identity,
        "results_sha256": sha(directory / results_name),
        "manifest_sha256": sha(directory / "offline_manifest.json"),
        "release_audit_sha256": sha(directory / "release_audit.json"),
        "tests": results["test_count"], "cases": results["case_count"],
        "numerical_digest_sha256": results["numerical_digest_sha256"],
    }


def cached_cold_row(cfg):
    path = ROOT / cfg["cold_panel_directory"] / "path_history.csv"
    with path.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    target = [
        row for row in rows
        if row["case_id"] == cfg["panel_case"]["cold_v11f_case_id"]
        and abs(float(row["gravity_factor"]) - cfg["loading"]["gravity_preload_factor"]) < 1e-12
    ]
    if len(target) != 1:
        raise ValueError("Expected one cached V11F quarter-gravity row")
    return target[0]


def calculate(cfg, cold_cfg, thermo_cfg, section_cfg, inputs, subdivisions=None, thermal_steps=None):
    return [
        physics.trace_case(
            cfg, cold_cfg, thermo_cfg, section_cfg, inputs, case,
            subdivisions=subdivisions, thermal_steps=thermal_steps,
        )[0]
        for case in cfg["thermal_cases"]
    ]


def static_state(cfg, cold_cfg, thermo_cfg, section_cfg, inputs, case, subdivisions, thermal_scale):
    panel = physics.ThermoElasticPanel(
        cfg, cold_cfg, thermo_cfg, section_cfg, inputs, case, subdivisions
    )
    gravity = cfg["loading"]["gravity_preload_factor"]
    preload = panel.solve(gravity, 0.0)
    state = panel.solve(gravity, thermal_scale, preload["u"])
    return state


def compare_runs(cfg, cold_cfg, thermo_cfg, section_cfg, inputs, reference, other, subdivisions, kind):
    ref_by_id = {row["summary"]["id"]: row for row in reference}
    other_by_id = {row["summary"]["id"]: row for row in other}
    case_by_id = {row["id"]: row for row in cfg["thermal_cases"]}
    floors = cfg["comparison_absolute_floors_si"]
    rows = []
    for case_id, ref in ref_by_id.items():
        alt = other_by_id[case_id]
        ref_scale = ref["summary"]["final"]["thermal_scale"]
        alt_scale = alt["summary"]["final"]["thermal_scale"]
        common = min(ref_scale, alt_scale)
        ref_state = static_state(cfg, cold_cfg, thermo_cfg, section_cfg, inputs, case_by_id[case_id], 4, common)
        alt_state = static_state(cfg, cold_cfg, thermo_cfg, section_cfg, inputs, case_by_id[case_id], subdivisions, common)
        groups = {
            "displacement": (
                ("max_slab_down_m", floors["displacement_m"]),
                ("max_slab_up_m", floors["displacement_m"]),
                ("max_truss_down_m", floors["displacement_m"]),
                ("max_opening_m", floors["displacement_m"]),
                ("max_overlap_m", floors["displacement_m"]),
            ),
            "reaction": (
                ("seat_vertical_reaction_N", floors["force_N"]),
                ("seat_horizontal_reaction_N", floors["force_N"]),
            ),
            "energy": (
                ("stored_J", floors["energy_J"]),
                ("spring_stored_J", floors["energy_J"]),
                ("slab_stored_J", floors["energy_J"]),
                ("sensible_enthalpy_J", floors["energy_J"]),
            ),
        }
        errors = {}
        field_errors = {}
        for group, fields in groups.items():
            values = []
            for field, floor in fields:
                error = abs(float(ref_state[field]) - float(alt_state[field])) / max(floor, abs(float(ref_state[field])))
                field_errors[field] = error
                values.append(error)
            errors[group] = max(values)
        scale_absolute = abs(ref_scale - alt_scale)
        scale_relative = scale_absolute / max(1e-9, abs(ref_scale))
        same_terminal = ref["summary"]["terminal"] == alt["summary"]["terminal"]
        if kind == "half_step":
            gates = {
                "terminal": same_terminal,
                "scale": scale_absolute <= cfg["acceptance"]["half_step_terminal_scale_absolute"],
                "displacement": errors["displacement"] <= cfg["acceptance"]["half_step_common_response_relative"],
                "reaction": errors["reaction"] <= cfg["acceptance"]["half_step_common_response_relative"],
                "energy": errors["energy"] <= cfg["acceptance"]["half_step_common_response_relative"],
            }
        else:
            gates = {
                "terminal": same_terminal,
                "scale": scale_relative <= cfg["acceptance"]["mesh_terminal_scale_relative"],
                "displacement": errors["displacement"] <= cfg["acceptance"]["mesh_common_displacement_relative"],
                "reaction": errors["reaction"] <= cfg["acceptance"]["mesh_common_reaction_relative"],
                "energy": errors["energy"] <= cfg["acceptance"]["mesh_common_energy_relative"],
            }
        rows.append({
            "case_id": case_id, "comparison": kind, "other_subdivisions": subdivisions,
            "reference_terminal": ref["summary"]["terminal"], "other_terminal": alt["summary"]["terminal"],
            "reference_terminal_scale": ref_scale, "other_terminal_scale": alt_scale,
            "common_scale": common, "terminal_scale_absolute_difference": scale_absolute,
            "terminal_scale_relative_difference": scale_relative,
            "displacement_relative_difference": errors["displacement"],
            "reaction_relative_difference": errors["reaction"],
            "energy_relative_difference": errors["energy"],
            "field_relative_differences": field_errors, "gates": gates, "pass": all(gates.values()),
        })
    return rows


def flatten_outputs(directory, reference, comparisons, mesh_runs):
    write_json(directory / "panel_paths.json", reference)
    write_csv(directory / "path_history.csv", (
        state for data in reference for state in data["history"]
    ))
    write_csv(directory / "panel_section_states.csv", (
        row for data in reference for row in data["sections"]
    ))
    write_csv(directory / "critical_fiber_states.csv", (
        row for data in reference for row in data["critical_fibers"]
    ))
    write_csv(directory / "connection_forces.csv", (
        row for data in reference for row in data["terms"]
    ))
    write_csv(directory / "slab_nodes.csv", (
        row for data in reference for row in data["slab_nodes"]
    ))
    energy_rows = []
    for data in reference:
        for state in data["history"]:
            energy_rows.append({
                key: state[key] for key in (
                    "case_id", "phase", "gravity_factor", "thermal_scale",
                    "slab_bottom_temperature_c", "slab_top_temperature_c",
                    "mechanical_external_work_J", "thermoelastic_work_J", "stored_J",
                    "spring_stored_J", "slab_stored_J", "sensible_enthalpy_J",
                    "total_mechanical_energy_residual_relative", "maximum_increment_energy_residual_relative",
                    "support_work_J", "dissipated_J", "global_energy_credit_J",
                )
            })
    write_csv(directory / "energy_ledger.csv", energy_rows)
    comparison_rows = []
    for row in comparisons["half_step"]:
        comparison_rows.append({key: value for key, value in row.items() if key not in ("field_relative_differences", "gates")})
    for mesh_rows in comparisons["mesh"].values():
        for row in mesh_rows:
            comparison_rows.append({key: value for key, value in row.items() if key not in ("field_relative_differences", "gates")})
    write_csv(directory / "discretization_comparison.csv", comparison_rows)
    mesh_summary = {
        key: [
            {"summary": data["summary"], "inventory": data["inventory"]}
            for data in runs
        ]
        for key, runs in mesh_runs.items()
    }
    write_json(directory / "mesh_runs.json", mesh_summary)


def font(size, bold=False):
    path = "C:/Windows/Fonts/segoeui" + ("b" if bold else "") + ".ttf"
    try:
        return ImageFont.truetype(path, size)
    except OSError:
        return ImageFont.load_default()


def figure(path, result):
    summaries = {row["id"]: row for row in result["case_summaries"]}
    cold = summaries["COLD_DELTA_T_ZERO"]["final"]
    uniform = summaries["SLAB_UNIFORM_100K"]["final"]
    gradient = summaries["SLAB_GRADIENT_TOP_100K"]["final"]
    image = Image.new("RGB", (1600, 1120), "#eef3f6")
    draw = ImageDraw.Draw(image)

    def text(x, y, value, size=20, color="#263e50", bold=False):
        draw.text((x, y), value, font=font(size, bold), fill=color)

    def card(box):
        draw.rounded_rectangle(box, radius=17, fill="white", outline="#d2dde4", width=2)

    text(42, 23, "WTC 1 / V11I — dalle thermoélastique dans un panneau", 34, bold=True)
    text(43, 73, "Un panneau R02, températures de dalle imposées, arrêt avant le domaine non linéaire.", 23)
    card((35, 122, 1565, 280))
    text(60, 143, f"{result['tests_passed']}/{result['test_count']} contrôles numériques réussis", 29, bold=True)
    text(60, 192, "V11F froid retrouvé dans les fichiers sauvegardés ; aucune ancienne itération modifiée.", 22)
    text(60, 232, "Travail de gravité + travail thermoélastique = énergie mécanique stockée.", 22)

    cards = [(35, 325, 520, 835), (558, 325, 1043, 835), (1080, 325, 1565, 835)]
    for box in cards:
        card(box)
    text(60, 347, "ΔT = 0", 26, bold=True)
    text(60, 400, f"Gravité : {cold['gravity_factor']:.2f}", 21)
    text(60, 440, f"Flèche dalle : {1000*cold['max_slab_down_m']:.2f} mm", 21)
    text(60, 480, f"DCR max : {cold['max_DCR']:.3f}", 21)
    text(60, 540, "Contrôle V11F froid", 21, color="#267a55", bold=True)
    text(60, 578, "reproduit à partir du", 20)
    text(60, 612, "point sauvegardé à 0,25 g.", 20)

    text(583, 347, "Uniforme", 26, bold=True)
    text(583, 400, f"T dalle : {uniform['slab_top_temperature_c']:.2f} °C", 21)
    text(583, 440, f"Échelle atteinte : {uniform['thermal_scale']:.4f}", 21)
    text(583, 480, f"DCR max : {uniform['max_DCR']:.3f}", 21)
    text(583, 525, f"Déplacement haut : {1000*uniform['max_slab_up_m']:.2f} mm", 21)
    text(583, 570, f"W thermo : {uniform['thermoelastic_work_J']/1000:.2f} kJ", 21)
    text(583, 638, summaries["SLAB_UNIFORM_100K"]["terminal"].replace("_", " "), 16, color="#9a5c18", bold=True)

    text(1105, 347, "Gradient", 26, bold=True)
    text(1105, 400, f"Faces : {gradient['slab_bottom_temperature_c']:.1f}/{gradient['slab_top_temperature_c']:.1f} °C", 21)
    text(1105, 440, f"Échelle atteinte : {gradient['thermal_scale']:.4f}", 21)
    text(1105, 480, f"DCR max : {gradient['max_DCR']:.3f}", 21)
    text(1105, 525, f"Déplacement haut : {1000*gradient['max_slab_up_m']:.2f} mm", 21)
    text(1105, 570, f"W thermo : {gradient['thermoelastic_work_J']/1000:.2f} kJ", 21)
    text(1105, 638, summaries["SLAB_GRADIENT_TOP_100K"]["terminal"].replace("_", " "), 16, color="#9a5c18", bold=True)

    card((35, 875, 1565, 1085))
    text(60, 898, "Limite d'interprétation", 25, bold=True)
    text(60, 944, "Le garde-fou DCR=0,90 arrête les parcours avant fissuration, plastification ou limite de composant.", 21)
    text(60, 983, "Le champ thermique est imposé : pas de conduction, feu calculé, propriétés dégradées ou fracture chaude.", 21)
    text(60, 1022, "Énergies locales du panneau uniquement ; aucun crédit d'impact, d'effondrement ou Blender.", 21)
    image.save(path)


def report(path, cfg, result, reference, comparisons, cached):
    summaries = {row["summary"]["id"]: row["summary"] for row in reference}
    lines = [
        "# V11I — couplage thermoélastique borné d'un panneau",
        "",
        "## Résultat",
        "",
        f"V11I passe {result['tests_passed']}/{result['test_count']} contrôles numériques et son audit de fichiers doit être exécuté séparément avant publication. Un seul panneau équivalent V11F R02 reçoit les déformations thermiques V11H de la dalle, à 25 % de la gravité de référence. Trois parcours sont calculés : DeltaT=0, température uniforme et gradient dans l'épaisseur.",
        "",
        "Les états acceptés restent sous le garde-fou DCR=0,90. Une tentative qui atteint ce seuil est seulement utilisée pour le borner ; elle n'est pas engagée. Aucune fissuration, plastification, rupture ou propriété dégradée n'est calculée.",
        "",
        "## 1. Faits directement observés ou transcrits",
        "",
        f"Le point COLD_R02 sauvegardé par V11F à un facteur de gravité 0,25 contient une énergie mécanique de {float(cached['stored_J']):.9f} J, une flèche de dalle de {1000*float(cached['max_slab_down_m']):.6f} mm et une réaction verticale de {float(cached['seat_reaction_N'])/1000:.6f} kN. V11I le relit par empreinte et le reproduit sans relancer le pilote V11F.",
        "",
        "Le panneau conserve 33 nœuds de treillis, 63 barres, 65 nœuds de dalle, 64 éléments de dalle, 128 sections de Gauss et 17 stations de contact au maillage de référence. Les anciens fichiers V11F/V11H et le fichier Blender maître sont protégés par empreinte.",
        "",
        "## 2. Résultats d'un modèle officiel",
        "",
        "Aucun nouveau résultat officiel n'est introduit. Les géométries équivalentes et capacités déjà héritées restent dépendantes de leurs transcriptions et hypothèses antérieures.",
        "",
        "## 3. Affirmations provenant des archives locales",
        "",
        "Aucune archive, photographie, vidéo ou nouvelle donnée historique n'est examinée dans V11I.",
        "",
        "## 4. Hypothèses propres au modèle",
        "",
        "La dalle seule reçoit un champ uniforme ou linéaire dans l'épaisseur, identique le long de la portée. Le treillis, les sièges, les contacts et les attaches restent à 20 °C. Les propriétés thermoélastiques constantes sont celles de V11H et le ferraillage R02 reste exploratoire, non as-built.",
        "",
        "La déformation de section est eps(y)=eps0-y*kappa ; eps_th=alpha*DeltaT ; sigma=E(eps-eps_th). Les résultantes de section sont intégrées aux deux points de Gauss de chaque élément. Le béton est seulement élastique jusqu'aux écrans froids ft/fc ; l'armature seulement élastique jusqu'à fy. Les composants gardent leurs lois élastiques V11F.",
        "",
        "L'énergie mécanique du panneau additionne dalle et ressorts. Le travail mécanique extérieur intègre la gravité ; le travail thermoélastique vaut moins l'intégrale de sigma d eps_th dans la dalle. Leur somme doit égaler l'énergie mécanique stockée. L'enthalpie sensible est enregistrée séparément et n'entre pas dans ce bilan. Les appuis fixes ont un travail nul, même avec réactions non nulles.",
        "",
        "## 5. Résultats dérivés",
        "",
        "| Parcours | État terminal | Échelle thermique | Faces dalle (°C) | DCR max | Gouvernant | Flèche bas/haut dalle (mm) | Réaction V/H (kN) | U (kJ) | Wthermo (kJ) | H sensible (MJ) |",
        "|---|---|---:|---:|---:|---|---:|---:|---:|---:|---:|",
    ]
    for case in cfg["thermal_cases"]:
        summary = summaries[case["id"]]
        final = summary["final"]
        lines.append(
            f"| {case['id']} | {summary['terminal']} | {final['thermal_scale']:.8f} | {final['slab_bottom_temperature_c']:.3f}/{final['slab_top_temperature_c']:.3f} | {final['max_DCR']:.9f} | {final['governing_kind']} / {final['governing_id']} | {1000*final['max_slab_down_m']:.4f}/{1000*final['max_slab_up_m']:.4f} | {final['seat_vertical_reaction_N']/1000:.4f}/{final['seat_horizontal_reaction_N']/1000:.4f} | {final['stored_J']/1000:.6f} | {final['thermoelastic_work_J']/1000:.6f} | {final['sensible_enthalpy_J']/1e6:.6f} |"
        )
    lines += [
        "",
        f"Résidu d'équilibre maximal : {result['maxima']['equilibrium_relative']:.3e}. Résidu incrémental maximal du bilan énergie : {result['maxima']['increment_energy_relative']:.3e}. Résidu total maximal : {result['maxima']['total_energy_relative']:.3e}.",
        "",
        f"Le demi-pas passe {sum(row['pass'] for row in comparisons['half_step'])}/{len(comparisons['half_step'])} parcours. Le raffinement 4 vers 8 subdivisions passe {sum(row['pass'] for row in comparisons['mesh']['8'])}/{len(comparisons['mesh']['8'])} parcours. Le maillage 2 reste un diagnostic grossier séparé.",
        "",
        "## 6. Contradictions, limites et informations manquantes",
        "",
        "La température est imposée, non calculée. Il manque une conduction transitoire validée, les échanges de surface, l'état SFRM, l'humidité et une histoire d'incendie. L'arrêt à 0,90 n'est ni une température critique réelle ni une prédiction de rupture : sa valeur dépend des propriétés, capacités et détails hypothétiques du panneau.",
        "",
        "La loi V11E endommagée n'est jamais appelée à chaud. Avant toute fissuration chauffée, il faut formuler une énergie libre dépendant de la température et de l'historique, ses forces thermodynamiques et l'irréversibilité. La localisation en flexion après fracture complète reste non validée.",
        "",
        "Ce panneau local à petits déplacements ne valide ni la structure spatiale, ni l'impact, ni l'incendie, ni l'initiation, l'arrêt ou la propagation d'un effondrement réel. Blender reste inchangé et sans crédit mécanique.",
        "",
        "## Suite bornée",
        "",
        result["next_objective"],
        "",
        f"Exécution : {result['runtime']['seconds']:.3f} s sur CPU ; Python {result['runtime']['python']}, NumPy {result['runtime']['numpy']}, Pillow {result['runtime']['Pillow']}. Graine {cfg['random_seed']}, sans tirage aléatoire. Empreinte numérique : {result['numerical_digest_sha256']}. Aucun GPU, solveur externe, réseau, rescannage d'archive ou Blender.",
        "",
    ]
    Path(path).write_text("\n".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    cfg = read(CONFIG)
    cold_cfg = read(ROOT / cfg["cold_panel_configuration"])
    thermo_cfg = read(ROOT / cfg["thermomechanical_configuration"])
    section_cfg = read(ROOT / cfg["section_configuration"])
    inputs, input_paths = load_inputs(cold_cfg)
    directory = (ROOT / args.output).resolve()
    roots = [(ROOT / cfg[key]).resolve() for key in ("output_directory", "scratch_directory")]
    if not any(directory == root or root in directory.parents for root in roots):
        raise ValueError("Outside V11I output roots")
    if directory.exists():
        raise FileExistsError("Preserve previous output; choose a new directory")

    v11f = saved_control(
        ROOT / cfg["cold_panel_directory"], "V11F", 132, 14,
        "14c653db4392244bc377a41705597d40adbc687fbd4afc92ffb33389d1c3ccff",
    )
    v11h = saved_control(
        ROOT / cfg["thermomechanical_directory"], "V11H", 27, 11,
        "a7a39e9a1a4f00709e390da28766c66806b81e9696a25eae1a5b82effa616f8e",
    )
    if v11f["status"] != "PASS" or v11h["status"] != "PASS":
        raise ValueError("Inherited V11F/V11H control failed")
    cached = cached_cold_row(cfg)

    code = [
        "wtc1_simulation_v8/scripts/v11i_thermoelastic_panel_model.py",
        "wtc1_simulation_v8/scripts/test_v11i_thermoelastic_panel.py",
        "wtc1_simulation_v8/scripts/run_v11i_thermoelastic_panel.py",
        "wtc1_simulation_v8/scripts/audit_v11i_release.py",
    ]
    paths = list(dict.fromkeys([
        CONFIG.relative_to(ROOT).as_posix(), cfg["cold_panel_configuration"],
        cfg["thermomechanical_configuration"], cfg["section_configuration"],
        *input_paths.values(), *cfg["protected_files"], *code,
    ]))
    missing = [path for path in paths if not (ROOT / path).is_file()]
    if missing:
        raise FileNotFoundError(f"Missing declared input(s): {missing}")
    before = {path: sha(ROOT / path) for path in paths}

    directory.mkdir(parents=True)
    started = datetime.now(timezone.utc).isoformat()
    start = time.perf_counter()
    reference = calculate(cfg, cold_cfg, thermo_cfg, section_cfg, inputs)
    print("Three reference thermoelastic panel paths computed", flush=True)
    replay = calculate(cfg, cold_cfg, thermo_cfg, section_cfg, inputs)
    half_step = calculate(
        cfg, cold_cfg, thermo_cfg, section_cfg, inputs,
        thermal_steps=cfg["loading"]["half_step_thermal_steps"],
    )
    mesh_runs = {
        str(sub): calculate(cfg, cold_cfg, thermo_cfg, section_cfg, inputs, subdivisions=sub)
        for sub in cfg["discretization"]["comparison_subdivisions"]
    }
    comparisons = {
        "half_step": compare_runs(
            cfg, cold_cfg, thermo_cfg, section_cfg, inputs,
            reference, half_step, 4, "half_step",
        ),
        "mesh": {
            key: compare_runs(
                cfg, cold_cfg, thermo_cfg, section_cfg, inputs,
                reference, run, int(key), "mesh",
            )
            for key, run in mesh_runs.items()
        },
    }
    print("Replay, half-step and two panel meshes computed", flush=True)

    tests = test_v11i_thermoelastic_panel.run(
        cfg, cold_cfg, thermo_cfg, section_cfg, inputs, reference, replay, half_step,
        mesh_runs, comparisons, cached, v11f, v11h,
    )
    tests.append({
        "test": "serialized_reference_digest_replay",
        "pass": digest(reference) == digest(replay),
        "evidence": digest(reference),
    })
    status = "PASS" if all(test["pass"] for test in tests) else "FAIL"
    histories = [state for run in reference + half_step for state in run["history"]]
    runtime = {
        "started_utc": started, "finished_utc": datetime.now(timezone.utc).isoformat(),
        "seconds": time.perf_counter() - start, "python": platform.python_version(),
        "numpy": np.__version__, "Pillow": pillow_version, "executable": sys.executable,
        "OPENBLAS_NUM_THREADS": os.environ.get("OPENBLAS_NUM_THREADS"),
        "scope": "Reference/replay/half-step/two meshes/static common-scale comparisons/tests before rendering",
    }
    next_objective = (
        "V11J : qualifier un coupon unidimensionnel de conduction transitoire dans l'épaisseur de la dalle équivalente, d'abord avec propriétés constantes et références analytiques, puis bilan flux-enthalpie et raffinement espace-temps. Ne relier aucun flux à un incendie WTC avant de disposer de conditions aux limites sourcées ; ne pas activer de fissuration chaude."
    )
    result = {
        "iteration": "V11I", "status": status,
        "test_count": len(tests), "tests_passed": sum(test["pass"] for test in tests),
        "case_count": len(reference), "reference_state_count": sum(len(run["history"]) for run in reference),
        "case_summaries": [run["summary"] for run in reference],
        "maxima": {
            "equilibrium_relative": max(state["equilibrium_residual"] for state in histories),
            "increment_energy_relative": max(state["maximum_increment_energy_residual_relative"] for state in histories),
            "total_energy_relative": max(state["total_mechanical_energy_residual_relative"] for state in histories),
            "accepted_DCR": max(state["max_DCR"] for state in histories),
            "half_step_terminal_scale_absolute": max(row["terminal_scale_absolute_difference"] for row in comparisons["half_step"]),
            "fine_mesh_terminal_scale_relative": max(row["terminal_scale_relative_difference"] for row in comparisons["mesh"]["8"]),
            "fine_mesh_displacement_relative": max(row["displacement_relative_difference"] for row in comparisons["mesh"]["8"]),
            "fine_mesh_reaction_relative": max(row["reaction_relative_difference"] for row in comparisons["mesh"]["8"]),
            "fine_mesh_energy_relative": max(row["energy_relative_difference"] for row in comparisons["mesh"]["8"]),
        },
        "cold_v11f_control_status": v11f["status"],
        "thermoelastic_v11h_control_status": v11h["status"],
        "runtime": runtime,
        "numerical_digest_sha256": digest({
            "reference": reference, "half_step": half_step,
            "mesh_summaries": {key: [row["summary"] for row in run] for key, run in mesh_runs.items()},
            "comparisons": comparisons,
        }),
        "bounded_elastic_panel_thermomechanical_coupling_validated": status == "PASS",
        "temperature_is_prescribed_not_calculated": True,
        "accepted_heated_crack_state_count": 0,
        "material_properties_degraded": False,
        "heat_transfer_solved": False, "fire_solved": False,
        "geometric_nonlinearity_solved": False, "aircraft_impact_computed": False,
        "collapse_validated": False, "blender_changed": False,
        "global_energy_credit_J": 0.0,
        "next_iteration": "V11J", "next_objective": next_objective,
    }

    write_json(directory / "results_v11i.json", result)
    flatten_outputs(directory, reference, comparisons, mesh_runs)
    write_json(directory / "half_step_paths.json", half_step)
    write_json(directory / "discretization_comparison.json", comparisons)
    write_json(directory / "cold_and_thermoelastic_controls.json", {
        "V11F": v11f, "V11H": v11h, "cached_V11F_quarter_gravity_row": cached,
        "old_drivers_reexecuted": False,
    })
    write_json(directory / "material_and_scope_ledger.json", {
        "iteration": "V11I", "panel_case": cfg["panel_case"],
        "scope": cfg["scope"], "loading": cfg["loading"],
        "thermal_properties": thermo_cfg["thermal_properties"],
        "section_cold_properties": {
            "concrete": section_cfg["concrete"], "reinforcement": section_cfg["reinforcement"]
        },
        "formulas": {
            "thermal_strain": "eps_th=alpha*(T-T_ref)",
            "mechanical_strain": "eps_m=eps0-y*kappa-eps_th",
            "stress": "sigma=E*eps_m",
            "panel_mechanical_balance": "Delta U=W_gravity+W_thermoelastic",
            "thermoelastic_work": "W_th=-integral_panel sum_fibers(A*sigma*d_eps_th)",
            "support_work": "zero because eliminated ground coordinates are fixed",
            "sensible_enthalpy": "H=integral_panel sum_fibers(rho*cp*A*DeltaT), separate from mechanical balance",
        },
        "no_damage_history_or_property_updated": True,
        "global_energy_credit_J": 0.0,
    })
    write_json(directory / "numerical_audit.json", {
        "iteration": "V11I", "status": status, "test_count": len(tests),
        "tests": tests, "comparisons": comparisons,
    })
    write_json(directory / "source_manifest.json", {
        "iteration": "V11I", "input_and_protected_sha256": before,
        "V11F_control": v11f, "V11H_control": v11h,
        "source_scope": "Saved local V11F/V11H artifacts and inherited configurations only; no archive rescan, video analysis or new web source.",
        "new_archive_pdf_photo_or_video_analysis": False,
        "internet_source_used": False, "external_solver_or_multiagent_validation": False,
    })
    figure(directory / "synthese_v11i_panneau_thermoelastique.png", result)
    report(directory / "rapport_v11i_panneau_thermoelastique.md", cfg, result, reference, comparisons, cached)

    after = {path: sha(ROOT / path) for path in paths}
    write_json(directory / "offline_manifest.json", {
        "iteration": "V11I", "implementation_status": status,
        "input_sha256": after, "input_and_protected_unchanged": before == after,
        "V11F_control_status": v11f["status"], "V11H_control_status": v11h["status"],
        "output_sha256": {path.name: sha(path) for path in sorted(directory.iterdir()) if path.is_file()},
        "manifest_excludes_itself": True,
    })
    summary = {
        "status": status, "tests": len(tests), "states": result["reference_state_count"],
        "runtime_seconds": runtime["seconds"], "maxima": result["maxima"],
        "V11F": v11f["status"], "V11H": v11h["status"],
        "inputs_unchanged": before == after,
        "failed_tests": [test for test in tests if not test["pass"]],
    }
    print(json.dumps(summary, ensure_ascii=False), flush=True)
    if status != "PASS" or before != after:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
