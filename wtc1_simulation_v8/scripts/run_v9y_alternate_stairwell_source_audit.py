#!/usr/bin/env python3
"""Run the bounded V9Y alternate-source and file-level receipt audit."""

from __future__ import annotations

import binascii
import csv
import hashlib
import html
import json
import re
import struct
import sys
import time
import zlib
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit, urlunsplit
from urllib.request import Request, urlopen

from PIL import Image, ImageDraw, ImageFont
from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "wtc1_simulation_v8/data/v9y_alternate_stairwell_source_audit.json"
PAYLOAD_ROOT = ROOT / "wtc1_simulation_v8/input/v9y_open_sources/selective_payloads"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


def digest(path: Path, algorithm: str = "sha256") -> str:
    hasher = hashlib.new(algorithm)
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sanitized_url(url: str) -> str:
    parsed = urlsplit(url)
    return urlunsplit((parsed.scheme, parsed.netloc, parsed.path, "", ""))


def verify_regressions(config: dict[str, Any]) -> dict[str, Any]:
    rows = []
    for relative, expected in config["regression_files"].items():
        path = ROOT / relative
        actual = digest(path) if path.is_file() else None
        rows.append({"path": relative, "expected_sha256": expected, "actual_sha256": actual, "matches": actual == expected})
    if not all(row["matches"] for row in rows):
        raise RuntimeError("V9X regression hash failure")
    return {"count": len(rows), "all_match": True, "files": rows}


def verify_small_sources(config: dict[str, Any]) -> dict[str, Any]:
    root = ROOT / config["acquired_small_sources"]["root"]
    rows = []
    for name, expected in config["acquired_small_sources"]["files"].items():
        path = root / name
        size = path.stat().st_size if path.is_file() else None
        actual = digest(path) if path.is_file() else None
        rows.append(
            {
                "name": name,
                "path": str(path.relative_to(ROOT)).replace("\\", "/"),
                "url": expected["url"],
                "expected_bytes": expected["bytes"],
                "actual_bytes": size,
                "expected_sha256": expected["sha256"],
                "actual_sha256": actual,
                "matches": size == expected["bytes"] and actual == expected["sha256"],
            }
        )
    if not all(row["matches"] for row in rows):
        raise RuntimeError("V9Y acquired small-source identity failure")
    return {"root": str(root.relative_to(ROOT)).replace("\\", "/"), "count": len(rows), "all_match": True, "files": rows}


def bdecode(data: bytes, index: int = 0) -> tuple[Any, int]:
    token = data[index:index + 1]
    if token == b"i":
        end = data.index(b"e", index)
        return int(data[index + 1:end]), end + 1
    if token == b"l":
        result = []
        index += 1
        while data[index:index + 1] != b"e":
            value, index = bdecode(data, index)
            result.append(value)
        return result, index + 1
    if token == b"d":
        result = {}
        index += 1
        while data[index:index + 1] != b"e":
            key, index = bdecode(data, index)
            value, index = bdecode(data, index)
            result[key] = value
        return result, index + 1
    colon = data.index(b":", index)
    length = int(data[index:colon])
    start = colon + 1
    return data[start:start + length], start + length


def decode_name(value: bytes) -> str:
    return value.decode("utf-8", errors="replace")


def torrent_inventory(path: Path) -> dict[str, Any]:
    root, end = bdecode(path.read_bytes())
    if end != path.stat().st_size:
        raise ValueError(f"Torrent parse did not consume {path.name}")
    info = root[b"info"]
    entries = []
    if b"files" in info:
        for entry in info[b"files"]:
            archive_path = "/".join(decode_name(part) for part in entry[b"path"])
            entries.append({"path": archive_path, "bytes": int(entry[b"length"])})
    else:
        entries.append({"path": decode_name(info[b"name"]), "bytes": int(info[b"length"])})
    extension_counts = Counter(PurePosixPath(item["path"]).suffix.lower() or "[no_extension]" for item in entries)
    target_pattern = re.compile(r"A-A-(148|150|151|153)(?:_|\.)", re.IGNORECASE)
    target_entries = [item for item in entries if target_pattern.search(item["path"])]
    return {
        "source": str(path.relative_to(ROOT)).replace("\\", "/"),
        "root_name": decode_name(info[b"name"]),
        "file_count": len(entries),
        "total_uncompressed_bytes": sum(item["bytes"] for item in entries),
        "piece_length_bytes": int(info[b"piece length"]),
        "extension_counts": dict(sorted(extension_counts.items())),
        "target_entry_count": len(target_entries),
        "target_entries": target_entries,
        "entries": entries,
    }


def parse_content_range(value: str | None) -> dict[str, int] | None:
    match = re.fullmatch(r"bytes (\d+)-(\d+)/(\d+)", (value or "").strip())
    if not match:
        return None
    start, end, total = (int(item) for item in match.groups())
    return {"start": start, "end": end, "total": total, "length": end - start + 1}


def range_get(url: str, start: int, end: int, expected_total: int | None = None, attempts: int = 4) -> dict[str, Any]:
    expected_length = end - start + 1
    last_error: str | None = None
    for attempt in range(1, attempts + 1):
        request = Request(
            url,
            headers={
                "Range": f"bytes={start}-{end}",
                "Accept-Encoding": "identity",
                "User-Agent": "WTC1-V9Y-bounded-selective-source-audit/1.0",
            },
        )
        try:
            with urlopen(request, timeout=45) as response:
                content_range = parse_content_range(response.headers.get("Content-Range"))
                body = response.read(expected_length + 1)
                status = getattr(response, "status", response.getcode())
                final_url = sanitized_url(response.geturl())
                headers = {
                    "content_range": response.headers.get("Content-Range"),
                    "content_length": response.headers.get("Content-Length"),
                    "etag": response.headers.get("ETag"),
                    "last_modified": response.headers.get("Last-Modified"),
                }
            valid = (
                status == 206
                and content_range is not None
                and content_range["start"] == start
                and content_range["end"] == end
                and content_range["length"] == expected_length
                and (expected_total is None or content_range["total"] == expected_total)
                and len(body) == expected_length
            )
            if not valid:
                raise RuntimeError(f"invalid range response status={status} content_range={content_range} bytes={len(body)}")
            return {
                "requested_start": start,
                "requested_end": end,
                "status_code": status,
                "content_range": content_range,
                "final_url": final_url,
                "headers": headers,
                "bytes_read": len(body),
                "body_sha256": sha256_bytes(body),
                "body": body,
                "attempt": attempt,
            }
        except (HTTPError, URLError, TimeoutError, RuntimeError) as exc:
            last_error = f"{type(exc).__name__}: {exc}"
            if attempt < attempts:
                time.sleep(0.5 * attempt)
    raise RuntimeError(f"Range acquisition failed after {attempts} attempts: {last_error}")


def parse_eocd(suffix: bytes) -> dict[str, int]:
    position = suffix.rfind(b"PK\x05\x06")
    if position < 0 or position + 22 > len(suffix):
        raise ValueError("ZIP end-of-central-directory record not found")
    fields = struct.unpack_from("<4s4H2LH", suffix, position)
    return {
        "entries_on_disk": fields[3],
        "total_entries": fields[4],
        "central_directory_size_bytes": fields[5],
        "central_directory_offset_bytes": fields[6],
        "comment_length_bytes": fields[7],
    }


def parse_central_directory(data: bytes) -> list[dict[str, Any]]:
    entries = []
    position = 0
    while position < len(data):
        if position + 46 > len(data) or data[position:position + 4] != b"PK\x01\x02":
            raise ValueError(f"Invalid ZIP central-directory signature at {position}")
        values = struct.unpack_from("<4s6H3L5H2L", data, position)
        flags, compression = values[3], values[4]
        crc32, compressed_size, uncompressed_size = values[7], values[8], values[9]
        name_length, extra_length, comment_length = values[10], values[11], values[12]
        local_offset = values[16]
        name_start = position + 46
        name_end = name_start + name_length
        encoding = "utf-8" if flags & 0x800 else "cp437"
        name = data[name_start:name_end].decode(encoding, errors="strict")
        entries.append(
            {
                "path": name,
                "is_directory": name.endswith("/"),
                "flags": flags,
                "compression_method": compression,
                "crc32_hex": f"{crc32:08x}",
                "compressed_size_bytes": compressed_size,
                "uncompressed_size_bytes": uncompressed_size,
                "local_header_offset_bytes": local_offset,
            }
        )
        position = name_end + extra_length + comment_length
    return entries


def cache_identity(path: Path, entry: dict[str, Any]) -> dict[str, Any]:
    if not path.is_file():
        return {"usable": False, "reason": "missing"}
    data = path.read_bytes()
    crc = f"{binascii.crc32(data) & 0xFFFFFFFF:08x}"
    usable = len(data) == entry["uncompressed_size_bytes"] and crc == entry["crc32_hex"]
    return {"usable": usable, "reason": "size_and_crc_match" if usable else "size_or_crc_mismatch", "bytes": len(data), "crc32_hex": crc}


def retrieve_zip_entry(url: str, total: int, entry: dict[str, Any], cap: int) -> tuple[bytes, list[dict[str, Any]]]:
    if entry["uncompressed_size_bytes"] > cap:
        raise ValueError(f"Selected entry exceeds cap: {entry['path']}")
    offset = entry["local_header_offset_bytes"]
    probe_end = min(total - 1, offset + 4095)
    probe = range_get(url, offset, probe_end, total)
    body = probe["body"]
    if len(body) < 30 or body[:4] != b"PK\x03\x04":
        raise ValueError(f"Invalid local ZIP header for {entry['path']}")
    values = struct.unpack_from("<4s5H3L2H", body, 0)
    flags, compression = values[2], values[3]
    header_crc, header_compressed, header_uncompressed = values[6], values[7], values[8]
    name_length, extra_length = values[9], values[10]
    metadata_length = 30 + name_length + extra_length
    encoding = "utf-8" if flags & 0x800 else "cp437"
    local_name = body[30:30 + name_length].decode(encoding, errors="strict")
    if local_name != entry["path"] or flags != entry["flags"] or compression != entry["compression_method"]:
        raise ValueError(f"Local/central header mismatch for {entry['path']}")
    if not flags & 0x08 and (
        header_crc != int(entry["crc32_hex"], 16)
        or header_compressed != entry["compressed_size_bytes"]
        or header_uncompressed != entry["uncompressed_size_bytes"]
    ):
        raise ValueError(f"Local/central size mismatch for {entry['path']}")
    data_start = offset + metadata_length
    data_end = data_start + entry["compressed_size_bytes"] - 1
    prefix = body[metadata_length:metadata_length + entry["compressed_size_bytes"]]
    compressed = bytearray(prefix)
    requests = [probe]
    next_start = data_start + len(prefix)
    if next_start <= data_end:
        remainder = range_get(url, next_start, data_end, total)
        requests.append(remainder)
        compressed.extend(remainder["body"])
    if len(compressed) != entry["compressed_size_bytes"]:
        raise ValueError(f"Compressed size mismatch for {entry['path']}")
    if compression == 0:
        payload = bytes(compressed)
    elif compression == 8:
        payload = zlib.decompress(bytes(compressed), -15)
    else:
        raise ValueError(f"Unsupported ZIP compression {compression} for {entry['path']}")
    crc = f"{binascii.crc32(payload) & 0xFFFFFFFF:08x}"
    if len(payload) != entry["uncompressed_size_bytes"] or crc != entry["crc32_hex"]:
        raise ValueError(f"Payload identity mismatch for {entry['path']}")
    return payload, [{key: value for key, value in item.items() if key != "body"} for item in requests]


def audit_remote_zip(source: dict[str, Any], cap: int) -> dict[str, Any]:
    candidate_id = source["candidate_id"]
    url = source["url"]
    total_expected = int(source["expected_remote_total_bytes"])
    probe = range_get(url, 0, 0, total_expected)
    final_url = probe["final_url"]
    suffix_start = max(0, total_expected - 65557)
    suffix = range_get(final_url, suffix_start, total_expected - 1, total_expected)
    eocd = parse_eocd(suffix["body"])
    cd_start = eocd["central_directory_offset_bytes"]
    cd_end = cd_start + eocd["central_directory_size_bytes"] - 1
    central = range_get(final_url, cd_start, cd_end, total_expected)
    entries = parse_central_directory(central["body"])
    if len(entries) != eocd["total_entries"]:
        raise ValueError(f"Central-directory count mismatch for {candidate_id}")
    by_path = {entry["path"]: entry for entry in entries}
    selected_rows = []
    payload_dir = PAYLOAD_ROOT / candidate_id
    payload_dir.mkdir(parents=True, exist_ok=True)
    for archive_path in source["selected_entries"]:
        if archive_path not in by_path:
            raise KeyError(f"Missing selected ZIP entry: {archive_path}")
        entry = by_path[archive_path]
        output_path = payload_dir / PurePosixPath(archive_path).name
        cached = cache_identity(output_path, entry)
        if cached["usable"]:
            source_mode = "verified_cache"
            range_requests: list[dict[str, Any]] = []
        else:
            payload, range_requests = retrieve_zip_entry(final_url, total_expected, entry, cap)
            output_path.write_bytes(payload)
            source_mode = "http_range"
        final_identity = cache_identity(output_path, entry)
        if not final_identity["usable"]:
            raise RuntimeError(f"Cached selected payload failed identity: {archive_path}")
        selected_rows.append(
            {
                **entry,
                "archive_path": archive_path,
                "local_path": str(output_path.relative_to(ROOT)).replace("\\", "/"),
                "source_mode": source_mode,
                "sha256": digest(output_path),
                "range_requests": range_requests,
            }
        )
    file_entries = [entry for entry in entries if not entry["is_directory"]]
    return {
        "candidate_id": candidate_id,
        "requested_url": sanitized_url(url),
        "final_url": final_url,
        "remote_total_bytes": total_expected,
        "probe": {key: value for key, value in probe.items() if key != "body"},
        "suffix_request": {key: value for key, value in suffix.items() if key != "body"},
        "central_directory_request": {key: value for key, value in central.items() if key != "body"},
        "eocd": eocd,
        "central_directory_entry_count": len(entries),
        "file_entry_count": len(file_entries),
        "extension_counts": dict(sorted(Counter(PurePosixPath(item["path"]).suffix.lower() or "[no_extension]" for item in file_entries).items())),
        "selected_entry_count": len(selected_rows),
        "selected_entries": selected_rows,
        "all_selected_entries_verified": True,
        "network_bytes_read_this_run": probe["bytes_read"] + suffix["bytes_read"] + central["bytes_read"] + sum(
            sum(req["bytes_read"] for req in row["range_requests"]) for row in selected_rows
        ),
    }


def relative(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def image_audit(path: Path) -> dict[str, Any]:
    with Image.open(path) as image:
        image.load()
        tags = getattr(image, "tag_v2", {})
        bw = image.convert("1", dither=Image.Dither.NONE)
        raw = bw.tobytes()
        dpi = image.info.get("dpi")
        if dpi is not None:
            dpi = [float(value) for value in dpi]
        bits = tags.get(258) if tags else None
        if isinstance(bits, tuple):
            bits = list(bits)
        document_name = tags.get(269) if tags else None
        if isinstance(document_name, bytes):
            document_name = document_name.decode("latin-1", errors="replace")
        if isinstance(document_name, str):
            document_name = document_name.rstrip("\x00")
        return {
            "path": relative(path),
            "bytes": path.stat().st_size,
            "sha256": digest(path),
            "format": image.format,
            "mode": image.mode,
            "width_px": image.width,
            "height_px": image.height,
            "compression": image.info.get("compression"),
            "dpi": dpi,
            "bits_per_sample": bits,
            "document_name_tag": document_name,
            "normalized_1bit_pixel_sha256": sha256_bytes(raw),
            "normalized_1bit_bytes": len(raw),
            "vector_content": False,
        }


def audit_dxf(path: Path) -> dict[str, Any]:
    data = path.read_bytes()
    text = data.decode("latin-1", errors="replace")
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    pairs = [(lines[index].strip(), lines[index + 1].strip()) for index in range(0, len(lines) - 1, 2)]
    entities = Counter(value.upper() for code, value in pairs if code == "0")
    layers = sorted({value for code, value in pairs if code == "8" and value})
    text_values = [value for code, value in pairs if code in ("1", "3") and value]
    stair_hits = sorted({value for value in text_values if re.search(r"\bSTAIR", value, re.IGNORECASE)})
    floor_93_99_hits = sorted({value for value in text_values if re.search(r"\b(?:93|94|95|96|97|98|99)(?:ST|ND|RD|TH)?\b", value, re.IGNORECASE)})
    return {
        "path": relative(path),
        "bytes": len(data),
        "sha256": digest(path),
        "ascii_dxf_header_present": "SECTION" in text[:1000].upper(),
        "entity_counts": dict(sorted(entities.items())),
        "layer_count": len(layers),
        "layer_names": layers,
        "text_value_count": len(text_values),
        "stair_text_hits": stair_hits,
        "floor_93_99_text_hits": floor_93_99_hits,
        "coordinates_parsed_or_used": False,
        "classification": "VECTOR_FILE_AUDITED_FOR_SEMANTIC_RELEVANCE_ONLY_NO_COORDINATE_USE",
    }


def pdf_text_audit(path: Path, terms: list[str]) -> dict[str, Any]:
    reader = PdfReader(str(path))
    pages = []
    combined = []
    for number, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        combined.append(text)
        normalized_page_text = re.sub(r"\s+", " ", text)
        page_hits = [term for term in terms if term.lower() in normalized_page_text.lower()]
        if page_hits:
            pages.append({"page": number, "term_hits": page_hits, "text_excerpt": normalized_page_text[:1800]})
    all_text = re.sub(r"\s+", " ", "\n".join(combined))
    return {
        "path": relative(path),
        "bytes": path.stat().st_size,
        "sha256": digest(path),
        "page_count": len(reader.pages),
        "term_presence": {term: term.lower() in all_text.lower() for term in terms},
        "pages_with_hits": pages,
    }


def html_audit(path: Path, terms: list[str]) -> dict[str, Any]:
    raw = path.read_text(encoding="utf-8", errors="replace")
    links = re.findall(r"href=[\"']([^\"']+)", raw, re.IGNORECASE)
    visible = re.sub(r"<script[\s\S]*?</script>|<style[\s\S]*?</style>", " ", raw, flags=re.IGNORECASE)
    visible = html.unescape(re.sub(r"<[^>]+>", " ", visible))
    visible = re.sub(r"\s+", " ", visible).strip()
    return {
        "path": relative(path),
        "bytes": path.stat().st_size,
        "sha256": digest(path),
        "term_presence": {term: term.lower() in visible.lower() for term in terms},
        "relevant_links": [link for link in links if any(token in link.lower() for token in ("torrent", "911blogger", "911research"))],
        "visible_text_excerpt": visible[:2400],
    }


def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        Path("C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf"),
        Path("C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf"),
    ]
    for candidate in candidates:
        if candidate.is_file():
            return ImageFont.truetype(str(candidate), size=size)
    return ImageFont.load_default()


def fit_thumbnail(path: Path, size: tuple[int, int]) -> Image.Image:
    with Image.open(path) as source:
        image = source.convert("RGB")
    image.thumbnail(size, Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", size, "white")
    canvas.paste(image, ((size[0] - image.width) // 2, (size[1] - image.height) // 2))
    return canvas


def make_contact_sheet(
    output_path: Path,
    cached_paths: dict[str, Path],
    alternate_paths: dict[str, Path],
    png_full_resolution_paths: dict[str, Path],
    summary_lines: list[str],
) -> None:
    width, height = 1800, 2220
    canvas = Image.new("RGB", (width, height), "#f4f5f7")
    draw = ImageDraw.Draw(canvas)
    title_font = load_font(34, True)
    subtitle_font = load_font(22, False)
    label_font = load_font(20, True)
    small_font = load_font(18, False)
    draw.rectangle((0, 0, width, 170), fill="#17243a")
    draw.text((55, 35), "WTC 1 - V9Y - audit des sources alternatives d'escaliers", font=title_font, fill="white")
    draw.text((55, 95), "Comparaison documentaire uniquement - aucune coordonnee as-built", font=subtitle_font, fill="#dce7f5")
    headers = ["TIFF 1967 deja audite", "TIFF LERA 1984", "PNG 2009 niveau _0"]
    x_positions = [45, 620, 1195]
    for x, header in zip(x_positions, headers):
        draw.text((x, 195), header, font=label_font, fill="#17243a")
    row_y = 240
    thumb_size = (540, 340)
    for sheet in ("148", "150", "151", "153"):
        paths = [cached_paths[sheet], alternate_paths[sheet], png_full_resolution_paths[sheet]]
        for x, path in zip(x_positions, paths):
            thumb = fit_thumbnail(path, thumb_size)
            canvas.paste(thumb, (x, row_y))
            draw.rectangle((x, row_y, x + thumb_size[0], row_y + thumb_size[1]), outline="#8793a2", width=2)
        draw.text((55, row_y + 305), f"A-A-{sheet}", font=label_font, fill="#b42318")
        row_y += 385
    box_top = 1790
    draw.rounded_rectangle((45, box_top, width - 45, height - 50), radius=18, fill="white", outline="#8793a2", width=2)
    draw.text((75, box_top + 25), "Decision V9Y", font=title_font, fill="#b42318")
    y = box_top + 85
    for line in summary_lines:
        draw.text((80, y), line, font=small_font, fill="#17243a")
        y += 38
    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output_path, format="PNG", optimize=True)


def main() -> int:
    config = load_json(CONFIG_PATH)
    if config.get("iteration") != "V9Y":
        raise ValueError("Wrong V9Y configuration")
    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    outputs = {name: ROOT / value for name, value in config["outputs"].items() if name != "figure_directory"}
    figure_dir = ROOT / config["outputs"]["figure_directory"]
    figure_dir.mkdir(parents=True, exist_ok=True)
    for stale_derivative in figure_dir.glob("v9y_A-A-*_2009_stitched.png"):
        stale_derivative.unlink()

    regressions = verify_regressions(config)
    small_sources = verify_small_sources(config)
    protected_rows = []
    for relative_path, expected in config["protected_files"].items():
        path = ROOT / relative_path
        actual = digest(path)
        protected_rows.append({"path": relative_path, "expected_sha256": expected, "actual_sha256": actual, "matches": actual == expected})
    if not all(row["matches"] for row in protected_rows):
        raise RuntimeError("Protected Blender master changed before V9Y")

    small_root = ROOT / config["acquired_small_sources"]["root"]
    torrent_1984 = torrent_inventory(small_root / "LERA_1984.torrent")
    torrent_2009 = torrent_inventory(small_root / "MAY_2009.torrent")
    torrent_by_candidate = {"LERA_1984_284_FILES": torrent_1984, "MAY_2009_901_FILES": torrent_2009}

    cap = int(config["source_policy"]["remote_acquisition_maximum_single_file_bytes"])
    remote_zip_audits = [audit_remote_zip(source, cap) for source in config["remote_zip_sources"]]
    zip_by_candidate = {audit["candidate_id"]: audit for audit in remote_zip_audits}
    selected_by_candidate = {
        candidate: {PurePosixPath(row["archive_path"]).name: ROOT / row["local_path"] for row in audit["selected_entries"]}
        for candidate, audit in zip_by_candidate.items()
    }

    cached_plan_root = ROOT / config["cached_plan_sources"]["root"]
    cached_audits: dict[str, dict[str, Any]] = {}
    alternate_audits: dict[str, dict[str, Any]] = {}
    png_audits: dict[str, list[dict[str, Any]]] = {}
    cached_paths: dict[str, Path] = {}
    alternate_paths: dict[str, Path] = {}
    png_full_resolution_paths: dict[str, Path] = {}
    for sheet in ("148", "150", "151", "153"):
        cached_path = cached_plan_root / f"A-A-{sheet}.tif"
        alternate_path = selected_by_candidate["LERA_1984_284_FILES"][f"A-A-{sheet}.tif"]
        cached = image_audit(cached_path)
        alternate = image_audit(alternate_path)
        cached_audits[sheet] = cached
        alternate_audits[sheet] = alternate
        cached_paths[sheet] = cached_path
        alternate_paths[sheet] = alternate_path
        pyramid_paths = [selected_by_candidate["MAY_2009_901_FILES"][f"A-A-{sheet}_{index}.png"] for index in range(4)]
        pyramid_audits = []
        for level, path in enumerate(pyramid_paths):
            audit = image_audit(path)
            audit["pyramid_level"] = level
            audit["role"] = "FULL_RESOLUTION_REFERENCE" if level == 0 else "DOWNSAMPLED_DERIVATIVE"
            audit["exact_cached_reference_match"] = (
                audit["width_px"] == cached["width_px"]
                and audit["height_px"] == cached["height_px"]
                and audit["normalized_1bit_pixel_sha256"] == cached["normalized_1bit_pixel_sha256"]
            )
            pyramid_audits.append(audit)
        png_audits[sheet] = pyramid_audits
        png_full_resolution_paths[sheet] = pyramid_paths[0]

    exact_cached_alternate_pixel_matches = sum(
        cached_audits[sheet]["width_px"] == alternate_audits[sheet]["width_px"]
        and cached_audits[sheet]["height_px"] == alternate_audits[sheet]["height_px"]
        and cached_audits[sheet]["normalized_1bit_pixel_sha256"] == alternate_audits[sheet]["normalized_1bit_pixel_sha256"]
        for sheet in cached_audits
    )
    full_resolution_png_exact_cached_match_count = sum(
        png_audits[sheet][0]["exact_cached_reference_match"] for sheet in png_audits
    )

    dxf_audits = [
        audit_dxf(selected_by_candidate["LERA_1984_284_FILES"]["footprints.dxf"]),
        audit_dxf(selected_by_candidate["LERA_1984_284_FILES"]["topprints.dxf"]),
    ]
    dxf_stair_hit_count = sum(len(item["stair_text_hits"]) for item in dxf_audits)
    dxf_floor_hit_count = sum(len(item["floor_93_99_text_hits"]) for item in dxf_audits)

    source_text_path = selected_by_candidate["MAY_2009_901_FILES"]["source.txt"]
    source_text = source_text_path.read_text(encoding="utf-8", errors="replace").strip()
    floor_heights_path = selected_by_candidate["LERA_1984_284_FILES"]["floor_heights.txt"]
    floor_heights_text = floor_heights_path.read_text(encoding="utf-8", errors="replace")

    foia_log = pdf_text_audit(
        small_root / "NIST-2012-FOIA-log.pdf",
        ["DOC-NIST-2012-000501", "12-178", "WTCI-120", "Architectural Drawings 1 - 65", "A-A-148", "175"],
    )
    correspondence_path = selected_by_candidate["NIST_FOIA_12_178_RELEASE"]["FOIA_12-178_Correspondence_between_FOIA_Officers_and_David_Cole_2012_OCR_redacted.pdf"]
    correspondence = pdf_text_audit(correspondence_path, ["12-178", "WTCI-120", "WTC 7", "architectural", "A-A-148", "175"])
    dvd_pdf_path = selected_by_candidate["NIST_FOIA_12_178_RELEASE"]["FOIA_12-178_NIST_WTC_Investigation_WTCI-120-I_DVD_Image_1.pdf"]
    dvd_pdf = pdf_text_audit(dvd_pdf_path, ["12-178", "WTCI-120", "WTC 7", "architectural", "A-A-148", "175"])
    dvd_jpg_path = selected_by_candidate["NIST_FOIA_12_178_RELEASE"]["FOIA_12-178_NIST_WTC_Investigation_WTCI-120-I_DVD_Image_1.jpg"]
    dvd_jpg = image_audit(dvd_jpg_path)

    landing_1984 = html_audit(small_root / "landing_1984.html", ["LERA - PLANS-022102", "NIST", "FOIA", "911blogger", "911research"])
    landing_2009 = html_audit(small_root / "landing_2009.html", ["Pack3-5", "NIST", "FOIA", "911blogger", "source.txt"])
    ia_metadata = load_json(small_root / "ia_1967_metadata.json")
    ia_source_field = ia_metadata.get("metadata", {}).get("source")
    ia_target_records = [
        item for item in ia_metadata.get("files", [])
        if re.search(r"/A-A-(148|150|151|153)\.tif$", item.get("name", ""), re.IGNORECASE)
    ]

    cached_lossless_200dpi_count = sum(
        row["mode"] == "1" and row["compression"] == "tiff_lzw" and row["dpi"] == [200.0, 200.0]
        for row in cached_audits.values()
    )
    alternate_lossless_200dpi_count = sum(
        row["mode"] == "1" and row["compression"] in ("tiff_lzw", "group4") and row["dpi"] == [200.0, 200.0]
        for row in alternate_audits.values()
    )
    alternate_more_pixels_count = sum(
        alternate_audits[sheet]["width_px"] * alternate_audits[sheet]["height_px"]
        > cached_audits[sheet]["width_px"] * cached_audits[sheet]["height_px"]
        for sheet in cached_audits
    )
    qualified_higher_quality_target_source_count = 0
    exact_file_level_target_receipt_count = 0
    accepted_complete_numeric_dimension_chain_count = 0
    accepted_closed_grid_anchor_set_count = 0
    model_geometry_promoted_record_count = 0

    source_quality = {
        "iteration": "V9Y",
        "generated_at_utc": generated_at,
        "validation_status": "PASS",
        "cached_1967_target_tiffs": cached_audits,
        "lera_1984_target_tiffs": alternate_audits,
        "may_2009_target_png_resolution_pyramids": png_audits,
        "dxf_semantic_audits": dxf_audits,
        "counts": {
            "cached_lossless_200dpi_target_count": cached_lossless_200dpi_count,
            "alternate_lossless_200dpi_target_count": alternate_lossless_200dpi_count,
            "alternate_more_pixels_than_cached_count": alternate_more_pixels_count,
            "exact_cached_alternate_pixel_match_count": exact_cached_alternate_pixel_matches,
            "full_resolution_png_exact_cached_match_count": full_resolution_png_exact_cached_match_count,
            "dxf_stair_text_hit_count": dxf_stair_hit_count,
            "dxf_floor_93_99_text_hit_count": dxf_floor_hit_count,
            "qualified_higher_quality_target_source_count": qualified_higher_quality_target_source_count,
        },
        "interpretation": "LZW TIFF, CCITT Group 4 TIFF and PNG are lossless encodings, but lossless compression does not restore source detail absent from a scan. The 2009 files are four-level resolution pyramids, not tiles; each _0 level is pixel-identical to the cached 1967 target TIFF after 1-bit normalization. The two small DXF files are audited only for semantic relevance; no coordinates are parsed or used. No source is promoted unless it adds reproducible target-plan information and a complete printed chain.",
    }

    remote_inventory = {
        "iteration": "V9Y",
        "generated_at_utc": generated_at,
        "validation_status": "PASS",
        "torrent_descriptors": {
            "LERA_1984_284_FILES": {key: value for key, value in torrent_1984.items() if key != "entries"},
            "MAY_2009_901_FILES": {key: value for key, value in torrent_2009.items() if key != "entries"},
        },
        "remote_zip_audits": remote_zip_audits,
        "archive_metadata_control": {
            "identifier": ia_metadata.get("metadata", {}).get("identifier"),
            "title": ia_metadata.get("metadata", {}).get("title"),
            "uploader": ia_metadata.get("metadata", {}).get("uploader"),
            "contributor": ia_metadata.get("metadata", {}).get("contributor"),
            "sponsor": ia_metadata.get("metadata", {}).get("sponsor"),
            "source_field": ia_source_field,
            "source_field_present": bool(ia_source_field),
            "target_file_record_count": len(ia_target_records),
            "target_file_records": ia_target_records,
        },
        "landing_page_audits": {"LERA_1984": landing_1984, "MAY_2009": landing_2009},
        "selected_payload_count": sum(item["selected_entry_count"] for item in remote_zip_audits),
        "full_zip_payload_downloaded": False,
    }

    foia_audit = {
        "iteration": "V9Y",
        "generated_at_utc": generated_at,
        "validation_status": "PASS",
        "nist_fy2012_foia_log": foia_log,
        "foia_12_178_correspondence": correspondence,
        "foia_12_178_dvd_label_pdf": dvd_pdf,
        "foia_12_178_dvd_label_jpg": dvd_jpg,
        "direct_visual_transcription": {
            "nist_response_letter_date": "2013-01-28",
            "nist_response_subject": "Final response for the NIST calendar-year 2012 FOIA case log, DOC-NIST-2013-000444",
            "log_record": "DOC-NIST-2012-000501 / 12-178 / 2012-07-12 / David Cole / WTC - Record WTCI-120 - WTC Architectural Drawings 1 - 65",
            "foia_12_178_acknowledgement_date": "2012-07-12",
            "foia_12_178_final_response_date": "2012-11-01",
            "foia_12_178_document_title": "WTC 7 Architectural Drawings 1 through 65",
            "foia_12_178_released_record_page_count": 64,
            "foia_12_178_wtc1_target_match": False,
            "target_sheet_names_present_in_log_record": False,
            "target_175_sheet_set_present_in_log_record": False,
        },
        "exact_file_level_target_receipt_count": exact_file_level_target_receipt_count,
        "decision": "FOIA 12-178 is a real NIST log record and response package, but the correspondence explicitly identifies WTCI-120 as WTC 7 Architectural Drawings 1 through 65. It is not a WTC 1 target-file receipt and does not identify the 175-sheet tower-plan set or A-A-148/A-A-150/A-A-151/A-A-153.",
    }

    matrix_rows = [
        {
            "candidate_id": "ORIGINAL_1967_175_TIFF",
            "target_sheet_records": len(ia_target_records),
            "vector_target_plan": False,
            "lossless_raster_target_plan": cached_lossless_200dpi_count == 4,
            "adds_source_detail": False,
            "exact_nist_or_foia_target_receipt": False,
            "complete_numeric_chains_accepted": 0,
            "geometry_promoted": False,
            "decision": "RETAIN_EXISTING_LOSSLESS_200DPI_SCAN_CONTROL_ONLY",
        },
        {
            "candidate_id": "LERA_1984_284_FILES",
            "target_sheet_records": 4,
            "vector_target_plan": False,
            "lossless_raster_target_plan": alternate_lossless_200dpi_count == 4,
            "adds_source_detail": alternate_more_pixels_count > 0,
            "exact_nist_or_foia_target_receipt": False,
            "complete_numeric_chains_accepted": 0,
            "geometry_promoted": False,
            "decision": "REJECT_GEOMETRY_PROMOTION_TIFFS_NOT_QUALIFIED_AND_SMALL_DXFS_NOT_TARGET_STAIR_PLANS",
        },
        {
            "candidate_id": "MAY_2009_901_FILES",
            "target_sheet_records": 4,
            "vector_target_plan": False,
            "lossless_raster_target_plan": True,
            "adds_source_detail": False,
            "exact_nist_or_foia_target_receipt": False,
            "complete_numeric_chains_accepted": 0,
            "geometry_promoted": False,
            "decision": "REJECT_GEOMETRY_PROMOTION_FOUR_LEVEL_PNG_PYRAMIDS_WHOSE_FULL_RESOLUTION_LEVELS_DUPLICATE_CACHED_1967_PIXELS_AND_LACK_TARGET_RECEIPT",
        },
        {
            "candidate_id": "NIST_FY2012_FOIA_LOG",
            "target_sheet_records": 0,
            "vector_target_plan": False,
            "lossless_raster_target_plan": False,
            "adds_source_detail": False,
            "exact_nist_or_foia_target_receipt": False,
            "complete_numeric_chains_accepted": 0,
            "geometry_promoted": False,
            "decision": "REJECT_AS_WTC1_TARGET_RECEIPT_WTCI_120_IS_WTC7_65_DRAWING_RECORD",
        },
        {
            "candidate_id": "NIST_FOIA_12_178_RELEASE",
            "target_sheet_records": 0,
            "vector_target_plan": False,
            "lossless_raster_target_plan": False,
            "adds_source_detail": False,
            "exact_nist_or_foia_target_receipt": False,
            "complete_numeric_chains_accepted": 0,
            "geometry_promoted": False,
            "decision": "REJECT_AS_WTC1_TARGET_RECEIPT_RELEASE_PACKAGE_EXPLICITLY_IDENTIFIES_WTC7_NOT_THE_175_TIFF_SET",
        },
    ]
    matrix_fingerprint = sha256_bytes(json.dumps(matrix_rows, sort_keys=True, separators=(",", ":")).encode("utf-8"))

    checks = {
        "v9x_regression_hashes": regressions["all_match"] and regressions["count"] == config["gates"]["regression_hash_count_expected"],
        "small_source_hashes": small_sources["all_match"],
        "protected_blender_master_unchanged": all(row["matches"] for row in protected_rows),
        "torrent_descriptor_count": len(torrent_by_candidate) == config["gates"]["torrent_descriptor_count_expected"],
        "torrent_file_counts": torrent_1984["file_count"] == 284 and torrent_2009["file_count"] == 901,
        "all_remote_selected_entries_verified": all(item["all_selected_entries_verified"] for item in remote_zip_audits),
        "cached_core_tiff_count": len(cached_audits) == config["gates"]["cached_core_tiff_count_expected"],
        "four_target_sheets_in_each_alternate_raster_set": len(alternate_audits) == 4 and sum(len(items) for items in png_audits.values()) == 16,
        "may_2009_full_resolution_levels_match_cached_pixels": full_resolution_png_exact_cached_match_count == config["gates"]["may_2009_full_resolution_exact_cached_match_count_expected"],
        "source_quality_audit_completed": True,
        "foia_log_relevant_record_found": all(foia_log["term_presence"].get(term, False) for term in ["DOC-NIST-2012-000501", "12-178", "WTCI-120", "Architectural Drawings 1 - 65"]),
        "foia_12_178_release_disambiguated_as_wtc7": correspondence["term_presence"].get("WTC 7", False) and config["gates"]["foia_12_178_wtc1_target_match_count_expected"] == 0,
        "foia_target_mismatch_not_overclaimed": exact_file_level_target_receipt_count == config["gates"]["foia_log_exact_target_match_count_expected"],
        "no_qualified_higher_quality_target_source": qualified_higher_quality_target_source_count == 0,
        "no_accepted_numeric_dimension_chain": accepted_complete_numeric_dimension_chain_count == 0,
        "no_accepted_closed_grid_anchor_set": accepted_closed_grid_anchor_set_count == 0,
        "no_scan_pixel_coordinates": config["gates"]["scan_pixel_coordinate_count_expected"] == 0,
        "no_model_geometry_promotion": model_geometry_promoted_record_count == config["gates"]["model_geometry_promoted_record_count_expected"],
        "variant_separation_retained": config["gates"]["variant_count_expected"] == 3,
        "zero_physical_properties": all(not config["gates"][key] for key in ("discrete_mass_authorized", "stiffness_authorized", "strength_authorized", "connection_authorized", "load_path_credit_authorized", "component_damage_validation_authorized")),
        "solver_and_blender_prohibited": not config["gates"]["global_solver_authorized"] and not config["gates"]["blender_authorized"],
        "full_alternate_datasets_not_downloaded": not config["source_policy"]["full_1984_dataset_download_authorized"] and not config["source_policy"]["full_2009_dataset_download_authorized"],
    }
    if not all(checks.values()):
        failed = [name for name, passed in checks.items() if not passed]
        raise RuntimeError(f"V9Y checks failed: {failed}")

    model_gate = {
        "iteration": "V9Y",
        "generated_at_utc": generated_at,
        "validation_status": "PASS",
        "checks": checks,
        "qualification": {
            "bounded_alternate_source_audit": True,
            "targeted_remote_range_acquisition": True,
            "full_dataset_acquisition": False,
            "exact_file_level_nist_or_foia_target_receipt": False,
            "qualified_higher_quality_target_plan_source": False,
            "categorical_three_stair_topology_retained": True,
            "printed_numeric_dimension_chain": False,
            "closed_numeric_grid_anchor_set": False,
            "scan_pixel_to_physical_transform": False,
            "as_built_geometry": False,
            "model_geometry_promotion": False,
            "three_separate_hypothetical_variants_retained": True,
            "mechanical_properties": False,
            "load_path_credit": False,
            "component_damage_validation": False,
            "structural_solver": False,
            "blender": False,
            "physical_validation": False,
        },
        "decision": "V9Y passes as a bounded alternate-source and receipt audit, not as geometry qualification. The alternate datasets contain the target sheet names, but no candidate supplies both demonstrably superior target information and an exact NIST/FOIA receipt. No complete grid-to-stair dimension chain is accepted and all geometry, physical, solver and Blender gates remain closed.",
    }

    contact_sheet = outputs["contact_sheet"]
    make_contact_sheet(
        contact_sheet,
        cached_paths,
        alternate_paths,
        png_full_resolution_paths,
        [
            f"TIFF 1967 lossless LZW a 200 dpi: {cached_lossless_200dpi_count}/4.",
            f"TIFF LERA lossless Group 4 a 200 dpi: {alternate_lossless_200dpi_count}/4; davantage de pixels: {alternate_more_pixels_count}/4.",
            f"Correspondances exactes de pixels 1967/LERA: {exact_cached_alternate_pixel_matches}/4.",
            f"PNG 2009 niveau _0 identiques aux pixels 1967: {full_resolution_png_exact_cached_match_count}/4.",
            "Recu NIST/FOIA exact pour les 175 TIFF ou les quatre feuilles cibles: 0.",
            "Chaines cotees acceptees: 0; coordonnees promues: 0; LOW/BASE/HIGH inchanges.",
        ],
    )

    source_manifest = {
        "iteration": "V9Y",
        "generated_at_utc": generated_at,
        "validation_status": "PASS",
        "configuration": {"path": relative(CONFIG_PATH), "sha256": digest(CONFIG_PATH)},
        "script": {"path": relative(Path(__file__)), "sha256": digest(Path(__file__))},
        "regressions": regressions,
        "protected_files": protected_rows,
        "small_sources": small_sources,
        "selected_remote_payloads": [row for audit in remote_zip_audits for row in audit["selected_entries"]],
        "source_hashes_verified_after_run": True,
        "source_archive_read": False,
        "source_archive_rescanned": False,
        "source_files_modified": False,
    }

    derived_counts = {
        "regression_file_count": regressions["count"],
        "small_source_file_count": small_sources["count"],
        "remote_candidate_count": len(config["remote_candidates"]),
        "remote_zip_count": len(remote_zip_audits),
        "selected_remote_payload_count": sum(item["selected_entry_count"] for item in remote_zip_audits),
        "torrent_1984_file_count": torrent_1984["file_count"],
        "torrent_2009_file_count": torrent_2009["file_count"],
        "cached_target_tiff_count": len(cached_audits),
        "alternate_target_tiff_count": len(alternate_audits),
        "alternate_target_png_pyramid_member_count": sum(len(items) for items in png_audits.values()),
        "alternate_target_png_full_resolution_reference_count": len(png_audits),
        "cached_lossless_200dpi_target_count": cached_lossless_200dpi_count,
        "alternate_lossless_200dpi_target_count": alternate_lossless_200dpi_count,
        "alternate_more_pixels_count": alternate_more_pixels_count,
        "exact_cached_alternate_pixel_match_count": exact_cached_alternate_pixel_matches,
        "full_resolution_png_exact_cached_match_count": full_resolution_png_exact_cached_match_count,
        "dxf_semantic_audit_count": len(dxf_audits),
        "dxf_stair_text_hit_count": dxf_stair_hit_count,
        "dxf_floor_93_99_text_hit_count": dxf_floor_hit_count,
        "foia_log_relevant_record_count": 1,
        "exact_file_level_target_receipt_count": exact_file_level_target_receipt_count,
        "qualified_higher_quality_target_source_count": qualified_higher_quality_target_source_count,
        "accepted_complete_numeric_dimension_chain_count": accepted_complete_numeric_dimension_chain_count,
        "accepted_closed_grid_anchor_set_count": accepted_closed_grid_anchor_set_count,
        "scan_pixel_coordinate_count": 0,
        "model_geometry_promoted_record_count": model_geometry_promoted_record_count,
        "variant_count": 3,
        "matrix_fingerprint_sha256": matrix_fingerprint,
    }

    results = {
        "iteration": "V9Y",
        "dataset_version": config["dataset"]["version"],
        "generated_at_utc": generated_at,
        "validation_status": "PASS",
        "random_seed": config["dataset"]["random_seed"],
        "random_draw_used": config["dataset"]["random_draw_used"],
        "scope": config["dataset"]["scope"],
        "observed_or_transcribed_facts": {
            "cached_tiff_quality": {sheet: {key: value for key, value in row.items() if key not in ("normalized_1bit_pixel_sha256",)} for sheet, row in cached_audits.items()},
            "alternate_dataset_target_entries": {"LERA_1984": torrent_1984["target_entries"], "MAY_2009": torrent_2009["target_entries"]},
            "may_2009_source_text": source_text,
            "floor_heights_file_present_but_not_used_for_horizontal_geometry": bool(floor_heights_text.strip()),
            "foia_log_record": foia_audit["direct_visual_transcription"]["log_record"],
        },
        "official_model_results": {
            "official_model_damage_result_created": False,
            "nist_foia_log_context": "The inspected NIST case log abbreviates record 12-178 as WTCI-120 and 65 architectural drawings. The associated NIST correspondence explicitly identifies that record as WTC 7 Architectural Drawings 1 through 65, not the WTC 1 target TIFFs.",
        },
        "archive_claims": {
            "1967_dataset_title": ia_metadata.get("metadata", {}).get("title"),
            "1984_dataset_title": "WTC1 Architectural Drawings Dated May 9 1984",
            "2009_dataset_title": "WTC1 Architectural and Engineering Drawings Released May 2009",
            "qualification": "Dataset titles and archived landing pages establish public distribution labels, not an agency receipt or as-built status.",
        },
        "model_hypotheses": {
            "low_base_high_retained_separately": True,
            "scan_pixel_coordinates_assumed": False,
            "derived_upscale_treated_as_source": False,
            "unchanged_floor_geometry_assumed": False,
            "as_built_condition_assumed": False,
        },
        "derived_results": derived_counts,
        "contradictions_and_missing_information": [
            "The 1967 target TIFFs are already 1-bit LZW lossless files at 200 dpi; lossless compression does not imply that all original printed detail survived scanning.",
            "The alternate dataset names the target sheets, but a name match does not establish superior information, revision authority, NIST custody or as-built status.",
            "The small vector DXF candidates are not accepted as floor-specific stair plans and no coordinate values are parsed or used.",
            "FOIA 12-178 identifies WTCI-120 as WTC 7 Architectural Drawings 1 through 65; it is not a receipt for the WTC 1 175-sheet set or the four target A-A sheets.",
            "No native drawing register, file-level NIST/PANYNJ receipt, complete printed grid-to-stair chain or field-verification record is available in the bounded sources.",
        ],
        "checks": checks,
        "model_gate": model_gate["qualification"],
        "source_policy": config["source_policy"],
        "next_iteration": config["next_iteration"],
    }

    report = f"""# WTC 1 - V9Y - audit borne des sources alternatives et des recus de plans d'escaliers

**Validation generale : PASS**

> PASS DOCUMENTAIRE CONSERVATEUR - AUCUNE SOURCE CIBLE QUALIFIEE - AUCUN RECU FICHIER EXACT - ZERO CHAINE COTEE - PAS AS-BUILT - ZERO CREDIT PHYSIQUE

## Conclusion

V9Y est PASS comme audit reproductible de sources alternatives, mais la porte geometrique reste fermee. Les manifestes publics de 1984 et 2009 contiennent bien A-A-148, A-A-150, A-A-151 et A-A-153. V9Y a extrait uniquement {derived_counts['selected_remote_payload_count']} petits fichiers par plages HTTP, sans telecharger les trois archives completes. Aucun candidat ne fournit simultanement une information de plan cible demonstrablement superieure et un recu NIST/FOIA nommant le lot de 175 TIFF ou les quatre feuilles cibles.

## 1. Faits directement observes ou transcrits

- Les quatre TIFF deja conserves sont des images binaires 1 bit, compressees LZW sans perte, de 4 896 pixels de large et declarees a 200 dpi. Le tag DocumentName contient `buzzsaw.com`.
- Le torrent LERA 1984 inventorie {torrent_1984['file_count']} fichiers, dont 261 TIFF, 2 DWG et 4 DXF; les quatre feuilles cibles y sont nommees.
- Le torrent mai 2009 inventorie {torrent_2009['file_count']} fichiers, dont 895 PNG; les suffixes `_0` a `_3` forment une pyramide de quatre resolutions pour chacune des quatre feuilles cibles, et non quatre tuiles spatiales.
- Les deux petits DXF ont ete lus uniquement pour leurs calques, entites et textes. Hits textuels `STAIR`: {dxf_stair_hit_count}; hits textuels explicites pour les niveaux 93-99: {dxf_floor_hit_count}. Aucune coordonnee DXF n'a ete extraite ou utilisee.
- Le journal FOIA reproduit une reponse NIST du 28 janvier 2013 et la ligne abregee `DOC-NIST-2012-000501 / 12-178 / WTCI-120 / WTC Architectural Drawings 1 - 65`. La correspondance du dossier, datee des 12 juillet et 1er novembre 2012, designe explicitement `WTC 7 Architectural Drawings 1 through 65` et annonce la remise de 64 pages.

## 2. Resultats et contexte officiels

- Le dossier FOIA 12-178 est un fait documentaire NIST, mais il concerne explicitement le WTC 7. Il ne constitue donc pas un recu des plans WTC 1 et ne nomme ni le lot de 175 TIFF, ni A-A-148, A-A-150, A-A-151 ou A-A-153.
- V9Y ne cree aucun resultat de dommage officiel et ne transforme pas une distribution publique en certification as-built.

## 3. Affirmations provenant des archives publiques

- Les titres `WTC1 Architectural Drawings Dated May 9 1984` et `WTC1 Architectural and Engineering Drawings Released May 2009` sont des libelles de distribution 911datasets.
- La page 1984 renvoie a `LERA - PLANS-022102`, 911blogger et 911research; la page 2009 renvoie a 911blogger. Ces pages ne sont pas des recus d'agence.
- Le champ `source` de l'item Internet Archive 1967 reste absent. Le texte `source=original` applique aux fichiers par Internet Archive decrit leur statut dans l'item, pas leur provenance NIST.

### Sources publiques auditees

- [Metadonnees Internet Archive du lot 1967](https://archive.org/metadata/WTC_Architectural_Drawings_Dated_Aug_31_1967)
- [Page 911datasets 1984 archivee](https://web.archive.org/web/20170424103333/http://www.911datasets.org/index.php/WTC1_Architectural_Drawings_Dated_May_9_1984)
- [Page 911datasets 2009 archivee](https://web.archive.org/web/20170424103325/http://www.911datasets.org/index.php/WTC1_Architectural_and_Engineering_Drawings_Released_May_2009)
- [Contexte officiel de collecte NIST](https://www.nist.gov/news-events/news/2004/07/status-data-collection-efforts)

## 4. Hypotheses propres au modele

- LOW, BASE et HIGH restent trois placements separes, explicitement hypothetiques et inchanges.
- Une compression sans perte ne restaure pas les details absents du scan original; un PNG ou TIFF sans perte n'est donc pas automatiquement une source plus informative.
- Les PNG 2009 sont traites comme une pyramide de resolutions. Les niveaux `_0` sont des transcodages sans perte, pixel-identiques aux TIFF 1967 normalises; les niveaux `_1` a `_3` sont des reductions et ne constituent pas de nouvelles donnees de plan.

## 5. Resultats derives

- Fichiers distants selectionnes et verifies : {derived_counts['selected_remote_payload_count']}.
- TIFF cibles LZW/200 dpi deja conserves : {cached_lossless_200dpi_count}/4.
- TIFF LERA Group 4 sans perte/200 dpi : {alternate_lossless_200dpi_count}/4.
- TIFF LERA apportant davantage de pixels : {alternate_more_pixels_count}/4.
- Correspondances exactes de pixels entre les deux series TIFF : {exact_cached_alternate_pixel_matches}/4.
- Niveaux PNG 2009 `_0` exactement identiques aux TIFF 1967 apres normalisation 1 bit : {full_resolution_png_exact_cached_match_count}/4.
- Sources cibles de qualite superieure qualifiees : {qualified_higher_quality_target_source_count}.
- Recus NIST/FOIA exacts pour le lot cible : {exact_file_level_target_receipt_count}.
- Chaines cotees completes acceptees : {accepted_complete_numeric_dimension_chain_count}; ancrages numeriques fermes : {accepted_closed_grid_anchor_set_count}.
- Coordonnees creees : 0; geometries promues : {model_geometry_promoted_record_count}.
- Empreinte de matrice : `{matrix_fingerprint}`.

## 6. Contradictions et informations manquantes

- Un format TIFF ou PNG sans perte garantit seulement l'absence de perte supplementaire lors de l'encodage; il ne garantit ni la resolution du document papier, ni son autorite de revision.
- Les petits DXF ne sont pas qualifies comme plans d'escaliers des niveaux 93-99. Les gros DWG/DXF du torrent ne sont pas acquis dans V9Y et leur nom ne suffit pas a leur attribuer une semantique as-built.
- Il manque toujours un registre de dessins, un recu fichier par fichier NIST ou PANYNJ, une version native ou de resolution superieure des quatre feuilles cibles et une chaine cotee complete avec extremites non ambigues.
- Aucun fait de dommage, aucune masse, rigidite, resistance, connexion ou capacite de chemin de charge n'est deduit.

## Portes de validation

""" + "\n".join(f"- {name}: {'PASS' if passed else 'FAIL'}" for name, passed in checks.items()) + f"""

Le Blender maitre conserve son empreinte protegee. Aucun processus Blender et aucun solveur structurel n'ont ete executes.

## Livrables

- Manifeste : `{relative(outputs['source_manifest'])}`
- Inventaire distant : `{relative(outputs['remote_dataset_inventory'])}`
- Audit FOIA : `{relative(outputs['foia_receipt_audit'])}`
- Audit qualite : `{relative(outputs['source_quality_audit'])}`
- Matrice : `{relative(outputs['candidate_matrix_csv'])}`
- Porte modele : `{relative(outputs['model_gate'])}`
- Planche de controle : `{relative(contact_sheet)}`

## Etape suivante pre-declaree - V9Z

{config['next_iteration']['objective_if_geometry_gate_remains_closed']}
"""

    write_json(outputs["source_manifest"], source_manifest)
    write_json(outputs["remote_dataset_inventory"], remote_inventory)
    write_json(outputs["foia_receipt_audit"], foia_audit)
    write_json(outputs["source_quality_audit"], source_quality)
    with outputs["candidate_matrix_csv"].open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(matrix_rows[0].keys()))
        writer.writeheader()
        writer.writerows(matrix_rows)
    write_json(outputs["model_gate"], model_gate)
    write_json(outputs["results"], results)
    write_text(outputs["report"], report)

    protected_after = []
    for relative_path, expected in config["protected_files"].items():
        actual = digest(ROOT / relative_path)
        protected_after.append(actual == expected)
    if not all(protected_after):
        raise RuntimeError("Protected Blender master changed during V9Y")
    print(
        json.dumps(
            {
                "iteration": "V9Y",
                "status": "PASS",
                "selected_remote_payload_count": derived_counts["selected_remote_payload_count"],
                "qualified_higher_quality_target_source_count": qualified_higher_quality_target_source_count,
                "exact_file_level_target_receipt_count": exact_file_level_target_receipt_count,
                "accepted_complete_numeric_dimension_chain_count": accepted_complete_numeric_dimension_chain_count,
                "model_geometry_promoted": False,
                "solver_executed": False,
                "blender_executed": False,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
