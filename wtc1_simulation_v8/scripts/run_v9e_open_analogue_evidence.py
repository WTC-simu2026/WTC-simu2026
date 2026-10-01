#!/usr/bin/env python3
"""Validate the V9E open-analogue evidence matrix without contact or solver work."""

from __future__ import annotations

import hashlib
import json
import platform
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "wtc1_simulation_v8/data/v9e_open_analogue_evidence.json"
RESULTS_PATH = ROOT / "wtc1_simulation_v8/output/resultats_wtc1_v9e_matrice_analogues_ouverts.json"
REPORT_PATH = ROOT / "wtc1_simulation_v8/output/rapport_wtc1_v9e_matrice_analogues_ouverts.md"
FOIA_NOTE_PATH = ROOT / "wtc1_simulation_v8/output/v9e_note_eligibilite_foia.md"


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(value.rstrip() + "\n")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def nested_get(value: Any, dotted_path: str) -> Any:
    current = value
    for part in dotted_path.split("."):
        current = current[int(part)] if isinstance(current, list) else current[part]
    return current


def verify_regressions(config: dict[str, Any]) -> dict[str, Any]:
    file_results: dict[str, Any] = {}
    for relative, expected in config["regressions"]["required_files"].items():
        path = ROOT / relative
        actual = sha256(path) if path.exists() else None
        file_results[relative] = {
            "exists": path.exists(),
            "expected_sha256": expected,
            "actual_sha256": actual,
            "passed": actual == expected,
        }

    metric_results = []
    for declaration in config["regressions"]["required_metrics"]:
        source = load_json(ROOT / declaration["results"])
        actual = nested_get(source, declaration["path"])
        expected = declaration["expected"]
        metric_results.append({**declaration, "actual": actual, "passed": actual == expected})

    files_passed = all(item["passed"] for item in file_results.values())
    metrics_passed = all(item["passed"] for item in metric_results)
    return {
        "files": file_results,
        "metrics": metric_results,
        "files_passed": files_passed,
        "metrics_passed": metrics_passed,
        "passed": files_passed and metrics_passed,
    }


def classify_sources(config: dict[str, Any]) -> dict[str, Any]:
    sources = config["open_analogue_sources"]
    tiers = sorted(config["proximity_tiers"])
    by_tier = {tier: sum(item["tier"] == tier for item in sources) for tier in tiers}
    machine_readable = [item["id"] for item in sources if item["raw_or_machine_readable"]]
    public_models = [item["id"] for item in sources if item["public_model_files"]]
    comparators = [item["id"] for item in sources if item["experimental_comparator"]]
    relevant_loading = [item["id"] for item in sources if item["relevant_rate_or_loading"]]
    exact = [item["id"] for item in sources if item["can_satisfy_exact_target_gate"]]
    invalid_urls = [item["id"] for item in sources if not item["url"].startswith("https://")]
    missing_limits = [item["id"] for item in sources if not item["limitation"].strip()]
    return {
        "source_count": len(sources),
        "by_tier": by_tier,
        "machine_readable_source_ids": machine_readable,
        "machine_readable_source_count": len(machine_readable),
        "public_model_source_ids": public_models,
        "public_model_source_count": len(public_models),
        "experimental_comparator_ids": comparators,
        "experimental_comparator_count": len(comparators),
        "relevant_rate_or_loading_ids": relevant_loading,
        "relevant_rate_or_loading_count": len(relevant_loading),
        "exact_target_source_ids": exact,
        "exact_target_source_count": len(exact),
        "invalid_https_source_ids": invalid_urls,
        "missing_limitation_source_ids": missing_limits,
    }


def check_gates(config: dict[str, Any], regressions: dict[str, Any], summary: dict[str, Any]) -> dict[str, Any]:
    declared = config["predeclared_documentary_gates"]
    proprietary = config["proprietary_source_access_matrix"]
    required_tiers = declared["required_tiers"]
    gates = {
        "v9d_regressions_unchanged": regressions["passed"],
        "minimum_open_analogue_sources": summary["source_count"] >= declared["minimum_open_analogue_source_count"],
        "required_tiers_present": all(summary["by_tier"].get(tier, 0) > 0 for tier in required_tiers),
        "minimum_machine_readable_sources": summary["machine_readable_source_count"] >= declared["minimum_machine_readable_source_count"],
        "minimum_experimental_comparators": summary["experimental_comparator_count"] >= declared["minimum_experimental_comparator_count"],
        "official_foia_sources": len(config["foia_eligibility"]["official_sources"]) >= declared["minimum_official_foia_source_count"],
        "foia_citizenship_not_required": config["foia_eligibility"]["requester_us_citizenship_required"] is False,
        "all_urls_https": not summary["invalid_https_source_ids"],
        "all_sources_have_limitations": not summary["missing_limitation_source_ids"],
        "no_analogue_claimed_as_exact": summary["exact_target_source_count"] == 0,
        "all_proprietary_routes_present": all(item["lawful_access_route"].strip() and item["route_url"].startswith("https://") for item in proprietary),
        "no_external_contact": not config["foia_eligibility"]["request_sent"] and all(not item["external_contact_made"] for item in proprietary),
        "no_proprietary_material_data_claimed_acquired": all(not item["actual_material_data_publicly_acquired"] for item in proprietary),
        "source_archive_not_rescanned": True,
        "generic_material_not_substituted": True,
        "solver_not_executed": True,
    }
    return {"gates": gates, "passed": all(gates.values())}


def build_foia_note(config: dict[str, Any]) -> str:
    sources = config["foia_eligibility"]["official_sources"]
    source_lines = "\n".join(f"- {item['id']}: {item['url']}" for item in sources)
    return f"""# V9E — Note sur l'éligibilité à une demande FOIA

## Fait vérifié

La citoyenneté américaine n'est pas exigée pour déposer une demande FOIA. Les sources officielles du Department of Justice indiquent qu'une personne non américaine peut déposer une demande. NIST publie sa propre voie de dépôt.

{source_lines}

## Limite

{config['foia_eligibility']['limitation']}

## État local

- Le brouillon V9D reste non envoyé et non publié.
- Aucune identité ni coordonnée de demandeur n'a été ajoutée.
- Aucun engagement de frais n'a été pris.
"""


def build_report(config: dict[str, Any], result: dict[str, Any]) -> str:
    summary = result["open_analogue_summary"]
    proprietary = result["proprietary_source_summary"]
    tier_lines = "\n".join(f"- Niveau {tier}: {count} source(s)" for tier, count in summary["by_tier"].items())
    source_lines = "\n".join(
        f"- **{item['id']}** — niveau {item['tier']} — usage permis: {item['permitted_use']} Limite: {item['limitation']}"
        for item in config["open_analogue_sources"]
    )
    proprietary_lines = "\n".join(
        f"- **{item['id']}** — {item['identifier_status']} Voie: {item['lawful_access_route']} Limite: {item['limitation']}"
        for item in config["proprietary_source_access_matrix"]
    )
    return f"""# WTC 1 — V9E, matrice de données analogues ouvertes

## Conclusion courte

V9E est une itération documentaire validée. Elle confirme que des données et essais analogues ouverts peuvent soutenir une prochaine vérification de **méthode** à petite échelle. Elle ne trouve aucune source de niveau A réunissant le matériau/composant exact, le régime d'impact pertinent et des enregistrements numériques traçables. La simulation physique de l'impact du Boeing 767/CF6-80A2 sur la façade reste donc bloquée.

## 1. Faits directement observés ou transcrits

- Le DOJ indique qu'une personne non américaine peut déposer une demande FOIA; la citoyenneté américaine n'est pas une condition de recevabilité.
- Le manuel GEK 50460, le bulletin GE CF6-80A 72-0869 R03 et les familles Boeing AMM/IPC/SRM/service bulletins ont des identifiants et des voies légales d'accès.
- Aucun de ces accès propriétaires n'a été sollicité et aucune donnée propriétaire n'a été acquise.
- {summary['source_count']} sources analogues publiques ont été classées.
{tier_lines}
- {summary['machine_readable_source_count']} sources annoncent des fichiers lisibles par machine; {summary['public_model_source_count']} fournit publiquement un modèle éléments finis.
- Le jeu Zenodo S355 contient un petit classeur d'inventaire et un complément d'environ 955 Mo; ce complément n'a pas été téléchargé.

## 2. Résultats de modèles officiels ou publics

- Le rapport FAA générique de perte d'aube compare un modèle de ventilateur complet à des essais de confinement, mais il ne représente pas un CF6-80A2 installé.
- Les rapports NASA de confinement comparent des calculs transitoires à des impacts de projectiles ou d'aubes sur panneaux et tissus génériques.
- Le rapport Fokker F28 et le modèle ouvert EMST fournissent des méthodes de construction et de vérification de modèles d'aéronefs, dans des régimes différents de l'impact WTC.

## 3. Affirmations provenant des archives locales

- Aucune. L'archive source n'a pas été rescannée.

## 4. Hypothèses propres à V9E

- Les niveaux A à D mesurent la proximité documentaire et physique; ils ne sont ni des probabilités ni des coefficients de confiance sur l'événement réel.
- Une source B, C ou D peut vérifier une chaîne numérique limitée mais ne peut pas remplacer les propriétés exactes WTC/CF6.

## 5. Résultats dérivés

- Tous les contrôles documentaires V9E passent: {result['documentary_gate_summary']['passed']}.
- Sources exactes de niveau A acquises: {summary['exact_target_source_count']}.
- La prochaine étape peut ingérer un petit jeu ouvert et tester la réduction des signaux/lois de matériau comme exercice analogue explicitement non-WTC.
- Le coupon WTC, la rupture du projectile, l'impact façade, l'aéronef complet, la tour globale, le thermique et Blender comme validation physique restent interdits.

## 6. Contradictions et informations manquantes

- Le rapport FDOT annonce une plage maximale de 500 s⁻¹ tandis que l'abstract de l'article compagnon annonce 250 s⁻¹; cette différence devra être résolue avant tout ajustement quantitatif.
- Le jeu S355 SHPB concerne surtout le cisaillement localisé d'éprouvettes entaillées, pas la traction uniaxiale WTC.
- Les données brutes NIST M26/C80 à température ambiante et grande vitesse restent absentes.
- Les matériaux, assemblages, joints et lois de rupture du CF6-80A2 et de la nacelle Boeing 767 restent à 0/9 exigences.
- Aucun modèle ouvert trouvé ne réunit la géométrie Boeing 767-200/CF6-80A2, les matériaux de production, la rupture et un essai d'impact façade comparable.

## Matrice des sources propriétaires

{proprietary_lines}

Résumé: {proprietary['entry_count']} identifiants/voies documentés, {proprietary['data_acquired_count']} jeu de données acquis, {proprietary['external_contact_count']} contact externe.

## Sources analogues et usage autorisé

{source_lines}

## Interprétation

{result['interpretation']}
"""


def main() -> int:
    started = datetime.now().astimezone()
    config = load_json(CONFIG_PATH)
    regressions = verify_regressions(config)
    source_summary = classify_sources(config)
    gate_summary = check_gates(config, regressions, source_summary)
    proprietary = config["proprietary_source_access_matrix"]
    proprietary_summary = {
        "entry_count": len(proprietary),
        "data_acquired_count": sum(item["actual_material_data_publicly_acquired"] for item in proprietary),
        "external_contact_count": sum(item["external_contact_made"] for item in proprietary),
        "entry_ids": [item["id"] for item in proprietary],
    }
    validated = gate_summary["passed"]
    result = {
        "iteration": "V9E",
        "generated_at": started.isoformat(),
        "status": "validated_open_analogue_matrix_exact_target_not_qualified" if validated else "invalid_documentary_gates_failed",
        "iteration_execution_validated": validated,
        "configuration": str(CONFIG_PATH.relative_to(ROOT)).replace("\\", "/"),
        "scope": config["dataset"]["scope"],
        "evidence_policy": config["evidence_policy"],
        "regressions": regressions,
        "foia_eligibility": config["foia_eligibility"],
        "proximity_tiers": config["proximity_tiers"],
        "proprietary_source_access_matrix": proprietary,
        "proprietary_source_summary": proprietary_summary,
        "open_analogue_sources": config["open_analogue_sources"],
        "open_analogue_summary": source_summary,
        "documentary_gate_summary": gate_summary,
        "exact_tier_a_source_acquired": False,
        "raw_nist_channels_acquired": False,
        "wtc_high_rate_material_curve_qualification_passed": False,
        "cf6_80a2_cowling_material_card_identification_passed": False,
        "analogue_data_ingestion_iteration_permitted": validated,
        "openradioss_wtc_coupon_authorized": False,
        "openradioss_wtc_coupon_executed": False,
        "failure_deletion_executed": False,
        "facade_impact_executed": False,
        "global_wtc_impact_physics_qualification_passed": False,
        "blender_executed": False,
        "scope_gates": config["scientific_and_scope_gates"],
        "interpretation": (
            "V9E validates a bounded evidence and access matrix, not WTC impact physics. Official DOJ sources confirm that non-U.S. citizenship does not bar a FOIA request, while the NIST, GE and Boeing routes remain unsent and no proprietary record is acquired. Public sources provide comparable structural-steel rate data, S355 shear-localization data, generic fan-containment experiments and open aircraft-panel workflows, but no source satisfies the exact target gate. These sources may support a separately gated analogue data-ingestion and numerical-method benchmark only. They cannot supply the missing WTC M26/C80 high-rate channels or the production CF6-80A2/Boeing 767 material, joint and fracture card, which remains 0 of 9. No solver or impact is run."
        ),
        "runtime": {
            "started_at": started.isoformat(),
            "completed_at": datetime.now().astimezone().isoformat(),
            "software": "Python",
            "python_version": platform.python_version(),
            "platform": platform.platform(),
            "random_seed": config["dataset"]["random_seed"],
            "solver_executed": False,
            "external_contact_made": False,
            "source_archive_rescanned": False,
            "large_zenodo_archive_downloaded": False,
        },
    }
    write_json(RESULTS_PATH, result)
    write_text(REPORT_PATH, build_report(config, result))
    write_text(FOIA_NOTE_PATH, build_foia_note(config))
    print(json.dumps({
        "iteration": result["iteration"],
        "validated": validated,
        "source_count": source_summary["source_count"],
        "tiers": source_summary["by_tier"],
        "machine_readable": source_summary["machine_readable_source_count"],
        "experimental_comparators": source_summary["experimental_comparator_count"],
        "exact_target_sources": source_summary["exact_target_source_count"],
        "external_contacts": proprietary_summary["external_contact_count"],
        "solver_executed": False,
    }, ensure_ascii=False, indent=2))
    return 0 if validated else 1


if __name__ == "__main__":
    sys.exit(main())
