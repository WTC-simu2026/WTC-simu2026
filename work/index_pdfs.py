from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from pathlib import Path

from pypdf import PdfReader


TERMS = {
    "ncstar": 20,
    "nist": 14,
    "fema 403": 12,
    "structural steel": 12,
    "column schedule": 18,
    "core column": 12,
    "perimeter column": 12,
    "exterior column": 10,
    "steel grade": 14,
    "yield strength": 12,
    "cross-section": 8,
    "cross section": 8,
    "buckling": 10,
    "plastic hinge": 10,
    "energy absorption": 10,
    "force-displacement": 12,
    "force displacement": 12,
    "world trade center": 3,
    "wtc 1": 5,
    "wtc1": 5,
    "floor 94": 8,
    "floor 95": 8,
    "floor 96": 8,
    "floor 97": 8,
    "floor 98": 8,
    "floor 99": 8,
}


def file_hash(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).lower()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    args.output.mkdir(parents=True, exist_ok=True)
    text_dir = args.output / "text"
    text_dir.mkdir(exist_ok=True)

    pdfs = sorted(args.source.rglob("*.pdf"), key=lambda p: str(p).lower())
    rows: list[dict[str, object]] = []
    seen_hashes: dict[str, str] = {}

    for idx, path in enumerate(pdfs, start=1):
        doc_id = f"L{idx:03d}"
        cached_text_path = text_dir / f"{doc_id}.txt"
        row: dict[str, object] = {
            "id": doc_id,
            "path": str(path),
            "relative_path": str(path.relative_to(args.source)),
            "size_bytes": path.stat().st_size,
            "sha256": "",
            "duplicate_of": "",
            "pages": 0,
            "text_chars": 0,
            "score": 0,
            "matched_terms": "",
            "error": "",
        }
        try:
            if cached_text_path.exists():
                cached = cached_text_path.read_text(encoding="utf-8", errors="replace")
                header, _, full_text = cached.partition("\n===== PAGE 1 =====")
                full_text = "\n===== PAGE 1 =====" + full_text if full_text else cached
                hash_match = re.search(r"^SHA256: ([0-9a-f]{64})$", header, re.MULTILINE)
                digest = hash_match.group(1) if hash_match else file_hash(path)
                row["pages"] = len(re.findall(r"^===== PAGE \d+ =====$", full_text, re.MULTILINE))
            else:
                digest = file_hash(path)
                reader = PdfReader(str(path), strict=False)
                row["pages"] = len(reader.pages)
                chunks: list[str] = []
                for page_no, page in enumerate(reader.pages, start=1):
                    try:
                        page_text = page.extract_text() or ""
                    except Exception as exc:  # keep indexing the rest of the file
                        page_text = f"[PAGE EXTRACTION ERROR: {type(exc).__name__}: {exc}]"
                    chunks.append(f"\n\n===== PAGE {page_no} =====\n\n{page_text}")
                full_text = "".join(chunks)
                cached_text_path.write_text(
                    f"SOURCE: {path}\nSHA256: {digest}\n" + full_text,
                    encoding="utf-8",
                    errors="replace",
                )
            row["sha256"] = digest
            if digest in seen_hashes:
                row["duplicate_of"] = seen_hashes[digest]
            else:
                seen_hashes[digest] = doc_id
            row["text_chars"] = len(full_text)
            normalized = normalize(full_text)
            matched = []
            score = 0
            for term, weight in TERMS.items():
                count = normalized.count(term)
                if count:
                    matched.append(f"{term}:{count}")
                    score += weight * min(count, 20)
            filename_norm = normalize(path.name)
            if re.search(r"wtc|world.?trade|tower|twin|fema|nist|ncstar|steel|collapse", filename_norm):
                score += 15
            row["score"] = score
            row["matched_terms"] = "; ".join(matched)
        except Exception as exc:
            row["error"] = f"{type(exc).__name__}: {exc}"
        rows.append(row)
        print(f"{idx}/{len(pdfs)} {doc_id} score={row['score']} {path.name}", flush=True)

    fields = list(rows[0]) if rows else []
    with (args.output / "manifest.csv").open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    (args.output / "manifest.json").write_text(
        json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    ranked = sorted(rows, key=lambda r: (-int(r["score"]), str(r["relative_path"])))
    with (args.output / "ranked.json").open("w", encoding="utf-8") as f:
        json.dump(ranked, f, ensure_ascii=False, indent=2)
    print(json.dumps({"pdf_count": len(rows), "errors": sum(bool(r["error"]) for r in rows), "duplicates": sum(bool(r["duplicate_of"]) for r in rows)}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
