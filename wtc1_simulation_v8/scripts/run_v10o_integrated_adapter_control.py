from __future__ import annotations

import copy
import csv
import hashlib
import json
import math
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from v10o_coupling_adapters import (
    CONTRACTS,
    EPISTEMIC_CLASS,
    INTERFACE_ORDER,
    ContractError,
    build_control_records,
    canonical_digest,
    exported_contracts,
    missing_field_negative,
    validate_record,
)


ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "wtc1_simulation_v8/data/v10o_integrated_adapter_control.json"
SCRIPT_PATH = Path(__file__).resolve()
ADAPTER_PATH = Path(__file__).resolve().with_name("v10o_coupling_adapters.py")


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as stream:
        return json.load(stream)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as stream:
        json.dump(payload, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as stream:
        stream.write(content.rstrip() + "\n")


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def abs_path(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def verify_hash(item: dict[str, Any]) -> dict[str, Any]:
    path = abs_path(item["path"])
    role = item.get("role", item.get("id", "file"))
    if not path.is_file():
        raise RuntimeError(f"Missing {role}: {path}")
    actual = sha256_file(path)
    if actual.lower() != item["expected_sha256"].lower():
        raise RuntimeError(f"Hash mismatch for {role}: expected {item['expected_sha256']}, got {actual}")
    return {"role": role, "path": rel(path), "sha256": actual, "bytes": path.stat().st_size, "status": "PASS"}


def load_config() -> dict[str, Any]:
    config = load_json(CONFIG_PATH)
    if config.get("iteration") != "V10O":
        raise RuntimeError("Configuration iteration must be V10O")
    expected = config["expected"]
    counts = {
        "regression_file_count": len(config["regression_files"]),
        "protected_file_count": len(config["protected_files"]),
        "cached_baseline_count": len(config["cached_baselines"]),
        "interface_count": len(config["required_interface_ids"]),
    }
    for key, actual in counts.items():
        if actual != expected[key]:
            raise RuntimeError(f"Unexpected {key}: {actual} != {expected[key]}")
    if config["required_interface_ids"] != INTERFACE_ORDER:
        raise RuntimeError("V10O interface order differs from the implemented adapter order")
    if set(config["cached_replay_expectations"]) != {item["id"] for item in config["cached_baselines"]}:
        raise RuntimeError("Cached replay expectation ids differ from cached baseline ids")
    control = config["control_scenario"]
    if control["scenario_class"] != "SYNTHETIC_SOFTWARE_CONTROL":
        raise RuntimeError("Control scenario class mismatch")
    if control["epistemic_class"] != EPISTEMIC_CLASS:
        raise RuntimeError("Control epistemic class mismatch")
    if control["historical_event_claim"] or control["values_are_wtc_properties"]:
        raise RuntimeError("V10O control must not make a historical or WTC property claim")
    return config


def close(left: float, right: float, tolerance: float) -> bool:
    return math.isclose(float(left), float(right), rel_tol=0.0, abs_tol=tolerance)


def cached_baseline_replay(config: dict[str, Any]) -> dict[str, Any]:
    items = {item["id"]: item for item in config["cached_baselines"]}
    expected = config["cached_replay_expectations"]
    checks: list[dict[str, Any]] = []

    v8s_path = abs_path(items["V8S_IMPACT_KINEMATICS"]["path"])
    v8s = load_json(v8s_path)
    target = expected["V8S_IMPACT_KINEMATICS"]
    base = v8s["derived_results"]["cases"][target["case"]]
    mass = float(base["inputs"]["mass_kg"])
    speed = float(base["inputs"]["speed_mps"])
    calculated_energy_gj = 0.5 * mass * speed**2 / 1e9
    calculated_momentum_mn_s = mass * speed / 1e6
    tolerance = float(target["absolute_tolerance"])
    v8s_assertions = {
        "mass_matches": close(mass, target["mass_kg"], tolerance),
        "speed_matches": close(speed, target["speed_mps"], tolerance),
        "kinetic_energy_recomputed_matches": close(calculated_energy_gj, target["kinetic_energy_gj"], tolerance),
        "momentum_recomputed_matches": close(calculated_momentum_mn_s, target["momentum_total_mn_s"], tolerance),
    }
    checks.append(
        {
            "id": "V8S_IMPACT_KINEMATICS",
            "status": "PASS" if all(v8s_assertions.values()) else "FAIL",
            "source": {"path": rel(v8s_path), "sha256": sha256_file(v8s_path)},
            "assertions": v8s_assertions,
            "observed": {
                "mass_kg": mass,
                "speed_mps": speed,
                "kinetic_energy_gj_stored": base["derived_kinematics"]["kinetic_energy_gj"],
                "kinetic_energy_gj_recomputed": calculated_energy_gj,
                "momentum_total_mn_s_stored": base["derived_kinematics"]["momentum_total_mn_s"],
                "momentum_total_mn_s_recomputed": calculated_momentum_mn_s,
            },
            "scope": "Arithmetic replay of the cached base kinematics only; no damage, force, impulse, breakup or collapse credit.",
        }
    )

    v8e_path = abs_path(items["V8E_SYNTHETIC_THERMAL_FIELDS"]["path"])
    v8e = load_json(v8e_path)
    target = expected["V8E_SYNTHETIC_THERMAL_FIELDS"]
    first_case = v8e["deterministic_cases"][0]
    v8e_assertions = {
        "ensemble_seed_count": v8e["ensemble"]["seeds"] == target["ensemble_seeds"],
        "gamma_values": v8e["ensemble"]["gamma_values"] == target["gamma_values"],
        "probability_prohibition": v8e["ensemble"]["fields_are_probabilities"] is target["fields_are_probabilities"],
        "deterministic_case_count": len(v8e["deterministic_cases"]) == target["deterministic_case_count"],
        "smooth_field_case_count": len(v8e["smooth_field_ensemble"]) == target["smooth_field_case_count"],
        "first_case_time": first_case["time_min"] == target["first_case_time_min"],
        "first_case_field": first_case["field"] == target["first_case_field"],
        "first_case_equilibrium_flag": first_case["system_equilibrium_all_floors"] is target["first_case_system_equilibrium_all_floors"],
    }
    checks.append(
        {
            "id": "V8E_SYNTHETIC_THERMAL_FIELDS",
            "status": "PASS" if all(v8e_assertions.values()) else "FAIL",
            "source": {"path": rel(v8e_path), "sha256": sha256_file(v8e_path)},
            "assertions": v8e_assertions,
            "observed": {
                "ensemble_seeds": v8e["ensemble"]["seeds"],
                "gamma_values": v8e["ensemble"]["gamma_values"],
                "fields_are_probabilities": v8e["ensemble"]["fields_are_probabilities"],
                "deterministic_case_count": len(v8e["deterministic_cases"]),
                "smooth_field_case_count": len(v8e["smooth_field_ensemble"]),
            },
            "scope": "Cached synthetic-field identity/control only; fields are not measured member temperatures or event probabilities.",
        }
    )

    v8j_path = abs_path(items["V8J_COLD_GATE"]["path"])
    v8j = load_json(v8j_path)
    target = expected["V8J_COLD_GATE"]
    observed_v8j = {key: v8j["gate_result"][key] for key in target}
    v8j_assertions = {key: observed_v8j[key] == value for key, value in target.items()}
    checks.append(
        {
            "id": "V8J_COLD_GATE",
            "status": "PASS" if all(v8j_assertions.values()) else "FAIL",
            "source": {"path": rel(v8j_path), "sha256": sha256_file(v8j_path)},
            "assertions": v8j_assertions,
            "observed": observed_v8j,
            "scope": "Replays the failed cold-gate status; it does not turn failure of a reduced model into a historical mechanism conclusion.",
        }
    )

    v8l_path = abs_path(items["V8L_MULTISTORY_COLD"]["path"])
    v8l = load_json(v8l_path)
    target = expected["V8L_MULTISTORY_COLD"]
    observed_v8l = {key: v8l["summary"][key] for key in target}
    v8l_assertions = {key: observed_v8l[key] == value for key, value in target.items()}
    checks.append(
        {
            "id": "V8L_MULTISTORY_COLD",
            "status": "PASS" if all(v8l_assertions.values()) else "FAIL",
            "source": {"path": rel(v8l_path), "sha256": sha256_file(v8l_path)},
            "assertions": v8l_assertions,
            "observed": observed_v8l,
            "scope": "Cached reduced topology diagnostic only; missing load paths and physical properties remain blocking.",
        }
    )

    v9m_path = abs_path(items["V9M_IMPACT_BRANCH_CLOSURE"]["path"])
    v9m = load_json(v9m_path)
    target = expected["V9M_IMPACT_BRANCH_CLOSURE"]
    observed_v9m = {
        "numerically_qualified": v9m["qualification_counts"]["numerically_qualified"],
        "conditional_numerical": v9m["qualification_counts"]["conditional_numerical"],
        "failed_or_physically_unqualified": v9m["qualification_counts"]["failed_or_physically_unqualified"],
        "visualization_only": v9m["qualification_counts"]["visualization_only"],
        "physical_track_met_trigger_count": v9m["physical_track_met_trigger_count"],
        "physical_track_reopening_authorized": v9m["physical_track_reopening_authorized"],
        "global_wtc_impact_physics_qualification_passed": v9m["global_wtc_impact_physics_qualification_passed"],
    }
    v9m_assertions = {key: observed_v9m[key] == value for key, value in target.items()}
    checks.append(
        {
            "id": "V9M_IMPACT_BRANCH_CLOSURE",
            "status": "PASS" if all(v9m_assertions.values()) else "FAIL",
            "source": {"path": rel(v9m_path), "sha256": sha256_file(v9m_path)},
            "assertions": v9m_assertions,
            "observed": observed_v9m,
            "scope": "Preserves the closed physical-impact gate; no solver branch is reopened.",
        }
    )

    failed = [item["id"] for item in checks if item["status"] != "PASS"]
    if failed:
        raise RuntimeError(f"Cached baseline replay failed: {failed}")
    return {
        "iteration": "V10O",
        "generated_at_utc": utc_now(),
        "validation_status": "PASS",
        "baseline_count": len(checks),
        "passed_count": len(checks),
        "failed_count": 0,
        "checks": checks,
        "interpretation": "These are identity and arithmetic replays of cached records. No prior physical scope or failed gate changes.",
    }


def validate_adapters(records: dict[str, dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    matrix: list[dict[str, Any]] = []
    details: list[dict[str, Any]] = []
    for index, interface_id in enumerate(INTERFACE_ORDER, start=1):
        record = records[interface_id]
        positive = validate_record(interface_id, record)
        negative, missing_field = missing_field_negative(interface_id, record)
        negative_rejected = False
        error_message = None
        try:
            validate_record(interface_id, negative)
        except ContractError as exc:
            negative_rejected = True
            error_message = str(exc)
        if not negative_rejected:
            raise RuntimeError(f"Negative missing-field test was not rejected for {interface_id}")
        contract = CONTRACTS[interface_id]
        matrix.append(
            {
                "step": index,
                "interface_id": interface_id,
                "producer": contract["producer"],
                "consumer": contract["consumer"],
                "schema_id": contract["schema_id"],
                "positive_validation": "PASS_SOFTWARE_CONTRACT_ONLY",
                "negative_test": f"REMOVE_PAYLOAD_FIELD:{missing_field}",
                "negative_rejected": True,
                "required_payload_field_count": positive["required_payload_field_count"],
                "unit_field_count": positive["unit_field_count"],
                "physical_ready": False,
                "physical_credit": "NONE",
            }
        )
        details.append(
            {
                "interface_id": interface_id,
                "positive": positive,
                "negative": {
                    "mutation": f"removed payload.{missing_field}",
                    "rejected": True,
                    "expected_error": error_message,
                },
                "record_digest": canonical_digest(record),
            }
        )
    return matrix, details


def cross_interface_checks(records: dict[str, dict[str, Any]], config: dict[str, Any]) -> dict[str, bool]:
    scenario_ids = {record["scenario_id"] for record in records.values()}
    damage_fire = copy.deepcopy(records["I02_DAMAGE_TO_FIRE"]["payload"])
    damage_cold = copy.deepcopy(records["I03_DAMAGE_TO_COLD_STRUCTURE"]["payload"])
    damage_fire.pop("provenance")
    damage_cold.pop("provenance")
    control = config["control_scenario"]
    checks = {
        "one_scenario_id_across_all_interfaces": scenario_ids == {control["scenario_id"]},
        "damage_branch_payloads_identical_except_interface_provenance": damage_fire == damage_cold,
        "thermal_and_cold_join_both_neutral": (
            records["I05_THERMAL_TO_INITIATION"]["payload"]["thermal_state"] == "CONTROL_NO_TEMPERATURE_INCREMENT"
            and records["I06_COLD_STATE_TO_INITIATION"]["payload"]["structural_state"] == "CONTROL_ZERO_INCREMENT"
        ),
        "no_initiation": records["I07_INITIATION_TO_PROPAGATION"]["payload"]["initiation_label"] == "CONTROL_NO_INITIATION",
        "terminal_label_matches_predeclaration": records["I08_PROPAGATION_TO_ENSEMBLE"]["payload"]["outcome_label"] == control["expected_terminal_label"],
        "terminal_label_not_historical_noncollapse": control["terminal_label_is_historical_noncollapse"] is False,
        "ensemble_probability_prohibition": records["I08_PROPAGATION_TO_ENSEMBLE"]["payload"]["fraction_is_historical_probability"] is False,
        "visualization_card_only": records["I09_ALL_VALIDATED_STATES_TO_BLENDER"]["payload"]["display_class"] == "CONTROL_CARD_ONLY",
        "visualization_has_no_object_transforms": records["I09_ALL_VALIDATED_STATES_TO_BLENDER"]["payload"]["object_transforms"] == [],
        "all_records_no_physical_credit": all(record["physical_credit"] == "NONE" for record in records.values()),
    }
    if not all(checks.values()):
        raise RuntimeError(f"Cross-interface checks failed: {[key for key, value in checks.items() if not value]}")
    return checks


def make_timeline(records: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    module_actions = {
        "I01_KINEMATICS_TO_DAMAGE": "zero kinematic sentinel delivered",
        "I02_DAMAGE_TO_FIRE": "zero-damage branch delivered to fire",
        "I03_DAMAGE_TO_COLD_STRUCTURE": "same zero-damage branch delivered to cold structure",
        "I04_FIRE_TO_THERMAL_SOLIDS": "zero fire load delivered",
        "I05_THERMAL_TO_INITIATION": "neutral thermal branch delivered to join",
        "I06_COLD_STATE_TO_INITIATION": "neutral cold branch delivered to join",
        "I07_INITIATION_TO_PROPAGATION": "no-initiation sentinel delivered",
        "I08_PROPAGATION_TO_ENSEMBLE": "control no-propagation outcome delivered",
        "I09_ALL_VALIDATED_STATES_TO_BLENDER": "card-only release prepared; Blender not launched",
    }
    rows = []
    for step, interface_id in enumerate(INTERFACE_ORDER, start=1):
        contract = CONTRACTS[interface_id]
        rows.append(
            {
                "step": step,
                "control_time_s": 0.0,
                "interface_id": interface_id,
                "producer": contract["producer"],
                "consumer": contract["consumer"],
                "schema_id": contract["schema_id"],
                "module_action": module_actions[interface_id],
                "validation_status": "PASS_SOFTWARE_CONTRACT_ONLY",
                "physical_credit": "NONE",
                "record_digest": canonical_digest(records[interface_id]),
            }
        )
    return rows


def make_report(config: dict[str, Any], replay: dict[str, Any], matrix: list[dict[str, Any]], checks: dict[str, bool]) -> str:
    return "\n".join(
        [
            "# WTC 1 — V10O : premier contrôle intégré des interfaces",
            "",
            f"Généré le {utc_now()} en {config['execution_policy']['maximum_runtime_seconds']} secondes maximales autorisées.",
            "",
            "## Résultat",
            "",
            "Les neuf interfaces gelées en V10N disposent maintenant d’un contrat typé exécutable. Pour chacune, un enregistrement valide est accepté et une copie où manque un champ obligatoire est rejetée. Deux exécutions indépendantes du contrôle donnent le même condensat canonique.",
            "",
            "Le scénario sentinelle traverse la branche impact, se sépare vers incendie et structure froide, rejoint l’initiation, puis atteint la propagation, l’ensemble et la sortie de visualisation. Son résultat terminal est `CONTROL_NO_PROPAGATION`. Ce libellé signifie uniquement qu’une entrée algébrique nulle produit une sortie nulle dans le logiciel. Il ne signifie ni « le WTC1 ne s’effondre pas », ni « l’effondrement est impossible ».",
            "",
            "## Vérifications",
            "",
            f"- Interfaces valides : {sum(row['positive_validation'].startswith('PASS') for row in matrix)}/9.",
            f"- Enregistrements invalides correctement rejetés : {sum(row['negative_rejected'] for row in matrix)}/9.",
            f"- Relectures de références en cache : {replay['passed_count']}/{replay['baseline_count']}.",
            f"- Contrôles inter-interfaces : {sum(checks.values())}/{len(checks)}.",
            "- Interfaces physiquement prêtes : 0/9.",
            "- Solveur, GPU, Blender : 0 exécution.",
            "",
            "## Ce que les relectures en cache prouvent",
            "",
            "- V8S : la masse et la vitesse du cas de base reproduisent exactement son énergie cinétique et sa quantité de mouvement enregistrées.",
            "- V8E : les nombres de champs synthétiques, graines et paramètres sont retrouvés, avec l’interdiction explicite d’y voir des probabilités.",
            "- V8J et V8L : leurs portes froides restent non validées ; V10O ne les transforme pas en résultats physiques.",
            "- V9M : la branche d’impact physique reste fermée, avec zéro déclencheur de réouverture satisfait.",
            "",
            "## Séparation des preuves",
            "",
            "1. **Faits observés** : empreintes des cinq fichiers en cache, valeurs relues, résultats des tests de contrat.",
            "2. **Résultats officiels dépendants** : aucune donnée NIST n’est promue ici ; les anciennes dépendances gardent leur statut.",
            "3. **Archives** : aucune archive source n’est lue.",
            "4. **Hypothèses** : la température de référence et les zéros sont des sentinelles logicielles, pas des propriétés du WTC1.",
            "5. **Résultats dérivés** : cohérence arithmétique, validation des neuf contrats, déterminisme du parcours.",
            "6. **Inconnues** : dommage réel, incendie, thermique des éléments, état froid, initiation et propagation physiques.",
            "",
            "## Portes maintenues fermées",
            "",
            "Les 22 exigences mécaniques restent ouvertes. Aucun modèle de dommage n’est qualifié, aucune entrée événementielle FDS/thermique n’est disponible et aucune loi de propagation globale n’est validée. Une sortie 3D éventuelle restera strictement en aval des états libérés et sans rétroaction mécanique.",
            "",
            "## Prochaine étape",
            "",
            config["next_iteration"]["objective"],
        ]
    )


def main() -> int:
    started = time.perf_counter()
    config = load_config()
    regression_rows = [verify_hash(item) for item in config["regression_files"]]
    protected_rows = [verify_hash(item) for item in config["protected_files"]]
    cached_rows = [verify_hash(item) for item in config["cached_baselines"]]
    regression = {
        "iteration": "V10O",
        "generated_at_utc": utc_now(),
        "validation_status": "PASS",
        "regression_file_count": len(regression_rows),
        "protected_file_count": len(protected_rows),
        "cached_baseline_file_count": len(cached_rows),
        "regression_files": regression_rows,
        "protected_files": protected_rows,
        "cached_baseline_files": cached_rows,
        "source_archive_read": False,
        "source_archive_modified": False,
        "official_sources_directory_modified": False,
        "blender_master_unchanged": True,
    }

    schemas = exported_contracts()
    schemas.update(
        {
            "iteration": "V10O",
            "generated_at_utc": utc_now(),
            "validation_status": "PASS",
            "adapter_library": {"path": rel(ADAPTER_PATH), "sha256": sha256_file(ADAPTER_PATH)},
        }
    )
    replay = cached_baseline_replay(config)
    source_hashes = {
        "v10o_configuration": sha256_file(CONFIG_PATH),
        "v10n_coupling_graph": sha256_file(abs_path("wtc1_simulation_v8/output/v10n_solver_neutral_coupling_graph.json")),
    }
    records_first = build_control_records(config["control_scenario"], source_hashes)
    records_second = build_control_records(config["control_scenario"], source_hashes)
    first_digest = canonical_digest(records_first)
    second_digest = canonical_digest(records_second)
    deterministic_match = first_digest == second_digest
    if not deterministic_match:
        raise RuntimeError("Independent control-record constructions are not deterministic")
    matrix, adapter_details = validate_adapters(records_first)
    cross_checks = cross_interface_checks(records_first, config)
    timeline = make_timeline(records_first)
    trace = {
        "iteration": "V10O",
        "generated_at_utc": utc_now(),
        "validation_status": "PASS_SOFTWARE_CONTROL_ONLY",
        "scenario": config["control_scenario"],
        "pipeline_topology": {
            "order": INTERFACE_ORDER,
            "branch": "I02 damage-to-fire and I03 damage-to-cold-structure share the same zero-damage state",
            "join": "I05 thermal and I06 cold state meet before I07 initiation-to-propagation",
            "release": "I09 emits a card-only record and does not launch Blender",
        },
        "records": records_first,
        "adapter_validation_details": adapter_details,
        "cross_interface_checks": cross_checks,
        "deterministic_replay": {
            "first_digest": first_digest,
            "second_digest": second_digest,
            "match": deterministic_match,
        },
        "terminal_control_outcome": {
            "label": records_first["I08_PROPAGATION_TO_ENSEMBLE"]["payload"]["outcome_label"],
            "historical_noncollapse_conclusion": False,
            "historical_collapse_conclusion": False,
            "interpretation": "A zero-input algebraic sentinel reached the expected zero-propagation software state. No physical WTC state was evaluated.",
        },
    }

    expected = config["expected"]
    positive_count = sum(row["positive_validation"] == "PASS_SOFTWARE_CONTRACT_ONLY" for row in matrix)
    negative_count = sum(row["negative_rejected"] for row in matrix)
    if positive_count != expected["positive_validation_count"]:
        raise RuntimeError("Unexpected positive adapter validation count")
    if negative_count != expected["negative_missing_field_rejection_count"]:
        raise RuntimeError("Unexpected negative adapter rejection count")
    runtime_seconds = time.perf_counter() - started
    if runtime_seconds > config["execution_policy"]["maximum_runtime_seconds"]:
        raise RuntimeError("V10O exceeded its predeclared maximum runtime")
    gate = {
        "iteration": "V10O",
        "generated_at_utc": utc_now(),
        "validation_status": "PASS",
        "regression_gate": "PASS",
        "protected_blender_master_gate": "PASS_UNCHANGED",
        "cached_replay_gate": f"PASS_{replay['passed_count']}_OF_{replay['baseline_count']}",
        "adapter_positive_gate": f"PASS_{positive_count}_OF_{len(matrix)}",
        "adapter_negative_gate": f"PASS_{negative_count}_OF_{len(matrix)}",
        "deterministic_replay_gate": "PASS" if deterministic_match else "FAIL",
        "cross_interface_gate": f"PASS_{sum(cross_checks.values())}_OF_{len(cross_checks)}",
        "terminal_control_gate": "PASS_CONTROL_NO_PROPAGATION",
        "terminal_control_is_historical_noncollapse": False,
        "historical_collapse_or_noncollapse_conclusion_authorized": False,
        "physically_ready_interface_count": 0,
        "mechanical_source_gate": "OPEN_0_OF_22_REQUIREMENTS",
        "impact_physics_gate": "CLOSED_V9M",
        "fire_event_reconstruction_gate": "CLOSED",
        "thermal_member_history_gate": "CLOSED",
        "cold_structural_gate": "CLOSED",
        "initiation_physics_gate": "CLOSED",
        "propagation_physics_gate": "CLOSED",
        "blender_release_gate": "CONTROL_CARD_ONLY_NO_RENDER",
        "physical_assignment_count": 0,
        "solver_run_count": 0,
        "gpu_compute_run_count": 0,
        "blender_run_count": 0,
        "v10p_bounded_three_track_handoff_authorized": True,
        "v10p_physical_damage_prediction_authorized": False,
    }

    outputs = config["outputs"]
    write_json(abs_path(outputs["regression_audit"]), regression)
    write_json(abs_path(outputs["schemas"]), schemas)
    write_csv(abs_path(outputs["adapter_matrix"]), list(matrix[0].keys()), matrix)
    write_json(abs_path(outputs["cached_replay"]), replay)
    write_json(abs_path(outputs["control_trace"]), trace)
    write_csv(abs_path(outputs["control_timeline"]), list(timeline[0].keys()), timeline)
    write_json(abs_path(outputs["integration_gate"]), gate)
    write_text(abs_path(outputs["report"]), make_report(config, replay, matrix, cross_checks))

    results = {
        "iteration": "V10O",
        "generated_at_utc": utc_now(),
        "validation_status": "PASS_SOFTWARE_INTEGRATION_CONTROL_ONLY",
        "dataset": config["dataset"],
        "configuration": {"path": rel(CONFIG_PATH), "sha256": sha256_file(CONFIG_PATH)},
        "adapter_library": {"path": rel(ADAPTER_PATH), "sha256": sha256_file(ADAPTER_PATH)},
        "script": {"path": rel(SCRIPT_PATH), "sha256": sha256_file(SCRIPT_PATH)},
        "regression_summary": {"files": len(regression_rows), "protected_files": len(protected_rows), "passed": True},
        "cached_replay_summary": {"baseline_count": replay["baseline_count"], "passed_count": replay["passed_count"]},
        "adapter_summary": {
            "interface_count": len(matrix),
            "positive_validation_count": positive_count,
            "negative_missing_field_rejection_count": negative_count,
            "deterministic_replay_match": deterministic_match,
            "trace_digest": first_digest,
            "physically_ready_interface_count": 0,
        },
        "control_summary": {
            "scenario_id": config["control_scenario"]["scenario_id"],
            "scenario_class": config["control_scenario"]["scenario_class"],
            "terminal_label": gate["terminal_control_gate"],
            "historical_scenario_count": 0,
            "historical_collapse_conclusion": False,
            "historical_noncollapse_conclusion": False,
        },
        "gates": gate,
        "epistemic_separation": {
            "observed_facts": "File hashes, cached fields, arithmetic replay and software validator outcomes.",
            "official_model_results": "No official-model field is promoted; dependencies retain their prior labels.",
            "archive_claims": "No archive source is read.",
            "model_hypotheses": "All zero values and the 293.15 K reference are software sentinels, not WTC properties.",
            "derived_results": "Nine positive validations, nine negative rejections, deterministic trace and zero-input terminal control.",
            "unknowns": "All physical impact, fire, thermal, structural, initiation and propagation states remain unresolved.",
        },
        "runtime_seconds": round(time.perf_counter() - started, 6),
        "next_iteration": config["next_iteration"],
    }
    write_json(abs_path(outputs["results"]), results)

    artifact_roles = [
        "regression_audit", "schemas", "adapter_matrix", "cached_replay", "control_trace",
        "control_timeline", "integration_gate", "report", "results",
    ]
    artifacts = []
    for role in artifact_roles:
        path = abs_path(outputs[role])
        if not path.is_file():
            raise RuntimeError(f"Missing output {role}: {path}")
        artifacts.append({"role": role, "path": rel(path), "sha256": sha256_file(path), "bytes": path.stat().st_size})
    offline = {
        "iteration": "V10O",
        "generated_at_utc": utc_now(),
        "validation_status": "PASS",
        "artifact_count": len(artifacts),
        "artifacts": artifacts,
        "configuration": {"path": rel(CONFIG_PATH), "sha256": sha256_file(CONFIG_PATH)},
        "adapter_library": {"path": rel(ADAPTER_PATH), "sha256": sha256_file(ADAPTER_PATH)},
        "script": {"path": rel(SCRIPT_PATH), "sha256": sha256_file(SCRIPT_PATH)},
        "regression_files_reverified_count": len(regression_rows),
        "cached_baseline_files_reverified_count": len(cached_rows),
        "protected_blender_master_unchanged": True,
        "source_archive_read": False,
        "source_archive_modified": False,
        "official_sources_directory_modified": False,
        "physical_assignment_count": 0,
        "solver_run_count": 0,
        "gpu_compute_run_count": 0,
        "blender_run_count": 0,
    }
    write_json(abs_path(outputs["offline_audit"]), offline)

    print(
        json.dumps(
            {
                "iteration": "V10O",
                "status": "PASS_SOFTWARE_INTEGRATION_CONTROL_ONLY",
                "cached_replays": replay["passed_count"],
                "positive_adapter_validations": positive_count,
                "negative_records_rejected": negative_count,
                "deterministic_replay_match": deterministic_match,
                "terminal_label": records_first["I08_PROPAGATION_TO_ENSEMBLE"]["payload"]["outcome_label"],
                "historical_noncollapse_conclusion": False,
                "solver_runs": 0,
                "next_iteration": config["next_iteration"]["id"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"V10O ERROR: {exc}", file=sys.stderr)
        raise
