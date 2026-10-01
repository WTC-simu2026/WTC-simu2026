#!/usr/bin/env python3
"""Retrieve and audit only the exact V9G-predeclared ZIP entries via HTTP Range."""

from __future__ import annotations

import binascii
import csv
import hashlib
import json
import math
import platform
import re
import struct
import sys
import zlib
from collections import Counter
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "wtc1_simulation_v8/data/v9h_selective_payload_ingestion.json"


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
    passed = all(item["passed"] for item in files.values()) and all(item["passed"] for item in metrics)
    return {"files": files, "metrics": metrics, "passed": passed}


def parse_content_range(value: str | None) -> dict[str, int] | None:
    if not value:
        return None
    match = re.fullmatch(r"bytes (\d+)-(\d+)/(\d+)", value.strip())
    if not match:
        return None
    start, end, total = (int(item) for item in match.groups())
    return {"start": start, "end": end, "total": total, "length": end - start + 1}


def bounded_range_get(url: str, start: int, end: int, config: dict[str, Any]) -> dict[str, Any]:
    expected_length = end - start + 1
    request = Request(
        url,
        method="GET",
        headers={
            "Range": f"bytes={start}-{end}",
            "Accept-Encoding": "identity",
            "User-Agent": "WTC1-V9H-exact-selective-payload-ingestion/1.0",
        },
    )
    try:
        response = urlopen(request, timeout=config["range_policy"]["request_timeout_seconds"])
    except HTTPError as exc:
        response = exc
    status = getattr(response, "status", response.getcode())
    content_range = parse_content_range(response.headers.get("Content-Range"))
    info = {
        "requested_start": start,
        "requested_end": end,
        "status_code": status,
        "content_range": content_range,
        "bytes_read": 0,
        "body_read": False,
        "error": None,
        "body": None,
    }
    required_status = config["range_policy"]["required_http_status"]
    required_total = config["range_policy"]["required_content_range_total_bytes"]
    if status != required_status or content_range is None:
        info["error"] = "partial_content_not_honored_body_not_read"
        response.close()
        return info
    if (
        content_range["start"] != start
        or content_range["end"] != end
        or content_range["total"] != required_total
        or content_range["length"] != expected_length
    ):
        info["error"] = "content_range_identity_mismatch_body_not_read"
        response.close()
        return info
    body = bytearray()
    while True:
        chunk = response.read(min(65536, expected_length + 1 - len(body)))
        if not chunk:
            break
        body.extend(chunk)
        if len(body) > expected_length:
            info["error"] = "response_body_exceeded_exact_range"
            response.close()
            return info
    response.close()
    if len(body) != expected_length:
        info["error"] = "response_body_length_mismatch"
        return info
    info["bytes_read"] = len(body)
    info["body_read"] = True
    info["body"] = bytes(body)
    return info


def safe_output_path(payload_root: Path, archive_path: str) -> Path:
    pure = PurePosixPath(archive_path)
    if pure.is_absolute() or not pure.parts or any(part in ("", ".", "..") for part in pure.parts):
        raise ValueError(f"unsafe ZIP entry path: {archive_path!r}")
    candidate = payload_root.joinpath(*pure.parts).resolve()
    root = payload_root.resolve()
    if root not in candidate.parents:
        raise ValueError(f"ZIP entry escapes output root: {archive_path!r}")
    return candidate


def cached_identity(path: Path, entry: dict[str, Any]) -> dict[str, Any]:
    if not path.exists() or not path.is_file():
        return {"usable": False, "reason": "missing"}
    data = path.read_bytes()
    crc = f"{binascii.crc32(data) & 0xFFFFFFFF:08x}"
    return {
        "usable": len(data) == entry["uncompressed_size_bytes"] and crc == entry["crc32_hex"],
        "reason": "size_and_crc_match" if len(data) == entry["uncompressed_size_bytes"] and crc == entry["crc32_hex"] else "size_or_crc_mismatch",
        "size_bytes": len(data),
        "crc32_hex": crc,
    }


def retrieve_entry(entry: dict[str, Any], config: dict[str, Any]) -> tuple[bytes, dict[str, Any]]:
    offset = entry["local_header_offset_bytes"]
    probe_bytes = config["range_policy"]["local_header_probe_bytes_per_entry"]
    probe = bounded_range_get(config["source"]["url"], offset, offset + probe_bytes - 1, config)
    if probe["body"] is None:
        raise RuntimeError(f"local-header range rejected for {entry['path']}: {probe['error']}")
    body = probe["body"]
    if len(body) < 30 or body[:4] != b"PK\x03\x04":
        raise ValueError(f"invalid local ZIP header for {entry['path']}")
    fields = struct.unpack_from("<4s5H3L2H", body, 0)
    _, version_needed, flags, compression, mod_time, mod_date, header_crc, header_compressed, header_uncompressed, name_length, extra_length = fields
    metadata_length = 30 + name_length + extra_length
    if metadata_length > config["range_policy"]["maximum_local_header_probe_bytes_per_entry"]:
        raise ValueError(f"local-header metadata exceeds cap for {entry['path']}")
    if metadata_length > len(body):
        raise ValueError(f"local-header metadata exceeds fixed probe for {entry['path']}")
    encoding = "utf-8" if flags & 0x800 else "cp437"
    local_name = body[30:30 + name_length].decode(encoding, errors="strict")
    if local_name != entry["path"]:
        raise ValueError(f"local/central path mismatch for {entry['path']}")
    if compression != entry["compression_method"] or flags != entry["flags"]:
        raise ValueError(f"local/central compression or flag mismatch for {entry['path']}")
    if not flags & 0x08:
        if header_crc != int(entry["crc32_hex"], 16) or header_compressed != entry["compressed_size_bytes"] or header_uncompressed != entry["uncompressed_size_bytes"]:
            raise ValueError(f"local/central size or CRC mismatch for {entry['path']}")
    data_start = offset + metadata_length
    data_end = data_start + entry["compressed_size_bytes"] - 1
    relative_start = metadata_length
    prefix_payload = body[relative_start:min(len(body), relative_start + entry["compressed_size_bytes"])]
    requests = [probe]
    compressed = bytearray(prefix_payload)
    next_start = data_start + len(prefix_payload)
    if next_start <= data_end:
        remainder = bounded_range_get(config["source"]["url"], next_start, data_end, config)
        requests.append(remainder)
        if remainder["body"] is None:
            raise RuntimeError(f"compressed-data range rejected for {entry['path']}: {remainder['error']}")
        compressed.extend(remainder["body"])
    compressed_bytes = bytes(compressed)
    if len(compressed_bytes) != entry["compressed_size_bytes"]:
        raise ValueError(f"compressed size mismatch for {entry['path']}")
    if compression == 0:
        payload = compressed_bytes
    elif compression == 8:
        payload = zlib.decompress(compressed_bytes, -15)
    else:
        raise ValueError(f"unsupported compression method {compression} for {entry['path']}")
    crc = f"{binascii.crc32(payload) & 0xFFFFFFFF:08x}"
    if len(payload) != entry["uncompressed_size_bytes"] or crc != entry["crc32_hex"]:
        raise ValueError(f"decompressed size or CRC mismatch for {entry['path']}")
    return payload, {
        "source_mode": "http_range",
        "local_header": {
            "version_needed": version_needed,
            "flags": flags,
            "compression_method": compression,
            "modification_time_raw": mod_time,
            "modification_date_raw": mod_date,
            "name_length": name_length,
            "extra_length": extra_length,
            "path_matches": True,
            "central_metadata_matches": True,
        },
        "range_requests": [
            {key: value for key, value in request.items() if key != "body"}
            for request in requests
        ],
        "bytes_transferred": sum(request["bytes_read"] for request in requests),
    }


def decode_text(data: bytes) -> tuple[str | None, str | None]:
    for encoding in ("utf-8-sig", "utf-16", "cp1252"):
        try:
            return data.decode(encoding), encoding
        except (UnicodeDecodeError, UnicodeError):
            continue
    return None, None


def number_value(token: str, delimiter: str) -> float | None:
    value = token.strip().replace("\u2212", "-")
    if not value:
        return None
    if delimiter != "," and value.count(",") == 1 and "." not in value:
        value = value.replace(",", ".")
    try:
        parsed = float(value)
    except ValueError:
        return None
    return parsed if math.isfinite(parsed) else None


def split_row(line: str, delimiter: str) -> list[str]:
    if delimiter == "whitespace":
        return re.split(r"\s+", line.strip())
    return next(csv.reader([line], delimiter=delimiter))


def audit_text_payload(data: bytes) -> dict[str, Any]:
    text, encoding = decode_text(data)
    if text is None:
        return {"text_decoded": False, "encoding": None}
    lines = [line for line in text.splitlines() if line.strip()]
    first = lines[0] if lines else ""
    delimiter_counts = {";": first.count(";"), "\t": first.count("\t"), ",": first.count(",")}
    delimiter = max(delimiter_counts, key=delimiter_counts.get) if delimiter_counts and max(delimiter_counts.values()) else "whitespace"
    rows = [split_row(line, delimiter) for line in lines]
    widths = Counter(len(row) for row in rows)
    first_values = [number_value(token, delimiter) for token in rows[0]] if rows else []
    first_is_header = bool(rows) and any(value is None for value in first_values)
    header = [token.strip() for token in rows[0]] if first_is_header else None
    data_rows = rows[1:] if first_is_header else rows
    maximum_columns = max((len(row) for row in data_rows), default=0)
    numeric_columns = []
    missing_total = 0
    non_numeric_total = 0
    for index in range(maximum_columns):
        values = []
        missing = 0
        non_numeric = 0
        for row in data_rows:
            if index >= len(row) or not row[index].strip():
                missing += 1
                continue
            value = number_value(row[index], delimiter)
            if value is None:
                non_numeric += 1
            else:
                values.append(value)
        missing_total += missing
        non_numeric_total += non_numeric
        numeric_columns.append({
            "index": index,
            "header": header[index] if header and index < len(header) else None,
            "numeric_count": len(values),
            "missing_count": missing,
            "non_numeric_count": non_numeric,
            "minimum": min(values) if values else None,
            "maximum": max(values) if values else None,
            "first": values[0] if values else None,
            "last": values[-1] if values else None,
            "monotonic_nondecreasing": all(b >= a for a, b in zip(values, values[1:])),
            "strictly_increasing": all(b > a for a, b in zip(values, values[1:])),
        })
    unit_tokens = sorted(set(re.findall(r"(?:\bms\b|\bmm\b|\bkn\b|\bmn\b|\bn\b|\bs\b|\bpa\b|\bmpa\b|\bgpa\b|%)", first.lower())))
    return {
        "text_decoded": True,
        "encoding": encoding,
        "nonempty_line_count": len(lines),
        "delimiter": "tab" if delimiter == "\t" else delimiter,
        "column_width_counts": {str(key): value for key, value in sorted(widths.items())},
        "consistent_column_count": len(widths) <= 1,
        "first_row_classified_as_header": first_is_header,
        "header": header,
        "explicit_unit_tokens_in_first_row": unit_tokens,
        "data_row_count": len(data_rows),
        "missing_cell_count": missing_total,
        "non_numeric_data_cell_count": non_numeric_total,
        "numeric_columns": numeric_columns,
        "first_three_nonempty_lines": lines[:3],
    }


def audit_dic_payload(data: bytes) -> dict[str, Any]:
    text, encoding = decode_text(data)
    if text is None:
        return {"text_decoded": False, "encoding": None, "format": "unreadable_DIC_export"}
    lines = [line for line in text.splitlines() if line.strip()]
    data_header_index = next((index for index, line in enumerate(lines) if line.lower().startswith("id;")), None)
    if data_header_index is None:
        return {"text_decoded": True, "encoding": encoding, "format": "unrecognized_DIC_export", "consistent_column_count": False}
    table = "\n".join(lines[data_header_index:]).encode("utf-8")
    audit = audit_text_payload(table)
    units: dict[str, str] = {}
    units_line = next((line for line in lines[:data_header_index] if line.lower().startswith("# units:")), None)
    if units_line:
        units = {
            key.lower(): value.lower()
            for key, value in re.findall(r"([A-Za-z_]+):([^\s]+)", units_line.partition(":")[2])
        }
    stage_labels_index = next((index for index, line in enumerate(lines[:data_header_index]) if line.lower() == "stage;index;relative_time;date"), None)
    stage: dict[str, Any] = {}
    if stage_labels_index is not None and stage_labels_index + 1 < len(lines):
        labels = split_row(lines[stage_labels_index], ";")
        values = split_row(lines[stage_labels_index + 1], ";")
        stage = {key: value.strip().strip('"') for key, value in zip(labels, values)}
        if "index" in stage:
            try:
                stage["index"] = int(stage["index"])
            except ValueError:
                pass
        if "relative_time" in stage:
            try:
                stage["relative_time"] = float(stage["relative_time"])
            except ValueError:
                pass
    name_line = next((line for line in lines[:data_header_index] if line.lower().startswith("# name")), None)
    audit.update({
        "format": "GOM_ARAMIS_multisection_DIC_export",
        "encoding": encoding,
        "declared_units": units,
        "stage_metadata": stage,
        "field_name": name_line.partition(":")[2].strip() if name_line else None,
        "metadata_line_count_before_data_table": data_header_index,
    })
    return audit


def jpeg_dimensions(data: bytes) -> dict[str, Any]:
    if len(data) < 4 or data[:2] != b"\xff\xd8":
        return {"jpeg_signature_valid": False, "width_px": None, "height_px": None}
    position = 2
    sof_markers = set(range(0xC0, 0xC4)) | set(range(0xC5, 0xC8)) | set(range(0xC9, 0xCC)) | set(range(0xCD, 0xD0))
    while position + 4 <= len(data):
        if data[position] != 0xFF:
            position += 1
            continue
        marker = data[position + 1]
        position += 2
        if marker in (0xD8, 0xD9) or 0xD0 <= marker <= 0xD7:
            continue
        if position + 2 > len(data):
            break
        length = struct.unpack_from(">H", data, position)[0]
        if marker in sof_markers and position + 7 <= len(data):
            height, width = struct.unpack_from(">HH", data, position + 3)
            return {"jpeg_signature_valid": True, "width_px": width, "height_px": height, "sof_marker_hex": f"ff{marker:02x}"}
        position += length
    return {"jpeg_signature_valid": True, "width_px": None, "height_px": None}


def aggregate_audit(files: list[dict[str, Any]]) -> dict[str, Any]:
    p4_dic_csv = [item for item in files if item["specimen"] == "P4V035" and item["path"].lower().endswith(".csv") and "/dic/" in item["path"].lower()]
    times = []
    for item in p4_dic_csv:
        match = re.search(r"_([0-9]+(?:\.[0-9]+)?) ms\.csv$", item["path"], re.IGNORECASE)
        if match:
            times.append(float(match.group(1)))
    times.sort()
    intervals = [b - a for a, b in zip(times, times[1:])]
    stage_times = sorted(
        item["text_audit"].get("stage_metadata", {}).get("relative_time")
        for item in p4_dic_csv
        if isinstance(item["text_audit"].get("stage_metadata", {}).get("relative_time"), (int, float))
    )
    stage_intervals = [b - a for a, b in zip(stage_times, stage_times[1:])]
    dic_column_missing: Counter[str] = Counter()
    dic_column_numeric: Counter[str] = Counter()
    for item in p4_dic_csv:
        for column in item["text_audit"].get("numeric_columns", []):
            name = column.get("header") or f"column_{column['index']}"
            dic_column_missing[name] += column["missing_count"]
            dic_column_numeric[name] += column["numeric_count"]
    text_files = [item for item in files if "text_audit" in item]
    return {
        "source_modes": dict(Counter(item["source_mode"] for item in files)),
        "dynamic_bar_files": [
            {
                "path": item["path"],
                "header": item["text_audit"].get("header"),
                "unit_tokens": item["text_audit"].get("explicit_unit_tokens_in_first_row"),
                "data_row_count": item["text_audit"].get("data_row_count"),
                "consistent_column_count": item["text_audit"].get("consistent_column_count"),
                "numeric_columns": item["text_audit"].get("numeric_columns"),
            }
            for item in files if item["expected_use"] == "dynamic_bar_boundary_condition"
        ],
        "dynamic_dic": {
            "csv_frame_count": len(p4_dic_csv),
            "filename_time_unit": "ms" if times else None,
            "first_time_ms": min(times) if times else None,
            "last_time_ms": max(times) if times else None,
            "strictly_increasing_unique_times": len(times) == len(set(times)) and all(value > 0 for value in intervals),
            "minimum_interval_ms": min(intervals) if intervals else None,
            "maximum_interval_ms": max(intervals) if intervals else None,
            "declared_unit_maps": sorted({json.dumps(item["text_audit"].get("declared_units"), sort_keys=True) for item in p4_dic_csv}),
            "stage_relative_time_range": [min(stage_times), max(stage_times)] if stage_times else None,
            "stage_relative_time_strictly_increasing": len(stage_times) == len(set(stage_times)) and all(value > 0 for value in stage_intervals),
            "unique_headers": sorted({json.dumps(item["text_audit"].get("header"), ensure_ascii=False) for item in p4_dic_csv}),
            "data_row_count_range": [
                min((item["text_audit"].get("data_row_count", 0) for item in p4_dic_csv), default=0),
                max((item["text_audit"].get("data_row_count", 0) for item in p4_dic_csv), default=0),
            ],
            "total_missing_cells": sum(item["text_audit"].get("missing_cell_count", 0) for item in p4_dic_csv),
            "missing_by_column": {
                name: {
                    "missing_count": dic_column_missing[name],
                    "numeric_count": dic_column_numeric[name],
                    "missing_fraction": dic_column_missing[name] / (dic_column_missing[name] + dic_column_numeric[name]),
                }
                for name in sorted(dic_column_missing)
            },
            "coordinate_reference_images": [
                {"path": item["path"], **item["image_audit"]}
                for item in files if "image_audit" in item
            ],
        },
        "quasi_static_force_displacement": [
            {
                "path": item["path"],
                "header": item["text_audit"].get("header"),
                "unit_tokens": item["text_audit"].get("explicit_unit_tokens_in_first_row"),
                "data_row_count": item["text_audit"].get("data_row_count"),
                "numeric_columns": item["text_audit"].get("numeric_columns"),
                "consistent_column_count": item["text_audit"].get("consistent_column_count"),
            }
            for item in files if item["expected_use"] == "quasi_static_force_displacement_comparator"
        ],
        "all_text_files_decoded": all(item["text_audit"].get("text_decoded") for item in text_files),
        "all_text_files_consistent_column_count": all(item["text_audit"].get("consistent_column_count") for item in text_files),
        "total_missing_cells": sum(item["text_audit"].get("missing_cell_count", 0) for item in text_files),
        "total_non_numeric_data_cells": sum(item["text_audit"].get("non_numeric_data_cell_count", 0) for item in text_files),
    }


def build_report(result: dict[str, Any]) -> str:
    audit = result["payload_audit_summary"]
    retrieval = result["retrieval_summary"]
    dic = audit["dynamic_dic"]
    quasi = audit["quasi_static_force_displacement"]
    quasi_header = quasi[0]["header"] if quasi else None
    bar_headers = [item["header"] for item in audit["dynamic_bar_files"]]
    return f"""# WTC 1 — V9H, ingestion sélective des signaux analogues S355

## Conclusion courte

V9H a vérifié et conservé {retrieval['verified_entry_count']} fichiers pré-déclarés, pour {retrieval['verified_uncompressed_size_bytes']} octets décompressés. Le ZIP complet n'a pas été téléchargé. Le serveur a transféré {retrieval['network_bytes_transferred']} octets par lectures partielles lors de cette exécution; {retrieval['cache_verified_entry_count']} fichier(s) provenaient d'un cache local vérifié.

Le reçu durable de l'acquisition distante initiale conserve {retrieval['initial_acquisition_network_bytes']} octets transférés et les plages HTTP exactes.

Cette étape qualifie l'identité et le format des petits fichiers analogues. Elle ne constitue ni un ajustement de loi matériau, ni une validation de rupture, ni une simulation d'impact de façade.

## 1. Faits directement observés ou transcrits

- Fichiers attendus/vérifiés: {retrieval['expected_entry_count']} / {retrieval['verified_entry_count']}.
- Taille compressée annoncée des entrées: {retrieval['verified_compressed_size_bytes']} octets.
- Taille décompressée vérifiée: {retrieval['verified_uncompressed_size_bytes']} octets.
- CRC32, taille et chemin ZIP conformes pour chaque fichier: {retrieval['all_entry_identity_checks_passed']}.
- En-têtes des deux fichiers de barre P4V035: `{bar_headers}`.
- Série DIC dynamique: {dic['csv_frame_count']} trames CSV nommées de {dic['first_time_ms']} à {dic['last_time_ms']} ms; pas nominal observé entre {dic['minimum_interval_ms']:.6g} et {dic['maximum_interval_ms']:.6g} ms.
- Unités explicitement déclarées dans chaque export DIC: `{dic['declared_unit_maps']}`.
- Temps relatif interne des étapes DIC: `{dic['stage_relative_time_range']}`; il s'agit d'un second repère à documenter avant toute synchronisation avec les signaux de barre.
- En-tête de la courbe quasi statique P6V035: `{quasi_header}`.
- Cellules manquantes détectées dans les tableaux texte: {audit['total_missing_cells']}.
- Répartition des valeurs DIC absentes par colonne: `{dic['missing_by_column']}`. Les identifiants et coordonnées restent complets; les cinq champs de déplacement/déformation présentent chacun 1 414 valeurs vides.
- Cellules non numériques dans les lignes de données: {audit['total_non_numeric_data_cells']}.

## 2. Résultats de modèles officiels

- Aucun modèle officiel ou calcul physique n'est exécuté dans V9H.

## 3. Affirmations provenant des archives locales

- Aucune. L'archive source WTC n'a pas été rescannée.

## 4. Hypothèses propres à V9H

- P4V035 et P6V035 sont traités comme un couple analogue de même catégorie géométrique d'après le classeur V9F; cela ne les transforme pas en matériau WTC ou CF6.
- Le séparateur, la ligne d'en-tête et les colonnes numériques sont détectés par des règles déterministes et restent à confronter à la documentation expérimentale.

## 5. Résultats dérivés

- Les temps DIC tirés des noms sont strictement croissants et uniques: {dic['strictly_increasing_unique_times']}.
- Tous les fichiers texte sont décodables: {audit['all_text_files_decoded']}.
- Tous les tableaux texte gardent un nombre de colonnes constant: {audit['all_text_files_consistent_column_count']}.
- La série DIC quasi statique P6V035 reste différée: {result['deferred_P6V035_DIC']['file_count']} fichiers, {result['deferred_P6V035_DIC']['compressed_size_bytes']} octets compressés.

## 6. Contradictions et informations manquantes

- Les libellés présents dans les fichiers doivent être interprétés avec la documentation du dépôt; une unité absente ne sera pas inventée.
- La petite figure géométrique ne fournit toujours pas toutes les dimensions, tolérances et rayons nécessaires à un maillage constitutif fidèle.
- Les données S355 concernent un essai analogue en cisaillement localisé et ne déterminent ni la loi de rupture des aciers WTC M26/C80, ni les matériaux et assemblages du CF6-80A2.
- Aucun ajustement de loi, régularisation de rupture, coupon OpenRadioss, projectile ou impact de façade n'est autorisé par V9H.

## Interprétation

{result['interpretation']}
"""


def main() -> int:
    started = datetime.now().astimezone()
    config = load_json(CONFIG_PATH)
    regressions = verify_regressions(config)
    selection_path = ROOT / config["selection"]["manifest"]
    selection_hash_matches = digest(selection_path) == config["selection"]["manifest_sha256"]
    selection = load_json(selection_path)
    entries = selection["selected_entries"]
    specimen_counts = Counter(item["specimen"] for item in entries)
    use_counts = Counter(item["expected_use"] for item in entries)
    selection_gates = {
        "manifest_hash_matches": selection_hash_matches,
        "entry_count_matches": len(entries) == config["selection"]["expected_entry_count"],
        "compressed_sum_matches": sum(item["compressed_size_bytes"] for item in entries) == config["selection"]["expected_compressed_size_bytes"],
        "uncompressed_sum_matches": sum(item["uncompressed_size_bytes"] for item in entries) == config["selection"]["expected_uncompressed_size_bytes"],
        "specimen_counts_match": dict(specimen_counts) == config["selection"]["required_specimen_counts"],
        "use_counts_match": dict(use_counts) == config["selection"]["required_use_counts"],
        "paths_unique": len({item["path"] for item in entries}) == len(entries),
    }
    payload_root = ROOT / config["output"]["payload_root"]
    receipt_path = ROOT / config["output"]["remote_acquisition_receipt"]
    existing_receipt = load_json(receipt_path) if receipt_path.exists() else None
    require_remote_receipt = existing_receipt is None
    full_zip_path = ROOT / config["source"]["full_zip_local_path_prohibited"]
    file_records: list[dict[str, Any]] = []
    total_transferred = 0
    error: str | None = None
    if regressions["passed"] and all(selection_gates.values()) and not full_zip_path.exists():
        for entry in entries:
            try:
                output_path = safe_output_path(payload_root, entry["path"])
                cache = cached_identity(output_path, entry)
                if cache["usable"] and not require_remote_receipt:
                    payload = output_path.read_bytes()
                    retrieval = {"source_mode": "verified_local_cache", "bytes_transferred": 0, "range_requests": []}
                else:
                    payload, retrieval = retrieve_entry(entry, config)
                    total_transferred += retrieval["bytes_transferred"]
                    if total_transferred > config["range_policy"]["maximum_total_transferred_bytes"]:
                        raise RuntimeError("total HTTP-range transfer exceeded the predeclared ceiling")
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    output_path.write_bytes(payload)
                record = {
                    **entry,
                    "output_path": str(output_path.relative_to(ROOT)).replace("\\", "/"),
                    "source_mode": retrieval["source_mode"],
                    "bytes_transferred": retrieval["bytes_transferred"],
                    "range_requests": retrieval["range_requests"],
                    "verified_uncompressed_size_bytes": len(payload),
                    "verified_crc32_hex": f"{binascii.crc32(payload) & 0xFFFFFFFF:08x}",
                    "sha256": hashlib.sha256(payload).hexdigest(),
                    "identity_passed": len(payload) == entry["uncompressed_size_bytes"] and f"{binascii.crc32(payload) & 0xFFFFFFFF:08x}" == entry["crc32_hex"],
                }
                suffix = PurePosixPath(entry["path"]).suffix.lower()
                if suffix == ".csv" and "/dic/" in entry["path"].lower():
                    record["text_audit"] = audit_dic_payload(payload)
                elif suffix in (".csv", ".txt"):
                    record["text_audit"] = audit_text_payload(payload)
                elif suffix in (".jpg", ".jpeg"):
                    record["image_audit"] = jpeg_dimensions(payload)
                file_records.append(record)
            except Exception as exc:
                error = f"{type(exc).__name__}: {exc}"
                break
    elif not regressions["passed"]:
        error = "V9G regression gate failed"
    elif not all(selection_gates.values()):
        error = "selection identity gate failed"
    else:
        error = "prohibited full ZIP path exists"

    payload_audit = aggregate_audit(file_records)
    all_identity = len(file_records) == len(entries) and all(item["identity_passed"] for item in file_records)
    if total_transferred and all_identity:
        existing_receipt = {
            "iteration": "V9H",
            "created_at": datetime.now().astimezone().isoformat(),
            "source_url": config["source"]["url"],
            "declared_zip_size_bytes": config["source"]["declared_zip_size_bytes"],
            "selection_manifest": config["selection"]["manifest"],
            "selection_manifest_sha256": config["selection"]["manifest_sha256"],
            "entry_count": len(file_records),
            "network_bytes_transferred": total_transferred,
            "required_http_status": config["range_policy"]["required_http_status"],
            "full_zip_downloaded": False,
            "entries": [
                {
                    "path": item["path"],
                    "sha256": item["sha256"],
                    "crc32_hex": item["verified_crc32_hex"],
                    "uncompressed_size_bytes": item["verified_uncompressed_size_bytes"],
                    "range_requests": item["range_requests"],
                }
                for item in file_records
            ],
        }
        write_json(receipt_path, existing_receipt)
    receipt_valid = bool(existing_receipt) and existing_receipt.get("selection_manifest_sha256") == config["selection"]["manifest_sha256"] and existing_receipt.get("entry_count") == len(entries)
    safety_gates = {
        "v9g_regressions_unchanged": regressions["passed"],
        "selection_predeclaration_matches": all(selection_gates.values()),
        "total_transfer_under_cap": total_transferred <= config["range_policy"]["maximum_total_transferred_bytes"],
        "full_zip_not_present": not full_zip_path.exists(),
        "only_predeclared_paths_written": {item["path"] for item in file_records}.issubset({item["path"] for item in entries}),
        "P6V035_DIC_not_acquired": not any("/DIC/P6V035/" in item["path"] for item in file_records),
        "source_archive_not_rescanned": True,
        "foia_request_unsent": config["foia_policy"]["request_sent"] is False,
        "external_contact_not_made": config["foia_policy"]["external_contact_authorized"] is False,
        "material_fit_not_executed": True,
        "solver_not_executed": True,
        "durable_remote_acquisition_receipt_valid": receipt_valid,
    }
    outcome_gates = {
        "all_55_entries_verified": all_identity,
        "all_text_payloads_decoded": payload_audit["all_text_files_decoded"],
        "P4V035_DIC_filename_times_unique_and_increasing": payload_audit["dynamic_dic"]["strictly_increasing_unique_times"],
        "two_dynamic_bar_files_present": len(payload_audit["dynamic_bar_files"]) == 2,
        "one_quasi_static_force_displacement_file_present": len(payload_audit["quasi_static_force_displacement"]) == 1,
    }
    execution_validated = all(safety_gates.values())
    outcome_passed = all(outcome_gates.values())
    retrieval_summary = {
        "expected_entry_count": len(entries),
        "verified_entry_count": len(file_records),
        "network_retrieved_entry_count": sum(item["source_mode"] == "http_range" for item in file_records),
        "cache_verified_entry_count": sum(item["source_mode"] == "verified_local_cache" for item in file_records),
        "network_bytes_transferred": total_transferred,
        "initial_acquisition_network_bytes": existing_receipt.get("network_bytes_transferred", 0) if existing_receipt else 0,
        "remote_acquisition_receipt": str(receipt_path.relative_to(ROOT)).replace("\\", "/") if existing_receipt else None,
        "maximum_network_bytes": config["range_policy"]["maximum_total_transferred_bytes"],
        "verified_compressed_size_bytes": sum(item["compressed_size_bytes"] for item in file_records),
        "verified_uncompressed_size_bytes": sum(item["verified_uncompressed_size_bytes"] for item in file_records),
        "all_entry_identity_checks_passed": all_identity,
        "error": error,
    }
    manifest = {
        "iteration": "V9H",
        "generated_at": started.isoformat(),
        "configuration": str(CONFIG_PATH.relative_to(ROOT)).replace("\\", "/"),
        "selection_manifest": config["selection"]["manifest"],
        "selection_gates": selection_gates,
        "retrieval_summary": retrieval_summary,
        "file_records": file_records,
        "payload_audit_summary": payload_audit,
        "safety_gates": safety_gates,
        "outcome_gates": outcome_gates,
    }
    manifest_path = ROOT / config["output"]["ingestion_manifest"]
    results_path = ROOT / config["output"]["results"]
    report_path = ROOT / config["output"]["report"]
    write_json(manifest_path, manifest)
    result = {
        "iteration": "V9H",
        "generated_at": started.isoformat(),
        "status": (
            "validated_exact_selective_payloads_format_audited_no_fit_no_solver"
            if execution_validated and outcome_passed
            else "validated_safe_stop_payload_outcome_incomplete"
            if execution_validated
            else "invalid_safety_or_regression_gate_failed"
        ),
        "iteration_execution_validated": execution_validated,
        "selective_payload_gate_passed": outcome_passed,
        "configuration": str(CONFIG_PATH.relative_to(ROOT)).replace("\\", "/"),
        "ingestion_manifest": str(manifest_path.relative_to(ROOT)).replace("\\", "/"),
        "scope": config["dataset"]["scope"],
        "evidence_policy": config["evidence_policy"],
        "regressions": regressions,
        "selection_gates": selection_gates,
        "retrieval_summary": retrieval_summary,
        "payload_audit_summary": payload_audit,
        "safety_gate_summary": {"gates": safety_gates, "passed": execution_validated},
        "outcome_gate_summary": {"gates": outcome_gates, "passed": outcome_passed},
        "deferred_P6V035_DIC": {
            "file_count": config["selection"]["deferred_P6V035_DIC_file_count"],
            "compressed_size_bytes": config["selection"]["deferred_P6V035_DIC_compressed_size_bytes"],
            "acquired": False,
        },
        "full_zip_downloaded": False,
        "local_full_zip_needed": False if execution_validated and outcome_passed else True,
        "analogue_signal_format_audit_passed": outcome_passed,
        "analogue_signal_reduction_authorized": False,
        "analogue_material_fit_authorized": False,
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
            "V9H validates exact bounded ingestion and structural format auditing of the selected open S355 analogue payloads. "
            f"All {len(file_records)} acquired or cache-verified entries match their central-directory paths, uncompressed sizes and CRC32 values. "
            f"The dynamic DIC filenames expose {payload_audit['dynamic_dic']['csv_frame_count']} ordered time points and the two bar files plus one quasi-static force-displacement comparator are present. "
            "This establishes traceable input identity and machine readability only. Units and sign conventions must be taken from explicit headers or repository documentation; no absent definition is inferred. "
            "The S355 notched shear data cannot identify WTC M26/C80 tensile fracture or production CF6-80A2 materials. No material fit, regularized failure law, solver, rupture or facade impact is authorized."
        ),
        "runtime": {
            "started_at": started.isoformat(),
            "completed_at": datetime.now().astimezone().isoformat(),
            "software": "Python standard-library bounded HTTP Range client, raw-deflate decoder and deterministic text/JPEG auditor",
            "python_version": platform.python_version(),
            "platform": platform.platform(),
            "random_seed": config["dataset"]["random_seed"],
            "source_archive_rescanned": False,
            "full_zip_downloaded": False,
            "P6V035_DIC_downloaded": False,
            "external_contact_made": False,
            "solver_executed": False,
        },
    }
    write_json(results_path, result)
    write_text(report_path, build_report(result))
    print(json.dumps({
        "iteration": result["iteration"],
        "execution_validated": execution_validated,
        "selective_payload_gate_passed": outcome_passed,
        "verified_entries": len(file_records),
        "network_bytes_transferred": total_transferred,
        "full_zip_downloaded": False,
        "P6V035_DIC_downloaded": False,
        "local_full_zip_needed": result["local_full_zip_needed"],
        "error": error,
    }, ensure_ascii=False, indent=2))
    return 0 if execution_validated and outcome_passed else 1


if __name__ == "__main__":
    sys.exit(main())
