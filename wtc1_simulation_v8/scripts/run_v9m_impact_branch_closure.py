#!/usr/bin/env python3
"""Build the V9M cached impact-branch closure synthesis.

This script reads only registered local result artifacts. It performs no source
acquisition, archive scan, network request, solver execution or Blender run.
"""

from __future__ import annotations

import hashlib
import json
import math
import platform
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "wtc1_simulation_v8/data/v9m_impact_branch_closure.json"


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def get_path(payload: Any, dotted_path: str) -> Any:
    value = payload
    for part in dotted_path.split("."):
        if not isinstance(value, dict) or part not in value:
            raise KeyError(f"Missing JSON path component {part!r} in {dotted_path!r}")
        value = value[part]
    return value


def compare(actual: Any, comparator: str, expected: Any) -> bool:
    if comparator == "equals":
        if isinstance(actual, float) or isinstance(expected, float):
            return math.isclose(float(actual), float(expected), rel_tol=1e-12, abs_tol=1e-12)
        return actual == expected
    if comparator == "less_or_equal":
        return float(actual) <= float(expected)
    if comparator == "greater_than":
        return float(actual) > float(expected)
    raise ValueError(f"Unsupported comparator: {comparator}")


def verify_files(config: dict[str, Any]) -> dict[str, Any]:
    records: dict[str, Any] = {}
    for relative, expected in config["regression_files"].items():
        path = ROOT / relative
        exists = path.is_file()
        actual = sha256(path) if exists else None
        records[relative] = {
            "exists": exists,
            "expected_sha256": expected,
            "actual_sha256": actual,
            "passed": exists and actual == expected,
        }
    return {"files": records, "passed": all(item["passed"] for item in records.values())}


def evaluate_check(check: dict[str, Any], cache: dict[str, dict[str, Any]]) -> dict[str, Any]:
    relative = check["results"]
    if relative not in cache:
        cache[relative] = load_json(ROOT / relative)
    actual = get_path(cache[relative], check["path"])
    passed = compare(actual, check["comparator"], check["expected"])
    return {
        "results": relative,
        "path": check["path"],
        "comparator": check["comparator"],
        "expected": check["expected"],
        "actual": actual,
        "passed": passed,
    }


def evaluate_checks(checks: list[dict[str, Any]], cache: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    return [evaluate_check(check, cache) for check in checks]


def classification_group(classification: str) -> str:
    if classification.startswith("NUMERICALLY_QUALIFIED"):
        return "numerically_qualified"
    if classification.startswith("CONDITIONAL_NUMERICAL"):
        return "conditional_numerical"
    if classification.startswith("VISUALIZATION_ONLY"):
        return "visualization_only"
    return "failed_or_physically_unqualified"


def build_report(result: dict[str, Any], rows: list[dict[str, Any]], tracks: list[dict[str, Any]]) -> str:
    matrix_lines = [
        "| Domaine | Itération | Classement | Résultat conservé | Usage permis |",
        "|---|---:|---|---|---|",
    ]
    for row in rows:
        matrix_lines.append(
            f"| {row['domain']} | {row['iteration']} | `{row['classification']}` | "
            f"{row['result_summary']} | {row['permitted_use']} |"
        )

    trigger_lines = []
    physical = next(track for track in tracks if track["id"] == "TRACK_B_DORMANT_PHYSICAL_SOLVER")
    for trigger in physical["required_triggers"]:
        trigger_lines.append(f"- [ ] **{trigger['id']}** — {trigger['requirement']}")

    return f"""# WTC 1 — V9M — Clôture de la branche impact

## Conclusion courte

V9M est validée comme synthèse en cache, sans nouvelle source, sans solveur et sans Blender. La chaîne sait exécuter des cas bornés, conserver un projectile déformable stable en vol libre et obtenir un contrôle de contact convergent lorsque l’érosion est supprimée. En revanche, la rupture physique du projectile, l’objectivité de la rupture et la convergence de l’impulsion avec érosion ne sont pas qualifiées. Une simulation physique de l’impact de l’avion sur la façade n’est donc pas autorisée.

Ce n’est pas l’échec d’un lancement logiciel : c’est une limite de validation physique liée aux données et à l’objectivité de la rupture.

## 1. Faits directement observés dans les résultats locaux

- Les huit artefacts V9L préservés correspondent à leurs empreintes SHA-256 enregistrées.
- Les douze lignes de la matrice reproduisent leurs valeurs attendues depuis les résultats V8S à V9L.
- V9M n’a lu que ces artefacts locaux déjà validés. Aucune archive source n’a été relue ou rescannée.
- Aucun accès réseau, téléchargement, contact externe, FOIA, solveur ou Blender n’a été exécuté.

## 2. Résultats de modèles officiels conservés comme comparateurs

- V8S conserve l’échelle officielle d’environ 0,25 s pour le dégagement de la queue. Son calcul réduit donne 0,239975469 s, soit 0,010024531 s d’écart.
- V8T conserve le passage du cas officiel de vérification d’installation OpenRadioss.

Ces deux comparaisons portent respectivement sur une échelle cinématique et sur l’exécution du logiciel. Elles ne valident pas l’impact physique du WTC 1.

## 3. Affirmations provenant de l’archive locale

Aucune nouvelle affirmation d’archive n’est introduite en V9M. L’archive source est restée en lecture seule et n’a pas été consultée.

## 4. Hypothèses du modèle

- Le seuil numérique de 10 % reste inchangé pour les écarts d’impulsion et de sensibilité à la longueur de rupture.
- Les catégories de la matrice distinguent un contrôle numérique, une réussite conditionnelle et une qualification physique.
- La voie physique ne peut être rouverte que si tous les déclencheurs de preuve primaire sont satisfaits ; aucune substitution générique n’est admise.

## 5. Résultats dérivés

| Groupe | Nombre |
|---|---:|
| Contrôles ou entrées qualifiés numériquement | {result['qualification_counts']['numerically_qualified']} |
| Réussite numérique conditionnelle, non physique | {result['qualification_counts']['conditional_numerical']} |
| Échecs de seuil ou qualifications physiques manquantes | {result['qualification_counts']['failed_or_physically_unqualified']} |
| Visualisation seulement | {result['qualification_counts']['visualization_only']} |

### Matrice de qualification

{chr(10).join(matrix_lines)}

## 6. Contradictions et informations manquantes

- Le contrôle sans érosion converge à 1,95062 %, mais il retire précisément la rupture que l’on cherche à qualifier.
- Le cas V8Y passe le pas de maillage 50→25 mm à 8,3414 %, mais dépend d’une longueur LeMAX=100 mm non mesurée et garde un écart 100→50 mm de 33,4297 %.
- La sensibilité V8Z atteint 37,8369 % lorsque LeMAX varie de 50 à 200 mm.
- Seulement 2 exigences sur 9 sont disponibles pour la carte de rupture WTC, contre 0 sur 9 pour le CF6-80A2 et sa coiffe/liaisons.
- Aucun benchmark inspecté ne réunit à la fois des mesures, un projectile déformable pouvant rompre, une rupture objectivée, trois maillages convergents et un modèle réutilisable localement.
- La fermeture de la recherche bornée ne signifie pas qu’aucun benchmark adéquat n’existe ailleurs.

## Deux voies futures strictement séparées

### A — Storyboard 3D illustratif

État : **préparation permise, non exécutée**. Une future spécification pourra montrer les trois enveloppes cinématiques V8S avec des bandes d’incertitude et la mention permanente « VISUALISATION ILLUSTRATIVE — NON VALIDÉE PHYSIQUEMENT ». Elle ne devra produire ni force, ni impulsion, ni rupture, ni trajectoire de débris présentée comme prédiction.

### B — Solveur physique dormant

État : **bloqué en attente de nouvelles preuves primaires**. Conditions cumulatives de réouverture :

{chr(10).join(trigger_lines)}

La FOIA reste un dernier recours non envoyé. Une nouvelle recherche générale sur le web n’est pas prévue ; seule une nouvelle source primaire précisément identifiée pourra être testée contre les seuils inchangés.

## Décision et suite

La branche impact physique est gelée proprement. Les portes façade, avion complet, tour globale, thermique, explosifs et thermite restent fermées. Blender reste un outil d’illustration et non de validation physique.

La prochaine itération est **V9N** : préparer uniquement la spécification du storyboard 3D illustratif, sans exécuter Blender ni aucun solveur.
"""


def main() -> int:
    started = datetime.now().astimezone()
    config = load_json(CONFIG_PATH)
    cache: dict[str, dict[str, Any]] = {}

    regressions = verify_files(config)
    regression_metrics = evaluate_checks(config["regression_metrics"], cache)
    regression_metrics_passed = all(item["passed"] for item in regression_metrics)

    matrix_rows: list[dict[str, Any]] = []
    counts = {
        "numerically_qualified": 0,
        "conditional_numerical": 0,
        "failed_or_physically_unqualified": 0,
        "visualization_only": 0,
    }
    for declared in config["qualification_rows"]:
        evaluated = evaluate_checks(declared["checks"], cache)
        row = {key: value for key, value in declared.items() if key != "checks"}
        row["checks"] = evaluated
        row["evidence_checks_passed"] = all(item["passed"] for item in evaluated)
        group = classification_group(row["classification"])
        row["classification_group"] = group
        counts[group] += 1
        matrix_rows.append(row)

    tracks = config["future_tracks"]
    physical = next(track for track in tracks if track["id"] == "TRACK_B_DORMANT_PHYSICAL_SOLVER")
    met_trigger_count = sum(bool(trigger["met"]) for trigger in physical["required_triggers"])
    expected = config["expected_counts"]
    count_gates = {
        "qualification_row_count": len(matrix_rows) == expected["qualification_row_count"],
        "numerically_qualified_row_count": counts["numerically_qualified"] == expected["numerically_qualified_row_count"],
        "conditional_numerical_row_count": counts["conditional_numerical"] == expected["conditional_numerical_row_count"],
        "failed_or_physically_unqualified_row_count": counts["failed_or_physically_unqualified"] == expected["failed_or_physically_unqualified_row_count"],
        "visualization_only_row_count": counts["visualization_only"] == expected["visualization_only_row_count"],
        "future_track_count": len(tracks) == expected["future_track_count"],
        "physical_track_met_trigger_count": met_trigger_count == expected["physical_track_met_trigger_count"],
    }

    safety_gates = {
        "V9L_regression_hashes_unchanged": regressions["passed"],
        "V9L_regression_metrics_unchanged": regression_metrics_passed,
        "all_matrix_evidence_checks_passed": all(row["evidence_checks_passed"] for row in matrix_rows),
        "all_predeclared_counts_match": all(count_gates.values()),
        "all_scope_gates_closed": all(value is False for value in config["scope_gates"].values()),
        "physical_track_has_no_met_trigger": met_trigger_count == 0,
        "visualization_track_not_executed": tracks[0]["v9m_execution"]["blender_executed"] is False,
        "no_source_or_web_search": config["scope_gates"]["new_source_acquisition_authorized"] is False and config["scope_gates"]["web_search_authorized"] is False,
        "no_solver_fit_or_substitution": all(
            config["scope_gates"][name] is False
            for name in (
                "solver_execution_authorized",
                "material_fit_authorized",
                "failure_law_fit_authorized",
                "generic_material_substitution_authorized",
            )
        ),
        "FOIA_and_external_contact_unsent": config["scope_gates"]["foia_request_authorized"] is False and config["scope_gates"]["external_contact_authorized"] is False,
        "Blender_not_used_as_physical_validation": config["scope_gates"]["blender_execution_authorized"] is False and config["scope_gates"]["blender_physics_validation_authorized"] is False,
    }
    execution_validated = all(safety_gates.values())

    matrix_output = {
        "iteration": "V9M",
        "generated_at": started.isoformat(),
        "evidence_policy": config["evidence_policy"],
        "classification_counts": counts,
        "qualification_rows": matrix_rows,
        "all_evidence_checks_passed": all(row["evidence_checks_passed"] for row in matrix_rows),
        "physical_facade_impact_qualification_passed": False,
        "global_wtc_impact_physics_qualification_passed": False,
    }
    future_output = {
        "iteration": "V9M",
        "generated_at": started.isoformat(),
        "tracks": tracks,
        "track_count": len(tracks),
        "physical_track_met_trigger_count": met_trigger_count,
        "physical_track_reopening_authorized": False,
        "scope_gates": config["scope_gates"],
        "next_iteration": config["next_iteration"],
    }
    result = {
        "iteration": "V9M",
        "generated_at": started.isoformat(),
        "status": "completed_validated_impact_branch_closed_two_tracks_separated_no_source_no_solver_no_blender" if execution_validated else "invalid_cached_closure_or_safety_gate_failed",
        "iteration_execution_validated": execution_validated,
        "impact_branch_closure_synthesis_passed": execution_validated,
        "configuration": str(CONFIG_PATH.relative_to(ROOT)).replace("\\", "/"),
        "qualification_matrix": config["output"]["qualification_matrix"],
        "future_tracks": config["output"]["future_tracks"],
        "scope": config["dataset"]["scope"],
        "evidence_policy": config["evidence_policy"],
        "regressions": {
            **regressions,
            "metrics": regression_metrics,
            "metrics_passed": regression_metrics_passed,
        },
        "qualification_counts": counts,
        "count_gates": count_gates,
        "numerically_qualified_domains": [
            row["domain"]
            for row in matrix_rows
            if row["classification_group"] == "numerically_qualified"
        ],
        "conditional_numerical_domains": [
            row["domain"]
            for row in matrix_rows
            if row["classification_group"] == "conditional_numerical"
        ],
        "controlling_physical_blockers": [
            "projectile rupture is not objectively qualified",
            "fracture energy or internal length is not independently identified",
            "eroding contact impulse does not meet the fixed convergence gate",
            "exact WTC M26/C80 fracture and joint data are incomplete",
            "production CF6-80A2 core, cowling and attachment failure data are absent",
            "no inspected open benchmark combines measurements, deformable-projectile rupture, objective regularization, convergence and a reusable bounded deck",
        ],
        "future_track_states": {track["id"]: track["state"] for track in tracks},
        "physical_track_met_trigger_count": met_trigger_count,
        "physical_track_reopening_authorized": False,
        "physical_facade_impact_qualification_passed": False,
        "projectile_rupture_qualification_passed": False,
        "eroding_impulse_convergence_passed": False,
        "global_wtc_impact_physics_qualification_passed": False,
        "thermal_qualification_passed": False,
        "blender_physics_validation_passed": False,
        "external_benchmark_search_closed": True,
        "scope_gates": config["scope_gates"],
        "safety_gate_summary": {"gates": safety_gates, "passed": execution_validated},
        "next_iteration": config["next_iteration"],
        "interpretation": (
            "V9M formally freezes the physical impact branch after separating four numerically qualified inputs or controls from one conditional numerical result, six failed or physically unqualified rows and one visualization-only row. "
            "The solver chain, free flight and non-eroding contact control are useful regressions, but they do not qualify deformable-projectile rupture or facade response. "
            "A labelled 3D storyboard may be specified next; the physical solver track remains dormant until all primary-evidence and convergence triggers are met."
        ),
        "runtime": {
            "started_at": started.isoformat(),
            "completed_at": datetime.now().astimezone().isoformat(),
            "software": "Python standard-library deterministic cached synthesis",
            "python_version": platform.python_version(),
            "platform": platform.platform(),
            "random_seed": config["dataset"]["random_seed"],
            "network_access_used": False,
            "new_source_acquired": False,
            "source_archive_read": False,
            "source_archive_rescanned": False,
            "solver_executed": False,
            "material_or_failure_fit_performed": False,
            "generic_material_substitution_performed": False,
            "blender_executed": False,
            "external_contact_made": False,
            "FOIA_request_sent": False,
        },
    }

    write_json(ROOT / config["output"]["qualification_matrix"], matrix_output)
    write_json(ROOT / config["output"]["future_tracks"], future_output)
    write_json(ROOT / config["output"]["results"], result)
    write_text(ROOT / config["output"]["report"], build_report(result, matrix_rows, tracks))

    print(json.dumps({
        "iteration": "V9M",
        "execution_validated": execution_validated,
        "qualification_counts": counts,
        "physical_track_met_trigger_count": met_trigger_count,
        "physical_facade_impact_qualification_passed": False,
        "solver_executed": False,
        "blender_executed": False,
        "next_iteration": config["next_iteration"]["id"],
    }, ensure_ascii=False, indent=2))
    return 0 if execution_validated else 1


if __name__ == "__main__":
    sys.exit(main())
