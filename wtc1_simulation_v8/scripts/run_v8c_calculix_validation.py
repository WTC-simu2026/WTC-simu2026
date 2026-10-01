"""V8C: validate CalculiX beam-column elastic buckling against Euler.

This is deliberately a solver-verification stage, not a WTC collapse model.
Each historic W section is represented by a square beam section whose weak-axis
second moment of area is exactly the tabulated Iy.  Its area is therefore not
physical; the construction is valid only for the elastic Euler eigenvalue check.
"""

from __future__ import annotations

import json
import math
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
V8 = ROOT / "wtc1_simulation_v8"
INPUT_JSON = V8 / "output" / "resultats_wtc1_v8b.json"
RUN_DIR = V8 / "calculix_validation"
OUTPUT_JSON = V8 / "output" / "resultats_wtc1_v8c_validation.json"
REPORT = V8 / "output" / "rapport_wtc1_v8c_validation.md"
CCX = Path(r"C:\Program Files\FreeCAD 1.1\bin\ccx.exe")

IN_TO_MM = 25.4
IN4_TO_MM4 = IN_TO_MM**4
STORY_HEIGHT_MM = 12.0 * 12.0 * IN_TO_MM  # 12 ft, explicit V8C assumption
E_MPA = 206_000.0
NU = 0.30
ELEMENT_COUNT = 24
ELEMENT_TYPE = "B31"


def make_deck(job: str, iy_in4: float) -> tuple[str, float, float]:
    """Return CalculiX deck, exact Iy in mm4, and equivalent square side."""
    iy_mm4 = iy_in4 * IN4_TO_MM4
    side_mm = (12.0 * iy_mm4) ** 0.25
    dz = STORY_HEIGHT_MM / ELEMENT_COUNT
    lines = [
        "*HEADING",
        f"V8C elastic Euler validation: {job}",
        "*NODE",
    ]
    for i in range(ELEMENT_COUNT + 1):
        lines.append(f"{i + 1},0.,0.,{i * dz:.9f}")
    lines.extend([f"*ELEMENT,TYPE={ELEMENT_TYPE},ELSET=COL"])
    for i in range(ELEMENT_COUNT):
        lines.append(f"{i + 1},{i + 1},{i + 2}")
    lines.extend(
        [
            "*NSET,NSET=BOTTOM",
            "1",
            "*NSET,NSET=TOP",
            str(ELEMENT_COUNT + 1),
            "*MATERIAL,NAME=STEEL",
            "*ELASTIC",
            f"{E_MPA:.9f},{NU:.6f}",
            "*BEAM SECTION,ELSET=COL,MATERIAL=STEEL,SECTION=RECT",
            f"{side_mm:.9f},{side_mm:.9f}",
            "0.,1.,0.",
            "*STEP",
            "*BUCKLE",
            "6,0.01",
            "*BOUNDARY",
            "BOTTOM,1,3",
            "BOTTOM,6,6",
            "TOP,1,2",
            "*CLOAD",
            f"{ELEMENT_COUNT + 1},3,-1.",
            "*NODE FILE",
            "U",
            "*END STEP",
            "",
        ]
    )
    return "\n".join(lines), iy_mm4, side_mm


def parse_eigenvalues(dat_path: Path) -> list[float]:
    text = dat_path.read_text(encoding="utf-8", errors="replace")
    values: list[float] = []
    # CalculiX prints one line per factor after an "EIGENVALUE OUTPUT" heading.
    active = False
    for line in text.splitlines():
        if "EIGENVALUE OUTPUT" in line.upper():
            active = True
            continue
        if not active:
            continue
        match = re.match(r"\s*\d+\s+([-+0-9.Ee]+)\s*$", line)
        if match:
            values.append(float(match.group(1)))
        elif values and line.strip() and not line.lstrip().startswith("MODE"):
            # End once the numeric table has been consumed.
            break
    if not values:
        # Fallback for version-specific formatting.
        for match in re.finditer(r"(?im)^\s*\d+\s+([-+0-9.Ee]+)\s*$", text):
            value = float(match.group(1))
            if value > 0:
                values.append(value)
    return values


def main() -> None:
    if not CCX.exists():
        raise FileNotFoundError(CCX)
    source = json.loads(INPUT_JSON.read_text(encoding="utf-8"))
    sections = source["floor_inputs"]["93"]["sections"]
    selected = ["501", "605", "705", "804"]
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    rows = []
    for column in selected:
        section = sections[column]
        job = f"v8c_f93_c{column}_{section['designation'].lower()}"
        deck, iy_mm4, side_mm = make_deck(job, float(section["iy_in4"]))
        inp = RUN_DIR / f"{job}.inp"
        inp.write_text(deck, encoding="ascii")
        result = subprocess.run(
            [str(CCX), job],
            cwd=RUN_DIR,
            capture_output=True,
            text=True,
            check=False,
        )
        dat = RUN_DIR / f"{job}.dat"
        eigenvalues = parse_eigenvalues(dat) if dat.exists() else []
        positive = [value for value in eigenvalues if value > 0]
        ccx_n = min(positive) if positive else None
        euler_n = math.pi**2 * E_MPA * iy_mm4 / STORY_HEIGHT_MM**2
        # B31 is a first-order shear-deformable beam.  For the artificial
        # square section, compare it with the Timoshenko column correction in
        # addition to Euler.  This also explains why the stockiest square is a
        # few percent below the Euler value.
        area_equiv_mm2 = side_mm**2
        shear_modulus_mpa = E_MPA / (2.0 * (1.0 + NU))
        shear_kappa = 5.0 / 6.0
        timoshenko_n = euler_n / (
            1.0 + euler_n / (shear_kappa * shear_modulus_mpa * area_equiv_mm2)
        )
        euler_error_pct = None if ccx_n is None else 100.0 * (ccx_n / euler_n - 1.0)
        timoshenko_error_pct = (
            None if ccx_n is None else 100.0 * (ccx_n / timoshenko_n - 1.0)
        )
        rows.append(
            {
                "floor": 93,
                "column": int(column),
                "designation": section["designation"],
                "iy_in4": section["iy_in4"],
                "equivalent_square_side_mm": side_mm,
                "length_mm": STORY_HEIGHT_MM,
                "e_mpa": E_MPA,
                "euler_n": euler_n,
                "timoshenko_n": timoshenko_n,
                "calculix_first_positive_eigenvalue_n": ccx_n,
                "relative_error_vs_euler_pct": euler_error_pct,
                "relative_error_vs_timoshenko_pct": timoshenko_error_pct,
                "all_parsed_eigenvalues": eigenvalues,
                "calculix_returncode": result.returncode,
                "stdout_tail": result.stdout[-1500:],
                "stderr_tail": result.stderr[-1500:],
                "input_file": str(inp),
                "dat_file": str(dat),
            }
        )

    payload = {
        "model": "WTC1_V8C_CALCULIX_ELASTIC_BUCKLING_VALIDATION",
        "scope": "solver verification only; not a WTC collapse result",
        "assumptions": {
            "member_length_mm": STORY_HEIGHT_MM,
            "end_conditions": "ideal pinned-pinned for flexure; bottom torsional rotation restrained to remove rigid mode",
            "elastic_modulus_mpa": E_MPA,
            "element": f"{ELEMENT_TYPE}, 24 elements, shear deformable",
            "section_representation": "equivalent square matching tabulated weak-axis Iy only; area and local section response are not physical",
            "reference_load_n": 1.0,
        },
        "cases": rows,
    }
    OUTPUT_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    lines = [
        "# WTC 1 — V8C : validation CalculiX du flambement élastique",
        "",
        "## Portée",
        "",
        "Cette étape vérifie uniquement que la chaîne CalculiX reproduit la charge critique d’Euler d’une colonne bi-articulée. Elle ne constitue ni une simulation d’impact, ni une simulation d’effondrement.",
        "",
        "La section rectangulaire équivalente est construite pour reproduire exactement `Iy` de chaque profil historique. Son aire n’est pas celle du profil W : elle ne peut donc servir qu’à cette vérification élastique de solveur.",
        "",
        "## Résultats",
        "",
        "| Colonne | Profil | Euler (MN) | Timoshenko (MN) | CalculiX (MN) | Écart vs Timoshenko |",
        "|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        ccx_text = "échec" if row["calculix_first_positive_eigenvalue_n"] is None else f"{row['calculix_first_positive_eigenvalue_n'] / 1e6:.4f}"
        err_text = "—" if row["relative_error_vs_timoshenko_pct"] is None else f"{row['relative_error_vs_timoshenko_pct']:+.3f} %"
        lines.append(
            f"| {row['column']} | {row['designation']} | {row['euler_n'] / 1e6:.4f} | {row['timoshenko_n'] / 1e6:.4f} | {ccx_text} | {err_text} |"
        )
    lines.extend(
        [
            "",
            "## Décision",
            "",
            "La chaîne est acceptée pour le sous-modèle V8C si les quatre erreurs absolues par rapport à la solution de colonne de Timoshenko restent inférieures à 1 %. La comparaison à Euler est conservée comme contrôle secondaire. L’étape suivante devra utiliser de vraies géométries de sections ou une composition de rectangles, avec imperfections, liaisons et comportement matériel dépendant de la température.",
            "",
        ]
    )
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
