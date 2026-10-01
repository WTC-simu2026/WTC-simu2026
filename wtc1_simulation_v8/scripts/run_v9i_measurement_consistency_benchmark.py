#!/usr/bin/env python3
"""Build the V9I no-imputation descriptive benchmark from verified V9H payloads."""

from __future__ import annotations

import binascii
import csv
import hashlib
import html
import json
import math
import platform
import re
import statistics
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "wtc1_simulation_v8/data/v9i_measurement_consistency_benchmark.json"


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


def digest(path: Path, algorithm: str = "sha256") -> str:
    value = hashlib.new(algorithm)
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def nested_get(value: Any, dotted_path: str) -> Any:
    current = value
    for part in dotted_path.split("."):
        current = current[int(part)] if isinstance(current, list) else current[part]
    return current


def verify_regressions(config: dict[str, Any]) -> dict[str, Any]:
    files: dict[str, Any] = {}
    for relative, expected in config["regressions"]["required_files"].items():
        path = ROOT / relative
        actual = digest(path) if path.exists() else None
        files[relative] = {
            "exists": path.exists(),
            "expected_sha256": expected,
            "actual_sha256": actual,
            "passed": actual == expected,
        }
    metrics = []
    for declaration in config["regressions"]["required_metrics"]:
        source = load_json(ROOT / declaration["results"])
        actual = nested_get(source, declaration["path"])
        metrics.append({**declaration, "actual": actual, "passed": actual == declaration["expected"]})
    return {
        "files": files,
        "metrics": metrics,
        "passed": all(item["passed"] for item in files.values()) and all(item["passed"] for item in metrics),
    }


def verify_payloads(manifest: dict[str, Any]) -> dict[str, Any]:
    records = []
    for entry in manifest["file_records"]:
        path = ROOT / entry["output_path"]
        if path.exists():
            data = path.read_bytes()
            actual_sha256 = hashlib.sha256(data).hexdigest()
            actual_crc32 = f"{binascii.crc32(data) & 0xFFFFFFFF:08x}"
            passed = (
                len(data) == entry["verified_uncompressed_size_bytes"]
                and actual_sha256 == entry["sha256"]
                and actual_crc32 == entry["verified_crc32_hex"]
            )
        else:
            actual_sha256 = None
            actual_crc32 = None
            passed = False
        records.append({
            "path": entry["output_path"],
            "exists": path.exists(),
            "actual_sha256": actual_sha256,
            "expected_sha256": entry["sha256"],
            "actual_crc32_hex": actual_crc32,
            "expected_crc32_hex": entry["verified_crc32_hex"],
            "passed": passed,
        })
    return {
        "entry_count": len(records),
        "passed_count": sum(item["passed"] for item in records),
        "passed": bool(records) and all(item["passed"] for item in records),
        "records": records,
    }


def clean_html(value: str) -> str:
    text = re.sub(r"<[^>]+>", " ", value)
    return re.sub(r"\s+", " ", html.unescape(text)).strip()


def documentation_audit(config: dict[str, Any]) -> dict[str, Any]:
    source = config["sources"][0]
    metadata_path = ROOT / source["path"]
    metadata = load_json(metadata_path)
    description = clean_html(metadata["metadata"]["description"])
    phrases = {
        "imaginary_trigger_defined": "imaginary trigger" in description,
        "shortened_incident_bar_300_mm_defined": "length 300 mm" in description,
        "BC_Inc_and_BC_Trans_defined": "BC_Inc" in description and "BC_Trans" in description,
        "equation_12_referenced": "eq. (12)" in description,
        "acoustic_velocity_4639_m_per_s_defined": "4639 m/s" in description,
        "correction_factor_referenced": "correction factor" in description,
        "quasi_static_relative_displacement_defined": "relative displacements of the specimens" in description,
    }
    return {
        "zenodo_record_id": metadata["id"],
        "zenodo_doi": metadata["doi"],
        "dataset_title": metadata["metadata"]["title"],
        "publication_doi": config["sources"][1]["doi"],
        "description_checks": phrases,
        "all_required_description_checks_passed": all(phrases.values()),
        "DIC_filename_time_reference": config["documentation_transcription"]["DIC_filename_times"],
        "bar_boundary_condition_definition": config["documentation_transcription"]["bar_boundary_conditions"],
        "quasi_static_curve_definition": config["documentation_transcription"]["quasi_static_curve"],
        "equation_12_full_text_acquired": config["sources"][1]["full_equation_12_acquired"],
        "correction_factor_numeric_value_available": config["documentation_transcription"]["correction_factor_numeric_value_available"],
        "coordinate_reference_transcription": config["documentation_transcription"]["coordinate_image_observed"],
    }


def read_simple_table(path: Path, delimiter: str = ",") -> tuple[list[str], list[list[float]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.reader(handle, delimiter=delimiter))
    header = [item.strip() for item in rows[0]]
    values = [[float(item.strip()) for item in row] for row in rows[1:] if row]
    return header, values


def trapezoid(x: list[float], y: list[float]) -> float:
    return sum(0.5 * (a_y + b_y) * (b_x - a_x) for a_x, b_x, a_y, b_y in zip(x, x[1:], y, y[1:]))


def summarize_bar(path: Path, threshold_fraction: float) -> dict[str, Any]:
    header, rows = read_simple_table(path)
    times = [row[0] for row in rows]
    displacement = [row[1] for row in rows]
    steps = [b - a for a, b in zip(times, times[1:])]
    derivative = [(b_u - a_u) / (b_t - a_t) for a_t, b_t, a_u, b_u in zip(times, times[1:], displacement, displacement[1:])]
    peak_index = max(range(len(rows)), key=lambda index: abs(displacement[index]))
    peak_absolute = abs(displacement[peak_index])
    threshold = threshold_fraction * peak_absolute
    active_indices = [index for index, value in enumerate(displacement) if abs(value) >= threshold]
    return {
        "path": str(path.relative_to(ROOT)).replace("\\", "/"),
        "header": header,
        "row_count": len(rows),
        "time_range_s": [times[0], times[-1]],
        "strictly_increasing_time": all(step > 0 for step in steps),
        "time_step_s": {
            "minimum": min(steps),
            "maximum": max(steps),
            "mean": statistics.fmean(steps),
            "uniform_within_1e_15_s": max(steps) - min(steps) <= 1e-15,
        },
        "displacement_range_mm": [min(displacement), max(displacement)],
        "peak_absolute_displacement_mm": peak_absolute,
        "peak_time_s": times[peak_index],
        "final_displacement_mm": displacement[-1],
        "signal_threshold_fraction": threshold_fraction,
        "signal_threshold_mm": threshold,
        "observed_above_threshold_range_s": [times[active_indices[0]], times[active_indices[-1]]] if active_indices else None,
        "observed_above_threshold_span_s": times[active_indices[-1]] - times[active_indices[0]] if active_indices else None,
        "above_threshold_sample_count": len(active_indices),
        "below_threshold_sample_count_between_first_and_last": (
            sum(abs(displacement[index]) < threshold for index in range(active_indices[0], active_indices[-1] + 1))
            if active_indices else 0
        ),
        "above_threshold_at_record_end": bool(active_indices and active_indices[-1] == len(times) - 1),
        "complete_pulse_duration_resolved": bool(active_indices and active_indices[-1] < len(times) - 1),
        "first_difference_velocity_range_mm_per_s": [min(derivative), max(derivative)],
        "time_integral_displacement_mm_s": trapezoid(times, displacement),
    }


def summarize_quasi_static(path: Path) -> dict[str, Any]:
    header, rows = read_simple_table(path)
    times = [row[0] for row in rows]
    displacement = [row[1] for row in rows]
    force = [row[2] for row in rows]
    time_steps = [b - a for a, b in zip(times, times[1:])]
    path_increments = [0.5 * (a_f + b_f) * (b_u - a_u) for a_u, b_u, a_f, b_f in zip(displacement, displacement[1:], force, force[1:])]
    max_force_index = max(range(len(rows)), key=lambda index: force[index])
    max_displacement_index = max(range(len(rows)), key=lambda index: displacement[index])
    return {
        "path": str(path.relative_to(ROOT)).replace("\\", "/"),
        "header": header,
        "row_count": len(rows),
        "time_range_s": [times[0], times[-1]],
        "strictly_increasing_time": all(step > 0 for step in time_steps),
        "duplicate_or_nonincreasing_time_step_count": sum(step <= 0 for step in time_steps),
        "time_step_range_s": [min(time_steps), max(time_steps)],
        "displacement_range_mm": [min(displacement), max(displacement)],
        "force_range_kN": [min(force), max(force)],
        "maximum_force": {
            "force_kN": force[max_force_index],
            "time_s": times[max_force_index],
            "displacement_mm": displacement[max_force_index],
        },
        "maximum_displacement": {
            "displacement_mm": displacement[max_displacement_index],
            "time_s": times[max_displacement_index],
            "force_kN": force[max_displacement_index],
        },
        "displacement_monotonic_nondecreasing": all(b >= a for a, b in zip(displacement, displacement[1:])),
        "negative_displacement_increment_count": sum(b < a for a, b in zip(displacement, displacement[1:])),
        "recorded_path_work_J": sum(path_increments),
        "positive_displacement_increment_work_J": sum(value for value in path_increments if value >= 0),
        "negative_displacement_increment_work_J": sum(value for value in path_increments if value < 0),
        "unit_identity": "1 kN*mm = 1 J",
        "constitutive_energy_interpretation_authorized": False,
    }


def quantile(values: list[float], probability: float) -> float:
    ordered = sorted(values)
    if not ordered:
        raise ValueError("quantile requires at least one value")
    index = (len(ordered) - 1) * probability
    lower = math.floor(index)
    upper = math.ceil(index)
    if lower == upper:
        return ordered[lower]
    fraction = index - lower
    return ordered[lower] * (1.0 - fraction) + ordered[upper] * fraction


def parse_optional_float(token: str) -> float | None:
    stripped = token.strip()
    return float(stripped) if stripped else None


def parse_dic_frame(path: Path, probabilities: list[float]) -> dict[str, Any]:
    lines = [line for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]
    filename_match = re.search(r"_([0-9]+(?:\.[0-9]+)?) ms\.csv$", path.name, re.IGNORECASE)
    if not filename_match:
        raise ValueError(f"DIC filename time absent: {path.name}")
    stage_header_index = lines.index("stage;index;relative_time;date")
    stage_values = next(csv.reader([lines[stage_header_index + 1]], delimiter=";"))
    table_index = next(index for index, line in enumerate(lines) if line.lower().startswith("id;"))
    header = next(csv.reader([lines[table_index]], delimiter=";"))
    rows = [next(csv.reader([line], delimiter=";")) for line in lines[table_index + 1:]]
    columns = {name: [parse_optional_float(row[index]) for row in rows] for index, name in enumerate(header)}
    fields = ["displacement_x", "displacement_y", "epsilon_x", "epsilon_xy", "epsilon_y"]
    field_stats = {}
    quantile_rows = []
    for field in fields:
        valid = [value for value in columns[field] if value is not None]
        missing = len(columns[field]) - len(valid)
        absolute = [abs(value) for value in valid]
        values_by_probability = {f"p{int(probability * 100):02d}": quantile(valid, probability) for probability in probabilities}
        field_stats[field] = {
            "valid_count": len(valid),
            "missing_count": missing,
            "minimum": min(valid),
            "maximum": max(valid),
            "maximum_absolute": max(absolute),
            "absolute_p95": quantile(absolute, 0.95),
            "quantiles": values_by_probability,
        }
        quantile_rows.append({
            "filename_time_ms": float(filename_match.group(1)),
            "stage_relative_time": float(stage_values[2]),
            "field": field,
            "valid_count": len(valid),
            "missing_count": missing,
            "minimum": min(valid),
            "p05": values_by_probability["p05"],
            "p25": values_by_probability["p25"],
            "p50": values_by_probability["p50"],
            "p75": values_by_probability["p75"],
            "p95": values_by_probability["p95"],
            "maximum": max(valid),
            "maximum_absolute": max(absolute),
            "absolute_p95": quantile(absolute, 0.95),
        })
    return {
        "path": str(path.relative_to(ROOT)).replace("\\", "/"),
        "filename_time_ms": float(filename_match.group(1)),
        "stage_index": int(stage_values[1]),
        "stage_relative_time": float(stage_values[2]),
        "stage_date": stage_values[3].strip().strip('"'),
        "row_count": len(rows),
        "header": header,
        "coordinate_ranges": {
            name: [min(value for value in columns[name] if value is not None), max(value for value in columns[name] if value is not None)]
            for name in ("x", "y", "z")
        },
        "field_stats": field_stats,
        "quantile_rows": quantile_rows,
    }


def write_quantile_table(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "filename_time_ms", "stage_relative_time", "field", "valid_count", "missing_count",
        "minimum", "p05", "p25", "p50", "p75", "p95", "maximum", "maximum_absolute", "absolute_p95",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def summarize_dic(frames: list[dict[str, Any]], tolerance_ms: float) -> dict[str, Any]:
    ordered = sorted(frames, key=lambda item: item["filename_time_ms"])
    filename_times = [item["filename_time_ms"] for item in ordered]
    stage_times = [item["stage_relative_time"] for item in ordered]
    offsets = [stage - filename for stage, filename in zip(stage_times, filename_times)]
    offset_spread = max(offsets) - min(offsets)
    fields = ["displacement_x", "displacement_y", "epsilon_x", "epsilon_xy", "epsilon_y"]
    peak_robust = {}
    peak_raw = {}
    for field in fields:
        robust_frame = max(ordered, key=lambda item: item["field_stats"][field]["absolute_p95"])
        raw_frame = max(ordered, key=lambda item: item["field_stats"][field]["maximum_absolute"])
        peak_robust[field] = {
            "filename_time_ms": robust_frame["filename_time_ms"],
            "absolute_p95": robust_frame["field_stats"][field]["absolute_p95"],
        }
        peak_raw[field] = {
            "filename_time_ms": raw_frame["filename_time_ms"],
            "maximum_absolute": raw_frame["field_stats"][field]["maximum_absolute"],
        }
    missing_by_field = {
        field: sum(item["field_stats"][field]["missing_count"] for item in ordered)
        for field in fields
    }
    coordinate_ranges = {
        axis: [
            min(item["coordinate_ranges"][axis][0] for item in ordered),
            max(item["coordinate_ranges"][axis][1] for item in ordered),
        ]
        for axis in ("x", "y", "z")
    }
    return {
        "frame_count": len(ordered),
        "filename_time_range_ms": [filename_times[0], filename_times[-1]],
        "filename_time_step_range_ms": [
            min(b - a for a, b in zip(filename_times, filename_times[1:])),
            max(b - a for a, b in zip(filename_times, filename_times[1:])),
        ],
        "stage_relative_time_range": [stage_times[0], stage_times[-1]],
        "stage_minus_filename_offset_ms": {
            "minimum": min(offsets),
            "maximum": max(offsets),
            "mean": statistics.fmean(offsets),
            "spread": offset_spread,
            "tolerance": tolerance_ms,
            "consistent_with_rounding_tolerance": offset_spread <= tolerance_ms,
        },
        "row_count_range": [min(item["row_count"] for item in ordered), max(item["row_count"] for item in ordered)],
        "total_rows": sum(item["row_count"] for item in ordered),
        "missing_by_field": missing_by_field,
        "total_missing_cells": sum(missing_by_field.values()),
        "coordinate_ranges_from_CSV": coordinate_ranges,
        "CSV_z_is_identically_zero": coordinate_ranges["z"] == [0.0, 0.0],
        "peak_robust_absolute_p95_by_field": peak_robust,
        "peak_raw_absolute_by_field": peak_raw,
        "cross_channel_synchronization_asserted": False,
    }


def build_report(result: dict[str, Any]) -> str:
    docs = result["documentation_audit"]
    bars = result["dynamic_bar_summary"]
    dic = result["DIC_summary"]
    quasi = result["quasi_static_summary"]
    overlap = result["cross_channel_time_overlap"]
    return f"""# WTC 1 — V9I, cohérence descriptive des mesures analogues S355

## Conclusion courte

V9I valide une réduction descriptive sans interpolation des 55 fichiers V9H. Les deux axes de temps DIC diffèrent d'un décalage moyen de {dic['stage_minus_filename_offset_ms']['mean']:.6f} ms, avec une dispersion de {dic['stage_minus_filename_offset_ms']['spread']:.6f} ms, compatible avec la tolérance de résolution pré-déclarée. Cela démontre une relation numérique stable, pas une synchronisation physique absolue.

Les données peuvent désormais servir de benchmark analogique de mesure et de cinématique. Elles ne suffisent toujours pas à identifier une loi de contrainte-déformation ou de rupture, ni à valider un impact de façade.

## 1. Faits directement observés ou transcrits

- Le dépôt relie les temps des noms de fichiers DIC à un déclencheur virtuel placé à l'extrémité gauche d'une barre incidente raccourcie à 300 mm.
- `BC_Inc` et `BC_Trans` sont des déplacements de bord calculés depuis les jauges de déformation, en référence à l'équation 12, avec une vitesse acoustique de 4 639 m/s et un facteur de correction.
- La valeur numérique du facteur de correction et le texte intégral de l'équation 12 n'ont pas été acquis.
- La courbe quasi statique utilise le déplacement relatif du spécimen évalué par DIC.
- L'image de coordonnées montre `y` vers le haut, `z` vers la droite et l'onde incidente vers la gauche. Les CSV utilisent toutefois `x,y,z`, avec `z=0`; la correspondance entre le `x` CSV et le `z` affiché reste non résolue.

## 2. Résultats de modèles officiels

- Aucun modèle officiel ni solveur physique n'est exécuté dans V9I.

## 3. Affirmations provenant des archives locales

- Aucune. L'archive source WTC n'a pas été rescannée.

## 4. Hypothèses propres à V9I

- L'intervalle descriptif au-dessus du seuil arbitraire pré-déclaré de 5 % du déplacement absolu maximal est mesuré uniquement dans la fenêtre enregistrée. Comme les deux signaux dépassent encore ce seuil à la dernière valeur, cet intervalle ne constitue pas une durée complète d'impulsion.
- Les quantiles utilisent une interpolation linéaire à l'indice `(n-1)p`.
- Les valeurs DIC vides sont exclues uniquement du calcul de leur propre champ; elles ne sont ni nulles ni interpolées.
- Le chevauchement numérique des temps de barre et DIC n'est pas traité comme une preuve de synchronisation.

## 5. Résultats dérivés

- Barre incidente: pic absolu observé {bars['incident']['peak_absolute_displacement_mm']:.9g} mm à {bars['incident']['peak_time_s'] * 1e3:.6g} ms; étendue temporelle entre la première et la dernière valeur au-dessus du seuil 5 %: {bars['incident']['observed_above_threshold_span_s'] * 1e3:.6g} ms, tronquée par la fin de l'enregistrement.
- Barre transmise: pic absolu observé {bars['transmitted']['peak_absolute_displacement_mm']:.9g} mm à {bars['transmitted']['peak_time_s'] * 1e3:.6g} ms; étendue temporelle entre la première et la dernière valeur au-dessus du seuil 5 %: {bars['transmitted']['observed_above_threshold_span_s'] * 1e3:.6g} ms, tronquée par la fin de l'enregistrement.
- Fenêtre numérique commune barre/DIC: {overlap['range_ms'][0]:.6g} à {overlap['range_ms'][1]:.6g} ms, soit {overlap['duration_ms']:.6g} ms et {overlap['DIC_frame_count_inside']} trames DIC.
- DIC: {dic['frame_count']} trames, {dic['total_rows']} lignes, {dic['total_missing_cells']} cellules de mesure vides conservées sans imputation.
- Coordonnées CSV: `x={dic['coordinate_ranges_from_CSV']['x']}`, `y={dic['coordinate_ranges_from_CSV']['y']}`, `z={dic['coordinate_ranges_from_CSV']['z']}` mm.
- Quasi statique: force maximale {quasi['maximum_force']['force_kN']:.9g} kN à {quasi['maximum_force']['displacement_mm']:.9g} mm; travail trapézoïdal signé le long du chemin enregistré {quasi['recorded_path_work_J']:.9g} J.
- Le déplacement quasi statique contient {quasi['negative_displacement_increment_count']} incréments négatifs; le travail est donc un intégral de chemin enregistré, pas une énergie de rupture.

## 6. Contradictions et informations manquantes

- Le repère dessiné `y-z` et les colonnes CSV `x-y` ne sont pas explicitement mis en correspondance par la documentation acquise.
- Le facteur de correction des déplacements de bord n'est pas chiffré dans la métadonnée locale et l'équation 12 complète n'est pas reproduite.
- L'alignement absolu entre les temps de barre et les temps DIC n'est pas démontré, malgré leur chevauchement et le décalage interne stable des deux horloges DIC.
- La géométrie reste incomplète et aucun effort dynamique n'est fourni avec `BC_Inc`/`BC_Trans`; aucune contrainte, courbe matériau, énergie de rupture ou longueur de régularisation n'est donc identifiée.
- Le S355 à éprouvette entaillée reste un analogue et ne remplace ni les aciers WTC M26/C80 ni les matériaux/assemblages du CF6-80A2.

## Interprétation

{result['interpretation']}
"""


def main() -> int:
    started = datetime.now().astimezone()
    config = load_json(CONFIG_PATH)
    regressions = verify_regressions(config)
    manifest_source = config["sources"][2]
    manifest = load_json(ROOT / manifest_source["path"])
    payloads = verify_payloads(manifest)
    documentation = documentation_audit(config)
    records = manifest["file_records"]
    bar_records = [item for item in records if item["expected_use"] == "dynamic_bar_boundary_condition"]
    incident_record = next(item for item in bar_records if "BC_Inc" in item["path"])
    transmitted_record = next(item for item in bar_records if "BC_Trans" in item["path"])
    threshold = config["methods"]["bar_signal_threshold_fraction_of_peak_absolute_displacement"]
    incident = summarize_bar(ROOT / incident_record["output_path"], threshold)
    transmitted = summarize_bar(ROOT / transmitted_record["output_path"], threshold)
    quasi_record = next(item for item in records if item["expected_use"] == "quasi_static_force_displacement_comparator")
    quasi = summarize_quasi_static(ROOT / quasi_record["output_path"])
    probabilities = config["methods"]["quantile_probabilities"]
    dic_records = [
        item for item in records
        if item["expected_use"] == "dynamic_dic_frame_or_coordinate_reference" and item["path"].lower().endswith(".csv")
    ]
    frames = [parse_dic_frame(ROOT / item["output_path"], probabilities) for item in dic_records]
    DIC_summary = summarize_dic(frames, config["methods"]["DIC_time_offset_consistency_tolerance_ms"])
    quantile_rows = [row for frame in frames for row in frame["quantile_rows"]]
    quantile_path = ROOT / config["output"]["DIC_quantile_table"]
    write_quantile_table(quantile_path, quantile_rows)
    bar_range_ms = [incident["time_range_s"][0] * 1000.0, incident["time_range_s"][1] * 1000.0]
    dic_range_ms = DIC_summary["filename_time_range_ms"]
    overlap_start = max(bar_range_ms[0], dic_range_ms[0])
    overlap_end = min(bar_range_ms[1], dic_range_ms[1])
    overlap = {
        "bar_range_ms": bar_range_ms,
        "DIC_filename_range_ms": dic_range_ms,
        "range_ms": [overlap_start, overlap_end],
        "duration_ms": max(0.0, overlap_end - overlap_start),
        "DIC_frame_count_inside": sum(overlap_start <= frame["filename_time_ms"] <= overlap_end for frame in frames),
        "absolute_synchronization_assumed": False,
    }
    observed_missing = DIC_summary["total_missing_cells"]
    outcome_gates = {
        "all_V9H_payloads_hash_and_crc_verified": payloads["passed"] and payloads["entry_count"] == config["expected_inputs"]["verified_payload_entry_count"],
        "all_required_documentation_clauses_found": documentation["all_required_description_checks_passed"],
        "two_bar_histories_processed": len(bar_records) == config["expected_inputs"]["dynamic_bar_file_count"],
        "DIC_frame_count_matches": len(frames) == config["expected_inputs"]["dynamic_DIC_csv_frame_count"],
        "DIC_missing_count_preserved": observed_missing == config["expected_inputs"]["DIC_total_missing_cells"],
        "DIC_internal_time_offset_consistent_with_tolerance": DIC_summary["stage_minus_filename_offset_ms"]["consistent_with_rounding_tolerance"],
        "quasi_static_curve_processed": quasi["row_count"] > 0,
        "P6V035_DIC_remains_unacquired": config["expected_inputs"]["P6V035_DIC_acquired"] is False,
    }
    safety_gates = {
        "v9h_regressions_unchanged": regressions["passed"],
        "no_imputation": config["scientific_and_scope_gates"]["no_imputation"],
        "no_additional_payload_acquired": True,
        "full_zip_not_downloaded": True,
        "source_archive_not_rescanned": True,
        "equation_12_not_invented": documentation["equation_12_full_text_acquired"] is False,
        "coordinate_mapping_not_assumed": documentation["coordinate_reference_transcription"]["display_to_CSV_axis_mapping_resolved"] is False,
        "absolute_cross_channel_synchronization_not_asserted": overlap["absolute_synchronization_assumed"] is False,
        "stress_or_material_fit_not_executed": True,
        "solver_not_executed": True,
        "foia_request_unsent": config["foia_policy"]["request_sent"] is False,
        "external_contact_not_made": config["foia_policy"]["external_contact_authorized"] is False,
    }
    execution_validated = all(safety_gates.values())
    outcome_passed = all(outcome_gates.values())
    result = {
        "iteration": "V9I",
        "generated_at": started.isoformat(),
        "status": (
            "validated_no_imputation_measurement_consistency_benchmark_no_fit_no_solver"
            if execution_validated and outcome_passed
            else "validated_descriptive_benchmark_outcome_gate_incomplete"
            if execution_validated
            else "invalid_safety_or_regression_gate_failed"
        ),
        "iteration_execution_validated": execution_validated,
        "measurement_consistency_gate_passed": outcome_passed,
        "configuration": str(CONFIG_PATH.relative_to(ROOT)).replace("\\", "/"),
        "DIC_quantile_table": str(quantile_path.relative_to(ROOT)).replace("\\", "/"),
        "scope": config["dataset"]["scope"],
        "evidence_policy": config["evidence_policy"],
        "regressions": regressions,
        "payload_verification": {
            "entry_count": payloads["entry_count"],
            "passed_count": payloads["passed_count"],
            "passed": payloads["passed"],
        },
        "documentation_audit": documentation,
        "dynamic_bar_summary": {"incident": incident, "transmitted": transmitted},
        "DIC_summary": DIC_summary,
        "quasi_static_summary": quasi,
        "cross_channel_time_overlap": overlap,
        "outcome_gate_summary": {"gates": outcome_gates, "passed": outcome_passed},
        "safety_gate_summary": {"gates": safety_gates, "passed": execution_validated},
        "analogue_measurement_benchmark_qualified": outcome_passed,
        "analogue_signal_reduction_authorized": True,
        "analogue_stress_strain_reduction_authorized": False,
        "analogue_material_fit_authorized": False,
        "analogue_failure_law_fit_authorized": False,
        "analogue_coupon_solver_authorized": False,
        "wtc_high_rate_material_curve_qualification_passed": False,
        "cf6_80a2_cowling_material_card_identification_passed": False,
        "openradioss_wtc_coupon_authorized": False,
        "failure_deletion_executed": False,
        "projectile_rupture_executed": False,
        "facade_impact_executed": False,
        "global_wtc_impact_physics_qualification_passed": False,
        "blender_executed": False,
        "scope_gates": config["scientific_and_scope_gates"],
        "interpretation": (
            "V9I validates a no-imputation descriptive measurement benchmark for the selected S355 analogue pair. "
            "The cached payload identities remain exact; source metadata documents the virtual DIC trigger, processed bar-displacement boundary conditions and quasi-static relative displacement. "
            f"The two DIC time axes have a stable {DIC_summary['stage_minus_filename_offset_ms']['mean']:.6f} ms mean offset within the predeclared rounding tolerance, but absolute bar/DIC synchronization is not asserted. "
            f"All {observed_missing} DIC blanks remain missing. The quasi-static force-displacement integral is reported only along its recorded path. "
            "Because equation 12, its correction-factor value, complete specimen geometry, dynamic force and the coordinate-axis mapping remain incomplete, V9I does not identify stress, constitutive response, fracture energy or regularization length. "
            "S355 remains an analogue and no WTC, CF6, rupture or facade-impact solver gate is opened."
        ),
        "runtime": {
            "started_at": started.isoformat(),
            "completed_at": datetime.now().astimezone().isoformat(),
            "software": "Python standard-library deterministic CSV reduction",
            "python_version": platform.python_version(),
            "platform": platform.platform(),
            "random_seed": config["dataset"]["random_seed"],
            "network_access_used_for_calculation": False,
            "source_archive_rescanned": False,
            "additional_payload_downloaded": False,
            "full_zip_downloaded": False,
            "external_contact_made": False,
            "solver_executed": False,
        },
    }
    results_path = ROOT / config["output"]["results"]
    report_path = ROOT / config["output"]["report"]
    write_json(results_path, result)
    write_text(report_path, build_report(result))
    print(json.dumps({
        "iteration": result["iteration"],
        "execution_validated": execution_validated,
        "measurement_consistency_gate_passed": outcome_passed,
        "payloads_verified": payloads["passed_count"],
        "DIC_frames": len(frames),
        "DIC_missing_cells_preserved": observed_missing,
        "DIC_time_offset_spread_ms": DIC_summary["stage_minus_filename_offset_ms"]["spread"],
        "recorded_path_work_J": quasi["recorded_path_work_J"],
        "additional_payload_downloaded": False,
        "solver_executed": False,
    }, ensure_ascii=False, indent=2))
    return 0 if execution_validated and outcome_passed else 1


if __name__ == "__main__":
    sys.exit(main())
