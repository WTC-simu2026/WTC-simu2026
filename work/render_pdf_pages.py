from __future__ import annotations

import argparse
from pathlib import Path

import pypdfium2 as pdfium


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("pages", nargs="+", type=int, help="One-based PDF page numbers")
    parser.add_argument("--scale", type=float, default=2.5)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    pdf = pdfium.PdfDocument(str(args.pdf))
    for page_no in args.pages:
        page = pdf[page_no - 1]
        image = page.render(scale=args.scale).to_pil()
        dest = args.output / f"{args.pdf.stem}_p{page_no:03d}.png"
        image.save(dest)
        print(dest.resolve())


if __name__ == "__main__":
    main()
