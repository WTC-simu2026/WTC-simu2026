from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "wtc1_simulation_v8/data/v10l_corrected_micro_window_audit.json"


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


def abs_path(relative: str) -> Path:
    return ROOT / Path(relative)


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def verify_hash(path: Path, expected: str, label: str) -> dict[str, Any]:
    if not path.is_file():
        raise RuntimeError(f"Missing {label}: {path}")
    actual = sha256_file(path)
    if actual.lower() != expected.lower():
        raise RuntimeError(f"Hash mismatch for {label}: expected {expected}, got {actual}")
    return {"role": label, "path": rel(path), "sha256": actual, "bytes": path.stat().st_size}


def load_and_validate(config: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    if config.get("iteration") != "V10L":
        raise RuntimeError("Configuration iteration must be V10L")

    pre_cfg = config["predeclaration"]
    pre_path = abs_path(pre_cfg["path"])
    verify_hash(pre_path, pre_cfg["expected_sha256"], "v10l_predeclaration")
    pre = load_json(pre_path)
    if pre.get("predeclaration_status") != pre_cfg["required_status"]:
        raise RuntimeError("Unexpected V10L predeclaration status")
    if pre.get("document_count") != pre_cfg["required_document_count"]:
        raise RuntimeError("Unexpected predeclared document count")
    if pre.get("window_count") != pre_cfg["required_window_count"]:
        raise RuntimeError("Unexpected predeclared window count")
    if pre.get("locator_count") != pre_cfg["required_locator_count"]:
        raise RuntimeError("Unexpected predeclared locator count")
    if pre.get("aggregate_candidate_page_count") != pre_cfg["required_aggregate_candidate_page_count"]:
        raise RuntimeError("Unexpected predeclared candidate page count")
    pages = pre["window"]["candidate_pdf_pages_1_based"]
    if pages != [275, 276, 277, 278]:
        raise RuntimeError(f"Unexpected candidate pages: {pages}")
    if set(pages) & set(pre["window"]["explicitly_excluded_already_reviewed_pdf_pages_1_based"]):
        raise RuntimeError("Candidate pages overlap excluded V10K pages")

    regression_rows = [
        verify_hash(abs_path(item["path"]), item["expected_sha256"], item["role"])
        for item in config["regression_files"]
    ]
    protected_rows = [
        verify_hash(abs_path(item["path"]), item["expected_sha256"], item["role"])
        for item in config["protected_files"]
    ]

    source = config["working_copy"]
    source_path = abs_path(source["path"])
    source_row = verify_hash(source_path, source["expected_sha256"], "v10i_book5_working_copy")
    if source_path.stat().st_size != source["expected_size_bytes"]:
        raise RuntimeError("Unexpected Book 5 working-copy byte size")
    source_row["container_page_count"] = source["expected_page_count"]
    source_row["read_only_policy"] = True
    return pre, regression_rows, protected_rows + [source_row]


def get_font(size: int) -> ImageFont.ImageFont:
    for candidate in (
        Path("C:/Windows/Fonts/arial.ttf"),
        Path("C:/Windows/Fonts/segoeui.ttf"),
    ):
        if candidate.is_file():
            return ImageFont.truetype(str(candidate), size=size)
    return ImageFont.load_default()


def make_contact_sheet(page_rows: list[dict[str, Any]], output_path: Path) -> None:
    title_font = get_font(32)
    label_font = get_font(24)
    margin = 28
    gap = 22
    thumb_width = 760
    thumbnails: list[tuple[Image.Image, str]] = []
    for row in page_rows:
        with Image.open(abs_path(row["render_path"])) as source:
            image = source.convert("L")
            height = round(image.height * thumb_width / image.width)
            thumbnails.append((image.resize((thumb_width, height), Image.Resampling.LANCZOS), f"Book 5 - PDF p. {row['pdf_page_1_based']}"))

    label_height = 42
    canvas_width = margin * 2 + thumb_width * 2 + gap
    row_heights: list[int] = []
    for index in range(0, len(thumbnails), 2):
        row_heights.append(max(item[0].height for item in thumbnails[index:index + 2]) + label_height)
    canvas_height = margin + 55 + sum(row_heights) + gap * (len(row_heights) - 1) + margin
    canvas = Image.new("L", (canvas_width, canvas_height), color=255)
    draw = ImageDraw.Draw(canvas)
    draw.text((margin, 18), "V10L - micro-fenetre corrigee 5-AB3-1", fill=0, font=title_font)
    y = margin + 55
    for index, (image, label) in enumerate(thumbnails):
        column = index % 2
        x = margin + column * (thumb_width + gap)
        draw.text((x, y), label, fill=0, font=label_font)
        canvas.paste(image, (x, y + label_height))
        if column == 1 or index == len(thumbnails) - 1:
            row_index = index // 2
            y += row_heights[row_index] + gap
    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output_path, format="PNG", optimize=True)


def render_phase(config: dict[str, Any], requested_renderer: str | None) -> dict[str, Any]:
    pre, regression_rows, source_rows = load_and_validate(config)
    renderer = requested_renderer or shutil.which("pdftoppm")
    if not renderer:
        raise RuntimeError("pdftoppm not found")

    source_path = abs_path(config["working_copy"]["path"])
    page_dir = abs_path(pre["render_policy"]["individual_page_directory"])
    page_dir.mkdir(parents=True, exist_ok=True)
    page_rows: list[dict[str, Any]] = []
    total_pixels = 0
    total_bytes = 0
    for page in pre["window"]["candidate_pdf_pages_1_based"]:
        output = page_dir / f"WTCI-000016-L__p{page:04d}.png"
        prefix = output.with_suffix("")
        command = [
            str(renderer), "-f", str(page), "-l", str(page), "-singlefile",
            "-r", str(pre["render_policy"]["dpi"]), "-gray", "-png",
            str(source_path), str(prefix),
        ]
        completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
        if completed.returncode != 0 or not output.is_file():
            raise RuntimeError(f"Render failed for PDF page {page}: {completed.stderr.strip()}")
        with Image.open(output) as image:
            width, height = image.size
        pixels = width * height
        byte_count = output.stat().st_size
        if pixels > pre["render_policy"]["maximum_pixels_per_page"]:
            raise RuntimeError(f"Page {page} exceeds pixel cap")
        total_pixels += pixels
        total_bytes += byte_count
        page_rows.append({
            "document_id": "WTCI-000016-L",
            "seed_locator": "5-AB3-1",
            "pdf_page_1_based": page,
            "render_path": rel(output),
            "render_sha256": sha256_file(output),
            "width_px": width,
            "height_px": height,
            "pixels": pixels,
            "png_bytes": byte_count,
        })

    if len(page_rows) != pre["hard_aggregate_render_cap"]:
        raise RuntimeError("Rendered-page count differs from hard cap")
    if total_pixels > pre["render_policy"]["maximum_aggregate_pixels"]:
        raise RuntimeError("Aggregate pixel cap exceeded")
    if total_bytes > pre["render_policy"]["maximum_aggregate_png_bytes"]:
        raise RuntimeError("Aggregate PNG byte cap exceeded")

    contact_path = abs_path(config["outputs"]["contact_sheet"])
    make_contact_sheet(page_rows, contact_path)
    generated = utc_now()
    source_manifest = {
        "iteration": "V10L",
        "generated_at_utc": generated,
        "validation_status": "PASS",
        "predeclaration": {"path": config["predeclaration"]["path"], "sha256": sha256_file(abs_path(config["predeclaration"]["path"]))},
        "configuration": {"path": rel(CONFIG_PATH), "sha256": sha256_file(CONFIG_PATH)},
        "sources": source_rows,
        "network_access_during_page_audit": False,
        "source_archive_read": False,
        "official_sources_directory_read": False,
    }
    regression_audit = {
        "iteration": "V10L",
        "generated_at_utc": generated,
        "validation_status": "PASS",
        "verified_regression_file_count": len(regression_rows),
        "files": regression_rows,
        "protected_blender_master_unchanged": True,
    }
    candidate_manifest = {
        "iteration": "V10L",
        "generated_at_utc": generated,
        "validation_status": "PASS",
        "selection_status": pre["predeclaration_status"],
        "candidate_page_count": len(page_rows),
        "candidate_pages": page_rows,
        "excluded_already_reviewed_pages": [279, 280],
    }
    render_audit = {
        "iteration": "V10L",
        "generated_at_utc": generated,
        "validation_status": "PASS",
        "renderer": str(renderer),
        "dpi": pre["render_policy"]["dpi"],
        "color_mode": "grayscale",
        "render_invocation_count": len(page_rows),
        "rendered_unique_page_count": len(page_rows),
        "aggregate_rendered_pixels": total_pixels,
        "aggregate_rendered_png_bytes": total_bytes,
        "pages": page_rows,
        "contact_sheet": {"path": rel(contact_path), "sha256": sha256_file(contact_path), "bytes": contact_path.stat().st_size},
        "non_candidate_page_content_read_count": 0,
        "ocr_count": 0,
        "embedded_text_extraction_count": 0,
    }
    write_json(abs_path(config["outputs"]["source_manifest"]), source_manifest)
    write_json(abs_path(config["outputs"]["regression_audit"]), regression_audit)
    write_json(abs_path(config["outputs"]["candidate_page_manifest"]), candidate_manifest)
    write_json(abs_path(config["outputs"]["render_audit"]), render_audit)
    return {
        "iteration": "V10L", "phase": "render", "status": "PASS",
        "candidate_page_count": len(page_rows), "rendered_page_count": len(page_rows),
        "aggregate_rendered_pixels": total_pixels,
    }


def validate_manual(config: dict[str, Any], pages: list[int]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    manual_path = abs_path(config["manual_transcription"]["path"])
    manual = load_json(manual_path)
    if manual.get("iteration") != "V10L":
        raise RuntimeError("Manual transcription iteration must be V10L")
    records = manual.get("records", [])
    record_pages = [row.get("pdf_page_1_based") for row in records]
    if record_pages != pages:
        raise RuntimeError(f"Manual record pages must equal {pages}, got {record_pages}")
    allowed = set(config["manual_transcription"]["allowed_page_classifications"])
    list_fields = (
        "visible_document_identifiers", "visible_title_or_index_headings", "visible_tower_labels",
        "visible_floor_labels", "visible_floor_ranges", "visible_revision_or_issue_fields",
        "visible_cross_reference_locators",
    )
    for row in records:
        if row.get("page_classification") not in allowed:
            raise RuntimeError(f"Invalid page classification on page {row.get('pdf_page_1_based')}")
        for field in list_fields:
            if not isinstance(row.get(field), list):
                raise RuntimeError(f"Manual field {field} must be a list")
    return manual, records


def finalize_phase(config: dict[str, Any]) -> dict[str, Any]:
    pre, regression_rows, source_rows = load_and_validate(config)
    candidate = load_json(abs_path(config["outputs"]["candidate_page_manifest"]))
    render = load_json(abs_path(config["outputs"]["render_audit"]))
    if candidate.get("validation_status") != "PASS" or render.get("validation_status") != "PASS":
        raise RuntimeError("Render-phase outputs are not PASS")
    pages = pre["window"]["candidate_pdf_pages_1_based"]
    manual, records = validate_manual(config, pages)

    identifiers = sorted({value for row in records for value in row["visible_document_identifiers"]})
    cross_refs = sorted({value for row in records for value in row["visible_cross_reference_locators"]})
    floor_labels = sorted({str(value) for row in records for value in row["visible_floor_labels"]})
    floor_ranges = sorted({str(value) for row in records for value in row["visible_floor_ranges"]})
    found_pages = [row["pdf_page_1_based"] for row in records if "5-AB3-1" in row["visible_document_identifiers"] or "5-AB3-1" in row["visible_cross_reference_locators"]]
    found = bool(found_pages)
    explicit_floor_pages = [row["pdf_page_1_based"] for row in records if row["visible_floor_labels"] or row["visible_floor_ranges"]]
    generated = utc_now()

    manual_audit = {
        "iteration": "V10L",
        "generated_at_utc": generated,
        "validation_status": "PASS",
        "manual_transcription_path": rel(abs_path(config["manual_transcription"]["path"])),
        "manual_transcription_sha256": sha256_file(abs_path(config["manual_transcription"]["path"])),
        "record_count": len(records),
        "reviewed_pages": pages,
        "seed_locator": "5-AB3-1",
        "seed_locator_found": found,
        "seed_locator_found_pages": found_pages,
        "pages_with_explicit_floor93_99_labels": explicit_floor_pages,
        "geometry_or_dimension_transcription_count": 0,
        "ocr_count": 0,
        "embedded_text_extraction_count": 0,
    }
    locator_rows = [{
        "document_id": "WTCI-000016-L",
        "seed_locator": "5-AB3-1",
        "predicted_pdf_page_1_based": 276,
        "candidate_pages": "275|276|277|278",
        "found": "YES" if found else "NO",
        "found_pages": "|".join(str(value) for value in found_pages),
        "bounded_outcome": "FOUND_IN_CORRECTED_MICRO_WINDOW" if found else "NOT_FOUND_IN_CORRECTED_MICRO_WINDOW_NOT_GLOBAL_ABSENCE",
    }]
    floor_rows = [{
        "floor": floor,
        "explicit_label_found": "YES" if str(floor) in floor_labels else "NO",
        "explicit_range_found": "YES" if any(str(floor) in value for value in floor_ranges) else "NO",
        "requirement_closed": "NO",
        "remains_solver_blocking": "YES",
    } for floor in range(93, 100)]
    write_csv(abs_path(config["outputs"]["locator_matrix_csv"]), list(locator_rows[0]), locator_rows)
    write_csv(abs_path(config["outputs"]["floor93_99_locator_matrix_csv"]), list(floor_rows[0]), floor_rows)

    gate = {
        "iteration": "V10L",
        "generated_at_utc": generated,
        "validation_status": "PASS",
        "bounded_micro_window_gate": "PASS",
        "seed_locator_recovery_gate": "PASS" if found else "FAIL_BOUNDED_NOT_GLOBAL_ABSENCE",
        "seed_locator": "5-AB3-1",
        "seed_locator_found_pages": found_pages,
        "official_nist_chain_gate": "OPEN",
        "revision_as_built_authority_gate": "OPEN",
        "wtc1_floor93_99_applicability_gate": "OPEN",
        "requirement_closure_gate": "OPEN_0_OF_22",
        "structural_solver_readiness_gate": "CLOSED_22_BLOCKING_REQUIREMENTS",
        "physical_assignments": 0,
        "physical_validation": False,
    }
    report_lines = [
        "# WTC 1 - V10L - Micro-fenetre corrigee pour 5-AB3-1",
        "",
        "## Perimetre",
        "",
        "V10L examine uniquement les pages PDF 275 a 278 du Book 5, figees avant toute nouvelle lecture. Les pages 279 et 280 deja examinees en V10K ne sont pas relues. Aucun OCR, aucune extraction de texte integre et aucun balayage du PDF ne sont utilises.",
        "",
        "## Faits directement observes ou transcrits",
        "",
        f"- Pages examinees : {', '.join(str(value) for value in pages)}.",
        f"- Identifiants visibles : {', '.join(identifiers) if identifiers else 'aucun'}.",
        f"- Le localisateur 5-AB3-1 est {'retrouve page ' + ', '.join(str(value) for value in found_pages) if found else 'non retrouve dans la micro-fenetre'}.",
        f"- Pages portant une etiquette explicite des etages 93-99 : {', '.join(str(value) for value in explicit_floor_pages) if explicit_floor_pages else 'aucune'}.",
        "",
        "## Resultats d'un modele officiel",
        "",
        "Aucun resultat de modele officiel n'est cree ou revalide par V10L.",
        "",
        "## Affirmations provenant des archives locales",
        "",
        "Le PDF est une copie de travail V10I dont l'identite binaire est preservee. Cette identite ne certifie pas a elle seule la chaine NIST, la revision gouvernante ou le statut as-built.",
        "",
        "## Hypotheses propres au modele",
        "",
        "La prediction de la page 276 repose uniquement sur l'ordre visible 5-AB3-4 page 279 puis 5-AB3-5 page 280. Elle ne constitue pas une hypothese mecanique.",
        "",
        "## Resultats derives",
        "",
        f"- Porte de recuperation du localisateur : {'PASS' if found else 'ECHEC BORNE'}.",
        "- Exigences structurelles closes : 0/22.",
        "- Credits de geometrie, masse, rigidite, resistance, assemblage, dommage et chemin de charge : zero.",
        "",
        "## Contradictions et informations manquantes",
        "",
        "La chaine officielle NIST, la revision gouvernante, l'autorite as-built et l'applicabilite exacte aux etages 93-99 restent a etablir. Un echec borne ne prouverait pas une absence globale.",
        "",
        "## Suite",
        "",
        "V10M doit auditer les sources primaires en ligne nouvellement autorisees, notamment le rapport NIST qui relie Tower A a WTC 1 et decrit les Books 5 et 6, puis rechercher les fichiers de base de donnees et modeles structurels cites par NIST.",
    ]
    report_path = abs_path(config["outputs"]["report"])
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(report_lines) + "\n", encoding="utf-8", newline="\n")
    write_json(abs_path(config["outputs"]["manual_transcription_audit"]), manual_audit)
    write_json(abs_path(config["outputs"]["model_gate"]), gate)

    results = {
        "iteration": "V10L",
        "started_at_utc": render.get("generated_at_utc"),
        "completed_at_utc": generated,
        "validation_status": "PASS",
        "dataset": {**config["dataset"], "status": "COMPLETE_CORRECTED_MICRO_WINDOW_REVIEW"},
        "observed_or_transcribed_facts": {
            "reviewed_pages": pages,
            "visible_document_identifiers": identifiers,
            "visible_cross_reference_locators": cross_refs,
            "seed_locator_found": found,
            "seed_locator_found_pages": found_pages,
            "pages_with_explicit_floor93_99_labels": explicit_floor_pages,
        },
        "official_model_results": [],
        "archive_claims_used": ["V10I working-copy identity only"],
        "model_hypotheses": ["Page 276 prediction from observed end-of-container suffix ordering"],
        "derived_results": {"requirements_closed": 0, "requirements_solver_blocking": 22, "physical_assignments": 0},
        "contradictions_and_missing_information": [
            "Official NIST chain, governing revision, as-built authority and exact Floors 93-99 applicability remain open.",
            "No geometry, dimensions, member properties, connection law, damage state or load path is transcribed.",
        ],
        "operation_counts": {
            "candidate_page_content_read_count": 4,
            "non_candidate_page_content_read_count": 0,
            "rendered_unique_page_count": 4,
            "ocr_count": 0,
            "embedded_text_extraction_count": 0,
            "network_request_count_during_page_audit": 0,
            "source_archive_read_count": 0,
            "official_sources_read_count": 0,
            "solver_executed": False,
            "thermal_continuation_executed": False,
            "blender_executed": False,
        },
        "outputs": config["outputs"],
        "next_iteration": config["next_iteration"],
        "errors": [],
    }
    write_json(abs_path(config["outputs"]["results"]), results)

    required = [
        config["predeclaration"]["path"], rel(CONFIG_PATH), config["manual_transcription"]["path"], rel(Path(__file__)),
        config["outputs"]["source_manifest"], config["outputs"]["regression_audit"], config["outputs"]["candidate_page_manifest"],
        config["outputs"]["render_audit"], config["outputs"]["manual_transcription_audit"], config["outputs"]["locator_matrix_csv"],
        config["outputs"]["floor93_99_locator_matrix_csv"], config["outputs"]["model_gate"], config["outputs"]["report"],
        config["outputs"]["results"], config["outputs"]["contact_sheet"],
    ]
    artifact_rows = []
    missing = []
    for relative in required:
        path = abs_path(relative)
        if not path.is_file():
            missing.append(relative)
        else:
            artifact_rows.append({"path": relative, "sha256": sha256_file(path), "bytes": path.stat().st_size})
    offline = {
        "iteration": "V10L",
        "generated_at_utc": generated,
        "validation_status": "PASS" if not missing else "FAIL",
        "required_artifact_count": len(required),
        "missing_artifact_count": len(missing),
        "missing_artifacts": missing,
        "artifacts": artifact_rows,
        "working_copy_hash_unchanged_after_finalize": sha256_file(abs_path(config["working_copy"]["path"])) == config["working_copy"]["expected_sha256"],
        "v10k_regression_hashes_unchanged_after_finalize": all(sha256_file(abs_path(item["path"])) == item["expected_sha256"] for item in config["regression_files"]),
        "source_archive_read": False,
        "network_access_during_page_audit": False,
        "solver_executed": False,
        "thermal_continuation_executed": False,
        "blender_executed": False,
    }
    write_json(abs_path(config["outputs"]["offline_audit"]), offline)
    if missing:
        raise RuntimeError(f"Missing final artifacts: {missing}")
    return {
        "iteration": "V10L", "phase": "finalize", "status": "PASS",
        "candidate_page_count": len(pages), "seed_locator_found": found,
        "seed_locator_found_pages": found_pages, "requirements_closed": 0,
        "requirements_solver_blocking": 22, "next_iteration": "V10M",
    }


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Run the corrected bounded V10L Book 5 locator audit")
    parser.add_argument("--phase", choices=("render", "finalize"), required=True)
    parser.add_argument("--renderer")
    args = parser.parse_args()
    config = load_json(CONFIG_PATH)
    result = render_phase(config, args.renderer) if args.phase == "render" else finalize_phase(config)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
