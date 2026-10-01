#!/usr/bin/env python3
"""V9S - bounded qualitative registration of WTC 1 Floor 95 stairwell footprints.

This iteration digitizes only source-visible shapes from two NIST figures.  It
does not create metric as-built geometry and assigns no physical or mechanical
property.  The source PDFs and all prior validated artifacts are read-only.
"""

from __future__ import annotations

import csv
import hashlib
import itertools
import json
import math
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from PIL import Image, ImageDraw, ImageFont
from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "wtc1_simulation_v8/data/v9s_stairwell_footprint_registration.json"
WARNING = (
    "V9S - ENVELOPPES QUALITATIVES - PAS DE COORDONNEES AS-BUILT - "
    "PAS DE VALIDATION PHYSIQUE"
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def resolve_map(mapping: dict[str, str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for relative_path, expected_hash in mapping.items():
        path = ROOT / relative_path
        exists = path.is_file()
        observed = sha256(path) if exists else None
        rows.append(
            {
                "path": relative_path,
                "exists": exists,
                "size_bytes": path.stat().st_size if exists else None,
                "expected_sha256": expected_hash,
                "observed_sha256": observed,
                "pass": exists and observed == expected_hash,
            }
        )
    return rows


def normalize_text(value: str) -> str:
    return " ".join(value.lower().replace("\u00ad", "").split())


def compact_text(value: str) -> str:
    """Remove PDF extraction spacing while retaining letters and digits."""
    return "".join(character for character in value.lower().replace("\u00ad", "") if character.isalnum())


def verify_pdf_anchors(anchors: list[dict[str, Any]]) -> list[dict[str, Any]]:
    readers: dict[str, PdfReader] = {}
    rows: list[dict[str, Any]] = []
    for anchor in anchors:
        source = anchor["source"]
        if source not in readers:
            readers[source] = PdfReader(str(ROOT / source))
        page_number = int(anchor["pdf_page"])
        reader = readers[source]
        page_valid = 1 <= page_number <= len(reader.pages)
        extracted = reader.pages[page_number - 1].extract_text() or "" if page_valid else ""
        text = normalize_text(extracted)
        compact = compact_text(extracted)
        terms = []
        for term in anchor["required_terms"]:
            normalized = normalize_text(term)
            compact_term = compact_text(term)
            present = normalized in text or compact_term in compact
            terms.append(
                {
                    "term": term,
                    "present": present,
                    "matching_rule": "normalized_whitespace_or_compact_alphanumeric",
                }
            )
        rows.append(
            {
                "source": source,
                "pdf_page": page_number,
                "printed_page": anchor["printed_page"],
                "figure": anchor["figure"],
                "page_valid": page_valid,
                "required_terms": terms,
                "pass": page_valid and all(item["present"] for item in terms),
            }
        )
    return rows


def find_pdftoppm() -> Path:
    discovered = shutil.which("pdftoppm")
    candidates = [
        Path(discovered) if discovered else None,
        Path.home()
        / ".cache/codex-runtimes/codex-primary-runtime/dependencies/native/poppler/Library/bin/pdftoppm.exe",
    ]
    for candidate in candidates:
        if candidate and candidate.is_file():
            return candidate
    raise FileNotFoundError("pdftoppm introuvable dans PATH ou dans le runtime local Codex")


def render_page(
    pdftoppm: Path,
    source: Path,
    page_number: int,
    dpi: int,
    output_path: Path,
) -> dict[str, Any]:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    prefix = output_path.with_suffix("")
    command = [
        str(pdftoppm),
        "-f",
        str(page_number),
        "-l",
        str(page_number),
        "-r",
        str(dpi),
        "-png",
        "-singlefile",
        str(source),
        str(prefix),
    ]
    completed = subprocess.run(command, check=False, capture_output=True, text=True)
    if completed.returncode != 0 or not output_path.is_file():
        raise RuntimeError(
            f"Echec du rendu {source.name} p.{page_number}: "
            f"code={completed.returncode}; stderr={completed.stderr.strip()}"
        )
    with Image.open(output_path) as image:
        size = list(image.size)
    return {
        "source": rel(source),
        "pdf_page": page_number,
        "renderer": str(pdftoppm),
        "dpi": dpi,
        "output": rel(output_path),
        "size_px": size,
        "sha256": sha256(output_path),
    }


def crop_image(source: Path, box: list[int], output: Path) -> dict[str, Any]:
    with Image.open(source) as image:
        cropped = image.convert("RGB").crop(tuple(box))
        output.parent.mkdir(parents=True, exist_ok=True)
        cropped.save(output, format="PNG")
        size = list(cropped.size)
    return {
        "source_render": rel(source),
        "crop_box_px": box,
        "output": rel(output),
        "size_px": size,
        "sha256": sha256(output),
    }


def normalize_point(
    point: Iterable[float], rectangle: Iterable[float], canvas: Iterable[float]
) -> list[float]:
    x, y = point
    x0, y0, x1, y1 = rectangle
    width, height = canvas
    return [
        round((x - x0) / (x1 - x0) * width, 3),
        round((y - y0) / (y1 - y0) * height, 3),
    ]


def normalize_polygon(
    polygon: list[list[float]], rectangle: list[float], canvas: list[float]
) -> list[list[float]]:
    return [normalize_point(point, rectangle, canvas) for point in polygon]


def polygon_bounds(polygon: list[list[float]]) -> dict[str, float]:
    xs = [point[0] for point in polygon]
    ys = [point[1] for point in polygon]
    return {
        "min_x": round(min(xs), 3),
        "min_y": round(min(ys), 3),
        "max_x": round(max(xs), 3),
        "max_y": round(max(ys), 3),
    }


def polygon_centroid(polygon: list[list[float]]) -> list[float]:
    return [
        round(sum(point[0] for point in polygon) / len(polygon), 3),
        round(sum(point[1] for point in polygon) / len(polygon), 3),
    ]


def coordinate_error_bound(
    coordinate: float,
    lower: float,
    upper: float,
    extent: float,
    outline_uncertainty: float,
    reference_uncertainty: float,
) -> float:
    nominal = (coordinate - lower) / (upper - lower) * extent
    deviations: list[float] = []
    for point_sign, lower_sign, upper_sign in itertools.product((-1.0, 1.0), repeat=3):
        varied_coordinate = coordinate + point_sign * outline_uncertainty
        varied_lower = lower + lower_sign * reference_uncertainty
        varied_upper = upper + upper_sign * reference_uncertainty
        if varied_upper <= varied_lower:
            continue
        varied = (varied_coordinate - varied_lower) / (varied_upper - varied_lower) * extent
        deviations.append(abs(varied - nominal))
    return max(deviations)


def polygon_uncertainty(
    polygon: list[list[float]],
    rectangle: list[float],
    canvas: list[float],
    outline_uncertainty: float,
    reference_uncertainty: float,
) -> dict[str, float]:
    x0, y0, x1, y1 = rectangle
    width, height = canvas
    x_error = max(
        coordinate_error_bound(point[0], x0, x1, width, outline_uncertainty, reference_uncertainty)
        for point in polygon
    )
    y_error = max(
        coordinate_error_bound(point[1], y0, y1, height, outline_uncertainty, reference_uncertainty)
        for point in polygon
    )
    return {
        "x_common_px": round(x_error, 3),
        "y_common_px": round(y_error, 3),
        "worst_axis_common_px": round(max(x_error, y_error), 3),
        "method": "interval_extremes_for_outline_point_and_both_core_reference_edges",
    }


def expanded_union_envelope(
    polygons: list[list[list[float]]], uncertainties: list[dict[str, float]], canvas: list[int]
) -> tuple[list[list[float]], dict[str, float]]:
    bounds = [polygon_bounds(polygon) for polygon in polygons]
    ux = max(item["x_common_px"] for item in uncertainties)
    uy = max(item["y_common_px"] for item in uncertainties)
    min_x = max(0.0, min(item["min_x"] for item in bounds) - ux)
    min_y = max(0.0, min(item["min_y"] for item in bounds) - uy)
    max_x = min(float(canvas[0]), max(item["max_x"] for item in bounds) + ux)
    max_y = min(float(canvas[1]), max(item["max_y"] for item in bounds) + uy)
    envelope = [
        [round(min_x, 3), round(min_y, 3)],
        [round(max_x, 3), round(min_y, 3)],
        [round(max_x, 3), round(max_y, 3)],
        [round(min_x, 3), round(max_y, 3)],
    ]
    return envelope, {"x_common_px": round(ux, 3), "y_common_px": round(uy, 3)}


def load_font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    names = [
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/calibrib.ttf" if bold else "C:/Windows/Fonts/calibri.ttf",
    ]
    for name in names:
        if Path(name).is_file():
            return ImageFont.truetype(name, size=size)
    return ImageFont.load_default()


def draw_warning(draw: ImageDraw.ImageDraw, width: int, text: str = WARNING) -> None:
    font_size = max(12, min(25, width // 42))
    font = load_font(font_size, bold=True)
    bbox = draw.textbbox((0, 0), text, font=font)
    while bbox[2] - bbox[0] > width - 20 and font_size > 10:
        font_size -= 1
        font = load_font(font_size, bold=True)
        bbox = draw.textbbox((0, 0), text, font=font)
    height = bbox[3] - bbox[1] + 18
    draw.rectangle((0, 0, width, height), fill=(15, 15, 15))
    draw.text((10, 8), text, fill=(255, 220, 30), font=font)


def annotate_source_crop(
    crop_path: Path,
    output_path: Path,
    title: str,
    core_rectangle: list[int],
    stairs: dict[str, Any],
    missing_note: str | None = None,
    display_height: int | None = None,
) -> None:
    with Image.open(crop_path) as source_image:
        image = source_image.convert("RGB")
    if display_height is not None:
        image = image.crop((0, 0, image.width, min(display_height, image.height)))
    draw = ImageDraw.Draw(image, "RGBA")
    draw_warning(draw, image.width)
    title_font = load_font(27, bold=True)
    label_font = load_font(24, bold=True)
    draw.rectangle((8, 56, min(image.width - 8, 650), 98), fill=(255, 255, 255, 225))
    draw.text((18, 64), title, fill=(0, 0, 0, 255), font=title_font)
    draw.rectangle(tuple(core_rectangle), outline=(0, 105, 255, 255), width=5)
    colors = {"A": (230, 40, 40, 255), "B": (20, 145, 55, 255), "C": (185, 60, 210, 255)}
    for stair, entry in stairs.items():
        polygon = entry.get("polygon_px")
        if not polygon:
            continue
        points = [tuple(point) for point in polygon]
        color = colors[stair]
        draw.polygon(points, fill=(*color[:3], 45), outline=color)
        draw.line(points + [points[0]], fill=color, width=5)
        min_x = min(point[0] for point in points)
        min_y = min(point[1] for point in points)
        draw.rectangle((min_x - 3, min_y - 31, min_x + 94, min_y - 2), fill=(255, 255, 255, 230))
        draw.text((min_x + 2, min_y - 30), stair, fill=color, font=label_font)
    if missing_note:
        note_font = load_font(21, bold=True)
        text_box = (10, image.height - 68, image.width - 10, image.height - 10)
        draw.rectangle(text_box, fill=(255, 248, 210, 235), outline=(170, 90, 0, 255), width=3)
        draw.text((20, image.height - 57), missing_note, fill=(120, 50, 0, 255), font=note_font)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path, format="PNG")


def to_overlay_point(point: list[float], margin: int) -> tuple[int, int]:
    return int(round(point[0] + margin)), int(round(point[1] + margin))


def draw_normalized_overlay(
    output_path: Path,
    normalized: dict[str, Any],
    envelopes: dict[str, Any],
    metrics: dict[str, Any],
) -> None:
    canvas_extent = 1000
    margin = 100
    image = Image.new("RGB", (1200, 1260), "white")
    draw = ImageDraw.Draw(image, "RGBA")
    draw_warning(draw, image.width)
    title_font = load_font(28, bold=True)
    legend_font = load_font(20, bold=False)
    draw.text(
        (margin, 53),
        "Inscription normalisee sur les reperes visibles du noyau (1000 x 1000 px)",
        fill=(0, 0, 0, 255),
        font=title_font,
    )
    draw.rectangle(
        (margin, margin, margin + canvas_extent, margin + canvas_extent),
        outline=(20, 20, 20, 255),
        width=3,
    )
    for index in range(1, 10):
        pos = margin + index * 100
        draw.line((pos, margin, pos, margin + canvas_extent), fill=(190, 190, 190, 100), width=1)
        draw.line((margin, pos, margin + canvas_extent, pos), fill=(190, 190, 190, 100), width=1)

    stair_colors = {"A": (225, 45, 45, 255), "B": (25, 145, 60, 255), "C": (175, 55, 205, 255)}
    for stair, entry in envelopes["stairs"].items():
        color = stair_colors[stair]
        polygon = [to_overlay_point(point, margin) for point in entry["polygon_common_px"]]
        draw.polygon(polygon, fill=(*color[:3], 28), outline=(*color[:3], 180))
        draw.line(polygon + [polygon[0]], fill=(*color[:3], 190), width=3)

    source_styles = {
        "figure_5_2": {"suffix": "Fig. 5-2", "width": 5},
        "figure_9_124": {"suffix": "Fig. 9-124", "width": 2},
    }
    for source_name, source in normalized.items():
        for stair, entry in source["stairs"].items():
            polygon = entry.get("polygon_common_px")
            if not polygon:
                continue
            color = stair_colors[stair]
            points = [to_overlay_point(point, margin) for point in polygon]
            width = source_styles[source_name]["width"]
            draw.line(points + [points[0]], fill=color, width=width)
            center = to_overlay_point(entry["centroid_common_px"], margin)
            draw.ellipse((center[0] - 4, center[1] - 4, center[0] + 4, center[1] + 4), fill=color)

    legend_y = 1118
    draw.text((margin, legend_y), "Trait epais : Figure 5-2 | trait fin : Figure 9-124 | plage pale : enveloppe", fill=(0, 0, 0), font=legend_font)
    legend_y += 29
    for stair in ("A", "B", "C"):
        color = stair_colors[stair]
        status = envelopes["stairs"][stair]["status"]
        distance = metrics[stair].get("centroid_distance_common_px")
        detail = f"ecart centroide={distance:.1f} px" if distance is not None else "une seule figure"
        draw.rectangle((margin, legend_y + 3, margin + 18, legend_y + 21), fill=color)
        draw.text((margin + 28, legend_y), f"{stair}: {detail}; {status}", fill=(0, 0, 0), font=legend_font)
        legend_y += 28
    image.save(output_path, format="PNG")


def make_contact_sheet(paths: list[tuple[str, Path]], output_path: Path) -> None:
    tile_width = 760
    tile_height = 610
    image = Image.new("RGB", (1580, 1325), (235, 235, 235))
    draw = ImageDraw.Draw(image)
    draw_warning(draw, image.width)
    title_font = load_font(25, bold=True)
    positions = [(20, 65), (800, 65), (410, 700)]
    for (title, path), (x, y) in zip(paths, positions):
        with Image.open(path) as source:
            tile = source.convert("RGB")
            tile.thumbnail((tile_width, tile_height - 42), Image.Resampling.LANCZOS)
        draw.rectangle((x, y, x + tile_width, y + tile_height), fill="white", outline=(40, 40, 40), width=2)
        draw.text((x + 10, y + 7), title, fill=(0, 0, 0), font=title_font)
        paste_x = x + (tile_width - tile.width) // 2
        paste_y = y + 40 + (tile_height - 42 - tile.height) // 2
        image.paste(tile, (paste_x, paste_y))
    image.save(output_path, format="PNG")


def write_metrics_csv(path: Path, metrics: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "stair",
        "figure_5_2_visible",
        "figure_9_124_visible",
        "cross_figure_comparable",
        "centroid_distance_common_px",
        "distance_gate_common_px",
        "distance_gate_pass",
        "envelope_status",
        "metric_as_built_geometry",
        "mechanical_credit",
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for stair in ("A", "B", "C"):
            writer.writerow({key: metrics[stair].get(key) for key in fields})


def main() -> int:
    config = read_json(CONFIG_PATH)
    generated_at = utc_now()
    outputs = {name: ROOT / value for name, value in config["outputs"].items()}
    figure_dir = outputs["figure_directory"]
    figure_dir.mkdir(parents=True, exist_ok=True)

    regression_checks = resolve_map(config["regression_files"])
    source_checks = resolve_map(config["source_files"])
    anchor_checks = verify_pdf_anchors(config["pdf_anchors"])

    pdftoppm = find_pdftoppm()
    render_rows: dict[str, dict[str, Any]] = {}
    crop_rows: dict[str, dict[str, Any]] = {}
    crop_paths: dict[str, Path] = {}
    for figure_name, filename in (
        ("figure_5_2", "ncstar1-7_figure_5-2_page112.png"),
        ("figure_9_124", "ncstar1-2b_figure_9-124_page165.png"),
    ):
        spec = config["rendering"][figure_name]
        render_path = figure_dir / filename
        render_row = render_page(
            pdftoppm,
            ROOT / spec["source"],
            int(spec["pdf_page"]),
            int(config["rendering"]["resolution_dpi"]),
            render_path,
        )
        render_row["expected_size_px"] = spec["expected_page_size_px"]
        render_row["size_pass"] = render_row["size_px"] == spec["expected_page_size_px"]
        render_rows[figure_name] = render_row
        crop_path = figure_dir / f"{figure_name}_analysis_crop.png"
        crop_row = crop_image(render_path, spec["analysis_crop_box_px"], crop_path)
        crop_row["expected_size_px"] = spec["analysis_crop_size_px"]
        crop_row["size_pass"] = crop_row["size_px"] == spec["analysis_crop_size_px"]
        crop_rows[figure_name] = crop_row
        crop_paths[figure_name] = crop_path

    canvas = config["registration"]["common_canvas_size_px"]
    normalized: dict[str, Any] = {}
    for figure_name, source_digitization in config["digitizations"].items():
        rectangle = config["registration"]["core_reference_rectangles_px"][figure_name]
        reference_uncertainty = config["registration"]["core_reference_pick_uncertainty_px"][figure_name]
        outline_uncertainty = source_digitization["outline_pick_uncertainty_px"]
        normalized_stairs: dict[str, Any] = {}
        for stair, entry in source_digitization["stairs"].items():
            polygon = entry.get("polygon_px")
            if polygon is None:
                normalized_stairs[stair] = {
                    **entry,
                    "polygon_common_px": None,
                    "centroid_common_px": None,
                    "uncertainty_common_px": None,
                }
                continue
            normalized_polygon = normalize_polygon(polygon, rectangle, canvas)
            uncertainty = polygon_uncertainty(
                polygon,
                rectangle,
                canvas,
                outline_uncertainty,
                reference_uncertainty,
            )
            normalized_stairs[stair] = {
                **entry,
                "polygon_common_px": normalized_polygon,
                "bounds_common_px": polygon_bounds(normalized_polygon),
                "centroid_common_px": polygon_centroid(normalized_polygon),
                "uncertainty_common_px": uncertainty,
            }
        normalized[figure_name] = {
            "source_semantics": source_digitization["source_semantics"],
            "core_reference_rectangle_px": rectangle,
            "outline_pick_uncertainty_px": outline_uncertainty,
            "core_reference_pick_uncertainty_px": reference_uncertainty,
            "stairs": normalized_stairs,
        }

    gate_distance = float(config["registration"]["inter_figure_centroid_distance_gate_common_px"])
    metrics: dict[str, Any] = {}
    envelopes: dict[str, Any] = {
        "iteration": config["iteration"],
        "generated_at_utc": generated_at,
        "coordinate_system": "QUALITATIVE_CORE_NORMALIZED_PIXEL_CANVAS",
        "common_canvas_size_px": canvas,
        "physical_scale_assigned": False,
        "stairs": {},
    }
    for stair in ("A", "B", "C"):
        first = normalized["figure_5_2"]["stairs"][stair]
        second = normalized["figure_9_124"]["stairs"][stair]
        first_visible = first["polygon_common_px"] is not None
        second_visible = second["polygon_common_px"] is not None
        comparable = first_visible and second_visible
        distance: float | None = None
        if comparable:
            c1 = first["centroid_common_px"]
            c2 = second["centroid_common_px"]
            distance = round(math.dist(c1, c2), 3)
            envelope_polygon, expansion = expanded_union_envelope(
                [first["polygon_common_px"], second["polygon_common_px"]],
                [first["uncertainty_common_px"], second["uncertainty_common_px"]],
                canvas,
            )
            envelope_status = "TWO_FIGURE_QUALITATIVE_UNION_WITH_BOUNDED_DIGITIZATION_ERROR"
            contributing_sources = ["figure_5_2", "figure_9_124"]
        else:
            envelope_polygon, expansion = expanded_union_envelope(
                [first["polygon_common_px"]], [first["uncertainty_common_px"]], canvas
            )
            envelope_status = "SINGLE_FIGURE_ONLY_NO_INTERFIGURE_BOUND"
            contributing_sources = ["figure_5_2"]
        distance_pass = distance is not None and distance <= gate_distance
        envelopes["stairs"][stair] = {
            "status": envelope_status,
            "contributing_sources": contributing_sources,
            "polygon_common_px": envelope_polygon,
            "bounds_common_px": polygon_bounds(envelope_polygon),
            "uncertainty_expansion_common_px": expansion,
            "metric_as_built_boundary": False,
            "solver_geometry_authorized": False,
            "mechanical_credit": False,
        }
        metrics[stair] = {
            "stair": stair,
            "figure_5_2_visible": first_visible,
            "figure_9_124_visible": second_visible,
            "cross_figure_comparable": comparable,
            "centroid_distance_common_px": distance,
            "distance_gate_common_px": gate_distance if comparable else None,
            "distance_gate_pass": distance_pass if comparable else None,
            "envelope_status": envelope_status,
            "metric_as_built_geometry": False,
            "mechanical_credit": False,
        }

    annotated_f52 = figure_dir / "figure_5_2_annotated.png"
    annotated_f9124 = figure_dir / "figure_9_124_floor95_annotated.png"
    overlay_path = figure_dir / "normalized_registration_overlay.png"
    contact_sheet_path = figure_dir / "v9s_contact_sheet.png"
    annotate_source_crop(
        crop_paths["figure_5_2"],
        annotated_f52,
        "NCSTAR 1-7, Figure 5-2 - etendue visible",
        config["registration"]["core_reference_rectangles_px"]["figure_5_2"],
        config["digitizations"]["figure_5_2"]["stairs"],
    )
    annotate_source_crop(
        crop_paths["figure_9_124"],
        annotated_f9124,
        "NCSTAR 1-2B, Figure 9-124 - panneau Floor 95",
        config["registration"]["core_reference_rectangles_px"]["figure_9_124"],
        config["digitizations"]["figure_9_124"]["stairs"],
        "C / repere 2 : contour ferme non recuperable sur ce panneau; aucune substitution.",
        display_height=820,
    )
    draw_normalized_overlay(overlay_path, normalized, envelopes, metrics)
    make_contact_sheet(
        [
            ("Figure 5-2 annotee", annotated_f52),
            ("Figure 9-124 / Floor 95 annotee", annotated_f9124),
            ("Comparaison normalisee", overlay_path),
        ],
        contact_sheet_path,
    )

    visible_f52 = sum(
        entry["polygon_px"] is not None for entry in config["digitizations"]["figure_5_2"]["stairs"].values()
    )
    visible_f9124 = sum(
        entry["polygon_px"] is not None for entry in config["digitizations"]["figure_9_124"]["stairs"].values()
    )
    cross_figure_count = sum(metrics[stair]["cross_figure_comparable"] for stair in metrics)
    mechanics_closed = all(
        config["gates"][key] is False
        for key in (
            "metric_as_built_solver_geometry_authorized",
            "discrete_mass_authorized",
            "stiffness_authorized",
            "strength_authorized",
            "connection_authorized",
            "load_path_credit_authorized",
            "component_damage_validation_authorized",
            "global_solver_authorized",
            "blender_physical_validation_authorized",
        )
    )
    source_policy_closed = all(
        config["source_policy"][key] is False
        for key in (
            "source_archive_read",
            "source_archive_rescanned",
            "network_access_used",
            "official_source_files_modified",
            "structural_solver_authorized",
            "blender_authorized",
            "physical_interpretation_authorized",
            "mass_assignment_authorized",
            "stiffness_assignment_authorized",
            "strength_assignment_authorized",
            "connection_assignment_authorized",
            "component_damage_validation_authorized",
        )
    )
    checks = {
        "regression_hashes": len(regression_checks) == config["gates"]["regression_hash_count_expected"]
        and all(row["pass"] for row in regression_checks),
        "source_hashes": len(source_checks) == config["gates"]["source_hash_count_expected"]
        and all(row["pass"] for row in source_checks),
        "pdf_anchors": len(anchor_checks) == config["gates"]["pdf_anchor_count_expected"]
        and all(row["pass"] for row in anchor_checks),
        "rendered_pages": len(render_rows) == config["gates"]["rendered_page_count_expected"]
        and all(row["size_pass"] for row in render_rows.values()),
        "analysis_crops": len(crop_rows) == config["gates"]["analysis_crop_count_expected"]
        and all(row["size_pass"] for row in crop_rows.values()),
        "figure_5_2_visible_count": visible_f52 == config["gates"]["figure_5_2_visible_outline_count_expected"],
        "figure_9_124_visible_count": visible_f9124 == config["gates"]["figure_9_124_visible_outline_count_expected"],
        "cross_figure_count": cross_figure_count == config["gates"]["cross_figure_visible_stair_count_expected"]
        and cross_figure_count >= config["registration"]["minimum_cross_figure_visible_stair_count"],
        "cross_figure_centroid_distances": all(
            metrics[stair]["distance_gate_pass"] for stair in metrics if metrics[stair]["cross_figure_comparable"]
        ),
        "stair_c_missing_not_guessed": normalized["figure_9_124"]["stairs"]["C"]["polygon_common_px"] is None
        and envelopes["stairs"]["C"]["status"] == "SINGLE_FIGURE_ONLY_NO_INTERFIGURE_BOUND",
        "mechanical_and_blender_gates_closed": mechanics_closed,
        "source_policy_closed": source_policy_closed,
    }
    overall_status = "PASS" if all(checks.values()) else "FAIL"

    manifest = {
        "iteration": config["iteration"],
        "generated_at_utc": generated_at,
        "status": overall_status,
        "source_archive_read": False,
        "source_archive_rescanned": False,
        "network_access_used": False,
        "regression_files": regression_checks,
        "source_files": source_checks,
        "pdf_anchors": anchor_checks,
        "renders": render_rows,
        "crops": crop_rows,
        "derived_figures": [
            {"path": rel(path), "sha256": sha256(path), "size_bytes": path.stat().st_size}
            for path in (annotated_f52, annotated_f9124, overlay_path, contact_sheet_path)
        ],
    }
    digitization_payload = {
        "iteration": config["iteration"],
        "generated_at_utc": generated_at,
        "status": overall_status,
        "method": config["registration"]["method"],
        "common_canvas_size_px": canvas,
        "physical_scale_assigned": False,
        "source_semantics_warning": (
            "Figure 5-2 and Figure 9-124 are official-model figures with different visible-outline semantics; "
            "the normalized polygons are not dimensioned as-built footprints."
        ),
        "sources": normalized,
    }
    model_gate = {
        "iteration": config["iteration"],
        "generated_at_utc": generated_at,
        "validation_status": overall_status,
        "checks": checks,
        "qualification": {
            "qualitative_two_figure_registration": overall_status == "PASS",
            "metric_as_built_geometry": False,
            "floor_95_stair_c_cross_figure_bound": False,
            "mechanical_properties": False,
            "load_path_credit": False,
            "component_damage_validation": False,
            "structural_solver": False,
            "blender_physical_validation": False,
        },
        "decision": (
            "V9S qualifies only bounded qualitative normalized envelopes for A and B, and a single-figure "
            "source-visible envelope for C. It does not qualify solver geometry or any physical mechanism."
        ),
    }
    results = {
        "iteration": config["iteration"],
        "dataset_version": config["dataset"]["version"],
        "generated_at_utc": generated_at,
        "validation_status": overall_status,
        "random_seed": config["dataset"]["random_seed"],
        "random_draw_used": config["dataset"]["random_draw_used"],
        "scope": config["dataset"]["scope"],
        "observed_or_transcribed_facts": {
            "figure_5_2_visible_stair_count": visible_f52,
            "figure_9_124_floor_95_visible_marker_count": visible_f9124,
            "figure_9_124_floor_95_stair_c_closed_outline_recoverable": False,
        },
        "official_model_results": {
            "both_figures_are_nist_model_visualizations": True,
            "independent_as_built_measurements": False,
        },
        "archive_claims_used": [],
        "model_hypotheses": {
            "core_rectangle_axis_normalization": True,
            "physical_scale": None,
            "missing_stair_c_outline_imputed": False,
        },
        "derived_results": {
            "common_canvas_size_px": canvas,
            "cross_figure_visible_stair_count": cross_figure_count,
            "metrics": metrics,
            "qualitative_envelopes": envelopes["stairs"],
        },
        "contradictions_and_missing_information": [
            "Stair C / marker 2 has no recoverable closed outline in the Figure 9-124 Floor 95 panel.",
            "The two figures have different visible-outline semantics and neither supplies dimensioned as-built coordinates.",
            "Both figures are outputs of official models, not independent event measurements.",
        ],
        "checks": checks,
        "model_gate": model_gate["qualification"],
        "source_policy": config["source_policy"],
        "next_iteration": config["next_iteration"],
    }

    write_json(outputs["source_manifest"], manifest)
    write_json(outputs["digitization"], digitization_payload)
    write_json(outputs["envelopes"], envelopes)
    write_metrics_csv(outputs["metrics_csv"], metrics)
    write_json(outputs["model_gate"], model_gate)
    write_json(outputs["results"], results)

    report_lines = [
        "# WTC 1 - V9S - inscription qualitative bornee des emprises d'escaliers au niveau 95",
        "",
        f"**Validation generale : {overall_status}**",
        "",
        "> V9S - ENVELOPPES QUALITATIVES - PAS DE COORDONNEES AS-BUILT - PAS DE VALIDATION PHYSIQUE",
        "",
        "## Portee",
        "",
        "V9S conserve les regressions V8U a V9R et inscrit deux figures NIST sur un canevas commun de 1000 x 1000 pixels, en utilisant uniquement des reperes visibles du contour du noyau. L'operation sert a borner des positions qualitatives; elle ne cree ni plan as-built metrique, ni geometrie solveur, ni propriete mecanique.",
        "",
        "## 1. Faits directement observes ou transcrits",
        "",
        "- NCSTAR 1-7, Figure 5-2 (page PDF 112, page imprimee 74) montre au niveau 95 trois emprises visibles etiquetees Stairwell A, C et B sur le panneau propre avant superposition des dommages.",
        "- NCSTAR 1-2B, Figure 9-124 (pages PDF 164-165, pages imprimees 346-347) presente la perturbation des escaliers; sur le panneau Floor 95, les boites numerotees 1 et 3 sont recuperables comme contours fermes.",
        "- Le contour ferme du repere 2 / escalier C n'est pas recuperable sur ce panneau Floor 95. Il n'est ni dessine par extrapolation ni remplace par un autre etage.",
        "",
        "## 2. Resultats d'un modele officiel",
        "",
        "Les deux figures sont des visualisations de modeles NIST. Elles ne constituent pas deux mesures independantes de la geometrie reelle. La Figure 5-2 montre une etendue d'escalier dans un plan modele; la Figure 9-124 montre des reperes numerotes superposes a un etat de dommage modele.",
        "",
        "## 3. Affirmations provenant des archives locales",
        "",
        "Aucune affirmation documentaire issue de l'archive source n'est employee dans V9S. L'archive n'a ete ni ouverte ni rescanee; seules les deux copies officielles deja presentes dans l'espace de travail ont ete lues en lecture seule.",
        "",
        "## 4. Hypotheses propres au modele",
        "",
        "- Les rectangles de reference visibles du noyau sont normalises independamment sur les axes X et Y.",
        "- Une erreur de pointage en pixels est declaree pour chaque contour et chaque bord du rectangle de reference. Les extremes de ces intervalles sont propages vers le canevas commun.",
        "- Aucune echelle physique, rotation as-built, masse, rigidite, resistance, connexion ou chemin de charge n'est infere.",
        "",
        "## 5. Resultats derives",
        "",
        f"- Deux escaliers sur trois sont comparables entre figures, conformement au minimum predeclare ({cross_figure_count}/2).",
        f"- Escalier A : ecart entre centroides = {metrics['A']['centroid_distance_common_px']:.3f} px communs, seuil qualitatif = {gate_distance:.1f} px, porte franchie = {str(metrics['A']['distance_gate_pass']).upper()}.",
        f"- Escalier B : ecart entre centroides = {metrics['B']['centroid_distance_common_px']:.3f} px communs, seuil qualitatif = {gate_distance:.1f} px, porte franchie = {str(metrics['B']['distance_gate_pass']).upper()}.",
        "- Les enveloppes A et B sont l'union rectangulaire conservative des deux contours normalises, elargie par la pire incertitude de pointage propagee sur chaque axe.",
        "- L'enveloppe C provient uniquement de la Figure 5-2 et porte le statut SINGLE_FIGURE_ONLY_NO_INTERFIGURE_BOUND.",
        "",
        "Ces nombres sont des pixels normalises derives. Ils ne sont pas des pieds, des metres, des coordonnees de noeuds ou une validation d'endommagement.",
        "",
        "## 6. Contradictions et informations manquantes",
        "",
        "- La seconde figure ne permet pas de fermer l'emprise de C au niveau 95.",
        "- Les semantiques graphiques different entre les deux figures; une superposition n'autorise donc pas un indicateur de recouvrement interprete physiquement.",
        "- Aucun plan as-built cote des trois emprises au niveau 95 n'est qualifie par cette iteration.",
        "",
        "## Portes de validation",
        "",
    ]
    for name, passed in checks.items():
        report_lines.append(f"- {name}: {'PASS' if passed else 'FAIL'}")
    report_lines.extend(
        [
            "",
            "Toutes les portes de masse, rigidite, resistance, connexion, chemin de charge, dommage composant, solveur global et validation physique Blender restent fermees.",
            "",
            "## Livrables",
            "",
            f"- Manifeste : `{rel(outputs['source_manifest'])}`",
            f"- Numerisation : `{rel(outputs['digitization'])}`",
            f"- Enveloppes : `{rel(outputs['envelopes'])}`",
            f"- Mesures : `{rel(outputs['metrics_csv'])}`",
            f"- Porte modele : `{rel(outputs['model_gate'])}`",
            f"- Planche de controle : `{rel(contact_sheet_path)}`",
            "",
            "## Etape suivante predeclaree - V9T",
            "",
            config["next_iteration"]["objective"],
            "",
        ]
    )
    outputs["report"].parent.mkdir(parents=True, exist_ok=True)
    outputs["report"].write_text("\n".join(report_lines), encoding="utf-8", newline="\n")

    print(
        json.dumps(
            {
                "iteration": config["iteration"],
                "validation_status": overall_status,
                "cross_figure_visible_stair_count": cross_figure_count,
                "centroid_distance_A_common_px": metrics["A"]["centroid_distance_common_px"],
                "centroid_distance_B_common_px": metrics["B"]["centroid_distance_common_px"],
                "stair_C_cross_figure_bound": False,
                "report": rel(outputs["report"]),
                "contact_sheet": rel(contact_sheet_path),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if overall_status == "PASS" else 2


if __name__ == "__main__":
    sys.exit(main())
