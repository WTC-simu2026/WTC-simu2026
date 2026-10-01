from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

from pypdf import PdfReader


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    if len(sys.argv) < 3:
        raise SystemExit("usage: extract_pdf_text.py OUTPUT_DIR PDF...")

    output_dir = Path(sys.argv[1])
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest: list[dict[str, object]] = []

    for raw_path in sys.argv[2:]:
        path = Path(raw_path)
        reader = PdfReader(path)
        pages: list[str] = []
        page_lengths: list[int] = []
        for number, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            page_lengths.append(len(text))
            pages.append(f"\n===== PAGE {number} =====\n{text}")

        text_path = output_dir / f"{path.stem}.txt"
        text_path.write_text("".join(pages), encoding="utf-8")
        manifest.append(
            {
                "source_path": str(path),
                "source_size_bytes": path.stat().st_size,
                "source_sha256": sha256(path),
                "page_count": len(reader.pages),
                "page_text_characters": page_lengths,
                "extracted_text_path": str(text_path),
                "metadata": {str(k): str(v) for k, v in (reader.metadata or {}).items()},
            }
        )

    (output_dir / "pdf_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
