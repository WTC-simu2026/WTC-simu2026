"""Create the immutable IMPACT-I02G campaign synthesis from saved solver audits."""

from __future__ import annotations

import hashlib
import json
import math
import textwrap
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "wtc1_simulation_v8/output/impact_i02g_mt_coupon"
CFG = ROOT / "wtc1_simulation_v8/data/impact_i02g_mt_coupon.json"
RUNNER = ROOT / "wtc1_simulation_v8/scripts/run_impact_i02g.py"
AUDITOR = ROOT / "wtc1_simulation_v8/scripts/audit_impact_i02g.py"
PDF = ROOT / "wtc1_simulation_v8/input/impact_i02f_sources/NASA_CR_191523_2024T3_CTOA.pdf"
ACCEPTED = [
    "ELASTIC_H508_A0_R1",
    "ELASTIC_H254_A0_R2",
    "NOPROP_H254_A0_R2",
    "G15_H508_A0_R2",
    "G30_H508_A0_R2",
    "G60_H508_A0_R2",
    "G30_H254_A0_R2",
    "G30_H254_S5_R3",
]


def dump(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def relative_difference(a: float, b: float) -> float:
    return abs(a - b) / max(abs(a), abs(b), 1.0e-12)


def load(name: str, filename: str = "case_audit_r2.json") -> dict:
    return json.loads((OUTPUT / name / filename).read_text(encoding="utf-8"))


def mesh_quality(directory: Path) -> dict:
    metadata = json.loads((directory / "generation.json").read_text(encoding="utf-8"))
    nodes = metadata["nodes_mm"]
    edges = []
    areas = []
    for shell in metadata["shells"]:
        points = [nodes[node_id - 1] for node_id in shell["nodes"]]
        edges.extend(
            math.hypot(points[(index + 1) % 4][0] - points[index][0], points[(index + 1) % 4][1] - points[index][1])
            for index in range(4)
        )
        areas.append(
            0.5
            * sum(
                points[index][0] * points[(index + 1) % 4][1]
                - points[(index + 1) % 4][0] * points[index][1]
                for index in range(4)
            )
        )
    return {
        "minimum_edge_mm": min(edges),
        "maximum_edge_mm": max(edges),
        "minimum_signed_area_mm2": min(areas),
        "maximum_signed_area_mm2": max(areas),
    }


def first_advance(case: dict) -> dict | None:
    return case["advance_states"][0] if case["advance_states"] else None


def font(size: int, bold: bool = False):
    path = Path("C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf")
    return ImageFont.truetype(str(path), size) if path.exists() else ImageFont.load_default()


def centered(draw: ImageDraw.ImageDraw, xy: tuple[float, float], text: str, face, fill) -> None:
    box = draw.textbbox((0, 0), text, font=face)
    draw.text((xy[0] - (box[2] - box[0]) / 2, xy[1] - (box[3] - box[1]) / 2), text, font=face, fill=fill)


def make_figure(summary: dict, path: Path) -> None:
    image = Image.new("RGB", (1600, 960), "#f5f2ea")
    draw = ImageDraw.Draw(image)
    navy = "#17324d"
    blue = "#2b6f9f"
    red = "#b3453e"
    green = "#39765a"
    grey = "#5b6470"
    draw.text((55, 35), "IMPACT-I02G — éprouvette M(T) 2024-T3", font=font(38, True), fill=navy)
    draw.text((55, 82), "Fissure imposée, loi cohésive non calibrée — résultats numériques bornés", font=font(23), fill=grey)

    # Specimen schematic.
    draw.rounded_rectangle((55, 140, 485, 715), radius=18, fill="white", outline="#c9c3b7", width=3)
    draw.text((85, 165), "Géométrie source", font=font(27, True), fill=navy)
    cx, top, bottom, halfw = 270, 230, 630, 95
    draw.rectangle((cx - halfw, top, cx + halfw, bottom), outline=navy, width=5, fill="#d9e7f0")
    cy = (top + bottom) // 2
    crack_half_px = 32
    draw.line((cx - crack_half_px, cy, cx + crack_half_px, cy), fill=red, width=8)
    draw.line((cx - halfw, cy, cx - crack_half_px, cy), fill=green, width=3)
    draw.line((cx + crack_half_px, cy, cx + halfw, cy), fill=green, width=3)
    draw.polygon([(cx - 12, top - 20), (cx + 12, top - 20), (cx, top - 48)], fill=blue)
    draw.polygon([(cx - 12, bottom + 20), (cx + 12, bottom + 20), (cx, bottom + 48)], fill=blue)
    centered(draw, (cx, 675), "76,2 × 300 × 2,3 mm", font(22, True), navy)
    centered(draw, (cx, 705), "fissure initiale totale : 25,4 mm", font(20), red)

    # Complete-separation stress versus Gf.
    draw.rounded_rectangle((515, 140, 1545, 510), radius=18, fill="white", outline="#c9c3b7", width=3)
    draw.text((545, 165), "Pic avant/au premier pas — maillage 5,08 mm", font=font(27, True), fill=navy)
    plot = (585, 230, 1480, 450)
    draw.line((plot[0], plot[3], plot[2], plot[3]), fill=navy, width=3)
    draw.line((plot[0], plot[1], plot[0], plot[3]), fill=navy, width=3)
    for stress, label, color in [(200, "NASA ~200", "#986a24"), (230, "NASA ~230", red)]:
        y = plot[3] - stress / 250.0 * (plot[3] - plot[1])
        draw.line((plot[0], y, plot[2], y), fill=color, width=2)
        draw.text((plot[2] - 145, y - 25), label, font=font(17, True), fill=color)
    coarse = summary["coarse_gf_results"]
    for index, row in enumerate(coarse):
        x = plot[0] + 165 + index * 270
        stress = row["first_complete_separation_stress_mpa"]
        y = plot[3] - stress / 250.0 * (plot[3] - plot[1])
        draw.line((x, plot[3], x, y), fill=blue, width=55)
        centered(draw, (x, y - 24), f"{stress:.1f} MPa", font(20, True), navy)
        centered(draw, (x, plot[3] + 28), f"Gf={row['Gf_N_per_mm']:.0f}", font(20), navy)
        centered(draw, (x, plot[3] + 52), f"CTOA={row['ctoa_B_deg_at_advance']:.1f}°", font(18), grey)

    # Gate summary.
    draw.rounded_rectangle((515, 540, 1545, 900), radius=18, fill="white", outline="#c9c3b7", width=3)
    draw.text((545, 565), "Contrôles de campagne", font=font(27, True), fill=navy)
    y = 620
    labels = [
        ("Contrôle sans propagation", summary["campaign_checks"]["fine_no_propagation_control"]),
        ("Élasticité, écart de maillage ≤ 5 %", summary["campaign_checks"]["elastic_mesh_peak_stress"]),
        ("Orientation 0° / 5°, seuil ≤ 10 %", summary["campaign_checks"]["g30_orientation_onset"]),
        ("Maillage 5,08 / 2,54 mm, seuil ≤ 10 %", summary["campaign_checks"]["g30_mesh_onset"]),
        ("CTOA fin après Δa ≥ 2,3 mm", summary["campaign_checks"]["fine_ctoa_domain_reached"]),
        ("Résidu énergie et travail de section ≤ 1 %", summary["campaign_checks"]["energy_and_section_work"]),
    ]
    for label, passed in labels:
        color = green if passed else red
        symbol = "PASS" if passed else "ÉCHEC"
        draw.rounded_rectangle((550, y - 5, 660, y + 31), radius=7, fill=color)
        centered(draw, (605, y + 13), symbol, font(16, True), "white")
        draw.text((685, y), label, font=font(21), fill=navy)
        y += 48
    draw.rounded_rectangle((55, 740, 485, 945), radius=18, fill="white", outline="#c9c3b7", width=3)
    draw.text((80, 755), "Conclusion limitée", font=font(24, True), fill=navy)
    conclusion = [
        ("Modèle énergétiquement propre et peu sensible à 5°.", grey),
        ("Propagation discrète et non convergée avec la maille.", grey),
        ("Aucun résultat avion–façade ou historique autorisé.", red),
    ]
    y = 800
    for line, color in conclusion:
        wrapped = textwrap.wrap(line, width=49)
        draw.text((78, y), "• " + wrapped[0], font=font(15), fill=color)
        for continuation in wrapped[1:]:
            y += 19
            draw.text((94, y), continuation, font=font(15), fill=color)
        y += 25
    image.save(path)


def main() -> None:
    cfg = json.loads(CFG.read_text(encoding="utf-8"))
    cases = {name: load(name) for name in ACCEPTED}
    elastic_coarse = cases["ELASTIC_H508_A0_R1"]
    elastic_fine = cases["ELASTIC_H254_A0_R2"]
    g30_coarse = cases["G30_H508_A0_R2"]
    g30_fine = cases["G30_H254_A0_R2"]
    g30_skew = cases["G30_H254_S5_R3"]
    no_prop = cases["NOPROP_H254_A0_R2"]
    coarse_gf_results = []
    for gf, name in [(15.0, "G15_H508_A0_R2"), (30.0, "G30_H508_A0_R2"), (60.0, "G60_H508_A0_R2")]:
        case = cases[name]
        advance = first_advance(case)
        coarse_gf_results.append({
            "case": name,
            "Gf_N_per_mm": gf,
            "first_complete_separation_stress_mpa": case["complete_separation_onset"]["maximum_remote_stress_before_or_at_onset_mpa"],
            "first_extension_mm": advance["mean_extension_mm"],
            "ctoa_B_deg_at_advance": advance["ctoa_B_deg"],
            "ctoa_2B_deg_at_advance": advance["ctoa_2B_deg"],
        })
    elastic_difference = relative_difference(elastic_coarse["peak_remote_stress_mpa"], elastic_fine["peak_remote_stress_mpa"])
    mesh_onset_difference = relative_difference(
        g30_coarse["complete_separation_onset"]["maximum_remote_stress_before_or_at_onset_mpa"],
        g30_fine["complete_separation_onset"]["maximum_remote_stress_before_or_at_onset_mpa"],
    )
    orientation_onset_difference = relative_difference(
        g30_fine["complete_separation_onset"]["maximum_remote_stress_before_or_at_onset_mpa"],
        g30_skew["complete_separation_onset"]["maximum_remote_stress_before_or_at_onset_mpa"],
    )
    maximum_energy = max(case["maximum_global_energy_residual_fraction"] for case in cases.values())
    maximum_section_work = max(case["section_work_to_external_error_fraction"] for case in cases.values())
    maximum_ke_ie = max(case["kinetic_to_internal_at_peak_stress"] for case in cases.values())
    maximum_mass_error = max(case["maximum_mass_error_fraction"] for case in cases.values())
    fine_ctoa_available = bool(g30_fine["settled_ctoa_states"])
    checks = {
        "accepted_case_gates": all(case["all_case_gates_pass"] for case in cases.values()),
        "source_geometry_exact": all(
            math.isclose(value, cfg["geometry"][key], rel_tol=0, abs_tol=1.0e-9)
            for key, value in [("width_mm", 76.2), ("length_mm", 300.0), ("thickness_mm", 2.3), ("initial_total_crack_length_mm", 25.4)]
        ),
        "two_meshes_present": {5.08, 2.54}.issubset({case["case"]["h_mm"] for case in cases.values()}),
        "two_accepted_orientations_present": {0.0, 5.0}.issubset({case["case"]["mesh_orientation_deg"] for case in cases.values()}),
        "fine_no_propagation_control": no_prop["final_state"]["mean_extension_mm"] == 0,
        "elastic_mesh_peak_stress": elastic_difference <= cfg["gates"]["maximum_elastic_mesh_peak_stress_difference_fraction"],
        "g30_mesh_onset": mesh_onset_difference <= cfg["gates"]["maximum_g30_mesh_onset_stress_difference_fraction"],
        "g30_orientation_onset": orientation_onset_difference <= cfg["gates"]["maximum_g30_orientation_onset_stress_difference_fraction"],
        "fine_ctoa_domain_reached": fine_ctoa_available,
        "energy_and_section_work": maximum_energy <= cfg["gates"]["maximum_global_energy_residual_fraction"] and maximum_section_work <= cfg["gates"]["maximum_section_work_to_external_error_fraction"],
        "mass": maximum_mass_error <= cfg["gates"]["maximum_initial_mass_error_fraction"],
        "historical_conclusion_disabled": True,
    }
    summary = {
        "experiment": "WTC1-IMPACT-I02G",
        "status": "completed_bounded_mt_coupon_with_failed_crack_mesh_convergence_and_unreached_fine_ctoa_domain",
        "accepted_cases": ACCEPTED,
        "accepted_case_count": len(ACCEPTED),
        "accepted_case_checks": sum(len(case["gates"]) for case in cases.values()),
        "accepted_execution_seconds": sum(sum(record["seconds"] for record in json.loads((OUTPUT / name / "execution.json").read_text(encoding="utf-8"))) for name in ACCEPTED),
        "geometry": cfg["geometry"],
        "material": cfg["material"],
        "seam": cfg["seam"],
        "coarse_gf_results": coarse_gf_results,
        "elastic_mesh_peak_stress_difference_fraction": elastic_difference,
        "g30_mesh_complete_separation_onset_difference_fraction": mesh_onset_difference,
        "g30_orientation_complete_separation_onset_difference_fraction": orientation_onset_difference,
        "g30_coarse_complete_separation_onset_mpa": g30_coarse["complete_separation_onset"]["maximum_remote_stress_before_or_at_onset_mpa"],
        "g30_fine_complete_separation_onset_mpa": g30_fine["complete_separation_onset"]["maximum_remote_stress_before_or_at_onset_mpa"],
        "g30_fine_skew5_complete_separation_onset_mpa": g30_skew["complete_separation_onset"]["maximum_remote_stress_before_or_at_onset_mpa"],
        "g30_coarse_final_extension_mm": g30_coarse["final_state"]["mean_extension_mm"],
        "g30_fine_final_extension_mm": g30_fine["final_state"]["mean_extension_mm"],
        "maximum_energy_residual_fraction": maximum_energy,
        "maximum_section_work_to_external_error_fraction": maximum_section_work,
        "maximum_kinetic_to_internal_at_peak_stress": maximum_ke_ie,
        "maximum_mass_error_fraction": maximum_mass_error,
        "published_comparators": cfg["published_comparators"],
        "campaign_checks": checks,
        "campaign_pass_count": sum(checks.values()),
        "campaign_check_count": len(checks),
        "all_campaign_checks_pass": all(checks.values()),
        "rejected_attempts": [
            {
                "directory": "ELASTIC_H508_A0_R0",
                "status": "starter_rejected",
                "reason": "invalid PLAS variable in /TH/PART; no solver state produced",
            },
            {
                "directory": "G30_H254_S20_R2",
                "status": "engine_timeout_600_s_rejected",
                "reason": "20 degree mapped mesh compressed local elements and made the explicit step prohibitively small",
                "mesh_quality": mesh_quality(OUTPUT / "G30_H254_S20_R2"),
            },
        ],
        "accepted_skew5_mesh_quality": mesh_quality(OUTPUT / "G30_H254_S5_R3"),
        "tab2_decision": {
            "examined": True,
            "selected": False,
            "reason": "The official card requires or permits failure plastic strain as functions of triaxiality, Lode parameter, temperature and element size. Those 2024-T3 inputs are not identified here; a constant TAB2 card would hide rather than close that evidence gap.",
        },
        "reaction_measurement": {
            "used": "sum of cohesive seam FY forces",
            "verification": "trapezoidal integral of section force over imposed grip displacement compared with solver external work",
            "raw_upper_grip_REACY_sum_used": False,
            "reason_raw_reaction_excluded": "the raw nodal REACY sum did not close the work balance in this deck",
        },
        "physical_2024_tearing_calibrated": False,
        "three_dimensional_crack_tunneling_reproduced": False,
        "boeing_767_wing_qualified": False,
        "full_facade_qualified": False,
        "historical_penetration_conclusion_authorized": False,
        "cold_V11F_preserved": True,
        "thermal_V11R_preserved": True,
        "next_iteration": "IMPACT-I02H",
    }
    dump(OUTPUT / "summary_i02g.json", summary)
    dump(OUTPUT / "comparisons.json", {
        "elastic_mesh": {"difference_fraction": elastic_difference, "gate": cfg["gates"]["maximum_elastic_mesh_peak_stress_difference_fraction"], "pass": checks["elastic_mesh_peak_stress"]},
        "g30_mesh_onset": {"difference_fraction": mesh_onset_difference, "gate": cfg["gates"]["maximum_g30_mesh_onset_stress_difference_fraction"], "pass": checks["g30_mesh_onset"]},
        "g30_orientation_onset": {"difference_fraction": orientation_onset_difference, "gate": cfg["gates"]["maximum_g30_orientation_onset_stress_difference_fraction"], "pass": checks["g30_orientation_onset"]},
        "coarse_gf": coarse_gf_results,
        "fine_ctoa_domain_reached": fine_ctoa_available,
    })
    dump(OUTPUT / "campaign_audit.json", {
        "checks": checks,
        "passed": sum(checks.values()),
        "total": len(checks),
        "all_pass": all(checks.values()),
        "failed": [name for name, passed in checks.items() if not passed],
    })
    source_manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "local_sources": [{"path": str(PDF.relative_to(ROOT)).replace("\\", "/"), "sha256": sha(PDF), "bytes": PDF.stat().st_size}],
        "online_primary_sources": [
            {"url": "https://help.altair.com/hwsolvers/rad/topics/solvers/rad/fail_tab2_starter_r.htm", "publisher": "Altair", "use": "TAB2 dependencies and decision not to use an unidentified constant surface"},
            {"url": "https://help.altair.com/hwsolvers/rad/topics/solvers/rad/th_node_starter_r.htm", "publisher": "Altair", "use": "nodal reaction output semantics"},
        ],
        "source_archive_modified": False,
    }
    dump(OUTPUT / "source_manifest.json", source_manifest)
    make_figure(summary, OUTPUT / "synthese_impact_i02g.png")
    report = f"""# IMPACT-I02G — éprouvette M(T) 2024-T3 à fissure explicite

## Résultat exécutif

I02G reproduit la géométrie nominale M(T) publiée (76,2 × 300 × 2,3 mm, fissure centrale totale 25,4 mm, orientation L-T) et exécute huit cas OpenRadioss retenus. La tôle est élastique parfaitement plastique et la fissure suit une ligne cohésive prescrite sans masse. Aucun paramètre n'a été ajusté après calcul pour viser les comparateurs NASA.

Les contrôles de masse, d'énergie, de quasi-staticité et de travail de section passent. Le contrôle sans propagation reste fermé. L'écart élastique entre les mailles 5,08 et 2,54 mm vaut {100*elastic_difference:.3f} %. À maille fine, l'inclinaison interne de 5° change le seuil de première séparation de {100*orientation_onset_difference:.3f} %, donc le contrôle d'orientation passe.

En revanche, le seuil Gf=30 passe de {summary['g30_coarse_complete_separation_onset_mpa']:.3f} MPa à {summary['g30_fine_complete_separation_onset_mpa']:.3f} MPa lorsque la maille passe de 5,08 à 2,54 mm : l'écart relatif de {100*mesh_onset_difference:.2f} % échoue au critère de 10 %. La maille fine ne propage que de 1,27 mm par côté, sous le minimum de 2,3 mm fixé avant comparaison CTOA. I02G n'est donc pas une validation de fissuration 2024-T3.

## 1. Faits directement observés ou transcrits

- NASA CR-191523 décrit une éprouvette M(T) 2024-T3 de 2,3 mm d'épaisseur, 76,2 mm de largeur, 300 mm de longueur et une fissure/entaille centrale totale de 25,4 mm, chargée en déplacement en orientation L-T.
- Le document situe approximativement le début de déchirure stable vers 200 MPa pour les faibles contraintes de préfissuration et vers 230 MPa pour les fortes contraintes de préfissuration.
- Les Figures 6 et 7 montrent un CTOA de surface qui se rapproche d'environ 6° après une extension de l'ordre d'une épaisseur ; les valeurs proches de l'amorçage sont plus fortes et dispersées.

Source locale en lecture seule : `wtc1_simulation_v8/input/impact_i02f_sources/NASA_CR_191523_2024T3_CTOA.pdf`, SHA-256 `{sha(PDF)}`.

## 2. Résultats de modèles ou documentations externes

- La documentation Altair décrit `/FAIL/TAB2` comme une loi de déformation plastique à rupture pouvant dépendre de la triaxialité, du paramètre de Lode, de la température, de la taille d'élément et de la vitesse de déformation.
- `/FAIL/TAB2` n'est pas utilisé ici : les surfaces 2024-T3 nécessaires ne sont pas identifiées. Une valeur constante aurait seulement caché cette lacune.

## 3. Affirmations des archives locales

Aucune affirmation d'archive non primaire n'est utilisée dans I02G. Le PDF NASA est une copie de travail en lecture seule déjà enregistrée avec son empreinte.

## 4. Hypothèses propres au modèle

- Tôle : ρ=0,00278 g/mm³, E=73 100 MPa, ν=0,33, limite d'élasticité 360 MPa, plasticité parfaite. Les résistances 360/495 MPa viennent du document ; ρ, E et ν sont des hypothèses génériques héritées d'I02F.
- Ligne cohésive : traction maximale 495 MPa, raideur normale par aire E/h, raideur tangentielle par aire G/h, adoucissement triangulaire, ouverture finale δf=2Gf/495.
- Gf=15/30/60 N/mm est la plage hypothétique déclarée en I02F, non une mesure 2024-T3.
- La fissure est contrainte à rester horizontale, en 2D ; la tunnellisation 3D et l'état réel de triaxialité/Lode ne sont pas reproduits.

## 5. Résultats dérivés

| Cas grossier | Pic avant/au premier pas (MPa) | Δa par côté (mm) | CTOA à B au pas d'avance |
|---|---:|---:|---:|
"""
    for row in coarse_gf_results:
        report += f"| Gf={row['Gf_N_per_mm']:.0f} N/mm | {row['first_complete_separation_stress_mpa']:.3f} | {row['first_extension_mm']:.2f} | {row['ctoa_B_deg_at_advance']:.3f}° |\n"
    report += f"""

Le cas grossier Gf=60 donne {coarse_gf_results[-1]['first_complete_separation_stress_mpa']:.3f} MPa et {coarse_gf_results[-1]['ctoa_B_deg_at_advance']:.3f}° au premier pas, proches des domaines publiés. Cette concordance porte sur un seul saut discret de 2,54 mm et ne survit pas encore à une démonstration de convergence : elle reste un comparateur, pas une calibration ni une preuve.

Le résidu énergétique maximal des cas retenus vaut {100*maximum_energy:.4f} %, l'erreur maximale entre le travail externe et l'intégrale force-de-section/déplacement vaut {100*maximum_section_work:.4f} %, et le rapport énergie cinétique/énergie interne au pic reste sous {100*maximum_ke_ie:.4f} %. La force publiée dans les résultats est la somme des `FY` de la section cohésive ; la somme brute des `REACY` nodaux du grip n'a pas fermé le bilan de travail et n'est pas utilisée.

## 6. Contradictions, échecs et informations manquantes

- ÉCHEC : sensibilité du seuil Gf=30 à la maille = {100*mesh_onset_difference:.2f} % > 10 %.
- ÉCHEC : la maille fine atteint seulement Δa={summary['g30_fine_final_extension_mm']:.2f} mm par côté ; aucun CTOA fin n'est comparé au domaine stabilisé après 2,3 mm.
- La tentative 20° a été arrêtée au plafond de 600 s car le mappage comprimait certains éléments ; elle est conservée comme tentative rejetée. La variante 5° termine et passe le contrôle d'orientation.
- Le seuil d'adoucissement et la séparation complète ne sont pas le même événement. Les tableaux les conservent séparément.
- Les courbes contrainte-déformation post-élastiques, les surfaces triaxialité/Lode/vitesse, la longueur interne physique et une énergie de rupture mesurée 2024-T3 restent absentes.
- La localisation en flexion après fracture complète reste non validée.

## Portée

I02G vérifie une éprouvette numérique bornée. Il ne qualifie ni une aile de Boeing 767, ni la façade du WTC1, ni une pénétration historique. Une température imposée n'est pas un incendie calculé. Le contrôle froid V11F et la branche thermique V11R sont préservés. Blender reste une visualisation tant qu'il n'est pas alimenté par des états mécaniques validés.

## Suite IMPACT-I02H

Remplacer les sauts nodaux de la ligne cohésive par une formulation permettant une propagation plus régulière ou une zone cohésive mieux résolue, avec une troisième maille locale économiquement bornée. Identifier une courbe plastique 2024-T3 et des données de ténacité/énergie compatibles avec l'épaisseur et l'orientation ; conserver 200/230 MPa et ~6° comme comparateurs indépendants. Ne transférer vers une deuxième zone I02E qu'après passage de la convergence du seuil et obtention d'au moins deux états CTOA fins au-delà de Δa=2,3 mm.
"""
    (OUTPUT / "rapport_impact_i02g.md").write_text(report, encoding="utf-8", newline="\n")

    manifest_paths = [CFG, RUNNER, AUDITOR, Path(__file__), PDF]
    for name in ACCEPTED:
        directory = OUTPUT / name
        manifest_paths.extend(path for path in directory.iterdir() if path.is_file())
    manifest_paths.extend([
        OUTPUT / "summary_i02g.json",
        OUTPUT / "comparisons.json",
        OUTPUT / "campaign_audit.json",
        OUTPUT / "source_manifest.json",
        OUTPUT / "synthese_impact_i02g.png",
        OUTPUT / "rapport_impact_i02g.md",
    ])
    unique_paths = sorted(set(manifest_paths), key=lambda path: str(path).lower())
    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "entries": [
            {"path": str(path.relative_to(ROOT)).replace("\\", "/"), "bytes": path.stat().st_size, "sha256": sha(path)}
            for path in unique_paths
        ],
    }
    dump(OUTPUT / "artifact_manifest.json", manifest)
    verified = all((ROOT / entry["path"]).exists() and sha(ROOT / entry["path"]) == entry["sha256"] for entry in manifest["entries"])
    release_checks = {
        "accepted_case_directories_exist": all((OUTPUT / name).is_dir() for name in ACCEPTED),
        "accepted_case_audits_pass": checks["accepted_case_gates"],
        "campaign_records_failed_scientific_gates": not all(checks.values()) and set(name for name, passed in checks.items() if not passed) == {"g30_mesh_onset", "fine_ctoa_domain_reached"},
        "report_exists": (OUTPUT / "rapport_impact_i02g.md").exists(),
        "summary_exists": (OUTPUT / "summary_i02g.json").exists(),
        "figure_exists": (OUTPUT / "synthese_impact_i02g.png").exists(),
        "source_pdf_hash": sha(PDF) == cfg["sources"][0]["sha256"],
        "artifact_manifest_verified": verified,
        "cold_control_preserved": True,
        "prior_iterations_preserved": True,
        "physical_claims_disabled": not summary["historical_penetration_conclusion_authorized"],
    }
    dump(OUTPUT / "release_audit.json", {
        "checks": release_checks,
        "passed": sum(release_checks.values()),
        "total": len(release_checks),
        "all_pass": all(release_checks.values()),
        "note": "Release audit validates artifact integrity and honest recording of failed scientific gates; it does not convert those failures into physical validation.",
    })
    print(json.dumps({
        "accepted_cases": len(ACCEPTED),
        "campaign_checks": f"{sum(checks.values())}/{len(checks)}",
        "failed_scientific_gates": [name for name, passed in checks.items() if not passed],
        "release_checks": f"{sum(release_checks.values())}/{len(release_checks)}",
        "release_pass": all(release_checks.values()),
        "mesh_onset_difference_fraction": mesh_onset_difference,
        "orientation_onset_difference_fraction": orientation_onset_difference,
    }, indent=2))


if __name__ == "__main__":
    main()
