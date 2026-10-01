from __future__ import annotations

import csv
import hashlib
import json
import math
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "wtc1_simulation_v8/data/v10q_three_track_fire_thermal_handoff.json"
SCRIPT_PATH = Path(__file__).resolve()


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


def close(left: float, right: float, tolerance: float = 1e-9) -> bool:
    return math.isclose(float(left), float(right), rel_tol=0.0, abs_tol=tolerance)


def verify_hash(item: dict[str, Any], read_mode: str = "FULL_ARTIFACT") -> dict[str, Any]:
    path = abs_path(item["path"])
    role = item.get("role", item.get("id", "file"))
    if not path.is_file():
        raise RuntimeError(f"Missing {role}: {path}")
    actual = sha256_file(path)
    if actual.lower() != item["expected_sha256"].lower():
        raise RuntimeError(f"Hash mismatch for {role}: expected {item['expected_sha256']}, got {actual}")
    row = {
        "role": role,
        "path": rel(path),
        "sha256": actual,
        "bytes": path.stat().st_size,
        "read_mode": read_mode,
        "status": "PASS",
    }
    for key in ("evidence_class", "use"):
        if key in item:
            row[key] = item[key]
    return row


def load_config() -> dict[str, Any]:
    config = load_json(CONFIG_PATH)
    if config.get("iteration") != "V10Q":
        raise RuntimeError("Configuration iteration must be V10Q")
    expected = config["expected"]
    counts = {
        "regression_file_count": len(config["regression_files"]),
        "protected_file_count": len(config["protected_files"]),
        "cached_input_file_count": len(config["cached_input_files"]),
        "official_source_hash_only_file_count": len(config["official_source_hash_only_files"]),
        "track_count": len(config["track_contract"]["required_track_ids"]),
        "component_family_count": len(config["track_contract"]["component_families"]),
        "floor_count": len(config["track_contract"]["analysis_floors"]),
        "sfrm_required_field_count": len(config["track_contract"]["required_sfrm_unknown_fields"]),
    }
    for key, actual in counts.items():
        if actual != expected[key]:
            raise RuntimeError(f"Unexpected {key}: {actual} != {expected[key]}")
    if config["track_contract"]["required_track_ids"] != [
        "CONTROL_ZERO_FIRE",
        "OFFICIAL_MODEL_DEPENDENT_THERMAL_REFERENCE",
        "UNKNOWN_EVENT_FIRE",
    ]:
        raise RuntimeError("Track order differs from predeclaration")
    return config


def expand_temperature_matrix(
    config: dict[str, Any], transfer: dict[str, Any], v8a: dict[str, Any]
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    fire = transfer["fire_case_b"]
    contract = config["track_contract"]
    expected = config["expected"]
    times = fire["times_min"]
    if len(times) != expected["time_knot_count"]:
        raise RuntimeError("Unexpected time-knot count")
    if any(right <= left for left, right in zip(times, times[1:])):
        raise RuntimeError("Published time support is not strictly increasing")
    time_seconds = [float(value) * contract["unit_conversions"]["min_to_s"] for value in times]
    rows: list[dict[str, Any]] = []
    conversion_checks = 0
    valid_range_count = 0
    for family_id, source_field in contract["component_families"].items():
        by_floor = fire[source_field]
        if set(by_floor) != {str(value) for value in contract["analysis_floors"]}:
            raise RuntimeError(f"Floor coverage mismatch for {family_id}")
        for floor in contract["analysis_floors"]:
            ranges = by_floor[str(floor)]
            if len(ranges) != len(times):
                raise RuntimeError(f"Time coverage mismatch for {family_id} Floor {floor}")
            for index, pair in enumerate(ranges):
                minimum_c = float(pair[0])
                maximum_c = float(pair[1])
                minimum_k = minimum_c + contract["unit_conversions"]["degC_to_K_offset"]
                maximum_k = maximum_c + contract["unit_conversions"]["degC_to_K_offset"]
                range_valid = minimum_c <= maximum_c
                min_conversion = close(minimum_k - minimum_c, 273.15)
                max_conversion = close(maximum_k - maximum_c, 273.15)
                if not range_valid or not min_conversion or not max_conversion:
                    raise RuntimeError(f"Temperature range or conversion failed for {family_id} F{floor} t={times[index]}")
                valid_range_count += int(range_valid)
                conversion_checks += int(min_conversion) + int(max_conversion)
                rows.append(
                    {
                        "track_id": "OFFICIAL_MODEL_DEPENDENT_THERMAL_REFERENCE",
                        "component_family": family_id,
                        "source_field": source_field,
                        "floor": floor,
                        "time_min": times[index],
                        "time_s": time_seconds[index],
                        "temperature_min_c": minimum_c,
                        "temperature_max_c": maximum_c,
                        "temperature_min_K": minimum_k,
                        "temperature_max_K": maximum_k,
                        "minimum_maximum_valid": range_valid,
                        "celsius_to_kelvin_checks_pass": min_conversion and max_conversion,
                        "maximum_above_600_c": maximum_c > 600.0,
                        "young_modulus_polynomial_valid_at_maximum": maximum_c <= 600.0,
                        "exact_member_assignment": False,
                        "gas_temperature_history": False,
                        "incident_heat_flux_history": False,
                        "temporal_interpolation_performed": False,
                        "temporal_extrapolation_performed": False,
                        "evidence_class": "OFFICIAL_MODEL_OUTPUT_DEPENDENT_RANGE",
                        "physical_thermal_release": False,
                    }
                )
    comparisons: list[dict[str, Any]] = []
    core_rows_100 = {
        row["floor"]: row
        for row in rows
        if row["component_family"] == "core_column" and row["time_min"] == 100
    }
    for floor in contract["analysis_floors"]:
        row = core_rows_100[floor]
        cached = v8a["case_b_thermal_envelopes_at_100_min"][str(floor)]
        min_match = close(row["temperature_min_c"], cached["temperature_min_c"])
        max_match = close(row["temperature_max_c"], cached["temperature_max_c"])
        comparisons.append(
            {
                "floor": floor,
                "source_min_c": row["temperature_min_c"],
                "v8a_min_c": cached["temperature_min_c"],
                "minimum_match": min_match,
                "source_max_c": row["temperature_max_c"],
                "v8a_max_c": cached["temperature_max_c"],
                "maximum_match": max_match,
                "status": "PASS_CACHED_TRANSFORMATION_CONSISTENCY" if min_match and max_match else "FAIL",
            }
        )
    if any(item["status"] == "FAIL" for item in comparisons):
        raise RuntimeError("V8A 100-minute core envelope comparison failed")
    summary = {
        "time_knots_min": times,
        "time_knots_s": time_seconds,
        "strictly_increasing_time_support": True,
        "temperature_envelope_row_count": len(rows),
        "celsius_to_kelvin_endpoint_check_count": conversion_checks,
        "valid_minimum_maximum_range_count": valid_range_count,
        "global_temperature_min_c": min(row["temperature_min_c"] for row in rows),
        "global_temperature_max_c": max(row["temperature_max_c"] for row in rows),
        "global_temperature_min_K": min(row["temperature_min_K"] for row in rows),
        "global_temperature_max_K": max(row["temperature_max_K"] for row in rows),
        "temperature_range_max_above_600c_count": sum(row["maximum_above_600_c"] for row in rows),
        "v8a_core_100min_comparisons": comparisons,
        "v8a_core_100min_comparison_count": len(comparisons),
        "v8a_core_100min_comparison_pass_count": sum(item["status"].startswith("PASS") for item in comparisons),
        "exact_member_temperature_assignment_count": 0,
        "gas_temperature_history_available_count": 0,
        "incident_heat_flux_history_available_count": 0,
    }
    return rows, summary


def audit_v8e(v8e: dict[str, Any], transfer: dict[str, Any]) -> dict[str, Any]:
    checks = {
        "floor_support_94_99": v8e["facts_transferred"]["floors"] == [94, 95, 96, 97, 98, 99],
        "time_support_matches_transfer": v8e["facts_transferred"]["times_min"] == transfer["fire_case_b"]["times_min"],
        "temperature_input_label_is_nist_range": v8e["facts_transferred"]["temperature_input"] == "NIST Case B per-floor spatial minimum and maximum",
        "ensemble_seed_count_200": v8e["ensemble"]["seeds"] == 200,
        "gamma_grid_exact": v8e["ensemble"]["gamma_values"] == [0.5, 1.0, 2.0, 4.0],
        "synthetic_fields_not_probabilities": v8e["ensemble"]["fields_are_probabilities"] is False,
    }
    if not all(checks.values()):
        raise RuntimeError(f"V8E cached consistency failed: {[key for key, value in checks.items() if not value]}")
    return {
        "check_count": len(checks),
        "pass_count": sum(checks.values()),
        "checks": checks,
        "scope": "V8E creates synthetic spatial fields inside official-model-dependent extrema. It does not provide measured or member-resolved temperatures and its case fractions are not event probabilities.",
    }


def fuel_and_support_audit(
    config: dict[str, Any], transfer: dict[str, Any], v10p_audit: dict[str, Any]
) -> dict[str, Any]:
    fire = transfer["fire_case_b"]
    conversions = config["track_contract"]["unit_conversions"]
    converted = (
        float(fire["office_fuel_load_lb_ft2"])
        * float(conversions["lb_to_kg"])
        / float(conversions["ft_to_m"]) ** 2
    )
    difference = float(fire["office_fuel_load_kg_m2"]) - converted
    times = fire["times_min"]
    time_rows = [
        {
            "index": index,
            "time_min": value,
            "time_s": float(value) * float(conversions["min_to_s"]),
            "conversion_pass": close(float(value) * float(conversions["min_to_s"]), float(value) * 60.0),
        }
        for index, value in enumerate(times)
    ]
    fuel_residual = float(v10p_audit["ledger_summary"]["fuel_bin_rounding_residual_lb"])
    return {
        "office_fuel_load_parallel_source_values": {
            "kg_m2_stated": fire["office_fuel_load_kg_m2"],
            "lb_ft2_stated": fire["office_fuel_load_lb_ft2"],
            "five_lb_ft2_converted_to_kg_m2": converted,
            "stated_kg_m2_minus_converted_kg_m2": difference,
            "relative_difference_to_stated_kg_m2": difference / float(fire["office_fuel_load_kg_m2"]),
            "status": "ROUNDED_PARALLEL_SOURCE_VALUES_RETAINED_NO_FORCED_EQUALITY",
        },
        "v10p_fuel_bin_rounding_residual_lb": fuel_residual,
        "v10p_fuel_bin_residual_status": "RETAINED_NOT_REDISTRIBUTED",
        "time_support": time_rows,
        "time_support_strictly_increasing": all(right > left for left, right in zip(times, times[1:])),
        "temporal_interpolation_performed": False,
        "temporal_extrapolation_performed": False,
        "fire_gas_temperature_history_available": False,
        "incident_heat_flux_history_available": False,
        "spatial_fire_mesh_or_polygon_mapping_available": False,
    }


def build_sfrm_rows(config: dict[str, Any], transfer: dict[str, Any]) -> list[dict[str, Any]]:
    description = transfer["fire_case_b"]["description"]
    return [
        {
            "track_id": "OFFICIAL_MODEL_DEPENDENT_THERMAL_REFERENCE",
            "field": field,
            "value": "",
            "unit": {
                "thickness_m": "m",
                "density_kg_m3": "kg/m3",
                "thermal_conductivity_W_mK": "W/(m K)",
                "specific_heat_J_kgK": "J/(kg K)",
                "emissivity": "1",
                "impact_damage_fraction": "1",
                "spatial_damage_map": "geometry/id map",
                "adhesion_or_failure_law": "constitutive law",
            }[field],
            "status": "UNKNOWN_NOT_NUMERIC_OR_SPATIALLY_AVAILABLE_IN_SELECTED_INPUTS",
            "available_context_only": description,
            "context_is_numeric_assignment": False,
            "required_for_physical_fire_to_solid_transfer": True,
            "physical_assignment": False,
        }
        for field in config["track_contract"]["required_sfrm_unknown_fields"]
    ]


def build_tracks(
    config: dict[str, Any],
    transfer: dict[str, Any],
    v10o: dict[str, Any],
    v10p: dict[str, Any],
    temperature_summary: dict[str, Any],
    fuel_audit: dict[str, Any],
    sfrm_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    upstream = {track["track_id"]: track for track in v10p["tracks"]}
    control_fire = v10o["records"]["I04_FIRE_TO_THERMAL_SOLIDS"]
    control_thermal = v10o["records"]["I05_THERMAL_TO_INITIATION"]
    sfrm_unknowns = {row["field"]: None for row in sfrm_rows}
    tracks = [
        {
            "track_id": "CONTROL_ZERO_FIRE",
            "upstream_track_id": "CONTROL_ZERO_INPUT",
            "epistemic_class": "SYNTHETIC_SOFTWARE_CONTROL_NOT_HISTORICAL",
            "status": "PASS_SOFTWARE_SENTINEL_ONLY",
            "fire_record": control_fire,
            "thermal_record": control_thermal,
            "temperature_reference_K_is_wtc_property": False,
            "downstream_software_control_release": True,
            "downstream_physical_release": False,
            "physical_validation": False,
        },
        {
            "track_id": "OFFICIAL_MODEL_DEPENDENT_THERMAL_REFERENCE",
            "upstream_track_id": "OFFICIAL_MODEL_DEPENDENT_REFERENCE",
            "epistemic_class": "OFFICIAL_MODEL_OUTPUT_DEPENDENT_PLUS_DERIVED_SYNTHETIC_FIELDS",
            "status": "PASS_RANGE_TRANSCRIPTION_AND_UNIT_SUPPORT_ONLY",
            "upstream_damage_reference_status": upstream["OFFICIAL_MODEL_DEPENDENT_REFERENCE"]["status"],
            "office_fuel_load": fuel_audit["office_fuel_load_parallel_source_values"],
            "fuel_distribution_lb": transfer["base_case_fuel_and_debris_lb"],
            "fuel_distribution_bin_residual_lb": fuel_audit["v10p_fuel_bin_rounding_residual_lb"],
            "fire_description": transfer["fire_case_b"]["description"],
            "fire_gas_history": None,
            "incident_heat_flux_history": None,
            "convection_boundary_history": None,
            "fire_mesh_or_opening_map": None,
            "sfrm_inputs": sfrm_unknowns,
            "structural_temperature_envelopes": {
                "matrix_path": config["outputs"]["temperature_matrix"],
                "row_count": temperature_summary["temperature_envelope_row_count"],
                "time_knots_min": temperature_summary["time_knots_min"],
                "time_knots_s": temperature_summary["time_knots_s"],
                "component_families": list(config["track_contract"]["component_families"]),
                "floors": config["track_contract"]["analysis_floors"],
                "range_only_not_member_assignment": True,
            },
            "member_temperature_histories": None,
            "v8e_synthetic_fields": {
                "path": "wtc1_simulation_v8/output/resultats_wtc1_v8e_champs_thermiques.json",
                "status": "DERIVED_SYNTHETIC_FIELDS_INSIDE_OFFICIAL_EXTREMA_NOT_MEASURED",
                "fractions_are_event_probabilities": False,
            },
            "downstream_software_reference_release": True,
            "downstream_physical_release": False,
            "physical_validation": False,
        },
        {
            "track_id": "UNKNOWN_EVENT_FIRE",
            "upstream_track_id": "UNKNOWN_PHYSICAL_DAMAGE",
            "epistemic_class": "UNKNOWN_EVENT_FIRE_AND_THERMAL_STATE",
            "status": "BLOCKED_EVENT_FIRE_AND_MEMBER_THERMAL_HISTORY_UNRESOLVED",
            "upstream_unknown_damage_status": upstream["UNKNOWN_PHYSICAL_DAMAGE"]["status"],
            "fuel_load": None,
            "fuel_distribution": None,
            "combustible_distribution": None,
            "opening_and_ventilation_map": None,
            "fire_gas_history": None,
            "incident_heat_flux_history": None,
            "sfrm_inputs": {field: None for field in config["track_contract"]["required_sfrm_unknown_fields"]},
            "member_temperature_histories": None,
            "blocking_reasons": [
                "physical impact damage, openings, debris and fuel distribution are unresolved upstream",
                "exact event FDS input package and fire mesh are unavailable",
                "gas temperature, heat flux and convection histories are unavailable",
                "SFRM thickness, properties, damage fraction and spatial map are unavailable in the selected inputs",
                "official structural-temperature ranges are not member-resolved histories and are not independent event observations",
            ],
            "downstream_software_unknown_status_release": True,
            "downstream_physical_release": False,
            "physical_validation": False,
        },
    ]
    if [track["track_id"] for track in tracks] != config["track_contract"]["required_track_ids"]:
        raise RuntimeError("Constructed fire/thermal track order differs from predeclaration")
    return tracks


def make_report(
    config: dict[str, Any], summary: dict[str, Any], fuel: dict[str, Any], v8e_audit: dict[str, Any]
) -> str:
    load = fuel["office_fuel_load_parallel_source_values"]
    return "\n".join(
        [
            "# WTC 1 — V10Q : transfert feu → thermique en trois pistes",
            "",
            f"Généré le {utc_now()}. Aucun FDS, solveur thermique, GPU ou Blender n’est lancé.",
            "",
            "## Résultat principal",
            "",
            "Le transfert feu→thermique conserve trois pistes non fusionnées : contrôle sans feu, référence dépendante du modèle officiel, et incendie réel inconnu. La référence officielle fournit 105 plages de température structurelle aux cinq instants publiés ; elle ne fournit pas, dans les entrées sélectionnées, les histoires de température des gaz, de flux thermique, de convection, ni les températures exactes élément par élément nécessaires à un nouveau calcul thermique.",
            "",
            "## Vérifications numériques",
            "",
            f"- Plages : {summary['temperature_envelope_row_count']} = 3 familles × 7 étages × 5 instants.",
            f"- Conversions °C→K : {summary['celsius_to_kelvin_endpoint_check_count']}/210 extrémités exactes.",
            f"- Ordre min≤max : {summary['valid_minimum_maximum_range_count']}/105.",
            f"- Comparaison aux extrêmes du noyau V8A à 100 min : {summary['v8a_core_100min_comparison_pass_count']}/7.",
            f"- Contrôles d’identité V8E : {v8e_audit['pass_count']}/{v8e_audit['check_count']}.",
            f"- Domaine total transcrit : {summary['global_temperature_min_c']:.0f} à {summary['global_temperature_max_c']:.0f} °C ({summary['global_temperature_min_K']:.2f} à {summary['global_temperature_max_K']:.2f} K).",
            "",
            "## Deux alertes quantitatives",
            "",
            f"La charge combustible est donnée à la fois comme 25 kg/m² et 5 lb/ft². La conversion exacte de 5 lb/ft² vaut {load['five_lb_ft2_converted_to_kg_m2']:.6f} kg/m², soit un écart conservé de {load['stated_kg_m2_minus_converted_kg_m2']:.6f} kg/m² ({100*load['relative_difference_to_stated_kg_m2']:.3f} %). Les deux valeurs sont donc traitées comme des valeurs sources parallèles arrondies, pas forcées à l’égalité.",
            "",
            f"Le polynôme du module d’Young sélectionné dans la transcription n’est déclaré valable que jusqu’à 600 °C, tandis que {summary['temperature_range_max_above_600c_count']}/105 maxima de plage dépassent 600 °C. V10Q interdit toute extrapolation silencieuse ; ces points devront être bloqués ou traités comme hypothèses séparées en V10R.",
            "",
            "Le résidu de 20 lb entre la somme des cases de carburant et le total publié, identifié en V10P, est conservé. Il n’est attribué à aucun étage.",
            "",
            "## SFRM et support spatial",
            "",
            "La phrase indiquant que le dommage de protection incendie suit le trajet d’impact est conservée comme contexte de modèle. Elle ne fournit aucune des huit entrées nécessaires : épaisseur, densité, conductivité, chaleur spécifique, émissivité, fraction endommagée, carte spatiale et loi d’adhésion/rupture. Les huit champs restent donc `null`.",
            "",
            "Les cinq nœuds temporels 20, 40, 60, 80 et 100 minutes sont convertis exactement en 1200, 2400, 3600, 4800 et 6000 secondes. Aucune interpolation ni extrapolation n’est effectuée, car les maxima eux-mêmes ne sont pas nécessairement monotones.",
            "",
            "## Séparation des preuves",
            "",
            "1. **Faits observés ici** : empreintes, structure des tableaux, conversions, comptages et comparaisons V8A/V8E.",
            "2. **Résultats du modèle officiel** : les 105 plages et la distribution de carburant restent dépendantes des calculs NIST.",
            "3. **Archives** : aucune archive source externe n’est lue ; trois PDF officiels locaux sont seulement rehachés.",
            "4. **Hypothèses** : les champs spatiaux V8E sont synthétiques ; aucune valeur SFRM ou température de membre n’est ajoutée.",
            "5. **Résultats dérivés** : conversions SI, écart de double unité, domaine thermique et dépassements de validité.",
            "6. **Inconnues** : feu réel, ouvertures, ventilation, flux, SFRM et températures élémentaires.",
            "",
            "## Décision",
            "",
            "La piste officielle peut alimenter uniquement une sensibilité portant ses étiquettes de dépendance et de champ synthétique. La piste physique reste bloquée. Zéro état thermique physique est libéré en aval et aucune conclusion d’effondrement ou de non-effondrement n’est autorisée.",
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
    cached_rows = [verify_hash(item) for item in config["cached_input_files"]]
    official_rows = [
        verify_hash(item, read_mode="HASH_ONLY_NO_PAGE_OR_TEXT_EXTRACTION")
        for item in config["official_source_hash_only_files"]
    ]
    regression = {
        "iteration": "V10Q",
        "generated_at_utc": utc_now(),
        "validation_status": "PASS",
        "regression_file_count": len(regression_rows),
        "protected_file_count": len(protected_rows),
        "regression_files": regression_rows,
        "protected_files": protected_rows,
        "source_archive_read": False,
        "source_archive_modified": False,
        "official_source_pdf_hash_only_count": len(official_rows),
        "official_source_pdf_page_read_count": 0,
        "official_source_pdf_text_extraction_count": 0,
        "official_sources_directory_modified": False,
        "blender_master_unchanged": True,
    }
    source_manifest = {
        "iteration": "V10Q",
        "generated_at_utc": utc_now(),
        "validation_status": "PASS",
        "cached_input_count": len(cached_rows),
        "official_source_hash_only_count": len(official_rows),
        "cached_inputs": cached_rows,
        "official_source_hash_only_files": official_rows,
        "source_use_rule": "PDFs provide hash continuity only. Numeric values are consumed from the frozen cached transcription and remain official-model dependent.",
    }
    inputs = {item["id"]: abs_path(item["path"]) for item in config["cached_input_files"]}
    transfer = load_json(inputs["NIST_WTC1_TRANSFER_TRANSCRIPTION"])
    v8a = load_json(inputs["V8A_TRANSFER_RESULTS"])
    v8e = load_json(inputs["V8E_SYNTHETIC_THERMAL_RESULTS"])
    v10o = load_json(inputs["V10O_ZERO_FIRE_CONTROL_TRACE"])
    v10p = load_json(inputs["V10P_IMPACT_DAMAGE_TRACK_MANIFEST"])
    v10p_audit = load_json(abs_path("wtc1_simulation_v8/output/v10p_conservation_ledger_audit.json"))

    matrix_rows, temperature_summary = expand_temperature_matrix(config, transfer, v8a)
    v8e_audit = audit_v8e(v8e, transfer)
    fuel_audit = fuel_and_support_audit(config, transfer, v10p_audit)
    sfrm_rows = build_sfrm_rows(config, transfer)
    tracks = build_tracks(config, transfer, v10o, v10p, temperature_summary, fuel_audit, sfrm_rows)
    expected = config["expected"]
    checks = {
        "track_count": len(tracks) == expected["track_count"],
        "temperature_envelope_row_count": temperature_summary["temperature_envelope_row_count"] == expected["temperature_envelope_row_count"],
        "celsius_to_kelvin_endpoint_check_count": temperature_summary["celsius_to_kelvin_endpoint_check_count"] == expected["celsius_to_kelvin_endpoint_check_count"],
        "valid_minimum_maximum_range_count": temperature_summary["valid_minimum_maximum_range_count"] == expected["valid_minimum_maximum_range_count"],
        "v8a_core_100min_comparison_count": temperature_summary["v8a_core_100min_comparison_count"] == expected["v8a_core_100min_comparison_count"],
        "v8a_core_100min_comparison_pass_count": temperature_summary["v8a_core_100min_comparison_pass_count"] == expected["v8a_core_100min_comparison_pass_count"],
        "v8e_cached_consistency_check_count": v8e_audit["check_count"] == expected["v8e_cached_consistency_check_count"] and v8e_audit["pass_count"] == expected["v8e_cached_consistency_check_count"],
        "sfrm_required_field_count": len(sfrm_rows) == expected["sfrm_required_field_count"],
        "sfrm_numeric_or_spatial_field_available_count": sum(bool(row["value"]) for row in sfrm_rows) == expected["sfrm_numeric_or_spatial_field_available_count"],
        "gas_temperature_history_available_count": temperature_summary["gas_temperature_history_available_count"] == expected["gas_temperature_history_available_count"],
        "incident_heat_flux_history_available_count": temperature_summary["incident_heat_flux_history_available_count"] == expected["incident_heat_flux_history_available_count"],
        "exact_member_temperature_assignment_count": temperature_summary["exact_member_temperature_assignment_count"] == expected["exact_member_temperature_assignment_count"],
        "temperature_range_max_above_600c_count": temperature_summary["temperature_range_max_above_600c_count"] == expected["temperature_range_max_above_600c_count"],
        "global_temperature_min_c": close(temperature_summary["global_temperature_min_c"], expected["global_temperature_min_c"]),
        "global_temperature_max_c": close(temperature_summary["global_temperature_max_c"], expected["global_temperature_max_c"]),
        "fuel_load_from_5_lb_ft2_kg_m2": close(fuel_audit["office_fuel_load_parallel_source_values"]["five_lb_ft2_converted_to_kg_m2"], expected["fuel_load_from_5_lb_ft2_kg_m2"]),
        "fuel_load_dual_unit_difference_kg_m2": close(fuel_audit["office_fuel_load_parallel_source_values"]["stated_kg_m2_minus_converted_kg_m2"], expected["fuel_load_dual_unit_difference_kg_m2"]),
        "fuel_bin_rounding_residual_lb": close(fuel_audit["v10p_fuel_bin_rounding_residual_lb"], expected["fuel_bin_rounding_residual_lb"]),
        "downstream_physical_release_count": sum(track["downstream_physical_release"] for track in tracks) == expected["downstream_physical_release_count"],
    }
    if not all(checks.values()):
        raise RuntimeError(f"V10Q predeclared checks failed: {[key for key, value in checks.items() if not value]}")
    unknown = next(track for track in tracks if track["track_id"] == "UNKNOWN_EVENT_FIRE")
    required_unknowns = [
        unknown["fuel_load"],
        unknown["fuel_distribution"],
        unknown["combustible_distribution"],
        unknown["opening_and_ventilation_map"],
        unknown["fire_gas_history"],
        unknown["incident_heat_flux_history"],
        unknown["member_temperature_histories"],
    ] + list(unknown["sfrm_inputs"].values())
    if any(value is not None for value in required_unknowns):
        raise RuntimeError("UNKNOWN_EVENT_FIRE contains an invented field")

    unit_temporal_audit = {
        "iteration": "V10Q",
        "generated_at_utc": utc_now(),
        "validation_status": "PASS_WITH_PHYSICAL_HANDOFF_BLOCKED",
        "predeclared_checks": checks,
        "temperature_summary": temperature_summary,
        "fuel_and_temporal_support": fuel_audit,
        "v8e_cached_consistency": v8e_audit,
        "steel_model_validity": {
            "young_modulus_polynomial_declared_valid_range_c": transfer["steel_temperature_model"]["young_modulus_valid_temperature_range_c"],
            "envelope_maxima_above_600c_count": temperature_summary["temperature_range_max_above_600c_count"],
            "silent_extrapolation_authorized": False,
            "yield_ratio_equation_present": bool(transfer["steel_temperature_model"]["yield_ratio_equation"]),
            "yield_ratio_validity_range_explicit_in_selected_transcription": False,
        },
        "interpretation": "Range transcription and SI conversion pass. A structural-temperature output range is not a gas/heat-flux boundary history or a member-specific thermal solution.",
    }
    track_manifest = {
        "iteration": "V10Q",
        "generated_at_utc": utc_now(),
        "validation_status": "PASS_THREE_TRACK_SOFTWARE_HANDOFF_ONLY",
        "contract": config["track_contract"],
        "tracks": tracks,
        "epistemic_nonmerge_rule": "CONTROL_ZERO_FIRE, OFFICIAL_MODEL_DEPENDENT_THERMAL_REFERENCE and UNKNOWN_EVENT_FIRE retain distinct identifiers and cannot be averaged or promoted across evidence classes.",
        "historical_physical_thermal_promotion_count": 0,
        "downstream_physical_release_count": 0,
    }
    gate = {
        "iteration": "V10Q",
        "generated_at_utc": utc_now(),
        "validation_status": "PASS",
        "regression_gate": "PASS",
        "protected_blender_master_gate": "PASS_UNCHANGED",
        "source_identity_gate": "PASS_6_CACHED_PLUS_3_OFFICIAL_HASH_ONLY",
        "three_track_separation_gate": "PASS_3_OF_3",
        "temperature_range_gate": "PASS_105_OF_105",
        "temperature_unit_conversion_gate": "PASS_210_OF_210",
        "temporal_support_gate": "PASS_5_KNOTS_NO_INTERPOLATION_NO_EXTRAPOLATION",
        "v8a_core_100min_gate": "PASS_7_OF_7",
        "v8e_identity_and_scope_gate": "PASS_6_OF_6_SYNTHETIC_NOT_PROBABILITY",
        "fuel_load_dual_unit_gate": "ROUNDED_PARALLEL_VALUES_DIFFER_BY_0_587861818_KG_M2",
        "fuel_bin_residual_gate": "RETAINED_20_LB",
        "sfrm_input_gate": "CLOSED_0_OF_8_FIELDS_AVAILABLE",
        "gas_temperature_history_gate": "CLOSED_0_AVAILABLE",
        "incident_heat_flux_history_gate": "CLOSED_0_AVAILABLE",
        "member_temperature_history_gate": "CLOSED_RANGE_OUTPUTS_ONLY",
        "young_modulus_validity_gate": "PARTIAL_47_OF_105_RANGE_MAXIMA_ABOVE_600C",
        "fire_to_thermal_physical_handoff_gate": "CLOSED",
        "historical_physical_thermal_promotion_count": 0,
        "downstream_physical_release_count": 0,
        "v10r_labelled_range_preprocessor_authorized": True,
        "v10r_silent_material_law_extrapolation_authorized": False,
        "v10r_physical_initiation_conclusion_authorized": False,
        "mechanical_source_gate": "OPEN_0_OF_22_REQUIREMENTS",
        "historical_collapse_or_noncollapse_conclusion_authorized": False,
        "physical_assignment_count": 0,
        "fds_run_count": 0,
        "thermal_solver_run_count": 0,
        "other_solver_run_count": 0,
        "gpu_compute_run_count": 0,
        "blender_run_count": 0,
    }
    runtime_seconds = time.perf_counter() - started
    if runtime_seconds > config["execution_policy"]["maximum_runtime_seconds"]:
        raise RuntimeError("V10Q exceeded its predeclared runtime limit")

    outputs = config["outputs"]
    write_json(abs_path(outputs["regression_audit"]), regression)
    write_json(abs_path(outputs["source_manifest"]), source_manifest)
    write_json(abs_path(outputs["track_manifest"]), track_manifest)
    write_csv(abs_path(outputs["temperature_matrix"]), list(matrix_rows[0].keys()), matrix_rows)
    write_json(abs_path(outputs["unit_temporal_audit"]), unit_temporal_audit)
    write_csv(abs_path(outputs["sfrm_matrix"]), list(sfrm_rows[0].keys()), sfrm_rows)
    write_json(abs_path(outputs["handoff_gate"]), gate)
    write_text(abs_path(outputs["report"]), make_report(config, temperature_summary, fuel_audit, v8e_audit))

    results = {
        "iteration": "V10Q",
        "generated_at_utc": utc_now(),
        "validation_status": "PASS_THREE_TRACK_SOFTWARE_HANDOFF_ONLY",
        "dataset": config["dataset"],
        "configuration": {"path": rel(CONFIG_PATH), "sha256": sha256_file(CONFIG_PATH)},
        "script": {"path": rel(SCRIPT_PATH), "sha256": sha256_file(SCRIPT_PATH)},
        "source_summary": {"cached_input_count": len(cached_rows), "official_source_hash_only_count": len(official_rows)},
        "track_summary": {
            "track_ids": [track["track_id"] for track in tracks],
            "track_count": len(tracks),
            "unknown_event_fields_null": True,
            "downstream_physical_release_count": 0,
        },
        "temperature_summary": temperature_summary,
        "fuel_and_temporal_support": fuel_audit,
        "sfrm_summary": {
            "required_field_count": len(sfrm_rows),
            "numeric_or_spatial_field_available_count": 0,
        },
        "gates": gate,
        "epistemic_separation": {
            "observed_facts": "File hashes, table structure, unit conversions, counts and cached transformation comparisons.",
            "official_model_results": "All Case B structural-temperature ranges and fuel distributions remain dependent NIST model outputs.",
            "archive_claims": "No external archive is read; three local official PDFs are hash-checked only.",
            "model_hypotheses": "V8E spatial fields remain synthetic and no SFRM or member-temperature value is added.",
            "derived_results": "SI ranges, dual-unit difference, temporal support and material-law-domain exceedance count.",
            "unknowns": "Event gas/heat-flux histories, SFRM map/properties, exact member temperatures and physical fire remain unresolved.",
        },
        "runtime_seconds": round(time.perf_counter() - started, 6),
        "next_iteration": config["next_iteration"],
    }
    write_json(abs_path(outputs["results"]), results)

    artifact_roles = [
        "regression_audit", "source_manifest", "track_manifest", "temperature_matrix",
        "unit_temporal_audit", "sfrm_matrix", "handoff_gate", "report", "results",
    ]
    artifacts = []
    for role in artifact_roles:
        path = abs_path(outputs[role])
        if not path.is_file():
            raise RuntimeError(f"Missing output {role}: {path}")
        artifacts.append({"role": role, "path": rel(path), "sha256": sha256_file(path), "bytes": path.stat().st_size})
    offline = {
        "iteration": "V10Q",
        "generated_at_utc": utc_now(),
        "validation_status": "PASS",
        "artifact_count": len(artifacts),
        "artifacts": artifacts,
        "configuration": {"path": rel(CONFIG_PATH), "sha256": sha256_file(CONFIG_PATH)},
        "script": {"path": rel(SCRIPT_PATH), "sha256": sha256_file(SCRIPT_PATH)},
        "regression_files_reverified_count": len(regression_rows),
        "cached_input_files_reverified_count": len(cached_rows),
        "official_source_hash_only_files_reverified_count": len(official_rows),
        "official_source_pdf_page_read_count": 0,
        "official_source_pdf_text_extraction_count": 0,
        "protected_blender_master_unchanged": True,
        "source_archive_read": False,
        "source_archive_modified": False,
        "official_sources_directory_modified": False,
        "historical_physical_thermal_promotion_count": 0,
        "downstream_physical_release_count": 0,
        "physical_assignment_count": 0,
        "fds_run_count": 0,
        "thermal_solver_run_count": 0,
        "other_solver_run_count": 0,
        "gpu_compute_run_count": 0,
        "blender_run_count": 0,
    }
    write_json(abs_path(outputs["offline_audit"]), offline)
    print(
        json.dumps(
            {
                "iteration": "V10Q",
                "status": "PASS_THREE_TRACK_SOFTWARE_HANDOFF_ONLY",
                "tracks": len(tracks),
                "temperature_ranges": temperature_summary["temperature_envelope_row_count"],
                "celsius_kelvin_checks": temperature_summary["celsius_to_kelvin_endpoint_check_count"],
                "v8a_core_100min_checks": temperature_summary["v8a_core_100min_comparison_pass_count"],
                "maxima_above_600c": temperature_summary["temperature_range_max_above_600c_count"],
                "sfrm_fields_available": 0,
                "gas_or_heat_flux_histories_available": 0,
                "physical_thermal_releases": 0,
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
        print(f"V10Q ERROR: {exc}", file=sys.stderr)
        raise
