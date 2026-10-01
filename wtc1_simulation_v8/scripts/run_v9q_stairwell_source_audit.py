#!/usr/bin/env python3
"""Verify cached sources and build the source-gated V9Q stairwell audit."""

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
CONFIG_PATH = ROOT / "wtc1_simulation_v8/data/v9q_stairwell_source_audit.json"


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
    """Collapse extraction differences without changing evidentiary content."""
    return re.sub(r"[^a-z0-9]+", "", value.casefold())


def verify_hashes(declared: dict[str, str]) -> dict[str, Any]:
    records: list[dict[str, Any]] = []
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
    return {"records": records, "passed": all(item["passed"] for item in records)}


def verify_pdf_anchors(config: dict[str, Any]) -> dict[str, Any]:
    readers: dict[str, PdfReader] = {}
    records: list[dict[str, Any]] = []
    for anchor in config["pdf_anchors"]:
        source = anchor["source"]
        readers.setdefault(source, PdfReader(ROOT / source))
        page_number = int(anchor["pdf_page"])
        reader = readers[source]
        page_exists = 1 <= page_number <= len(reader.pages)
        text = reader.pages[page_number - 1].extract_text() or "" if page_exists else ""
        haystack = normalized(text)
        term_checks = [
            {"term": term, "found": normalized(term) in haystack}
            for term in anchor["required_terms"]
        ]
        records.append(
            {
                "source": source,
                "pdf_page": page_number,
                "printed_page": anchor["printed_page"],
                "section": anchor["section"],
                "page_exists": page_exists,
                "required_terms": term_checks,
                "passed": page_exists and all(check["found"] for check in term_checks),
            }
        )
    return {
        "anchor_count": len(records),
        "records": records,
        "passed": len(records) == config["gates"]["pdf_anchor_count_expected"]
        and all(item["passed"] for item in records),
    }


def verify_indexed_government_source(config: dict[str, Any]) -> dict[str, Any]:
    declaration = config["indexed_government_source"]
    manifest_path = ROOT / declaration["manifest_path"]
    with manifest_path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    row = next((item for item in rows if item.get("id") == declaration["index_id"]), None)

    cached_path = ROOT / declaration["cached_text_path"]
    lines = cached_path.read_text(encoding="utf-8", errors="replace").splitlines()
    continuity_start, continuity_end = declaration["cached_text_lines"]["continuity"]
    transfer_start, transfer_end = declaration["cached_text_lines"]["transfer_floor_ranges"]
    continuity = " ".join(lines[continuity_start - 1 : continuity_end])
    transfer = " ".join(lines[transfer_start - 1 : transfer_end])
    continuity_terms = [
        "three central stairwells",
        "Stairwells A and C",
        "110th floor",
        "Stairwell B",
        "107th floor",
        "level B6",
        "two deviations",
    ]
    transfer_terms = ["heavy elevators", "42nd and 48th floors", "76th and 82nd floors"]
    continuity_checks = [
        {"term": term, "found": normalized(term) in normalized(continuity)}
        for term in continuity_terms
    ]
    transfer_checks = [
        {"term": term, "found": normalized(term) in normalized(transfer)} for term in transfer_terms
    ]
    manifest_passed = bool(
        row
        and row.get("sha256") == declaration["source_sha256_from_manifest"]
        and row.get("pages") == "585"
    )
    return {
        "index_id": declaration["index_id"],
        "source_status": declaration["source_status"],
        "manifest_row_found": row is not None,
        "manifest_source_sha256": row.get("sha256") if row else None,
        "manifest_page_count": int(row["pages"]) if row and row.get("pages") else None,
        "manifest_passed": manifest_passed,
        "continuity_line_range": [continuity_start, continuity_end],
        "continuity_term_checks": continuity_checks,
        "transfer_line_range": [transfer_start, transfer_end],
        "transfer_term_checks": transfer_checks,
        "original_external_path_opened": False,
        "passed": manifest_passed
        and all(item["found"] for item in continuity_checks)
        and all(item["found"] for item in transfer_checks),
    }


def conversion_block(config: dict[str, Any]) -> dict[str, Any]:
    enclosure = config["enclosure_construction"]
    mass = config["mass_treatment"]
    inch_to_mm = 25.4
    foot_to_m = 0.3048
    psf_to_pa = 47.88025898
    pound_to_kg = 0.45359237
    return {
        "constants": {
            "inch_to_mm": inch_to_mm,
            "foot_to_m": foot_to_m,
            "psf_to_pa": psf_to_pa,
            "pound_mass_equivalent_to_kg": pound_to_kg,
        },
        "stair_clear_widths": {
            "44_in_mm": round(44.0 * inch_to_mm, 3),
            "56_in_mm": round(56.0 * inch_to_mm, 3),
        },
        "minimum_stairwell_door_separation": {"ft": 70.0, "m": round(70.0 * foot_to_m, 6)},
        "shaft_wall": {
            "typical_plank_thickness_mm": round(
                enclosure["cast_gypsum_plank_thickness_in_typical"] * inch_to_mm, 3
            ),
            "sixteen_foot_floor_plank_thickness_mm": round(
                enclosure["cast_gypsum_plank_thickness_in_16ft_ceiling_floors"] * inch_to_mm, 3
            ),
            "plank_width_mm": round(enclosure["cast_gypsum_plank_width_in"] * inch_to_mm, 3),
            "board_sheet_thickness_mm": round(
                enclosure["gypsum_board_sheet_thickness_in"] * inch_to_mm, 3
            ),
        },
        "core_loads_not_discrete_stair_mass": {
            "live_load_kpa": round(mass["core_live_load_psf"] * psf_to_pa / 1000.0, 6),
            "superimposed_dead_load_kpa": round(
                mass["core_superimposed_dead_load_psf"] * psf_to_pa / 1000.0, 6
            ),
            "live_load_mass_equivalent_kg": round(mass["core_live_load_added_lb"] * pound_to_kg, 3),
            "superimposed_dead_load_mass_equivalent_kg": round(
                mass["core_superimposed_dead_load_added_lb"] * pound_to_kg, 3
            ),
            "warning": mass["future_double_counting_warning"],
        },
    }


def damage_for_floor(floor: int) -> tuple[str, str]:
    if floor == 92:
        return (
            "TRANSCRIBED_EYEWITNESS_IMPASSABLE_MODEL_LIMITED",
            "Official report transcribes all three as impassable; base model lacked core disruption and omitted floor-92 partitions.",
        )
    if floor == 93:
        return (
            "POSSIBLY_IMPASSABLE_MODEL_LIMITED_FIGURE_PRESENT",
            "Eyewitness wording extends possibly above floor 92; partitions absent in model; Figure 9-124 shown.",
        )
    if 94 <= floor <= 96:
        return (
            "OFFICIAL_BASE_MODEL_ALL_THREE_APPEAR_IMPASSABLE",
            "NIST base-case damage or debris assessment for floors 94-96.",
        )
    if floor == 97:
        return (
            "MODEL_FIGURE_PRESENT_TEXT_CONCLUSION_NOT_EXTENDED",
            "Figure 9-124 includes floor 97, but adjacent text does not extend the all-three conclusion.",
        )
    return "NOT_AUDITED", "No floor-specific component damage conclusion in the bounded V9Q passage."


def build_floor_rows(config: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    by_id = {item["stair_id"]: item for item in config["stairways"]}
    for floor in range(config["gates"]["floor_matrix_floor_range"][0], config["gates"]["floor_matrix_floor_range"][1] + 1):
        damage_status, damage_note = damage_for_floor(floor)
        for stair_id in (1, 2, 3):
            stair = by_id[stair_id]
            present = stair_id in (1, 2) or floor <= 107
            transfer = any(start <= floor <= end for start, end in stair["transfer_deviation_floor_ranges"])
            if 93 <= floor <= 97:
                position_status = "QUALITATIVE_FIGURE_9_124_ONLY"
                relative_position = stair["impact_zone_qualitative_position_north_up"]
            elif transfer:
                position_status = "TRANSFER_RANGE_DOCUMENTED_EXACT_OFFSET_UNKNOWN"
                relative_position = "unknown"
            else:
                position_status = "EXACT_METRIC_POSITION_UNKNOWN"
                relative_position = "unknown"
            rows.append(
                {
                    "floor": floor,
                    "stair_id": stair_id,
                    "letter_alias": stair["letter_alias"],
                    "standpipe_riser": stair["standpipe_riser"],
                    "present_in_reported_vertical_extent": str(present).lower(),
                    "clear_width_in": f"{stair['clear_width_in']:.1f}",
                    "clear_width_mm": f"{stair['clear_width_in'] * 25.4:.3f}",
                    "documented_transfer_range": str(transfer).lower(),
                    "plan_position_status": position_status,
                    "relative_position_north_up": relative_position,
                    "damage_evidence_status": damage_status,
                    "damage_evidence_note": damage_note,
                    "solver_geometry_qualified": "false",
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


def build_model_gate(config: dict[str, Any], floor_rows: list[dict[str, Any]]) -> dict[str, Any]:
    statuses = {"COMPLETE": 0, "PARTIAL": 0, "MISSING": 0}
    for record in config["required_model_fields"]:
        statuses[record["status"]] += 1
    gates = config["gates"]
    closed_credits = {
        "metric_solver_geometry": gates["metric_solver_geometry_authorized"],
        "stair_or_enclosure_discrete_mass": gates["stair_or_enclosure_discrete_mass_authorized"],
        "stair_or_enclosure_stiffness": gates["stair_or_enclosure_stiffness_authorized"],
        "stair_or_enclosure_strength": gates["stair_or_enclosure_strength_authorized"],
        "stair_or_enclosure_load_path": gates["stair_or_enclosure_load_path_credit_authorized"],
        "global_solver": gates["global_solver_authorized"],
        "blender_physical_validation": gates["blender_physical_validation_authorized"],
    }
    return {
        "iteration": config["iteration"],
        "required_model_fields": config["required_model_fields"],
        "field_status_counts": statuses,
        "qualitative_topology_layer_authorized": gates["qualitative_topology_layer_authorized"],
        "closed_credits": closed_credits,
        "all_structural_and_physical_validation_credits_closed": not any(closed_credits.values()),
        "floor_matrix_row_count": len(floor_rows),
        "decision": "DOCUMENT_THREE_STAIRS_AS_GEOMETRIC_VOIDS_AND_NONSTRUCTURAL_OBSTACLES_ONLY",
        "structural_coherence_note": (
            "The three stair systems matter to core openings, local framing topology, occupancy, debris and mass accounting, "
            "but V9Q does not qualify their exact geometry or any stiffness, strength or load path."
        ),
        "double_counting_warning": config["mass_treatment"]["future_double_counting_warning"],
        "next_gate": config["next_iteration"],
    }


def make_report(
    config: dict[str, Any],
    source_manifest: dict[str, Any],
    model_gate: dict[str, Any],
    result: dict[str, Any],
) -> str:
    stairs = config["stairways"]
    counts = model_gate["field_status_counts"]
    return f"""# V9Q — Audit sourcé des trois cages d'escalier du WTC 1

## Conclusion

V9Q est **{result['status']}** comme audit documentaire reproductible. Les trois cages doivent être conservées dans le futur modèle pour la cohérence géométrique du noyau : vides de plancher, obstacles non structuraux, interfaces avec le plancher, masse globale et topologie des dommages. En revanche, les sources auditées ne qualifient ni leur géométrie métrique complète, ni leurs assemblages, ni leur masse discrète, ni une contribution porteuse. Aucun crédit de rigidité, résistance ou chemin de charge n'est donc attribué.

## 1. Faits directement observés ou transcrits

- Le WTC 1 comportait trois cages centrales, avec les correspondances 1/A/FS-F3, 2/C/FS-F2 et 3/B/FS-F1.
- A et C avaient une largeur libre publiée de 44 in ({stairs[0]['clear_width_in'] * 25.4:.1f} mm) ; B, 56 in ({stairs[2]['clear_width_in'] * 25.4:.1f} mm).
- A et C reliaient le 110e étage à la mezzanine surélevée ; B reliait le 107e étage au niveau B6.
- Deux plages de déviation sont rapportées pour A et C : étages 42–48 et 76–82. Leur décalage métrique exact n'est pas donné.
- L'enveloppe générique des gaines/cages était un assemblage non structural en panneaux de gypse moulé, maintenus par des profils métalliques aux dalles, avec parements en plaques de gypse.

## 2. Résultats et choix du modèle officiel

- NIST a classé ces parois comme non structurales et n'a pas effectué d'essais matériaux propres aux matériaux non structuraux pour son modèle d'impact.
- Le modèle NIST a utilisé une loi approchée à 500 psi et 60 % de déformation de rupture ; ce choix de calcul n'est pas une validation du composant réel.
- Dans le modèle global WTC 1, les cloisons du noyau n'étaient explicites qu'aux étages 94 à 97. La base des parois était fusionnée à la dalle ; leur sommet n'était pas contraint.
- Le passage audité indique que les dommages ou débris du cas de base rendaient les trois cages apparemment impraticables aux étages 94 à 96. Les témoignages transcrits pour l'étage 92 et la synthèse générale NIST restent des classes de preuve distinctes.

## 3. Source gouvernementale indexée, distincte d'un plan de structure

Le texte mis en cache du rapport de la Commission du 11-Septembre fournit la continuité verticale et les plages de déviation, en renvoyant à une réponse de la Port Authority. Il ne constitue ni un plan métrique d'exécution ni une validation structurale NIST. Le PDF externe mentionné par l'index n'a pas été ouvert.

## 4. Exigence utilisateur

Le futur modèle de tour doit représenter explicitement trois cages d'escalier. V9Q traduit cette exigence en champs vérifiables et en garde-fous, sans inventer les données manquantes.

## 5. Résultats dérivés

- {model_gate['floor_matrix_row_count']} lignes ont été produites : 110 étages × 3 cages.
- Couverture des sept champs nécessaires : {counts['COMPLETE']} complet, {counts['PARTIAL']} partiels, {counts['MISSING']} manquant.
- La position relative des trois cages aux étages 93–97 est seulement qualitative, dérivée de la figure 9-124 avec le nord en haut : 1/A au nord-est, 2/C au nord-ouest, 3/B au sud-centre.
- Les conversions d'unités sont calculées séparément ; les charges globales du noyau publiées par NIST ne sont pas converties en masses discrètes de cages.

## 6. Hypothèses propres au modèle

Aucune géométrie métrique ou propriété mécanique nouvelle n'est admise en V9Q. Une future esquisse qualitative pourra représenter les trois vides/obstacles, mais toute coordonnée au-delà de la topologie relative documentée restera une hypothèse affichée comme telle.

## 7. Contradictions, limites et informations manquantes

- coordonnées et orientations métriques par étage ;
- géométrie exacte des deux transferts de A et C ;
- volées, paliers, limons, marches et attaches ;
- connexions réelles aux dalles et à l'ossature du noyau ;
- masses discrètes et détails de construction par étage ;
- dommages composant par composant sur toute la zone d'impact.

La masse globale du noyau déjà intégrée par NIST impose un contrôle de double comptage avant l'ajout futur d'éléments discrets.

## 8. Contrôles de reproductibilité et périmètre

- Régressions V9P : **{'PASS' if source_manifest['regressions']['passed'] else 'FAIL'}**.
- Empreintes des sources mises en cache : **{'PASS' if source_manifest['sources']['passed'] else 'FAIL'}**.
- Ancrages de pages PDF : **{'PASS' if source_manifest['pdf_anchors']['passed'] else 'FAIL'}** ({source_manifest['pdf_anchors']['anchor_count']} contrôles).
- Rapport gouvernemental indexé : **{'PASS' if source_manifest['indexed_government_source']['passed'] else 'FAIL'}**.
- Archive source externe : non ouverte et non rescannée.
- Réseau, solveur, Blender et calcul physique global : non utilisés.

Blender reste un outil de visualisation. Il ne constitue pas une validation physique de l'impact, des cages d'escalier ou du comportement global de la tour.

## 9. Décision et suite

Le seul niveau autorisé est une couche topologique qualitative à trois cages. Tous les crédits de masse discrète, rigidité, résistance, connexion porteuse, dommage quantifié, solveur global et validation physique restent fermés.

**V9R :** {config['next_iteration']['objective']}
"""


def main() -> int:
    started = time.perf_counter()
    config = load_json(CONFIG_PATH)
    outputs = {name: ROOT / relative for name, relative in config["outputs"].items()}

    regressions = verify_hashes(config["regression_files"])
    sources = verify_hashes(config["source_files"])
    pdf_anchors = verify_pdf_anchors(config)
    indexed_source = verify_indexed_government_source(config)
    conversions = conversion_block(config)
    floor_rows = build_floor_rows(config)
    model_gate = build_model_gate(config, floor_rows)

    source_manifest = {
        "iteration": config["iteration"],
        "configuration": str(CONFIG_PATH.relative_to(ROOT)).replace("\\", "/"),
        "configuration_sha256": sha256(CONFIG_PATH),
        "source_policy": config["source_policy"],
        "regressions": regressions,
        "sources": sources,
        "pdf_anchors": pdf_anchors,
        "indexed_government_source": indexed_source,
        "passed": regressions["passed"] and sources["passed"] and pdf_anchors["passed"] and indexed_source["passed"],
    }
    geometry_matrix = {
        "iteration": config["iteration"],
        "epistemic_scope": "SOURCE_GATED_DOCUMENTARY_MATRIX_NOT_SOLVER_GEOMETRY",
        "stairway_count": len(config["stairways"]),
        "stairways": config["stairways"],
        "enclosure_construction": config["enclosure_construction"],
        "nist_impact_model_treatment": config["nist_impact_model_treatment"],
        "mass_treatment": config["mass_treatment"],
        "damage_evidence": config["damage_evidence"],
        "unit_conversions": conversions,
        "evidence_policy": config["evidence_policy"],
    }

    write_floor_csv(outputs["floor_matrix"], floor_rows)
    write_json(outputs["source_manifest"], source_manifest)
    write_json(outputs["stairwell_matrix"], geometry_matrix)
    write_json(outputs["model_gate"], model_gate)

    all_credits_closed = model_gate["all_structural_and_physical_validation_credits_closed"]
    checks = {
        "source_manifest_passed": source_manifest["passed"],
        "stairway_count_matches": len(config["stairways"]) == config["gates"]["stairway_count_expected"],
        "floor_matrix_row_count_matches": len(floor_rows) == 330,
        "complete_required_model_field_count_matches": model_gate["field_status_counts"]["COMPLETE"]
        == config["gates"]["complete_required_model_field_count_expected"],
        "all_structural_and_physical_validation_credits_closed": all_credits_closed,
        "qualitative_topology_only": config["gates"]["qualitative_topology_layer_authorized"]
        and not config["gates"]["metric_solver_geometry_authorized"],
        "archive_source_not_read_or_rescanned": not config["source_policy"]["source_archive_read"]
        and not config["source_policy"]["source_archive_rescanned"],
        "no_network_solver_or_blender": not config["source_policy"]["network_access_used"]
        and not config["source_policy"]["structural_solver_authorized"]
        and not config["source_policy"]["blender_authorized"],
    }
    passed = all(checks.values())
    result = {
        "iteration": config["iteration"],
        "status": "PASS" if passed else "FAIL",
        "purpose": config["dataset"]["scope"],
        "checks": checks,
        "counts": {
            "pdf_anchors": pdf_anchors["anchor_count"],
            "stairways": len(config["stairways"]),
            "floor_matrix_rows": len(floor_rows),
            "required_model_fields": model_gate["field_status_counts"],
        },
        "authorized_result": model_gate["decision"],
        "physical_result": "NONE",
        "structural_solver_executed": False,
        "blender_executed": False,
        "physical_validation": False,
        "source_archive_read": False,
        "source_archive_rescanned": False,
        "network_access_used": False,
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
