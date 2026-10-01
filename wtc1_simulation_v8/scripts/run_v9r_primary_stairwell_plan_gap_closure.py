#!/usr/bin/env python3
"""Verify sources and build the bounded V9R stairwell plan gap closure."""

from __future__ import annotations

import csv
import hashlib
import json
import platform
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "wtc1_simulation_v8/data/v9r_primary_stairwell_plan_gap_closure.json"


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


def normalized(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.casefold())


def verify_hashes(declared: dict[str, str]) -> dict[str, Any]:
    records = []
    for relative, expected in declared.items():
        path = ROOT / relative
        actual = sha256(path) if path.is_file() else None
        records.append(
            {
                "path": relative,
                "exists": path.is_file(),
                "expected_sha256": expected,
                "actual_sha256": actual,
                "passed": path.is_file() and actual == expected,
            }
        )
    return {"record_count": len(records), "records": records, "passed": all(item["passed"] for item in records)}


def verify_pdf_anchors(config: dict[str, Any]) -> dict[str, Any]:
    readers: dict[str, PdfReader] = {}
    records = []
    for anchor in config["pdf_anchors"]:
        source = anchor["source"]
        readers.setdefault(source, PdfReader(ROOT / source))
        reader = readers[source]
        page_number = int(anchor["pdf_page"])
        page_exists = 1 <= page_number <= len(reader.pages)
        text = (reader.pages[page_number - 1].extract_text() or "") if page_exists else ""
        haystack = normalized(text)
        terms = [{"term": term, "found": normalized(term) in haystack} for term in anchor["required_terms"]]
        records.append(
            {
                "source": source,
                "pdf_page": page_number,
                "printed_page": anchor["printed_page"],
                "section": anchor["section"],
                "page_exists": page_exists,
                "required_terms": terms,
                "passed": page_exists and all(item["found"] for item in terms),
            }
        )
    expected = config["gates"]["pdf_anchor_count_expected"]
    return {"anchor_count": len(records), "records": records, "passed": len(records) == expected and all(item["passed"] for item in records)}


def verify_acquisition(config: dict[str, Any]) -> dict[str, Any]:
    declaration = config["acquisition"]
    source_path = ROOT / "wtc1_simulation_v8/input/v9r_official_sources/ncstar1-7.pdf"
    reader = PdfReader(source_path)
    actual_size = source_path.stat().st_size
    actual_hash = sha256(source_path)
    header = source_path.read_bytes()[:5]
    checks = {
        "official_domain_is_nist": declaration["official_domain"] == "nist.gov",
        "http_head_status_200": declaration["http_head_status"] == 200,
        "content_type_pdf": declaration["http_head_content_type"].startswith("application/pdf"),
        "head_and_download_sizes_match": declaration["http_head_content_length_bytes"] == declaration["downloaded_size_bytes"],
        "local_size_matches": actual_size == declaration["downloaded_size_bytes"],
        "local_sha256_matches": actual_hash == declaration["downloaded_sha256"],
        "pdf_header_present": header == b"%PDF-",
        "page_count_matches": len(reader.pages) == declaration["pdf_page_count"],
        "content_unmodified": declaration["content_modified_after_download"] is False,
    }
    return {
        **declaration,
        "local_path": str(source_path.relative_to(ROOT)).replace("\\", "/"),
        "actual_size_bytes": actual_size,
        "actual_sha256": actual_hash,
        "actual_page_count": len(reader.pages),
        "checks": checks,
        "passed": all(checks.values()),
    }


def verify_indexed_commission_source(config: dict[str, Any]) -> dict[str, Any]:
    manifest_path = ROOT / "work/pdf_index/manifest.csv"
    with manifest_path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    row = next((item for item in rows if item.get("id") == "L049"), None)
    lines = (ROOT / "work/pdf_index/text/L049.txt").read_text(encoding="utf-8", errors="replace").splitlines()
    continuity = " ".join(lines[14314:14336])
    transfer = " ".join(lines[27943:27950])
    terms = [
        "Stairwells A and C",
        "Stairwell B",
        "two deviations",
        "42nd and 48th floors",
        "76th and 82nd floors",
    ]
    checks = [{"term": term, "found": normalized(term) in normalized(continuity + " " + transfer)} for term in terms]
    manifest_passed = bool(row and row.get("sha256") == "6fa7e90a750a3e1168c06d859369896b1ee377ca314a251c9c6d7db3f87462d8")
    return {
        "index_id": "L049",
        "manifest_row_found": row is not None,
        "manifest_source_sha256": row.get("sha256") if row else None,
        "term_checks": checks,
        "external_source_pdf_opened": False,
        "passed": manifest_passed and all(item["found"] for item in checks),
    }


def verify_visual_qa(config: dict[str, Any]) -> dict[str, Any]:
    records = []
    for declaration in config["visual_qa"]:
        source_text = declaration["source"]
        individual_sources = [part.strip() for part in source_text.split(" and ")]
        sources_exist = all((ROOT / part).is_file() for part in individual_sources)
        records.append(
            {
                **declaration,
                "sources_exist": sources_exist,
                "observation_is_nonempty": bool(declaration["observation"].strip()),
                "metric_and_solver_credit_consistent": declaration["metric_scale_present"] is False
                and declaration["solver_geometry_qualified"] is False,
                "passed": sources_exist
                and bool(declaration["observation"].strip())
                and declaration["metric_scale_present"] is False
                and declaration["solver_geometry_qualified"] is False,
            }
        )
    expected = config["gates"]["visual_qa_record_count_expected"]
    return {"record_count": len(records), "records": records, "passed": len(records) == expected and all(item["passed"] for item in records)}


def floor_band(config: dict[str, Any], floor: int) -> dict[str, Any]:
    matches = [item for item in config["floor_bands"] if item["floor_start"] <= floor <= item["floor_end"]]
    if len(matches) != 1:
        raise ValueError(f"Expected one floor band for floor {floor}, got {len(matches)}")
    return matches[0]


def transfer_event(alias: str, floor: int) -> str:
    if alias in {"A", "C"}:
        return {
            42: "MAJOR_TRANSFER_OUTSIDE_CORE",
            48: "MAJOR_TRANSFER_BACK_INSIDE_CORE",
            66: "SLIGHT_CHANGE_EXACT_GEOMETRY_UNKNOWN",
            68: "SLIGHT_CHANGE_EXACT_GEOMETRY_UNKNOWN",
            76: "MAJOR_TRANSFER_OUTSIDE_CORE",
            82: "MAJOR_TRANSFER_BACK_INSIDE_CORE",
        }.get(floor, "NONE")
    if alias == "B" and floor == 76:
        return "HORIZONTAL_TRANSFER_EXACT_PATH_UNKNOWN"
    return "NONE"


def core_relation(alias: str, floor: int) -> str:
    if alias in {"A", "C"}:
        if floor in {42, 48, 76, 82}:
            return "TRANSFER_CROSSES_CORE_BOUNDARY"
        if 43 <= floor <= 47 or 77 <= floor <= 81:
            return "OUTSIDE_CORE_PER_TABLE_2_2"
        if floor in {66, 67, 68}:
            return "INSIDE_CORE_SLIGHT_CHANGE_UNDIMENSIONED"
        return "INSIDE_CORE_SCHEMATIC"
    if floor == 76:
        return "TRANSFER_WITHIN_OR_AROUND_CORE_EXACT_PATH_UNKNOWN"
    return "VERTICAL_ALIGNMENT_EXCEPT_FLOOR_76"


def inherited_damage_status(floor: int) -> str:
    if floor == 92:
        return "TRANSCRIBED_EYEWITNESS_IMPASSABLE_MODEL_LIMITED"
    if floor == 93:
        return "POSSIBLY_IMPASSABLE_MODEL_LIMITED"
    if 94 <= floor <= 96:
        return "OFFICIAL_BASE_MODEL_ALL_THREE_APPEAR_IMPASSABLE"
    if floor == 97:
        return "MODEL_FIGURE_PRESENT_TEXT_CONCLUSION_NOT_EXTENDED"
    return "NOT_AUDITED"


def build_floor_rows(config: dict[str, Any]) -> list[dict[str, Any]]:
    stairs = {item["letter_alias"]: item for item in config["stairways"]}
    rows = []
    for floor in range(1, 111):
        band = floor_band(config, floor)
        for alias in ("A", "C", "B"):
            stair = stairs[alias]
            present = (alias in {"A", "C"} and 2 <= floor <= 110) or (alias == "B" and floor <= 107)
            if not present:
                service = "NOT_PRESENT_IN_REPORTED_VERTICAL_EXTENT"
            elif floor == 1 and alias == "B":
                service = "SERVICES_CONCOURSE"
            elif floor == 2 and alias in {"A", "C"}:
                service = "STARTS_AT_PLAZA_MEZZANINE"
            elif floor == 2 and alias == "B":
                service = "PASSES_FLOOR_WITH_NO_EXIT"
            elif floor == 107 and alias == "B":
                service = "TERMINATES_AT_FLOOR_107"
            elif floor == 110 and alias in {"A", "C"}:
                service = "TERMINATES_AT_FLOOR_110"
            else:
                service = "CONTINUES"
            event = transfer_event(alias, floor) if present else "NOT_APPLICABLE"
            rows.append(
                {
                    "floor": floor,
                    "stair_alias": alias,
                    "v9q_numeric_alias": stair["v9q_numeric_alias"],
                    "present_in_reported_vertical_extent": str(present).lower(),
                    "service_status": service,
                    "floor_band_layout": band["layout"],
                    "table_2_2_panel_present": str(band["table_panel"]).lower(),
                    "transfer_event": event,
                    "core_relation": core_relation(alias, floor) if present else "NOT_APPLICABLE",
                    "clear_width_in": f"{stair['clear_width_in']:.1f}",
                    "clear_width_mm": f"{stair['clear_width_in'] * 25.4:.3f}",
                    "landing_width_in": f"{stair['landing_by_exit_door_width_in']:.1f}",
                    "landing_width_mm": f"{stair['landing_by_exit_door_width_in'] * 25.4:.3f}",
                    "landing_depth_in": f"{stair['landing_by_exit_door_depth_in']:.1f}",
                    "landing_depth_mm": f"{stair['landing_by_exit_door_depth_in'] * 25.4:.3f}",
                    "floor_95_labelled_overlay": str(floor == 95).lower(),
                    "qualitative_floor_95_position": stair["impact_floor_95_position"] if floor == 95 else "not_applicable",
                    "inherited_damage_evidence": inherited_damage_status(floor),
                    "exact_metric_plan_coordinates_qualified": "false",
                    "flight_and_stringer_geometry_qualified": "false",
                    "connections_qualified": "false",
                    "discrete_mass_qualified": "false",
                    "stiffness_qualified": "false",
                    "strength_qualified": "false",
                    "load_path_credit_qualified": "false",
                }
            )
    return rows


def write_floor_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def build_topology(config: dict[str, Any]) -> dict[str, Any]:
    return {
        "iteration": config["iteration"],
        "status": "SOURCE_GATED_CATEGORICAL_TOPOLOGY_NOT_METRIC_SOLVER_GEOMETRY",
        "stairways": config["stairways"],
        "floor_bands": config["floor_bands"],
        "v9q_reconciliation": config["v9q_reconciliation"],
        "unit_conversions": {
            "A_C_clear_width_mm": 44.0 * 25.4,
            "B_clear_width_mm": 56.0 * 25.4,
            "A_C_landing_by_exit_door_mm": [92.0 * 25.4, 78.0 * 25.4],
            "B_landing_by_exit_door_mm": [116.0 * 25.4, 78.0 * 25.4],
            "reported_transfer_distance_range": {
                "minor_66_68": "several feet; exact per-stair value unavailable",
                "major_42_48_76_82": "up to over 100 ft (33 m); exact per-floor and per-stair values unavailable",
            },
        },
        "authorized_use": [
            "categorical floor-band continuity",
            "transfer-event topology",
            "landing dimensions by exit door",
            "qualitative Floor 95 footprint registration target",
        ],
        "prohibited_use": [
            "exact as-built solver coordinates",
            "whole-enclosure footprints",
            "flight, tread, riser, landing steel or stringer geometry",
            "connections, discrete mass, stiffness, strength or load path",
            "independent impact-damage validation",
        ],
    }


def build_model_gate(config: dict[str, Any], floor_rows: list[dict[str, Any]]) -> dict[str, Any]:
    counts = {"COMPLETE": 0, "PARTIAL": 0, "MISSING": 0}
    for field in config["required_model_fields"]:
        counts[field["status"]] += 1
    gates = config["gates"]
    closed = {
        "metric_as_built_solver_geometry": gates["metric_as_built_solver_geometry_authorized"],
        "discrete_mass": gates["discrete_mass_authorized"],
        "stiffness": gates["stiffness_authorized"],
        "strength": gates["strength_authorized"],
        "load_path_credit": gates["load_path_credit_authorized"],
        "component_damage_validation": gates["component_damage_validation_authorized"],
        "global_solver": gates["global_solver_authorized"],
        "blender_physical_validation": gates["blender_physical_validation_authorized"],
    }
    return {
        "iteration": config["iteration"],
        "required_model_fields": config["required_model_fields"],
        "field_status_counts": counts,
        "floor_matrix_row_count": len(floor_rows),
        "topology_layer_authorized": gates["topology_layer_authorized"],
        "landing_dimension_layer_authorized": gates["landing_dimension_layer_authorized"],
        "closed_mechanical_and_validation_credits": closed,
        "all_mechanical_and_validation_credits_closed": not any(closed.values()),
        "decision": "USE_CATEGORICAL_TOPOLOGY_AND_LANDING_DIMENSIONS_ONLY",
        "reason": "No dimensioned floor-specific as-built WTC 1 stair plans, flight/stringer details or actual structural connections were found in the bounded public-source search.",
        "next_iteration": config["next_iteration"],
    }


def make_report(config: dict[str, Any], manifest: dict[str, Any], gate: dict[str, Any], result: dict[str, Any]) -> str:
    counts = gate["field_status_counts"]
    return f"""# V9R - Fermeture bornée des lacunes de plans des escaliers du WTC 1

## Conclusion

V9R est **{result['status']}** comme audit documentaire. Le rapport final officiel NCSTAR 1-7 a été acquis depuis NIST, vérifié par taille, empreinte et pagination, puis contrôlé page par page et visuellement. Il améliore fortement la topologie des trois cages, mais ne fournit toujours pas un plan d'exécution métrique complet. La tour peut donc recevoir une couche topologique à trois cages et les dimensions publiées des paliers ; elle ne peut pas encore recevoir une géométrie mécanique exacte des escaliers.

## 1. Faits directement observés ou transcrits

- A et C mesurent 44 in de large et s'étendent du 2e au 110e étage. Le palier près de la porte est donné comme 92 in × 78 in.
- B mesure 56 in, s'étend du sous-sol B6 au 107e étage et possède un palier de 116 in × 78 in. B ne possède pas de sortie au 2e étage.
- A et C ont des transferts aux étages 42, 48, 66, 68, 76 et 82. Les transferts majeurs sont 42, 48, 76 et 82 ; les changements 66 et 68 sont décrits comme faibles.
- B exige aussi un transfert horizontal au 76e étage et reste verticalement aligné ailleurs.
- Les grands transferts de A/C comportaient plusieurs angles droits et pouvaient dépasser 100 ft ; les changements 66/68 étaient de quelques pieds. Les longueurs exactes par cage et par étage ne sont pas publiées.

## 2. Résultats et figures du modèle officiel

- La table 2-2 et la figure 2-11 de NCSTAR 1-7 fournissent une topologie par bandes d'étages et une continuité verticale. Ce sont des schémas sans échelle métrique.
- La figure 5-2 superpose les trois cages au plan du modèle d'impact du 95e étage. Elle fournit des repères de noyau et une orientation, mais reste une sortie du modèle officiel, pas un plan d'exécution indépendant.
- Les figures structurelles du 96e étage dans NCSTAR 1-6/1-6C donnent les grilles de colonnes mais omettent les volées, enveloppes et connexions des escaliers.

## 3. Source gouvernementale indexée et différence de détail

Le rapport de la Commission décrivait deux grandes déviations de A/C et présentait B comme essentiellement droit. NCSTAR 1-7 donne une liste plus détaillée : six niveaux pour A/C et un transfert de B au 76e. V9R conserve cette différence comme un écart de niveau de détail. Sans plans d'exécution, elle ne constitue pas une contradiction géométrique entièrement résolue.

## 4. Résultats dérivés

- {len(config['floor_bands'])} bandes d'étages documentaires ont été encodées.
- {gate['floor_matrix_row_count']} lignes étage/cage ont été produites.
- Couverture des sept champs nécessaires : {counts['COMPLETE']} complet, {counts['PARTIAL']} partiels, {counts['MISSING']} manquant.
- La catégorie « volées, paliers, limons et attaches » passe de manquante à partielle grâce aux dimensions des paliers ; les limons, marches, hauteurs, girons et attaches restent inconnus.

## 5. Hypothèses propres au modèle

Aucune coordonnée métrique, aucun contour complet d'enveloppe et aucune propriété mécanique n'ont été inventés. Les panneaux de la table 2-2 servent uniquement de catégories topologiques. Le plan représentatif reproduit dans NCSTAR 1-1A et le plan du 26e étage du WTC 2 dans NCSTAR 1-2A ne sont pas substitués à un plan exact du WTC 1.

## 6. Contradictions et informations manquantes

- plans WTC 1 cotés et identifiés par étage ;
- distances et tracés exacts de chaque transfert ;
- contours complets des cages et positions par rapport aux colonnes ;
- volées, marches, paliers intermédiaires, limons et détails d'acier ;
- connexions aux dalles et à l'ossature du noyau ;
- masses discrètes et dommages composant par composant.

## 7. Reproductibilité et périmètre

- Régressions V9Q : **{'PASS' if manifest['regressions']['passed'] else 'FAIL'}**.
- Nouvelle acquisition officielle NCSTAR 1-7 : **{'PASS' if manifest['acquisition']['passed'] else 'FAIL'}**.
- Empreintes des sources : **{'PASS' if manifest['sources']['passed'] else 'FAIL'}**.
- Ancrages PDF : **{'PASS' if manifest['pdf_anchors']['passed'] else 'FAIL'}** ({manifest['pdf_anchors']['anchor_count']}).
- Contrôles visuels : **{'PASS' if manifest['visual_qa']['passed'] else 'FAIL'}** ({manifest['visual_qa']['record_count']}).
- Archive source externe : non ouverte et non rescannée.
- Réseau : limité à la découverte et au téléchargement du PDF final officiel NIST.
- FOIA, contact externe, solveur et Blender : non utilisés.

Blender reste un outil de visualisation et ne constitue pas une validation physique.

## 8. Décision et suite

Le modèle futur peut utiliser la continuité, les événements de transfert, les largeurs et dimensions de paliers comme contraintes documentaires. Les coordonnées métriques, masses, rigidités, résistances, connexions, dommages et chemins de charge restent interdits.

**V9S :** {config['next_iteration']['objective']}
"""


def main() -> int:
    started = time.perf_counter()
    config = load_json(CONFIG_PATH)
    outputs = {key: ROOT / value for key, value in config["outputs"].items()}

    regressions = verify_hashes(config["regression_files"])
    sources = verify_hashes(config["source_files"])
    acquisition = verify_acquisition(config)
    pdf_anchors = verify_pdf_anchors(config)
    indexed_commission = verify_indexed_commission_source(config)
    visual_qa = verify_visual_qa(config)

    source_manifest = {
        "iteration": config["iteration"],
        "configuration": str(CONFIG_PATH.relative_to(ROOT)).replace("\\", "/"),
        "configuration_sha256": sha256(CONFIG_PATH),
        "source_policy": config["source_policy"],
        "regressions": regressions,
        "sources": sources,
        "acquisition": acquisition,
        "pdf_anchors": pdf_anchors,
        "indexed_commission_source": indexed_commission,
        "visual_qa": visual_qa,
        "passed": regressions["passed"]
        and sources["passed"]
        and acquisition["passed"]
        and pdf_anchors["passed"]
        and indexed_commission["passed"]
        and visual_qa["passed"],
    }

    floor_rows = build_floor_rows(config)
    topology = build_topology(config)
    model_gate = build_model_gate(config, floor_rows)
    candidate_matrix = {
        "iteration": config["iteration"],
        "candidate_count": len(config["candidate_figures"]),
        "candidates": config["candidate_figures"],
        "metric_solver_geometry_candidate_count": sum(bool(item["metric_solver_geometry"]) for item in config["candidate_figures"]),
        "decision": "NO_PUBLIC_CANDIDATE_QUALIFIES_EXACT_METRIC_AS_BUILT_WTC1_STAIR_GEOMETRY",
    }

    write_json(outputs["acquisition_receipt"], acquisition)
    write_json(outputs["source_manifest"], source_manifest)
    write_json(outputs["candidate_matrix"], candidate_matrix)
    write_json(outputs["topology"], topology)
    write_floor_csv(outputs["floor_matrix"], floor_rows)
    write_json(outputs["model_gate"], model_gate)

    gates = config["gates"]
    checks = {
        "source_manifest_passed": source_manifest["passed"],
        "regression_hash_count_matches": regressions["record_count"] == gates["regression_hash_count_expected"],
        "source_hash_count_matches": sources["record_count"] == gates["source_hash_count_expected"],
        "candidate_figure_count_matches": candidate_matrix["candidate_count"] == gates["candidate_figure_count_expected"],
        "zero_metric_solver_candidates": candidate_matrix["metric_solver_geometry_candidate_count"] == 0,
        "stairway_count_matches": len(config["stairways"]) == gates["stairway_count_expected"],
        "floor_matrix_row_count_matches": len(floor_rows) == gates["floor_matrix_row_count_expected"],
        "complete_field_count_matches": model_gate["field_status_counts"]["COMPLETE"] == gates["complete_required_model_field_count_expected"],
        "partial_field_count_matches": model_gate["field_status_counts"]["PARTIAL"] == gates["partial_required_model_field_count_expected"],
        "all_mechanical_and_validation_credits_closed": model_gate["all_mechanical_and_validation_credits_closed"],
        "archive_not_read_or_rescanned": not config["source_policy"]["source_archive_read"] and not config["source_policy"]["source_archive_rescanned"],
        "no_solver_blender_foia_or_external_contact": not config["source_policy"]["structural_solver_authorized"]
        and not config["source_policy"]["blender_authorized"]
        and not config["source_policy"]["foia_request_sent"]
        and config["source_policy"]["external_contact_count"] == 0,
    }
    passed = all(checks.values())
    result = {
        "iteration": config["iteration"],
        "status": "PASS" if passed else "FAIL",
        "purpose": config["dataset"]["scope"],
        "checks": checks,
        "counts": {
            "regression_hashes": regressions["record_count"],
            "source_hashes": sources["record_count"],
            "pdf_anchors": pdf_anchors["anchor_count"],
            "visual_qa_records": visual_qa["record_count"],
            "candidate_figures": candidate_matrix["candidate_count"],
            "stairways": len(config["stairways"]),
            "floor_bands": len(config["floor_bands"]),
            "floor_matrix_rows": len(floor_rows),
            "required_model_fields": model_gate["field_status_counts"],
        },
        "new_documented_results": {
            "A_C_transfer_floors": [42, 48, 66, 68, 76, 82],
            "B_transfer_floors": [76],
            "A_C_landing_in": [92.0, 78.0],
            "B_landing_in": [116.0, 78.0],
            "metric_as_built_geometry_qualified": False,
        },
        "authorized_result": model_gate["decision"],
        "physical_result": "NONE",
        "network_access_used": True,
        "network_scope": config["source_policy"]["network_scope"],
        "source_archive_read": False,
        "source_archive_rescanned": False,
        "structural_solver_executed": False,
        "blender_executed": False,
        "physical_validation": False,
        "foia_request_sent": False,
        "external_contact_count": 0,
        "next_iteration": config["next_iteration"],
        "runtime": {
            "executed_at": datetime.now().astimezone().isoformat(timespec="seconds"),
            "elapsed_s": round(time.perf_counter() - started, 6),
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "random_seed_declared": config["dataset"]["random_seed"],
            "random_draw_used": config["dataset"]["random_draw_used"],
        },
    }
    write_json(outputs["results"], result)
    write_text(outputs["report"], make_report(config, source_manifest, model_gate, result))

    print(json.dumps({"iteration": config["iteration"], "status": result["status"], "checks": checks}, ensure_ascii=False, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
