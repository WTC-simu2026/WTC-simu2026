"""Produce a new, non-overwriting V11A component package and numerical checks."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import platform
import shutil
import sys
import time
from collections import Counter
from datetime import datetime
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

import v11a_component_model as model

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "wtc1_simulation_v8/data/v11a_component_resistance_predeclaration.json"
LIBRARY = Path(model.__file__).resolve()


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def digest(path: Path) -> str:
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def numerical_digest(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, allow_nan=False, separators=(",", ":")).encode()).hexdigest()


def write_json(path: Path, value) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, ensure_ascii=False, allow_nan=False, indent=2)
        handle.write("\n")


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        raise ValueError(f"Empty output {path}")
    with path.open("x", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def inputs_from_sources(cfg: dict) -> dict:
    source = cfg["source_files"]
    result = {key: read_json(ROOT/path) for key, path in zip(
        ["columns", "geometry", "aisc", "transfer", "seats", "v8h", "v8m"], source[:7], strict=True)}
    with (ROOT/source[7]).open(encoding="utf-8-sig", newline="") as handle:
        result["topology"] = list(csv.DictReader(handle))
    return result


def calculate(cfg: dict, inputs: dict) -> dict:
    inventory, columns, beams, beam_curves = model.core_inventory(cfg, inputs)
    cases, members, pairs, curves, geometries = model.floor_cases(cfg, inputs)
    return {"inventory": inventory, "column_capacities": columns, "core_beam_capacities": beams,
            "core_beam_force_displacement": beam_curves, "seat_capacities": model.seat_table(cfg, inputs),
            "floor_bay_cases": cases, "floor_bay_members": members, "floor_bay_seat_pairs": pairs,
            "floor_bay_force_displacement": curves, "floor_bay_geometries": geometries}


def audit(cfg: dict, inputs: dict, data: dict, replay_hash: str) -> dict:
    tests = model.unit_tests(cfg, inputs)
    def check(name, ok, evidence):
        tests.append({"test": name, "pass": bool(ok), "evidence": evidence})
    inv, accepted = data["inventory"], cfg["acceptance"]
    for key, expect in [("nodes", "expected_core_node_count"),
                        ("core_column_segments", "expected_core_column_segment_count"),
                        ("core_beam_candidates", "expected_core_beam_candidate_count")]:
        check(f"count_{key}", len(inv[key]) == accepted[expect], len(inv[key]))
        id_key = "node_id" if key == "nodes" else "member_id"
        check(f"unique_identifiers_{key}", len({r[id_key] for r in inv[key]}) == len(inv[key]), len(inv[key]))
    nodes = {r["node_id"] for r in inv["nodes"]}
    all_members = inv["core_column_segments"] + inv["core_beam_candidates"]
    check("member_endpoints_exist_and_lengths_positive", all(r["node_i"] in nodes and r["node_j"] in nodes and r["length_m"] > 0 for r in all_members), len(all_members))
    count_moment = sum("official_model_moment" in b["topology_family"] for b in inv["core_beam_candidates"])
    check("official_moment_reference_count", count_moment == accepted["expected_moment_reference_beam_count"], count_moment)
    source_moment = {tuple(sorted(e)) for e in inputs["v8h"]["moment_beam_topology"]["edges"]}
    check("moment_edges_match_source_at_each_floor", all(
        {tuple(sorted([b["column_i"], b["column_j"]])) for b in inv["core_beam_candidates"]
         if b["floor"] == floor and "official_model_moment" in b["topology_family"]} == source_moment
        for floor in cfg["floors"]), len(source_moment))
    check("intact_baseline_does_not_claim_impact_assignment", not cfg["impact_damage_applied"] and all(
        r["damage_state"] == "INTACT_BASELINE_HYPOTHESIS_NO_IMPACT_DAMAGE_APPLIED" for r in all_members), len(all_members))
    check("no_beam_proxy_promoted_to_as_built", all(b["section_assignment_status"] == "HYPOTHESIS_NOT_AS_BUILT" for b in inv["core_beam_candidates"]), len(inv["core_beam_candidates"]))
    band_actual = {f: {c["splice_band"] for c in inv["core_column_segments"] if c["floor"] == f} for f in cfg["floors"]}
    bands = {93: "95-92", 94: "95-92", 95: "98-95", 96: "98-95", 97: "98-95", 98: "101-98", 99: "101-98"}
    check("splice_band_boundary_convention", all(band_actual[f] == {bands[f]} for f in cfg["floors"]), {f: list(v) for f, v in band_actual.items()})
    check("existing_geometry_roof_height_reproduced", math.isclose(inv["roof_target_reproduced_m"], 416.9664, abs_tol=1e-8), inv["roof_target_reproduced_m"])
    check("column_capacity_matrix_count", len(data["column_capacities"]) == 329*3*4, len(data["column_capacities"]))
    check("beam_capacity_matrix_count", len(data["core_beam_capacities"]) == 553*3*2*4, len(data["core_beam_capacities"]))
    check("nominal_column_screen_positive_below_ideal_bounds", all(0 < r["nominal_flexural_buckling_screen_N"] <= min(r["squash_load_N"], r["ideal_euler_load_N"])*(1+1e-12) for r in data["column_capacities"]), len(data["column_capacities"]))
    check("seat_library_includes_all_15_details_11_temperatures", len(data["seat_capacities"]) == 165, len(data["seat_capacities"]))
    seat1013 = [r for r in data["seat_capacities"] if r["detail"] == "1013" and r["temperature_c"] in (20, 100)]
    check("preserve_nonmonotonic_published_horizontal_capacity", [r["horizontal_tension_kip"] for r in seat1013] == [100, 138], seat1013)
    cases = data["floor_bay_cases"]
    check("floor_bay_case_count", len(cases) == accepted["expected_floor_bay_case_count"], len(cases))
    check("all_56_seat_pairs_evaluated_per_bay", len(data["floor_bay_seat_pairs"]) == len(cases)*56, len(data["floor_bay_seat_pairs"]))
    eq = max(r["equilibrium_residual"] for r in cases)
    energy = max(r["energy_residual"] for r in cases)
    reactions = max(r["reaction_balance_residual"] for r in cases)
    check("all_bay_equilibrium_residuals", eq < accepted["maximum_relative_equilibrium_residual"], eq)
    check("all_bay_strain_energy_equals_ramped_external_work", energy < accepted["maximum_relative_energy_residual"], energy)
    check("paired_gravity_load_equals_both_paired_reactions", reactions < accepted["maximum_relative_equilibrium_residual"], reactions)
    check("symmetric_bay_reactions", all(math.isclose(r["paired_exterior_reaction_kip"], r["paired_interior_reaction_kip"], rel_tol=1e-10) for r in cases), len(cases))
    check("truss_connectivity_is_statically_determinate", all(len(g["members"]) == 2*len(g["nodes_m"])-3 for g in data["floor_bay_geometries"].values()), len(data["floor_bay_geometries"]))
    members_by_case = {}
    for row in data["floor_bay_members"]:
        members_by_case.setdefault(row["case_id"], []).append(row)
    check("member_first_limit_reaches_DCR_one", all(math.isclose(
        max(r["service_trial_DCR"] for r in members_by_case[c["case_id"]])*c["first_member_limit_factor"], 1, rel_tol=1e-12) for c in cases), len(cases))
    force_reference = {}
    forces_invariant = True
    for case in cases:
        vector = [r["trial_axial_force_single_N"] for r in members_by_case[case["case_id"]]]
        key = case["geometry_id"]
        force_reference.setdefault(key, vector)
        forces_invariant &= bool(np.allclose(vector, force_reference[key], rtol=1e-10, atol=1e-5))
    check("determinate_bar_forces_independent_of_stiffness_variants", forces_invariant, len(cases))
    check("long_bay_seat_service_load_near_published_16kip", all(abs(r["paired_exterior_reaction_kip"]-16)/16 < 0.02 for r in cases if r["span_in"] == 713), next(r["paired_exterior_reaction_kip"] for r in cases if r["span_in"] == 713))
    check("paired_member_forces_are_twice_single_truss", all(r["trial_axial_force_pair_N"] == 2*r["trial_axial_force_single_N"] for r in data["floor_bay_members"]), len(data["floor_bay_members"]))
    check("composite_force_sharing_balances_total", all(math.isclose(r["trial_steel_force_single_N"]+r["trial_concrete_force_single_N"], r["trial_axial_force_single_N"], abs_tol=1e-6, rel_tol=1e-12) for r in data["floor_bay_members"]), len(data["floor_bay_members"]))
    limit_by_id = {c["case_id"]: c["first_limit_factor_weakest_seats"] for c in cases}
    check("no_reported_bay_curve_beyond_first_limit", all(r["load_factor"] <= limit_by_id[r["case_id"]]*(1+1e-12) for r in data["floor_bay_force_displacement"]), len(data["floor_bay_force_displacement"]))
    check("no_global_collapse_energy_credit", all(r["global_collapse_energy_credit_J"] == 0 for r in cases) and not inv["global_collapse_coupling"], 0)
    numerical_hash = numerical_digest(data)
    check("exact_deterministic_replay", numerical_hash == replay_hash, numerical_hash)
    return {"status": "PASS" if all(t["pass"] for t in tests) else "FAIL", "tests": tests,
            "tests_passed": sum(t["pass"] for t in tests), "test_count": len(tests),
            "numerical_digest_sha256": numerical_hash,
            "maximum_equilibrium_residual": eq, "maximum_energy_residual": energy,
            "physical_validation": False, "historical_validation": False}


def representative_cases(data: dict) -> list:
    return [r for r in data["floor_bay_cases"] if r["span_in"] == 713 and r["panels_hypothesis"] == 16
            and r["fy_hypothesis_ksi"] == 36 and r["web_diameter_hypothesis_in"] == 1.09
            and r["temperature_c"] in (20, 400, 600)]


def draw_overview(out: Path, data: dict) -> None:
    image = Image.new("RGB", (1500, 1190), "#f5f7fa")
    draw = ImageDraw.Draw(image)
    font_path = Path("C:/Windows/Fonts/segoeui.ttf")
    bold_path = Path("C:/Windows/Fonts/segoeuib.ttf")
    def font(size=22, bold=False):
        return ImageFont.truetype(str(bold_path if bold else font_path), size)
    def text(x, y, value, size=22, color="#1e293b", bold=False):
        draw.text((x, y), value, font=font(size, bold), fill=color)
    text(45, 28, "WTC 1 · V11A · Résistances par composants", 36, bold=True)
    text(45, 83, "Zone 93–99 · prototype mécanique exploratoire · aucune nouvelle conclusion sur l’effondrement", 22)
    draw.rounded_rectangle((30, 130, 738, 680), 16, fill="white", outline="#d1dae5", width=2)
    draw.rounded_rectangle((758, 130, 1470, 680), 16, fill="white", outline="#d1dae5", width=2)
    text(55, 147, "Noyau au niveau 96", 28, bold=True)
    text(55, 188, "47 colonnes · coordonnées approchées (± 0,30 m)", 20)
    inv = data["inventory"]
    points = {n["column_id"]: (384+n["x_m"]*13.5, 430-n["y_m"]*12) for n in inv["nodes"] if n["floor"] == 96}
    for beam in inv["core_beam_candidates"]:
        if beam["floor"] != 96:
            continue
        official = "official_model_moment" in beam["topology_family"]
        draw.line((points[beam["column_i"]], points[beam["column_j"]]), fill="#2563a7" if official else "#bdc7d2", width=4 if official else 2)
    for cid, (x, y) in points.items():
        draw.ellipse((x-5, y-5, x+5, y+5), fill="#1e293b")
        text(x-17, y+7, str(cid), 16)
    text(55, 613, "Bleu : 17 liaisons du modèle NIST", 20, "#2563a7")
    text(55, 643, "Gris : 62 liaisons hypothétiques · sections des poutres estimées", 18)
    text(785, 147, "Travée de plancher représentative", 28, bold=True)
    text(785, 188, "18,11 m · 2 treillis · bande chargée de 2,032 m", 21)
    geo = data["floor_bay_geometries"]["L713_P16"]
    node_points = [(790+x/18.1102*645, 350-z*105) for x, z in geo["nodes_m"]]
    draw.rectangle((790, 325, 1435, 342), fill="#adc9be")
    for i, j, family in geo["members"]:
        draw.line((node_points[i], node_points[j]), fill="#2563a7" if family != "web" else "#526277", width=3 if family != "web" else 2)
    for x in range(810, 1435, 55):
        draw.line((x, 275, x, 318), fill="#b94d24", width=2)
        draw.polygon([(x-5, 310), (x+5, 310), (x, 320)], fill="#b94d24")
    for x in (790, 1435):
        draw.polygon([(x, 350), (x-10, 373), (x+10, 373)], fill="#1e293b")
    text(795, 460, "Appuis verticaux : effort calculé / résistance à T", 21)
    text(795, 501, "Barres : traction, compression et flambement idéal", 21)
    text(795, 542, "Dalle : sans participation ou compression idéale", 21)
    text(795, 592, "Disposition des panneaux et liaisons : hypothèses.", 20, "#994719")
    text(795, 622, "Fluage, rupture des attaches et flexion de dalle : non résolus.", 18, "#994719")
    text(45, 706, "Premier seuil nominal de la travée — sensibilité, pas charge admissible réelle", 25, bold=True)
    text(45, 745, "16 panneaux · acier supposé à 36 ksi · barres Ø 1,09 in · appuis les moins résistants des tables", 21)
    headers = [(55, "T acier"), (215, "Participation de dalle"), (615, "Pression au seuil"), (915, "Flèche au seuil"), (1190, "Élément limitant")]
    draw.rectangle((40, 785, 1460, 825), fill="#dbe5f0")
    for x, value in headers:
        text(x, 790, value, 21, bold=True)
    for n, case in enumerate(representative_cases(data)):
        y = 831+42*n
        if n % 2 == 0:
            draw.rectangle((40, y-2, 1460, y+37), fill="white")
        text(55, y, f"{case['temperature_c']} °C", 21)
        text(215, y, "Compression idéale" if case["composite_mode"] != "bare_steel" else "Aucune", 21)
        pressure = case["first_limit_pressure_weakest_seats_psf"] * model.PSF/1000
        text(615, y, f"{pressure:.2f} kPa", 21)
        text(915, y, f"{case['first_limit_deflection_weakest_seats_m']*1000:.1f} mm", 21)
        family = {"top_chord": "Membrure haute", "bottom_chord": "Membrure basse", "web": "Diagonale"}[case["governing_member_family"]]
        text(1190, y, family, 20)
    text(45, 1100, "Charge de service de référence : 80 psf ≈ 3,83 kPa. Arrêt du calcul de chargement au premier seuil.", 21)
    text(45, 1135, "Résistances de forces ≠ énergie d’un étage. Ces valeurs ne sont pas encore reliées à l’animation V10Z.", 21, "#994719")
    image.save(out / "synthese_v11a_composants.png")


def report_text(cfg: dict, data: dict, checked: dict, elapsed: float) -> str:
    column_examples = [r for r in data["column_capacities"] if r["floor"] == 96 and r["column_id"] in (501, 704, 804, 1008)
                       and r["temperature_c"] == 20 and r["effective_length_factor"] == 1]
    col_table = "\n".join(f"| {r['column_id']} | {r['section']} | {r['nominal_flexural_buckling_screen_N']/1e6:.3f} |" for r in column_examples)
    bay_table = "\n".join(f"| {r['temperature_c']} | {'acier seul' if r['composite_mode']=='bare_steel' else 'dalle en compression idéale'} | {r['first_limit_pressure_weakest_seats_psf']*model.PSF/1000:.3f} | {r['first_limit_deflection_weakest_seats_m']*1000:.1f} | {r['governing_member_family']} |" for r in representative_cases(data))
    counts = Counter(r["service_trial_status"] for r in data["floor_bay_cases"])
    return f"""# WTC 1 — V11A : résistances individuelles et travée de plancher

## Résultat utilisable

V11A ajoute une bibliothèque mécanique exécutable pour la zone 93–99 : **329 tronçons de colonnes du noyau** (47 × 7), **553 liaisons candidates de poutres** (79 × 7), **15 familles d'appuis** et **192 variantes d'une travée de plancher**. Chaque composant porte son identifiant, ses unités, sa source ou son statut d'hypothèse. Les calculs portent sur les efforts, rigidités et premiers seuils nominaux, pas sur une simple résistance unique par étage.

Cela ne signifie pas que chaque poutre et chaque plancher réels du WTC1 sont identifiés. Les sections des colonnes proviennent d'une transcription des plans ; toutes les affectations de sections aux poutres restent estimées. Les sept niveaux pointent vers une bibliothèque de travées : ils ne reçoivent pas un nombre inventé de treillis ni une implantation complète supposée exacte.

Les composants sont ici supposés intacts : aucun dommage d'impact ni rupture antérieure d'assemblage ne leur est appliqué. Les températures imposées servent à comparer leurs propriétés, sans représenter une histoire thermique localisée.

La demande récente de Jeremy donne priorité à ce sous-modèle de composants. Les corrections globales V10Y déjà signalées (temps/résistance pendant le premier déplacement, demi-plancher de masse manquant, arrivée au sol avec énergie résiduelle) restent à effectuer ; V11A ne les déclare pas résolues et ne modifie pas V10Y/V10Z.

## 1. Faits directement transcrits ou vérifiés

Les six pages déclarées ont été rendues puis lues visuellement. Les avertissements de substitution de polices du lecteur PDF n'empêchaient pas la lecture des tableaux et dimensions ; les images sont conservées dans `source_pages/`.

- [NIST NCSTAR 1-6C](https://nvlpubs.nist.gov/nistpubs/Legacy/NCSTAR/ncstar1-6c.pdf), PDF 117–118, pages imprimées 69–70 : description de C32T1 au plancher 96, colonne extérieure 143 ; portée 713 in, bande de dalle 40 in par treillis, double cornière supérieure 2 × 1,5 × 0,25 in, inférieure 3 × 2 × 0,37 in, diagonales rondes 1,09 ou 1,14 in.
- La dimension verticale de 29 in du schéma est utilisée comme distance nodale approximative ; les centres réels des cornières ne sont pas redéterminés. La dalle du modèle détaillé fait 4,35 in équivalents, contre 4,3 in arrondis dans le rapport d'ensemble. La dalle n'est pas confondue avec la seule épaisseur supérieure de béton de 4 in.
- [NIST NCSTAR 1-6](https://nvlpubs.nist.gov/nistpubs/Legacy/NCSTAR/ncstar1-6.pdf), PDF 156–158, pages 74–76, et PDF 167, page 85 : tableaux d'appuis, géométrie et charge morte + exploitation de référence de 80 psf. La réaction calculée pour une paire de treillis de 713 in est 15,844 kip à chaque appui, proche des 16 kip arrondis dans le texte. La charge inclut déjà le poids propre ; aucun poids propre additionnel n'est ajouté.

Conversions gardées dans le code et les données : 1 in = 0,0254 m ; 1 ft = 0,3048 m ; 1 kip = 4 448,221615 N ; 1 ksi = 6,894757 MPa ; 80 psf = 3,830421 kPa. La portée de 713 in vaut 18,1102 m.

## 2. Résultats de modèles officiels réutilisés

Les capacités d'appui ne sont pas des mesures de résistance de tous les appuis réels : ce sont les résultats calculés du NIST pour des détails types. Les tableaux verticaux intérieurs/extérieurs de V8G sont conservés. V11A ajoute la transcription complète des capacités horizontales extérieures du tableau 4-5 ; l'augmentation de 100 à 138 kip entre 20 et 100 °C du détail 1013 est conservée, sans correction arbitraire.

Les deux directions de sollicitation restent distinctes. Leur interaction n'est pas inventée. Le modèle de travée, avec un appui roulant horizontal, ne mobilise pas les capacités horizontales et ne vérifie pas les poussées thermiques ni l'arrachement par chaînette.

Pour les poutres, 119 liaisons des sept niveaux reprennent le sous-réseau de connexions de moment du modèle NIST. Les 434 autres liaisons proviennent de l'enveloppe orthogonale hypothétique antérieure. L'absence d'une liaison dans le sous-réseau NIST n'est pas interprétée comme l'absence de charpente réelle.

## 3. Informations provenant des archives locales

Les 47 nomenclatures du noyau sont reprises de `core_sections_impact_zone.json` : Drawing Book 3, feuilles 3-A1-2 à 3-A1-48, bandes 95–92, 98–95 et 101–98. Cette transcription manuelle conserve ses pages d'origine et son besoin de seconde lecture indépendante. Les propriétés des profils WF proviennent de la base historique AISC, édition ASD7 utilisée comme proxy ; les caissons sont reconstruits à partir des plaques transcrites. Aucun nouvel examen de l'archive source n'a été lancé.

Les coordonnées du noyau conservent leur incertitude de plan estimée à ±0,30 m. Les hauteurs viennent du calendrier hétérogène existant : le sommet de référence reste 416,9664 m, et non 110 fois une hauteur uniforme. Les raccords de colonnes sont encore alignés aux niveaux dans le prototype ; les vrais décalages de joints restent inconnus.

## 4. Hypothèses propres au modèle

### Colonnes et poutres

Les colonnes ont une rigidité EA/L et des écrans de compression : écrasement A·Fy, Euler, puis courbe nominale de flambement flexionnel déjà employée en V8B (forme E3). K = 0,7 / 1 / 2 est balayé. La forme est traçable dans [AISC 360-16, chapitre E3](https://www.aisc.org/globalassets/aisc/publications/standards/a360-16w-rev-june-2019.pdf), mais son usage ici n'est ni un calcul réglementaire historique ni une vérification incendie. Flambement local/torsionnel, imperfections, interactions flexion-compression et assemblages ne sont pas vérifiés.

Chaque poutre candidate possède sa longueur reconstruite et trois sections alternatives : 12WF65 / 14WF136 / 14WF228. Les moments élastique/plastique, le cisaillement idéal de l'âme et la rigidité relative 12EI/L³ sont calculés séparément. Les facteurs d'assemblage 0,5 / 1, le durcissement 1 % et la rotation de rupture 0,02 rad sont explicitement hypothétiques. Le déversement et la mécanique des boulons/soudures restent absents. Le travail d'un ressort isolé est exporté pour audit mais reçoit **zéro crédit d'énergie de résistance globale**.

Le module d'Young est évalué seulement entre 20 et 600 °C. Toute demande au-delà est rejetée. La réduction de limite d'élasticité est normalisée à 20 °C. Les quatre températures sont imposées, pas calculées par une simulation d'incendie.

### Treillis et dalle

Le solveur est un treillis plan linéaire à barres axiales, appui articulé + rouleau. Il utilise une disposition Warren idéalisée, 12 / 16 / 20 panneaux : c'est une sensibilité à la disposition physique, pas une convergence de maillage du treillis réel. Les panneaux d'extrémité, encastrements et soudures ne sont pas reconstruits exactement. Les deux nuances 36 / 50 ksi sont des hypothèses ; la nuance du matériau des poutres du noyau n'est pas transférée silencieusement aux treillis.

La portée de 433 in est une seconde hypothèse de travée courte issue de V8M ; lui affecter les mêmes cornières que C32T1 n'est pas une transcription du véritable treillis court. Les calculs à 1,09 / 1,14 in utilisent un diamètre uniforme ; la distribution réelle des deux diamètres n'est pas connue.

La dalle est soit absente mécaniquement, soit parfaitement liée, comprimée et supposée maintenir la membrure supérieure contre le flambement. Dans le second cas, seul son EA axial en compression est ajouté à la membrure supérieure. Module, résistance en compression et leur réduction thermique sont des hypothèses déclarées (2 500 ksi et 3 ksi à 20 °C). Aucune résistance en traction, flexion de dalle, poinçonnement, dalle fissurée, armatures, bac acier, goujons ou « knuckles » n'est ajoutée. Le partage acier/béton est vérifié. Le cas idéal est donc une limite de modèle, pas une affirmation que la dalle reste liée après l'impact.

Pour les barres comprimées, le minimum écrasement/Euler est un écran idéal. Il ne reproduit pas le flambement inélastique ou local. Les courbes s'arrêtent au premier seuil nominal sous augmentation proportionnelle de la pesanteur ; aucune solution après ce seuil n'est produite.

## 5. Résultats dérivés

### Exemples de colonnes au niveau 96

À 20 °C, K = 1, écran nominal de flambement uniquement — **pas des charges admissibles réelles** :

| Colonne | Section transcrite | Écran nominal (MN) |
|---|---|---:|
{col_table}

La matrice complète contient {len(data['column_capacities']):,} évaluations de colonnes et {len(data['core_beam_capacities']):,} évaluations de poutres. Ces nombres comptent des variantes de paramètres, pas autant de pièces réelles différentes.

### Exemple de travée longue

Portée 713 in, 16 panneaux hypothétiques, Fy supposé 36 ksi, diamètre uniforme 1,09 in. Le tableau emploie les appuis les moins résistants parmi les détails tabulés, à la température considérée :

| Acier (°C) | Dalle | Pression au premier seuil (kPa) | Flèche au seuil (mm) | Famille limitante |
|---:|---|---:|---:|---|
{bay_table}

Ces valeurs ne sont pas une prédiction de résistance d'un étage réel. Si un treillis sans dalle atteint son écran idéal avant les 80 psf de référence, cela renseigne sur cette hypothèse de contreventement et de liaison, pas sur une faiblesse prouvée du plancher construit. Une grande résistance verticale des appuis ne protège pas automatiquement d'un autre mécanisme : barre comprimée, perte de liaison, poussée horizontale ou instabilité globale.

Sur les 192 variantes, {counts.get('BELOW_MODEL_FIRST_LIMIT', 0)} restent sous le premier seuil à la charge de référence et {counts.get('ELASTIC_TRIAL_EXCEEDS_FIRST_LIMIT', 0)} ont un essai élastique au-delà de ce seuil. Ces comptes décrivent seulement la grille déclarée ; ils ne sont **jamais des probabilités historiques**. Chaque variante teste les 56 combinaisons de détails d'appuis, sans en sélectionner une par ressemblance à la chronologie.

### Vérifications numériques

{checked['tests_passed']}/{checked['test_count']} contrôles passent, dont un treillis triangulaire à solution analytique indépendante, le travail virtuel/énergie élastique, les unités, la charge nulle, les bandes de sections, la connectivité du catalogue, la duplication d'un treillis vers une paire, les réactions et la répétition déterministe exacte.

- Résidu relatif maximal d'équilibre : {checked['maximum_equilibrium_residual']:.3e}.
- Résidu relatif maximal d'énergie élastique : {checked['maximum_energy_residual']:.3e}.
- Durée d'exécution et répétition : {elapsed:.2f} s. NumPy {np.__version__}, Python {platform.python_version()}, calcul CPU ; aucune installation, aucun calcul GPU ou Blender.

Ces contrôles valident l'exécution de ce sous-modèle, pas sa fidélité complète au bâtiment ni la cause historique de l'effondrement.

## 6. Contradictions, limites et suite

Le détail 4,35/4,3 in est une différence de représentation/arrondi dans deux rapports, pas une preuve de deux planchers différents. Les dimensions de profils historiques et les joints de colonnes gardent leurs limites de transcription. Le nombre et l'implantation réelle des travées, les poutres porteuses de rive du noyau, le ferraillage et les ouvertures ne sont pas remplacés par une grille déclarée exacte.

Restent : nomenclature des façades et allèges, assemblages complets, transferts dalle–poutres–colonnes, rupture des soudures/goujons, cisaillement et flexion de dalle, dilatation, gradients thermiques, fluage, flambement non linéaire et redistribution après rupture. La maquette Blender V10Z reste inchangée et ne reçoit aucune de ces capacités comme si le couplage était déjà validé.

Prochaine V11B : corriger explicitement l'initialisation et l'inventaire de masse du calcul global V10Y, sans recalibrer ses scénarios sur la chronologie ; conserver l'arrêt comme issue possible. Ensuite construire un panneau de plancher avec liaisons à raideur/rupture explicites et vérifier son comportement froid avant tout couplage progressif à la tour. Aucune conclusion « effondrement nécessaire » ou « impossible » ne découle de V11A.

## Livrables

- `component_inventory.json` : identifiants, sections, géométrie, sources et statuts.
- `column_capacities.csv` et `core_beam_capacities.csv` : capacités individuelles et variantes.
- `seat_capacities.csv` : appuis verticaux et horizontaux, unités originales et SI.
- `floor_bay_cases.csv`, `floor_bay_members.csv`, `floor_bay_seat_pairs.csv` : solutions et premiers seuils par composant.
- `floor_bay_force_displacement.csv` : courbes de chargement arrêtées au premier seuil.
- `source_manifest.json`, `numerical_audit.json`, `offline_manifest.json` : traçabilité, contrôles et empreintes.
- `synthese_v11a_composants.png` : vue de contrôle, avec hypothèses visibles.
"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="wtc1_simulation_v8/output/v11a_component_resistance")
    args = parser.parse_args()
    cfg = read_json(CONFIG)
    out = (ROOT / args.output_dir).resolve()
    allowed = [(ROOT / "tmp/v11a_component_resistance").resolve(),
               (ROOT / cfg["output_directory"]).resolve()]
    if not any(out == p or p in out.parents for p in allowed) or out.exists():
        raise ValueError("Output must be a new V11A directory inside the declared destinations")
    out.mkdir(parents=True, exist_ok=False)
    started = datetime.now().astimezone().isoformat()
    start = time.perf_counter()
    files = cfg["source_files"] + [r["path"] for r in cfg["bounded_pdf_review"]] + cfg["protected_files"]
    tracked = {path: digest(ROOT/path) for path in files}
    inputs = inputs_from_sources(cfg)
    data = calculate(cfg, inputs)
    replay_hash = numerical_digest(calculate(cfg, inputs))
    checked = audit(cfg, inputs, data, replay_hash)
    write_json(out / "numerical_audit.json", checked)
    if checked["status"] != "PASS":
        print(json.dumps(checked, ensure_ascii=False))
        raise RuntimeError("Numerical audit failed; incomplete attempt retained")
    for key, value in data.items():
        filename = "component_inventory" if key == "inventory" else key
        if isinstance(value, list):
            write_csv(out / f"{filename}.csv", value)
        else:
            write_json(out / f"{filename}.json", value)
    page_dir = out / "source_pages"
    page_dir.mkdir()
    pages = []
    for source in cfg["bounded_pdf_review"]:
        stem = Path(source["path"]).stem
        for page in source["pdf_pages_1based"]:
            source_png = ROOT / cfg["scratch_directory"] / f"{stem}-{page:03d}.png"
            destination = page_dir/source_png.name
            shutil.copy2(source_png, destination)
            pages.append({"source_pdf": source["path"], "pdf_page_1based": page,
                          "image": destination.relative_to(out).as_posix(), "sha256": digest(destination),
                          "visual_inspection": "MAIN_AGENT_READ_COMPLETE_PAGE_2026-09-05",
                          "renderer": "Poppler pdftoppm 115 dpi; font-substitution warnings; tables and figures readable"})
    draw_overview(out, data)
    after = {path: digest(ROOT/path) for path in files}
    if after != tracked:
        raise RuntimeError("A source or protected input changed during V11A")
    elapsed = time.perf_counter()-start
    manifest = {"iteration": "V11A", "started_at": started,
        "finished_at": datetime.now().astimezone().isoformat(), "elapsed_seconds": elapsed,
        "python_executable": sys.executable, "python_version": platform.python_version(),
        "numpy_version": np.__version__, "random_seed": cfg["random_seed"], "random_draw_used": False,
        "numerical_evaluation_passes": 2, "global_FE_solver_runs": 0, "linear_bay_solves_per_pass": len(data["floor_bay_cases"]),
        "blender_runs": 0, "gpu_runs": 0, "source_archive_reads": 0,
        "source_and_protected_files_unchanged": True,
        "inputs": [{"path": path, "sha256_before": value, "sha256_after": after[path], "size_bytes": (ROOT/path).stat().st_size} for path, value in tracked.items()],
        "code": [{"path": p.relative_to(ROOT).as_posix(), "sha256": digest(p)} for p in (CONFIG, LIBRARY, Path(__file__).resolve())],
        "source_page_review": pages}
    write_json(out / "source_manifest.json", manifest)
    with (out / "rapport_v11a_resistances_composants.md").open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(report_text(cfg, data, checked, elapsed))
    summary = {"iteration": "V11A", "status": "PASS_EXPLORATORY_COMPONENT_MODEL_NOT_AS_BUILT_GLOBAL_MODEL",
        "counts": {"core_nodes": len(data["inventory"]["nodes"]), "core_column_segments": len(data["inventory"]["core_column_segments"]),
                   "core_beam_candidates": len(data["inventory"]["core_beam_candidates"]),
                   "official_model_moment_references": 119, "hypothetical_beam_links": 434,
                   "column_capacity_evaluations": len(data["column_capacities"]), "beam_capacity_evaluations": len(data["core_beam_capacities"]),
                   "seat_detail_families": 15, "seat_temperature_rows": len(data["seat_capacities"]),
                   "bay_variants": len(data["floor_bay_cases"]), "bay_member_evaluations": len(data["floor_bay_members"]),
                   "bay_seat_pair_evaluations": len(data["floor_bay_seat_pairs"]), "source_pages_visually_reviewed": len(pages)},
        "bay_service_trial_counts": dict(Counter(r["service_trial_status"] for r in data["floor_bay_cases"])),
        "representative_bay_cases": representative_cases(data),
        "numerical_audit_status": checked["status"], "tests_passed": checked["tests_passed"], "test_count": checked["test_count"],
        "numerical_digest_sha256": checked["numerical_digest_sha256"],
        "maximum_equilibrium_residual": checked["maximum_equilibrium_residual"], "maximum_energy_residual": checked["maximum_energy_residual"],
        "elapsed_seconds": elapsed, "source_and_protected_files_unchanged": True,
        "all_real_beams_identified": False, "all_real_floors_modelled": False,
        "impact_damage_applied": False,
        "historical_event_probability": None, "new_collapse_outcome": None,
        "V10Y_initialization_mass_and_terminal_state_fixed": False,
        "global_collapse_coupling": False, "blender_changed": False,
        "next_iteration": "V11B", "next_objective": "Fix the V10Y initial-motion resistance/time and mass inventory without retuning the existing scenarios; then connect explicit floor support/connection laws to a cold-stable structural panel."}
    write_json(out / "results_v11a.json", summary)
    output_files = sorted(p for p in out.rglob("*") if p.is_file())
    write_json(out / "offline_manifest.json", {"iteration": "V11A", "status": "PASS",
        "files": [{"path": p.relative_to(out).as_posix(), "size_bytes": p.stat().st_size, "sha256": digest(p)} for p in output_files],
        "input_and_code_manifest": "source_manifest.json", "self_hash_excluded": True})
    print(json.dumps({k: v for k, v in summary.items() if k != "representative_bay_cases"}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
