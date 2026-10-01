"""Create the IMPACT-I02F report and compact scientific summary figure."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "wtc1_simulation_v8/output/impact_i02f_tear_coupon"
CFG = ROOT / "wtc1_simulation_v8/data/impact_i02f_tear_coupon.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    name = "segoeuib.ttf" if bold else "segoeui.ttf"
    path = Path("C:/Windows/Fonts") / name
    return ImageFont.truetype(str(path), size) if path.is_file() else ImageFont.load_default()


def main() -> None:
    report_path = OUT / "rapport_impact_i02f_r1.md"
    figure_path = OUT / "synthese_impact_i02f_r1.png"
    summary_path = OUT / "summary_i02f_r1.json"
    for path in (report_path, figure_path, summary_path):
        if path.exists():
            raise RuntimeError("Existing I02F summary artifact preserved: " + str(path))
    cfg = json.loads(CFG.read_text(encoding="utf-8"))
    campaign = json.loads((OUT / "campaign_audit_r5.json").read_text(encoding="utf-8"))
    comparisons = json.loads((OUT / "comparisons_r5.json").read_text(encoding="utf-8"))
    zone = json.loads((OUT / "ZONE_AA2024_G30_H0635_R0/zone_audit_r0.json").read_text(encoding="utf-8"))
    labels = ["2024\n15", "2024\n30", "2024\n60", "7075\nmin", "7075\nmoy.", "7075\nmax"]
    keys = [
        "AA2024_G15", "AA2024_G30", "AA2024_G60",
        "AA7075_GMIN", "AA7075_GMEAN", "AA7075_GMAX",
    ]
    targets = []
    h4 = []
    h2 = []
    for key in keys:
        coarse = campaign["case_results"][key + "_H4_R3"]["metrics"]
        fine = campaign["case_results"][key + "_H2_R3"]["metrics"]
        targets.append(fine["target_plastic_work_J"])
        h4.append(coarse["plastic_work_at_separation_J"])
        h2.append(fine["plastic_work_at_separation_J"])
    canvas = Image.new("RGB", (1800, 920), "white")
    draw = ImageDraw.Draw(canvas)
    draw.text((900, 28), "IMPACT-I02F — vérification numérique, pas calibration Boeing", anchor="ma", font=font(34, True), fill="#17212b")
    left = (85, 135, 865, 700)
    right = (1015, 135, 1745, 700)
    draw.text(((left[0] + left[2]) / 2, 92), "Cellule de bande fissurée", anchor="mm", font=font(25, True), fill="#17212b")
    draw.line((left[0], left[3], left[2], left[3]), fill="#222222", width=2)
    draw.line((left[0], left[1], left[0], left[3]), fill="#222222", width=2)
    ymax = 1.2 * max(targets + h4 + h2)
    for tick in range(6):
        value = ymax * tick / 5
        y = left[3] - (left[3] - left[1]) * tick / 5
        draw.line((left[0], y, left[2], y), fill="#d9dee3", width=1)
        draw.text((left[0] - 12, y), f"{value:.2f}", anchor="rm", font=font(16), fill="#38444f")
    colors = {"cible": "#111111", "h4": "#3d6f9f", "h2": "#b45c3f"}
    series = [(targets, colors["cible"], "cible analytique"), (h4, colors["h4"], "maille 4 mm"), (h2, colors["h2"], "maille 2 mm")]
    xs = [left[0] + (left[2] - left[0]) * (index + 0.5) / len(labels) for index in range(len(labels))]
    for values, color, _name in series:
        points = [(x, left[3] - (left[3] - left[1]) * value / ymax) for x, value in zip(xs, values)]
        draw.line(points, fill=color, width=4)
        for x, y in points:
            draw.ellipse((x - 6, y - 6, x + 6, y + 6), fill=color)
    for x, label in zip(xs, labels):
        first, second = label.split("\n")
        draw.text((x, left[3] + 18), first, anchor="ma", font=font(17, True), fill="#28343f")
        draw.text((x, left[3] + 40), second, anchor="ma", font=font(16), fill="#28343f")
    draw.text((left[0], left[1] - 24), "Travail plastique (J)", anchor="lm", font=font(18), fill="#28343f")
    for index, (_values, color, name) in enumerate(series):
        x0 = left[0] + 110 + 210 * index
        draw.line((x0, 790, x0 + 45, 790), fill=color, width=5)
        draw.text((x0 + 55, 790), name, anchor="lm", font=font(16), fill="#28343f")
    baseline = {
        "Impulsion\ncontact": 127.2944,
        "Travail\nliaison": 4.867118955,
        "Énergie interne\naile max.": 10215.838667,
    }
    tearing = {
        "Impulsion\ncontact": zone["final_contact_impulse_abs_Ns"],
        "Travail\nliaison": zone["final_joint_work_J"],
        "Énergie interne\naile max.": zone["max_wing_shell_internal_energy_J"],
    }
    names = list(baseline)
    normalized = [100 * tearing[name] / baseline[name] for name in names]
    draw.text(((right[0] + right[2]) / 2, 92), "Zone locale, hypothèse Gf = 30 N/mm", anchor="mm", font=font(25, True), fill="#17212b")
    draw.line((right[0], right[3], right[2], right[3]), fill="#222222", width=2)
    draw.line((right[0], right[1], right[0], right[3]), fill="#222222", width=2)
    for tick in range(0, 121, 20):
        y = right[3] - (right[3] - right[1]) * tick / 120
        draw.line((right[0], y, right[2], y), fill="#d9dee3", width=1)
        draw.text((right[0] - 12, y), f"{tick} %", anchor="rm", font=font(16), fill="#38444f")
    y100 = right[3] - (right[3] - right[1]) * 100 / 120
    draw.line((right[0], y100, right[2], y100), fill="#111111", width=3)
    bar_colors = ["#35618c", "#7f5a83", "#a45542"]
    centers = [right[0] + (right[2] - right[0]) * (index + 0.5) / 3 for index in range(3)]
    for center, name, value, color in zip(centers, names, normalized, bar_colors):
        bar_width = 125
        y = right[3] - (right[3] - right[1]) * value / 120
        draw.rectangle((center - bar_width / 2, y, center + bar_width / 2, right[3]), fill=color)
        draw.text((center, y - 16), f"{value:.1f} %", anchor="mb", font=font(20, True), fill=color)
        first, second = name.split("\n")
        draw.text((center, right[3] + 18), first, anchor="ma", font=font(17, True), fill="#28343f")
        draw.text((center, right[3] + 40), second, anchor="ma", font=font(16), fill="#28343f")
    draw.text(((right[0] + right[2]) / 2, 790), "Trait noir = référence I02E sans rupture du métal (100 %)", anchor="mm", font=font(16), fill="#28343f")
    draw.text((900, 885), "Énergies de rupture hypothétiques/diagnostiques ; aucun résultat historique n'est validé.", anchor="mm", font=font(18), fill="#8b2f2f")
    canvas.save(figure_path)
    max_plastic_error = max(
        result["metrics"]["plastic_work_target_error_fraction"] or 0.0
        for result in campaign["case_results"].values()
    )
    max_force_mesh = max(value["plastic_plateau_force_difference_fraction"] for value in comparisons["mesh_pairs"].values())
    max_plastic_mesh = max(value["plastic_work_difference_fraction"] for value in comparisons["mesh_pairs"].values())
    max_total_mesh = max(value["total_separation_work_difference_fraction"] for value in comparisons["mesh_pairs"].values())
    temporal_max = max(comparisons["temporal_half_dt"].values())
    summary = {
        "iteration": "IMPACT-I02F",
        "status": "PASS" if campaign["status"] == zone["status"] == "PASS" else "FAIL",
        "accepted_solver_revision": "R3",
        "accepted_audit_policy_revision": "R5",
        "unit_cell_cases": len(campaign["accepted_cases"]),
        "unit_cell_case_checks": campaign["case_check_count"],
        "unit_cell_campaign_checks": campaign["campaign_check_count"],
        "maximum_plastic_work_target_error_fraction": max_plastic_error,
        "maximum_mesh_force_difference_fraction": max_force_mesh,
        "maximum_mesh_plastic_work_difference_fraction": max_plastic_mesh,
        "maximum_mesh_total_work_difference_fraction": max_total_mesh,
        "maximum_half_dt_difference_fraction": temporal_max,
        "zone_checks": len(zone["checks"]),
        "zone_first_skin_erosion_time_ms": zone["first_skin_erosion_time_ms"],
        "zone_skin_eroded_shells": zone["max_wing_eroded_shells"],
        "zone_skin_eroded_fraction": zone["skin_eroded_fraction"],
        "zone_skin_mass_loss_g": zone["skin_mass_loss_g"],
        "zone_contact_impulse_Ns": zone["final_contact_impulse_abs_Ns"],
        "zone_contact_impulse_change_fraction": zone["comparison_to_no_metal_tearing_baseline"]["contact_impulse_change_fraction"],
        "zone_global_energy_residual_fraction": zone["max_abs_energy_error_fraction"],
        "physical_2024_tearing_calibrated": False,
        "boeing_767_wing_qualified": False,
        "full_facade_qualified": False,
        "historical_penetration_conclusion_authorized": False,
        "figure": str(figure_path.relative_to(ROOT)).replace("\\", "/"),
    }
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    report = f"""# WTC 1 — IMPACT-I02F : bande de déchirure et transfert local borné

## Résultat

Le portail numérique I02F est **{summary['status']}** : {summary['unit_cell_cases']} cas de cellule, {summary['unit_cell_case_checks']} contrôles de cas, {summary['unit_cell_campaign_checks']} contrôles de campagne et {summary['zone_checks']} contrôles sur le transfert dans une seule zone I02E. La régularisation du **travail plastique prescrit** entre des mailles de 2 et 4 mm est vérifiée. Elle ne constitue pas une calibration physique de la déchirure du 2024-T3 ni une validation du Boeing 767.

Dans la zone locale, l'hypothèse centrale `Gf = 30 N/mm` provoque la première suppression de peau à **{zone['first_skin_erosion_time_ms']:.6f} ms**. **{int(zone['max_wing_eroded_shells'])}/{zone['skin_shell_count']}** coques de peau sont supprimées ({zone['skin_eroded_fraction']:.3%}, {zone['skin_mass_loss_g']:.3f} g). L'impulsion de contact vaut **{zone['final_contact_impulse_abs_Ns']:.4f} N·s**, soit une variation de **{zone['comparison_to_no_metal_tearing_baseline']['contact_impulse_change_fraction']:.3%}** par rapport au même cas I02E sans rupture du métal. Ce résultat est une sensibilité à la loi imposée, pas une conclusion sur l'événement réel.

## 1. Faits directement observés ou transcrits

- NASA CR-191523 étudie une tôle 2024-T3 de 2,3 mm : limite d'élasticité 360 MPa, résistance maximale 495 MPa, éprouvette M(T) de 76,2 × 300 mm avec fissure initiale totale de 25,4 mm. La déchirure stable passe d'un front tridimensionnel/tunnellisé à un régime oblique dont le CTOA de surface devient voisin de 6° après une extension d'environ une épaisseur (PDF pp. 3–16 et figure 1, p. 21).
- NASA/ARL-CR-198 publie pour des panneaux 2024-T3 un CTOA moyen de 5,15° ± 1° et emploie 5,4° dans STAGS avec un cœur de déformation plane et une maille minimale de 1 mm. Ces choix sont ajustés au modèle, pas directement transposables à `/FAIL/TAB1` (PDF pp. 4–5).
- NASA TN D-7262 rapporte, pour une tôle 7075-T6 de 2,3 mm, `E = 69,6 GPa`, `Rp = 523 MPa`, `Rm = 574 MPa` et 12 % d'allongement. Les douze `Kc` en air vont de 45,7 à 61,6 MPa√m (tableaux I et V, PDF pp. 20 et 26).
- La documentation officielle Radioss définit `/FAIL/TAB1` comme une table de déformation plastique à rupture pouvant dépendre notamment de la triaxialité ; le solveur 2026 avertit que cette carte est obsolète et recommande `/FAIL/TAB2`.

## 2. Résultats de modèles officiels ou publiés

- Les valeurs CTOA publiées décrivent la propagation de fissure dans des géométries et orientations précises. I02F ne reproduit ni la géométrie M(T), ni le front de fissure tridimensionnel, ni le modèle STAGS.
- L'équivalent 7075 `G = Kc²/E` donne **30,007 / 44,069 / 54,520 N/mm** (minimum / moyenne de `Kc²` / maximum). C'est une dérivation élastique diagnostique à partir de ténacités d'éprouvettes minces, pas une énergie de rupture ductile mesurée pour une structure d'aile.

## 3. Affirmations des archives locales

- Aucune nouvelle affirmation de l'archive locale n'est utilisée et l'archive source n'a pas été rescannée. Les quatre PDF d'entrée ont été copiés dans le dossier d'entrée I02F et traités en lecture seule ; l'un d'eux (`NASA_19740003601...`) est conservé mais non sélectionné car son contenu ne correspondait pas à la description du résultat de recherche.

## 4. Hypothèses propres au modèle

- La cellule active a une section de 8 × 2,3 mm ; sa longueur vaut la maille `h`. Le matériau est élastique-parfaitement plastique et toute la colonne d'éléments est une bande de localisation prescrite.
- La loi impose `eps_p,rupture = Gf / (sigma_y h)`. Le 2024-T3 est testé à 15, 30 et 60 N/mm ; cette plage est heuristique. La table de rupture est constante avec la triaxialité et ignore Lode, vitesse, température, direction de laminage et endommagement antérieur.
- Le transfert local conserve intégralement la carte I02E existante (`sigma_y = 310,264 MPa`) et son historique énergétique ; seule la rupture de la peau reçoit `Gf = 30 N/mm`, d'où `eps_p,rupture = {zone['qualification']['unit_cell_energy_gate_passed'] and 30/(310.264*6.35):.9f}` au maillage nominal 6,35 mm.
- Les éléments irréguliers de la zone utilisent la même longueur nominale 6,35 mm : ce transfert n'est donc pas régularisé élément par élément.

## 5. Résultats dérivés

- Erreur maximale entre travail plastique calculé et cible : **{max_plastic_error:.3%}**.
- Écart maximal 4 mm ↔ 2 mm : force de plateau **{max_force_mesh:.3%}**, travail plastique **{max_plastic_mesh:.3%}**, travail total jusqu'à suppression **{max_total_mesh:.3%}**.
- Sensibilité au demi-pas de temps : **{temporal_max:.5%}** au maximum.
- Zone locale : résidu énergétique maximal **{zone['max_abs_energy_error_fraction']:.3%}** (portail 5 %), erreur impulsion-contact/moment de l'aile **{zone['contact_wing_momentum_error_fraction']:.3%}**, erreur réaction/moment global **{zone['support_total_momentum_error_fraction']:.3%}**.
- La liaison cohésive ne se supprime toujours pas ; c'est la peau métallique hypothétique qui change ici la réponse. Le travail de liaison diminue de **{zone['comparison_to_no_metal_tearing_baseline']['joint_work_change_fraction']:.3%}** et le maximum d'énergie interne de l'aile de **{zone['comparison_to_no_metal_tearing_baseline']['maximum_wing_internal_energy_change_fraction']:.3%}**.

![Synthèse I02F](synthese_impact_i02f_r1.png)

## 6. Contradictions et informations manquantes

- Les sources donnent des CTOA, propriétés statiques et ténacités d'éprouvettes ; elles ne donnent pas une surface de rupture dynamique 2024-T3/7075-T6 complète pour les pièces réelles d'un 767.
- Une table constante de déformation à rupture ne représente ni l'initiation tridimensionnelle ni le tunneling observé. Le bon prochain test est une éprouvette M(T) entaillée, à deux maillages et orientations, avec propagation et CTOA mesuré.
- Le calcul local ne contient qu'une baie d'aile réduite de 1,98 kg et une colonne représentative, pas l'avion complet ni la façade complète. La baisse d'impulsion n'autorise aucune conclusion sur l'intégrité réelle des ailes, la pénétration historique ou une hypothèse de projection.
- Le bilan énergétique de zone passe de peu (4,856 % pour une limite de 5 %) ; il doit être resserré avec la rupture et la longueur caractéristique avant extension spatiale.
- Le contrôle froid V11F, les itérations I01–I02E et les sources originales restent inchangés.
"""
    report_path.write_text(report, encoding="utf-8", newline="\n")
    summary["report_sha256"] = sha(report_path)
    summary["figure_sha256"] = sha(figure_path)
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"status": summary["status"], "report": str(report_path.relative_to(ROOT)), "figure": str(figure_path.relative_to(ROOT)), "max_plastic_error": max_plastic_error, "zone_eroded_fraction": zone["skin_eroded_fraction"]}))


if __name__ == "__main__":
    main()
