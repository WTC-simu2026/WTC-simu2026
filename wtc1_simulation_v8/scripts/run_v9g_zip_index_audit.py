#!/usr/bin/env python3
"""Audit a remote ZIP central directory with bounded HTTP Range reads only."""

from __future__ import annotations

import hashlib
import json
import platform
import re
import struct
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import urlsplit, urlunsplit
from urllib.error import HTTPError
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "wtc1_simulation_v8/data/v9g_selective_zip_index.json"
FIGURE_PATH = ROOT / "wtc1_simulation_v8/input/v9g_open_sources/Fig1.jpg"
MANIFEST_PATH = ROOT / "wtc1_simulation_v8/output/v9g_zip_central_directory_manifest.json"
CANDIDATES_PATH = ROOT / "wtc1_simulation_v8/output/v9g_selective_payload_candidates.json"
RESULTS_PATH = ROOT / "wtc1_simulation_v8/output/resultats_wtc1_v9g_index_zip_selectif.json"
REPORT_PATH = ROOT / "wtc1_simulation_v8/output/rapport_wtc1_v9g_index_zip_selectif.md"


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
    file_results: dict[str, Any] = {}
    for relative, expected in config["regressions"]["required_files"].items():
        path = ROOT / relative
        actual = digest(path) if path.exists() else None
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


def sanitized_url(url: str) -> str:
    parsed = urlsplit(url)
    return urlunsplit((parsed.scheme, parsed.netloc, parsed.path, "", ""))


def selected_headers(headers: Any) -> dict[str, Any]:
    names = ["Accept-Ranges", "Content-Length", "Content-Range", "Content-Type", "ETag", "Last-Modified"]
    return {name.lower().replace("-", "_"): headers.get(name) for name in names}


def parse_content_range(value: str | None) -> dict[str, int] | None:
    if not value:
        return None
    match = re.fullmatch(r"bytes (\d+)-(\d+)/(\d+)", value.strip())
    if not match:
        return None
    start, end, total = (int(item) for item in match.groups())
    return {"start": start, "end": end, "total": total, "length": end - start + 1}


def bounded_range_get(
    url: str,
    range_header: str,
    maximum_body_bytes: int,
    timeout_seconds: int,
) -> dict[str, Any]:
    request = Request(
        url,
        method="GET",
        headers={
            "Range": range_header,
            "Accept-Encoding": "identity",
            "User-Agent": "WTC1-V9G-bounded-zip-index-audit/1.0",
        },
    )
    try:
        response = urlopen(request, timeout=timeout_seconds)
    except HTTPError as exc:
        response = exc
    status_code = getattr(response, "status", response.getcode())
    info: dict[str, Any] = {
        "requested_range": range_header,
        "status_code": status_code,
        "final_url": sanitized_url(response.geturl()),
        "headers": selected_headers(response.headers),
        "content_range": parse_content_range(response.headers.get("Content-Range")),
        "body_read": False,
        "bytes_read": 0,
        "body_sha256": None,
        "error": None,
        "body": None,
    }
    if status_code != 206 or info["content_range"] is None:
        info["error"] = "partial_content_not_honored_body_not_read"
        response.close()
        return info
    advertised = info["content_range"]["length"]
    if advertised > maximum_body_bytes:
        info["error"] = "advertised_range_exceeds_predeclared_cap_body_not_read"
        response.close()
        return info

    body = bytearray()
    while True:
        chunk = response.read(65536)
        if not chunk:
            break
        body.extend(chunk)
        if len(body) > maximum_body_bytes:
            info["error"] = "stream_exceeded_predeclared_cap"
            response.close()
            return info
    response.close()
    if len(body) != advertised:
        info["error"] = "received_length_does_not_match_content_range"
        return info
    info["body_read"] = True
    info["bytes_read"] = len(body)
    info["body_sha256"] = hashlib.sha256(body).hexdigest()
    info["body"] = bytes(body)
    return info


def parse_eocd(suffix: bytes) -> dict[str, int] | None:
    signature = b"PK\x05\x06"
    position = suffix.rfind(signature)
    if position < 0 or position + 22 > len(suffix):
        return None
    fields = struct.unpack_from("<4s4H2LH", suffix, position)
    _, disk_number, central_directory_disk, entries_on_disk, total_entries, directory_size, directory_offset, comment_length = fields
    if position + 22 + comment_length > len(suffix):
        return None
    return {
        "position_in_suffix": position,
        "disk_number": disk_number,
        "central_directory_disk": central_directory_disk,
        "entries_on_disk": entries_on_disk,
        "total_entries": total_entries,
        "central_directory_size_bytes": directory_size,
        "central_directory_offset_bytes": directory_offset,
        "comment_length_bytes": comment_length,
    }


def classify_channel(path: str) -> list[str]:
    lowered = path.lower()
    families = []
    if "/dic/" in lowered or lowered.startswith("dic/"):
        families.append("DIC")
    if "fu_curves" in lowered or "f(u)" in lowered:
        families.append("force_displacement")
    if "bardispl" in lowered or "barstrain" in lowered or "bar_strain" in lowered or "bc_inc" in lowered or "bc_trans" in lowered:
        families.append("bar_strain_or_bar_displacement_boundary_condition")
    if "microhardness" in lowered:
        families.append("microhardness")
    if "ebsd" in lowered:
        families.append("EBSD")
    return families or ["unclassified"]


def parse_central_directory(data: bytes, expected_entries: int, target_tokens: list[str]) -> dict[str, Any]:
    position = 0
    entries: list[dict[str, Any]] = []
    extension_counts: Counter[str] = Counter()
    top_level_counts: Counter[str] = Counter()
    target_patterns = {
        token: re.compile(rf"(?<![A-Z0-9]){re.escape(token.upper())}(?![A-Z0-9])")
        for token in target_tokens
    }
    target_matches: dict[str, list[dict[str, Any]]] = {token: [] for token in target_tokens}

    while position < len(data):
        if position + 46 > len(data) or data[position:position + 4] != b"PK\x01\x02":
            raise ValueError(f"invalid central-directory signature at byte {position}")
        fields = struct.unpack_from("<4s6H3L5H2L", data, position)
        (
            _, version_made, version_needed, flags, compression, mod_time, mod_date,
            crc32, compressed_size, uncompressed_size, name_length, extra_length,
            comment_length, disk_start, internal_attributes, external_attributes,
            local_header_offset,
        ) = fields
        name_start = position + 46
        name_end = name_start + name_length
        extra_end = name_end + extra_length
        comment_end = extra_end + comment_length
        if comment_end > len(data):
            raise ValueError("central-directory entry extends beyond acquired bytes")
        encoding = "utf-8" if flags & 0x800 else "cp437"
        name = data[name_start:name_end].decode(encoding, errors="replace")
        is_directory = name.endswith("/")
        path = PurePosixPath(name)
        suffix = path.suffix.lower() or "[no_extension]"
        first_component = path.parts[0] if path.parts else "[root]"
        if not is_directory:
            extension_counts[suffix] += 1
            top_level_counts[first_component] += 1
        entry = {
            "path": name,
            "is_directory": is_directory,
            "compressed_size_bytes": compressed_size,
            "uncompressed_size_bytes": uncompressed_size,
            "crc32_hex": f"{crc32:08x}",
            "compression_method": compression,
            "flags": flags,
            "local_header_offset_bytes": local_header_offset,
            "disk_start": disk_start,
            "version_needed": version_needed,
            "version_made": version_made,
            "internal_attributes": internal_attributes,
            "external_attributes": external_attributes,
            "channel_family_guess": classify_channel(name),
        }
        entries.append(entry)
        if not is_directory:
            upper = name.upper()
            for token, pattern in target_patterns.items():
                if pattern.search(upper):
                    target_matches[token].append(entry)
        position = comment_end

    if position != len(data):
        raise ValueError("central-directory parse did not consume the acquired range")
    file_entries = [item for item in entries if not item["is_directory"]]
    return {
        "parsed_entry_count": len(entries),
        "expected_entry_count": expected_entries,
        "entry_count_matches_end_record": len(entries) == expected_entries,
        "file_entry_count": len(file_entries),
        "directory_entry_count": len(entries) - len(file_entries),
        "sum_compressed_file_bytes": sum(item["compressed_size_bytes"] for item in file_entries),
        "sum_uncompressed_file_bytes": sum(item["uncompressed_size_bytes"] for item in file_entries),
        "extension_counts": dict(sorted(extension_counts.items())),
        "top_level_file_counts": dict(sorted(top_level_counts.items())),
        "target_matches": target_matches,
        "target_match_counts": {token: len(matches) for token, matches in target_matches.items()},
    }


def compact_entry(entry: dict[str, Any]) -> dict[str, Any]:
    return {
        key: entry[key]
        for key in (
            "path",
            "compressed_size_bytes",
            "uncompressed_size_bytes",
            "crc32_hex",
            "compression_method",
            "flags",
            "local_header_offset_bytes",
            "channel_family_guess",
        )
    }


def compact_central_summary(summary: dict[str, Any]) -> dict[str, Any]:
    targets: dict[str, Any] = {}
    for token, entries in summary.get("target_matches", {}).items():
        ordered = sorted(entries, key=lambda item: item["local_header_offset_bytes"])
        family_stats: dict[str, Any] = {}
        for family in sorted({family for item in ordered for family in item["channel_family_guess"]}):
            members = [item for item in ordered if family in item["channel_family_guess"]]
            family_stats[family] = {
                "file_count": len(members),
                "compressed_size_bytes": sum(item["compressed_size_bytes"] for item in members),
                "uncompressed_size_bytes": sum(item["uncompressed_size_bytes"] for item in members),
            }
        mechanical = [
            compact_entry(item)
            for item in ordered
            if any(
                family in item["channel_family_guess"]
                for family in ("force_displacement", "bar_strain_or_bar_displacement_boundary_condition")
            )
        ]
        dic_entries = [item for item in ordered if "DIC" in item["channel_family_guess"]]
        dic_auxiliary = [
            compact_entry(item)
            for item in dic_entries
            if PurePosixPath(item["path"]).suffix.lower() != ".csv"
        ]
        targets[token] = {
            "target_match_count": len(ordered),
            "compressed_size_bytes": sum(item["compressed_size_bytes"] for item in ordered),
            "uncompressed_size_bytes": sum(item["uncompressed_size_bytes"] for item in ordered),
            "family_stats": family_stats,
            "exact_mechanical_entries": mechanical,
            "dic_summary": {
                "file_count": len(dic_entries),
                "compressed_size_bytes": sum(item["compressed_size_bytes"] for item in dic_entries),
                "uncompressed_size_bytes": sum(item["uncompressed_size_bytes"] for item in dic_entries),
                "first_entries_in_archive_order": [compact_entry(item) for item in dic_entries[:3]],
                "last_entries_in_archive_order": [compact_entry(item) for item in dic_entries[-3:]],
                "non_csv_auxiliary_entries": dic_auxiliary,
            },
        }
    return {
        key: summary.get(key)
        for key in (
            "parsed_entry_count",
            "expected_entry_count",
            "entry_count_matches_end_record",
            "file_entry_count",
            "directory_entry_count",
            "sum_compressed_file_bytes",
            "sum_uncompressed_file_bytes",
            "extension_counts",
            "top_level_file_counts",
            "target_match_counts",
        )
    } | {"targets": targets}


def build_payload_candidates(summary: dict[str, Any]) -> dict[str, Any]:
    selected: list[dict[str, Any]] = []
    for token, entries in summary.get("target_matches", {}).items():
        for item in entries:
            families = item["channel_family_guess"]
            basename = PurePosixPath(item["path"]).name.lower()
            purpose = None
            if token == "P4V035" and "bar_strain_or_bar_displacement_boundary_condition" in families:
                purpose = "dynamic_bar_boundary_condition"
            elif token == "P4V035" and "DIC" in families and basename != "thumbs.db":
                purpose = "dynamic_dic_frame_or_coordinate_reference"
            elif token == "P6V035" and "force_displacement" in families:
                purpose = "quasi_static_force_displacement_comparator"
            if purpose is not None:
                selected.append({"specimen": token, "expected_use": purpose, **compact_entry(item)})
    selected.sort(key=lambda item: item["local_header_offset_bytes"])
    p6_dic = [
        item
        for item in summary.get("target_matches", {}).get("P6V035", [])
        if "DIC" in item["channel_family_guess"]
    ]
    compressed = sum(item["compressed_size_bytes"] for item in selected)
    return {
        "iteration": "V9G",
        "purpose": "Exact central-directory-derived candidate list for a separately predeclared V9H selective payload extraction.",
        "payload_downloaded_in_v9g": False,
        "selection_is_authorization": False,
        "selected_entry_count": len(selected),
        "selected_compressed_size_bytes": compressed,
        "selected_uncompressed_size_bytes": sum(item["uncompressed_size_bytes"] for item in selected),
        "conservative_future_range_transfer_ceiling_bytes": compressed + 4096 * len(selected),
        "selected_entries": selected,
        "deferred": {
            "P6V035_DIC": {
                "reason": "The quasi-static force-displacement file is the minimal comparator; the large DIC series is deferred pending signal inspection.",
                "file_count": len(p6_dic),
                "compressed_size_bytes": sum(item["compressed_size_bytes"] for item in p6_dic),
                "uncompressed_size_bytes": sum(item["uncompressed_size_bytes"] for item in p6_dic),
            },
            "microhardness_and_EBSD": "Outside the first mechanical-signal reduction and not selected.",
        },
    }


def build_report(result: dict[str, Any]) -> str:
    geometry = result["geometry_audit"]
    network = result["range_audit"]
    manifest = result["central_directory_summary"]
    target_lines = []
    for token, target in manifest.get("targets", {}).items():
        target_lines.append(
            f"### {token} — {target['target_match_count']} fichier(s), "
            f"{target['compressed_size_bytes']} octets compressés"
        )
        for family, stats in target["family_stats"].items():
            target_lines.append(
                f"- Famille `{family}`: {stats['file_count']} fichier(s), "
                f"{stats['compressed_size_bytes']} octets compressés."
            )
        for entry in target["exact_mechanical_entries"]:
            target_lines.append(
                f"- Entrée mécanique exacte: `{entry['path']}` — compressé {entry['compressed_size_bytes']} octets; "
                f"décompressé {entry['uncompressed_size_bytes']} octets; CRC32 `{entry['crc32_hex']}`; "
                f"famille(s): {', '.join(entry['channel_family_guess'])}."
            )
        dic = target["dic_summary"]
        if dic["file_count"]:
            target_lines.append(
                f"- Série DIC: {dic['file_count']} fichier(s), {dic['compressed_size_bytes']} octets compressés; "
                "la liste exacte reste dans le manifeste machine."
            )
    target_text = "\n".join(target_lines) if target_lines else "Aucune entrée cible n'a pu être inventoriée."
    candidates = result["selective_payload_candidates"]
    if network["partial_content_supported"]:
        access_sentence = (
            f"Le serveur accepte les lectures partielles. V9G a transféré {network['total_bytes_read']} octets, "
            f"soit {100.0 * network['total_bytes_read'] / network['declared_zip_size_bytes']:.6f} % du ZIP déclaré."
        )
    else:
        access_sentence = "Le serveur n'a pas accepté une lecture partielle sûre; aucun corps ZIP complet n'a été lu."
    return f"""# WTC 1 — V9G, audit sélectif de l'index ZIP S355

## Conclusion courte

{access_sentence}

Téléchargement complet du ZIP: **non**. Extraction de signaux: **non**. Solveur ou impact: **non**.

## 1. Faits directement observés ou transcrits

- `Fig1.jpg` mesure {geometry['size_bytes']} octets et correspond au MD5 Zenodo `{geometry['md5']}`.
- La figure indique des dimensions globales 17 × 10 × 12,2 mm, une séparation verticale cotée 2 mm et un décalage de géométrie `x = 0,35 mm`.
- Ces cotes ne constituent pas encore une définition géométrique complète: rayons, profondeurs de toutes les entailles et tolérances ne sont pas tous spécifiés dans la petite figure.
- Statut de la requête partielle initiale: {network['initial_range_status_code']}.
- Statut de la requête du répertoire central: {network.get('central_directory_status_code')}.
- Octets réellement lus: {network['total_bytes_read']} sous un plafond de {network['maximum_total_transferred_bytes']}.

## 2. Résultats de modèles officiels

- Aucun modèle officiel ou calcul physique n'est exécuté dans V9G.

## 3. Affirmations provenant des archives locales

- Aucune. L'archive source WTC n'a pas été rescannée.

## 4. Hypothèses propres à V9G

- Une correspondance de chemin contenant exactement `P4V035` ou `P6V035` identifie seulement un fichier candidat; elle ne valide ni ses unités ni sa qualité.
- La classification DIC, force-déplacement ou signal de barre est dérivée du nom de chemin et devra être confirmée par le contenu et la documentation avant toute réduction.

## 5. Résultats dérivés

- Répertoire central accessible: {network['central_directory_acquired']}.
- Entrées ZIP annoncées/parsées: {manifest.get('expected_entry_count')} / {manifest.get('parsed_entry_count')}.
- Fichiers P4V035: {manifest.get('target_match_counts', {}).get('P4V035', 0)}.
- Fichiers P6V035: {manifest.get('target_match_counts', {}).get('P6V035', 0)}.
- Une prochaine acquisition sélective peut être pré-déclarée: {result['selective_payload_predeclaration_possible']}.
- Sélection minimale proposée pour V9H: {candidates['selected_entry_count']} fichier(s), {candidates['selected_compressed_size_bytes']} octets compressés.
- La série DIC quasi-statique P6V035 reste différée: {candidates['deferred']['P6V035_DIC']['file_count']} fichier(s), {candidates['deferred']['P6V035_DIC']['compressed_size_bytes']} octets compressés.
- Un ZIP local fourni par Jeremy est nécessaire: {result['local_full_zip_needed']}.

## 6. Contradictions et informations manquantes

- Les fichiers de mesure n'ont pas été extraits; leurs unités, fréquences d'échantillonnage, synchronisation et qualité restent inconnues.
- La géométrie de la petite figure reste incomplète pour un maillage constitutif fidèle.
- Le jeu S355 reste un analogue en cisaillement et ne fournit aucune propriété WTC ou CF6 de production.

## Entrées candidates exactes

{target_text}

## Interprétation

{result['interpretation']}
"""


def main() -> int:
    started = datetime.now().astimezone()
    config = load_json(CONFIG_PATH)
    regressions = verify_regressions(config)
    geometry_declared = config["geometry_source"]
    geometry_audit = {
        "path": geometry_declared["local_path"],
        "exists": FIGURE_PATH.exists(),
        "size_bytes": FIGURE_PATH.stat().st_size if FIGURE_PATH.exists() else None,
        "md5": digest(FIGURE_PATH, "md5") if FIGURE_PATH.exists() else None,
        "sha256": digest(FIGURE_PATH) if FIGURE_PATH.exists() else None,
        "size_matches": FIGURE_PATH.exists() and FIGURE_PATH.stat().st_size == geometry_declared["expected_size_bytes"],
        "md5_matches": FIGURE_PATH.exists() and digest(FIGURE_PATH, "md5") == geometry_declared["expected_md5"],
        "transcription": {
            "units": "mm according to the Zenodo record description",
            "overall_width": 17.0,
            "overall_thickness": 10.0,
            "overall_height": 12.2,
            "vertical_notch_separation": 2.0,
            "offset_x": 0.35,
            "complete_for_constitutive_mesh": False,
        },
    }
    geometry_audit["passed"] = geometry_audit["size_matches"] and geometry_audit["md5_matches"]

    remote = config["remote_zip"]
    head_info: dict[str, Any] = {"status_code": None, "final_url": None, "headers": {}, "error": None}
    initial_info: dict[str, Any] = {"status_code": None, "bytes_read": 0, "body": None, "error": "not_attempted"}
    central_info: dict[str, Any] = {"status_code": None, "bytes_read": 0, "body": None, "error": "not_attempted"}
    eocd = None
    central_summary: dict[str, Any] = {
        "expected_entry_count": None,
        "parsed_entry_count": None,
        "target_matches": {},
        "target_match_counts": {},
    }
    error: str | None = None

    try:
        head_request = Request(
            remote["url"],
            method="HEAD",
            headers={"User-Agent": "WTC1-V9G-bounded-zip-index-audit/1.0"},
        )
        try:
            head = urlopen(head_request, timeout=remote["request_timeout_seconds"])
        except HTTPError as exc:
            head = exc
        head_status = getattr(head, "status", head.getcode())
        head_info = {
            "status_code": head_status,
            "final_url": sanitized_url(head.geturl()),
            "headers": selected_headers(head.headers),
            "error": None,
        }
        head.close()
        initial_info = bounded_range_get(
            remote["url"],
            f"bytes=-{remote['initial_suffix_range_bytes']}",
            remote["maximum_initial_body_bytes"],
            remote["request_timeout_seconds"],
        )
        if initial_info["body"] is not None:
            content_range = initial_info["content_range"]
            if content_range["total"] != remote["required_content_range_total_bytes"]:
                error = "content_range_total_does_not_match_declared_zip_size"
            else:
                eocd = parse_eocd(initial_info["body"])
                if eocd is None:
                    error = "end_of_central_directory_not_found_in_bounded_suffix"
                elif eocd["central_directory_size_bytes"] > remote["maximum_central_directory_bytes"]:
                    error = "central_directory_exceeds_predeclared_cap"
                else:
                    start = eocd["central_directory_offset_bytes"]
                    end = start + eocd["central_directory_size_bytes"] - 1
                    central_info = bounded_range_get(
                        remote["url"],
                        f"bytes={start}-{end}",
                        remote["maximum_central_directory_bytes"],
                        remote["request_timeout_seconds"],
                    )
                    if central_info["body"] is not None:
                        central_summary = parse_central_directory(
                            central_info["body"],
                            eocd["total_entries"],
                            [item["id"] for item in config["target_inventory"]["specimens"]],
                        )
                    else:
                        error = central_info["error"]
        else:
            error = initial_info["error"]
    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"
    finally:
        pass

    initial_body = initial_info.pop("body", None)
    central_body = central_info.pop("body", None)
    total_bytes_read = int(initial_info.get("bytes_read", 0) or 0) + int(central_info.get("bytes_read", 0) or 0)
    full_zip_path = ROOT / remote["full_local_path_prohibited"]
    range_supported = initial_info.get("status_code") == remote["required_http_status"] and initial_info.get("body_read", False)
    directory_acquired = central_info.get("status_code") == remote["required_http_status"] and central_info.get("body_read", False)
    target_counts = central_summary.get("target_match_counts", {})
    compact_summary = compact_central_summary(central_summary)
    payload_candidates = build_payload_candidates(central_summary)
    targets_found = all(
        target_counts.get(item["id"], 0) >= config["target_inventory"]["minimum_matching_file_entries_per_specimen"]
        for item in config["target_inventory"]["specimens"]
    )
    single_disk = bool(eocd) and eocd["disk_number"] == 0 and eocd["central_directory_disk"] == 0
    outcome_gates = {
        "http_partial_content_supported": range_supported,
        "content_range_total_matches": bool(initial_info.get("content_range")) and initial_info["content_range"]["total"] == remote["required_content_range_total_bytes"],
        "end_of_central_directory_found": eocd is not None,
        "single_disk_zip": single_disk,
        "central_directory_under_cap": bool(eocd) and eocd["central_directory_size_bytes"] <= remote["maximum_central_directory_bytes"],
        "central_directory_acquired": directory_acquired,
        "central_directory_entry_count_matches": central_summary.get("entry_count_matches_end_record", False),
        "target_specimen_tokens_inventoried": targets_found,
    }
    safety_gates = {
        "v9f_regressions_unchanged": regressions["passed"],
        "geometry_file_verified": geometry_audit["passed"],
        "total_transfer_under_cap": total_bytes_read <= remote["maximum_total_transferred_bytes"],
        "full_zip_not_present": not full_zip_path.exists(),
        "no_payload_entry_downloaded": True,
        "response_200_body_not_read": not (
            initial_info.get("status_code") == 200 and initial_info.get("body_read", False)
        ) and not (
            central_info.get("status_code") == 200 and central_info.get("body_read", False)
        ),
        "foia_request_unsent": config["foia_policy"]["request_sent"] is False,
        "external_contact_not_authorized_or_made": config["foia_policy"]["external_contact_authorized"] is False,
        "source_archive_not_rescanned": True,
        "generic_material_not_substituted": True,
        "solver_not_executed": True,
    }
    execution_validated = all(safety_gates.values())
    outcome_passed = all(outcome_gates.values())
    range_audit = {
        "declared_zip_size_bytes": remote["declared_total_size_bytes"],
        "maximum_total_transferred_bytes": remote["maximum_total_transferred_bytes"],
        "head": head_info,
        "initial_suffix_request": initial_info,
        "central_directory_request": central_info,
        "initial_range_status_code": initial_info.get("status_code"),
        "central_directory_status_code": central_info.get("status_code"),
        "partial_content_supported": range_supported,
        "central_directory_acquired": directory_acquired,
        "total_bytes_read": total_bytes_read,
        "error": error,
    }
    manifest = {
        "iteration": "V9G",
        "source_url": remote["url"],
        "declared_zip_size_bytes": remote["declared_total_size_bytes"],
        "declared_zip_md5": remote["declared_md5"],
        "full_zip_downloaded": False,
        "payload_entry_downloaded": False,
        "range_audit": range_audit,
        "end_of_central_directory": eocd,
        "central_directory_sha256": hashlib.sha256(central_body).hexdigest() if central_body else None,
        "central_directory_summary": central_summary,
        "outcome_gates": outcome_gates,
        "safety_gates": safety_gates,
    }
    write_json(MANIFEST_PATH, manifest)
    write_json(CANDIDATES_PATH, payload_candidates)

    local_zip_needed = not range_supported
    result = {
        "iteration": "V9G",
        "generated_at": started.isoformat(),
        "status": (
            "validated_remote_zip_index_targets_inventoried_no_payload_download"
            if execution_validated and outcome_passed
            else "validated_negative_remote_range_or_target_gate_failed_no_full_download"
            if execution_validated
            else "invalid_safety_or_regression_gate_failed"
        ),
        "iteration_execution_validated": execution_validated,
        "target_inventory_gate_passed": outcome_passed,
        "configuration": str(CONFIG_PATH.relative_to(ROOT)).replace("\\", "/"),
        "manifest": str(MANIFEST_PATH.relative_to(ROOT)).replace("\\", "/"),
        "selective_payload_candidates_path": str(CANDIDATES_PATH.relative_to(ROOT)).replace("\\", "/"),
        "scope": config["dataset"]["scope"],
        "evidence_policy": config["evidence_policy"],
        "regressions": regressions,
        "foia_policy": config["foia_policy"],
        "geometry_audit": geometry_audit,
        "range_audit": range_audit,
        "end_of_central_directory": eocd,
        "central_directory_summary": compact_summary,
        "selective_payload_candidates": payload_candidates,
        "safety_gate_summary": {"gates": safety_gates, "passed": execution_validated},
        "target_outcome_gate_summary": {"gates": outcome_gates, "passed": outcome_passed},
        "selective_payload_predeclaration_possible": execution_validated and outcome_passed,
        "local_full_zip_needed": local_zip_needed,
        "full_zip_download_authorized": False,
        "full_zip_downloaded": False,
        "selective_payload_download_authorized": False,
        "payload_entry_downloaded": False,
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
            "V9G validates a bounded remote ZIP-index audit only. "
            + (
                f"Zenodo honored HTTP Range requests; {total_bytes_read} bytes were read and the central directory exposes "
                f"{target_counts.get('P4V035', 0)} P4V035 plus {target_counts.get('P6V035', 0)} P6V035 file entries. "
                "Their exact paths, sizes and CRC32 values can now support a separately predeclared selective-download iteration. "
                if outcome_passed else
                "The partial-range or exact-target outcome gate did not pass, but the script safely stopped without reading a full response body. "
            )
            + "The 955 MB ZIP and all measurement payloads remain undownloaded. Fig1 confirms several millimetre-scale dimensions but is incomplete for a constitutive mesh. No material law, WTC or CF6 property, solver, rupture or facade impact is authorized."
        ),
        "runtime": {
            "started_at": started.isoformat(),
            "completed_at": datetime.now().astimezone().isoformat(),
            "software": "Python standard-library HTTP client plus bounded binary ZIP central-directory parser",
            "python_version": platform.python_version(),
            "platform": platform.platform(),
            "random_seed": config["dataset"]["random_seed"],
            "source_archive_rescanned": False,
            "full_zip_downloaded": False,
            "payload_entry_downloaded": False,
            "external_contact_made": False,
            "solver_executed": False,
        },
    }
    write_json(RESULTS_PATH, result)
    write_text(REPORT_PATH, build_report(result))
    print(json.dumps({
        "iteration": result["iteration"],
        "execution_validated": execution_validated,
        "target_inventory_passed": outcome_passed,
        "partial_content_supported": range_supported,
        "bytes_read": total_bytes_read,
        "zip_size_bytes": remote["declared_total_size_bytes"],
        "parsed_entries": central_summary.get("parsed_entry_count"),
        "target_match_counts": target_counts,
        "full_zip_downloaded": False,
        "local_full_zip_needed": local_zip_needed,
        "error": error,
    }, ensure_ascii=False, indent=2))
    return 0 if execution_validated else 1


if __name__ == "__main__":
    sys.exit(main())
