"""Extract only WTC 1 impact-zone WF properties from the official AISC v16.0H workbook.

The source workbook is read-only.  The derived JSON records the selected edition
for every shape.  NIST NCSTAR 1-2A states that the sixth-edition AISC manual was
used, except 14WF455–14WF730, which came from LRFD third edition.  Because the
v16.0H database does not expose a sixth-edition row in its main database, ASD7 is
kept as an explicit historical proxy for shapes below 455 lb/ft.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "work" / "external_sources" / "aisc-shapes-database-v160h.xlsx"
SCHEDULE = ROOT / "wtc1_3d_v4" / "data" / "core_sections_impact_zone.json"
OUTPUT = ROOT / "wtc1_simulation_v8" / "data" / "aisc_historic_wf_properties.json"


def schedule_to_aisc(shape: str) -> str:
    match = re.fullmatch(r"(12|14)WF([0-9.]+)", shape)
    if not match:
        raise ValueError(shape)
    return f"W{match.group(1)}X{match.group(2)}"


def normalize(value: object) -> str:
    text = re.sub(r"[^A-Z0-9X]", "", str(value).upper())
    return text[:-1] if text.endswith("A") else text


def main() -> None:
    schedule = json.loads(SCHEDULE.read_text(encoding="utf-8"))
    requested = sorted(
        {
            segment["shape"]
            for column in schedule["columns"]
            for segment in column["segments"].values()
            if segment["kind"] == "WF"
        }
    )
    mapping = {schedule_to_aisc(shape): shape for shape in requested}
    frame = pd.read_excel(SOURCE, sheet_name="Database v16.0H")
    frame = frame.copy()
    frame["_normalized"] = frame["Designation"].map(normalize)

    output_rows: dict[str, object] = {}
    for aisc_name, schedule_name in mapping.items():
        candidates = frame[frame["_normalized"] == aisc_name]
        if candidates.empty:
            raise RuntimeError(f"Profil absent de la base AISC: {aisc_name}")
        weight = float(re.search(r"([0-9.]+)$", schedule_name).group(1))
        required_edition = "LRFD3" if schedule_name.startswith("14WF") and weight >= 455.0 else "ASD7"
        selected = candidates[candidates["Edition"].astype(str) == required_edition]
        if selected.empty:
            raise RuntimeError(f"Édition {required_edition} absente pour {aisc_name}")
        row = selected.iloc[0]
        output_rows[schedule_name] = {
            "aisc_designation": str(row["Designation"]),
            "edition": required_edition,
            "selection_status": (
                "NIST_SPECIFIED_LRFD3_FOR_14WF455_TO_14WF730"
                if required_edition == "LRFD3"
                else "ASD7_PROXY_FOR_NIST_REPORTED_AISC_6TH_EDITION"
            ),
            "area_in2": float(row["A "]),
            "depth_in": float(row["d"]),
            "web_thickness_in": float(row["tw"]),
            "flange_width_in": float(row["bf"]),
            "flange_thickness_in": float(row["tf"]),
            "ix_in4": float(row["Ix"]),
            "iy_in4": float(row["Iy"]),
            "rx_in": float(row["rx"]),
            "ry_in": float(row["ry"]),
        }

    payload = {
        "dataset": {
            "name": "AISC historic WF properties used in WTC 1 V8B",
            "version": "1.0.0",
            "source_workbook": str(SOURCE),
            "source_url": "https://cloud.aisc.org/biggie_bin/aisc-shapes-database-v160h.xlsx",
            "source_sheet": "Database v16.0H",
            "source_sha256": "66D0A8028EAA2ED50AB3C114A37F279D80BF09FAEA0AEA2A49483F9F21527A53",
            "selection_basis": "NCSTAR 1-2A section 2.6.5; ASD7 is an explicit proxy where v16.0H has no sixth-edition row.",
            "warning": "ASD7 proxy rows must be replaced if NIST Shape Property Table.xls or a digitized sixth-edition table becomes available."
        },
        "shapes": dict(sorted(output_rows.items())),
    }
    OUTPUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"{len(output_rows)} profils extraits -> {OUTPUT}")


if __name__ == "__main__":
    main()
