"""V8C-bis: represent historic W shapes as three rectangular CalculiX beams.

The web and two flanges share the same reference-line nodes.  Flange offsets
place their centroids at the historic shape depth.  This checks whether a
lightweight beam representation can carry actual area and section geometry
before it is used in nonlinear force-displacement studies.
"""

from __future__ import annotations

import json
import math
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
V8 = ROOT / "wtc1_simulation_v8"
V8B = V8 / "output" / "resultats_wtc1_v8b.json"
AISC = V8 / "data" / "aisc_historic_wf_properties.json"
RUN_DIR = V8 / "calculix_w_section_validation"
OUT = V8 / "output" / "resultats_wtc1_v8c_w_sections.json"
REPORT = V8 / "output" / "rapport_wtc1_v8c_w_sections.md"
CCX = Path(r"C:\Program Files\FreeCAD 1.1\bin\ccx.exe")

IN_TO_MM = 25.4
IN4_TO_MM4 = IN_TO_MM**4
LENGTH_MM = 3657.6
E_MPA = 206_000.0
NU = 0.3
N_ELEMS = 24


def eigs(path: Path) -> list[float]:
    text = path.read_text(encoding="utf-8", errors="replace")
    values: list[float] = []
    active = False
    for line in text.splitlines():
        upper = line.upper()
        if "EIGENVALUE OUTPUT" in upper or "BUCKLING   F A C T O R" in upper or "B U C K L I N G   F A C T O R" in upper:
            active = True
            continue
        if active:
            m = re.match(r"\s*\d+\s+([-+0-9.Ee]+)\s*$", line)
            if m:
                values.append(float(m.group(1)))
            elif values and line.strip():
                break
    if not values:
        for match in re.finditer(r"(?im)^\s*\d+\s+([-+0-9.Ee]+)\s*$", text):
            value = float(match.group(1))
            if value > 0:
                values.append(value)
    return values


def section_geometry(shape: dict[str, float | str]) -> dict[str, float]:
    d = float(shape["depth_in"]) * IN_TO_MM
    tw = float(shape["web_thickness_in"]) * IN_TO_MM
    bf = float(shape["flange_width_in"]) * IN_TO_MM
    tf = float(shape["flange_thickness_in"]) * IN_TO_MM
    hw = d - 2.0 * tf
    area = 2.0 * bf * tf + tw * hw
    iy = 2.0 * tf * bf**3 / 12.0 + hw * tw**3 / 12.0
    y = d / 2.0 - tf / 2.0
    ix = 2.0 * (bf * tf**3 / 12.0 + bf * tf * y**2) + tw * hw**3 / 12.0
    return {"d": d, "tw": tw, "bf": bf, "tf": tf, "hw": hw, "area": area, "ix": ix, "iy": iy, "flange_y": y}


def deck(job: str, geom: dict[str, float]) -> str:
    dz = LENGTH_MM / N_ELEMS
    lines = ["*HEADING", f"V8C composite W validation {job}", "*NODE"]
    for i in range(N_ELEMS + 1):
        lines.append(f"{i + 1},0.,0.,{i * dz:.9f}")
    for name, offset in (("WEB", 0), ("TOP", N_ELEMS), ("BOTTOM", 2 * N_ELEMS)):
        lines.append(f"*ELEMENT,TYPE=B31,ELSET={name}")
        for i in range(N_ELEMS):
            lines.append(f"{offset + i + 1},{i + 1},{i + 2}")
    lines.extend(
        [
            "*NSET,NSET=BASE",
            "1",
            "*NSET,NSET=TOPNODE",
            str(N_ELEMS + 1),
            "*MATERIAL,NAME=STEEL",
            "*ELASTIC",
            f"{E_MPA},{NU}",
            "*BEAM SECTION,ELSET=WEB,MATERIAL=STEEL,SECTION=RECT",
            f"{geom['tw']:.9f},{geom['hw']:.9f}",
            "1.,0.,0.",
            f"*BEAM SECTION,ELSET=TOP,MATERIAL=STEEL,SECTION=RECT,OFFSET2={-geom['flange_y'] / geom['tf']:.9f}",
            f"{geom['bf']:.9f},{geom['tf']:.9f}",
            "1.,0.,0.",
            f"*BEAM SECTION,ELSET=BOTTOM,MATERIAL=STEEL,SECTION=RECT,OFFSET2={geom['flange_y'] / geom['tf']:.9f}",
            f"{geom['bf']:.9f},{geom['tf']:.9f}",
            "1.,0.,0.",
            "*STEP",
            "*BUCKLE",
            "6,0.01",
            "*BOUNDARY",
            "BASE,1,3",
            "BASE,6,6",
            "TOPNODE,1,2",
            "*CLOAD",
            f"{N_ELEMS + 1},3,-1.",
            "*NODE FILE",
            "U",
            "*END STEP",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    model = json.loads(V8B.read_text(encoding="utf-8"))
    props = json.loads(AISC.read_text(encoding="utf-8"))["shapes"]
    selected = ["501", "605", "705", "804"]
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    rows = []
    for column in selected:
        sec = model["floor_inputs"]["93"]["sections"][column]
        shape = props[sec["designation"]]
        geom = section_geometry(shape)
        job = f"v8c_w_f93_c{column}_{sec['designation'].lower()}"
        inp = RUN_DIR / f"{job}.inp"
        inp.write_text(deck(job, geom), encoding="ascii")
        result = subprocess.run([str(CCX), job], cwd=RUN_DIR, capture_output=True, text=True, check=False)
        values = eigs(RUN_DIR / f"{job}.dat") if (RUN_DIR / f"{job}.dat").exists() else []
        positive = [v for v in values if v > 0]
        ccx = min(positive) if positive else None
        euler_geom = math.pi**2 * E_MPA * geom["iy"] / LENGTH_MM**2
        euler_tab = math.pi**2 * E_MPA * float(shape["iy_in4"]) * IN4_TO_MM4 / LENGTH_MM**2
        rows.append(
            {
                "column": int(column),
                "designation": sec["designation"],
                "tabulated_area_mm2": float(shape["area_in2"]) * IN_TO_MM**2,
                "built_area_mm2": geom["area"],
                "tabulated_iy_mm4": float(shape["iy_in4"]) * IN4_TO_MM4,
                "built_iy_mm4": geom["iy"],
                "tabulated_ix_mm4": float(shape["ix_in4"]) * IN4_TO_MM4,
                "built_ix_mm4": geom["ix"],
                "euler_from_built_iy_n": euler_geom,
                "euler_from_tabulated_iy_n": euler_tab,
                "calculix_first_positive_n": ccx,
                "ccx_vs_euler_built_pct": None if ccx is None else 100.0 * (ccx / euler_geom - 1.0),
                "built_vs_tabulated_area_pct": 100.0 * (geom["area"] / (float(shape["area_in2"]) * IN_TO_MM**2) - 1.0),
                "built_vs_tabulated_iy_pct": 100.0 * (geom["iy"] / (float(shape["iy_in4"]) * IN4_TO_MM4) - 1.0),
                "built_vs_tabulated_ix_pct": 100.0 * (geom["ix"] / (float(shape["ix_in4"]) * IN4_TO_MM4) - 1.0),
                "returncode": result.returncode,
                "eigenvalues": values,
                "input_file": str(inp),
            }
        )
    payload = {
        "model": "WTC1_V8C_COMPOSITE_W_SECTION_VALIDATION",
        "scope": "three-rectangle historic W-shape solver validation; not a collapse result",
        "representation": "web plus two flange B31 beams sharing nodes; AISC dimensions; fillets omitted",
        "cases": rows,
    }
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    md = [
        "# WTC 1 — V8C : sections W composées dans CalculiX",
        "",
        "Cette vérification utilise l’âme et les deux semelles réelles comme trois rectangles liés à la même ligne de référence. Les congés de laminage ne sont pas représentés.",
        "",
        "| Colonne | Profil | ΔA géométrique | ΔIy géométrique | ΔIx géométrique | CalculiX / Euler(Iy géom.) |",
        "|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        ccxerr = "échec" if row["ccx_vs_euler_built_pct"] is None else f"{row['ccx_vs_euler_built_pct']:+.2f} %"
        md.append(f"| {row['column']} | {row['designation']} | {row['built_vs_tabulated_area_pct']:+.2f} % | {row['built_vs_tabulated_iy_pct']:+.2f} % | {row['built_vs_tabulated_ix_pct']:+.2f} % | {ccxerr} |")
    md.extend(
        [
            "",
            "Les écarts géométriques par rapport à la table AISC proviennent principalement des congés omis et des arrondis de dimensions. Ce modèle n’est accepté pour V8C que si son premier mode est physiquement identifiable et si l’écart avec Euler calculé sur sa propre géométrie reste maîtrisé.",
            "",
        ]
    )
    REPORT.write_text("\n".join(md), encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
