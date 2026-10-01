from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
TMP_INVENTORY = ROOT / "tmp" / "pdfs" / "thermite_corpus_v1" / "inventory.json"
ASSESSMENT = OUT / "assessment.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


inventory = json.loads(TMP_INVENTORY.read_text(encoding="utf-8"))
assessment = json.loads(ASSESSMENT.read_text(encoding="utf-8"))

source_rows = list(inventory["pdfs"]) + [inventory["image"]]
assessment_by_id = {row["source_id"]: row for row in assessment["sources"]}
inventory_ids = {row["source_id"] for row in source_rows}
assessment_ids = set(assessment_by_id)
if inventory_ids != assessment_ids:
    raise SystemExit(
        f"Source ID mismatch: inventory-only={sorted(inventory_ids - assessment_ids)}, "
        f"assessment-only={sorted(assessment_ids - inventory_ids)}"
    )

verified_sources = []
for row in source_rows:
    path = Path(row["path"])
    expected_hash = row["sha256_before"]
    if not path.exists():
        if row["source_id"] != "collapse_schematic":
            raise SystemExit(f"Designated PDF missing: {path}")
        verified_sources.append(
            {
                "source_id": row["source_id"],
                "path": str(path),
                "filename": row["filename"],
                "size_bytes": row["size_bytes"],
                "sha256_initial": expected_hash,
                "sha256_final": None,
                "page_count": row.get("page_count"),
                "dimensions_px": row.get("dimensions_px"),
                "available_at_final_check": False,
                "final_verification_status": "MISSING_AT_ORIGINAL_PATH_AFTER_INITIAL_HASH_AND_VISUAL_INSPECTION",
            }
        )
        continue
    current_hash = sha256(path)
    if current_hash != expected_hash:
        raise SystemExit(f"Source changed: {path}")
    verified_sources.append(
        {
            "source_id": row["source_id"],
            "path": str(path),
            "filename": row["filename"],
            "size_bytes": row["size_bytes"],
            "sha256_initial": expected_hash,
            "sha256_final": current_hash,
            "page_count": row.get("page_count"),
            "dimensions_px": row.get("dimensions_px"),
            "available_at_final_check": True,
            "final_verification_status": "UNCHANGED",
        }
    )

generated_at = datetime.now(timezone.utc).isoformat()
source_inventory = {
    "schema_version": "1.0",
    "iteration_id": assessment["iteration_id"],
    "generated_at_utc": generated_at,
    "source_policy": "read-only; no source copied, renamed, moved, deleted, or modified",
    "pdf_count": inventory["pdf_count"],
    "image_count": inventory["image_count"],
    "pdf_page_count": sum(row.get("page_count", 0) for row in inventory["pdfs"]),
    "all_pdfs_unchanged": all(
        row["final_verification_status"] == "UNCHANGED"
        for row in verified_sources
        if row["source_id"] != "collapse_schematic"
    ),
    "all_designated_sources_available_at_final_check": all(
        row["available_at_final_check"] for row in verified_sources
    ),
    "sources": verified_sources,
}
write_json(OUT / "source_inventory.json", source_inventory)

with (OUT / "evidence_matrix.csv").open("w", encoding="utf-8-sig", newline="") as stream:
    fields = [
        "source_id",
        "title",
        "document_class",
        "provenance",
        "direct_facts",
        "author_claim",
        "assessment",
        "key_limits",
        "probative_weight",
        "simulation_effect",
        "page_refs",
        "source_sha256_initial",
        "final_verification_status",
    ]
    writer = csv.DictWriter(stream, fieldnames=fields)
    writer.writeheader()
    for source_id in [row["source_id"] for row in source_rows]:
        entry = dict(assessment_by_id[source_id])
        inv = next(row for row in verified_sources if row["source_id"] == source_id)
        entry["source_sha256_initial"] = inv["sha256_initial"]
        entry["final_verification_status"] = inv["final_verification_status"]
        writer.writerow({field: entry[field] for field in fields})

with (OUT / "claim_matrix.csv").open("w", encoding="utf-8-sig", newline="") as stream:
    fields = ["claim_id", "claim", "support", "counter_or_alternative", "status"]
    writer = csv.DictWriter(stream, fieldnames=fields)
    writer.writeheader()
    writer.writerows(assessment["claims"])

manifest_files = [
    "assessment.json",
    "build_audit.py",
    "report.md",
    "future_archive_sorting_notes.md",
    "source_inventory.json",
    "evidence_matrix.csv",
    "claim_matrix.csv",
]
missing = [name for name in manifest_files if not (OUT / name).exists()]
if missing:
    raise SystemExit(f"Missing deliverables: {missing}")

manifest = {
    "schema_version": "1.0",
    "iteration_id": assessment["iteration_id"],
    "generated_at_utc": generated_at,
    "inputs": {
        "temporary_inventory": str(TMP_INVENTORY),
        "assessment": str(ASSESSMENT),
        "existing_dust_audit": str(ROOT / "outputs" / "dust_mass_v1" / "report.md"),
    },
    "source_verification": {
        "count": len(verified_sources),
        "pdfs_unchanged": source_inventory["all_pdfs_unchanged"],
        "all_designated_sources_available_at_final_check": source_inventory[
            "all_designated_sources_available_at_final_check"
        ],
        "note": (
            "All designated sources were available and unchanged at final verification."
            if source_inventory["all_designated_sources_available_at_final_check"]
            else "The collapse schematic was hashed and visually inspected during the initial pass, then was absent from its original path at final verification. No source file was modified by this audit."
        ),
    },
    "outputs": [
        {
            "path": str(OUT / name),
            "size_bytes": (OUT / name).stat().st_size,
            "sha256": sha256(OUT / name),
        }
        for name in manifest_files
    ],
    "simulation_boundary": "No harness state, experiment registry, solver input, or Blender file modified.",
}
write_json(OUT / "run_manifest.json", manifest)

print(
    json.dumps(
        {
            "status": (
                "PASS"
                if source_inventory["all_designated_sources_available_at_final_check"]
                else "PASS_WITH_SOURCE_AVAILABILITY_NOTE"
            ),
            "verified_sources": len(verified_sources),
            "pdf_pages": source_inventory["pdf_page_count"],
            "deliverables": len(manifest_files) + 1,
            "all_pdfs_unchanged": source_inventory["all_pdfs_unchanged"],
            "all_designated_sources_available_at_final_check": source_inventory[
                "all_designated_sources_available_at_final_check"
            ],
        },
        ensure_ascii=False,
    )
)
