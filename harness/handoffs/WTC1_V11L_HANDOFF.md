# WTC1 — passation V11L vers V11M

## Reprise

Lire `AGENTS.md`, `harness/state.json`, puis cette passation. L'état local actuel prévaut sur les anciens points V8H/V11H. Exécuter `harness/tools/Test-WtcHarness.ps1` depuis la racine avant toute modification importante.

## V11L achevée

Premier transfert unidirectionnel d'un profil transitoire V11K sauvegardé vers le panneau thermoélastique V11I non endommagé, à 0,25 gravité. Le treillis et les assemblages gardent leurs températures et lois froides.

- 33/33 contrôles numériques ; 25/25 contrôles de relecture indépendante.
- 5 cas et 314 états de référence : froid, uniforme +100 K, gradient linéaire +5 K, profil courbe V11K, moyenne uniformisée de V11K.
- Comparaisons : demi-pas d'interpolation, panneau 4→8 subdivisions, fibres 160→320.
- Contrôles V11F, V11H, V11I et V11K vérifiés par empreintes ; anciens pilotes non relancés.
- Calcul validé : `tmp/v11l_profile_panel/attempt_003`, environ 8,24 s CPU.
- Sorties finales : `wtc1_simulation_v8/output/v11l_profile_panel/` ; copie exacte de la tentative 003 et audit de relecture final PASS.
- Empreinte numérique : `81f6e861e6f1223fd43837acc33654ff1a71fb46576d185c7bfb5831f02ea0d2`.

## Résultat essentiel

Le profil courbe atteint le garde-fou DCR=0,9 à la **coordonnée interpolée 64,576253 s**, entre les profils thermiques sauvegardés à 45 et 90 s. Le garde-fou gouvernant est la traction du béton à un point intérieur du profil. Cet instant n'est pas un temps de rupture ni un temps thermique résolu.

À cet état accepté :

- énergie élastique : 275,423556 J ;
- travail extérieur cumulé : 94,287547 J ;
- travail thermoélastique : 181,136009 J ;
- réaction verticale : 35 239,800130 N ;
- enthalpie sensible du coupon étendu au panneau : 17 689 070,887 J ;
- enthalpie sensible du panneau composite : 17 655 062,545 J ;
- écart composite moins coupon : −34 008,342 J.

Résidu mécanique énergétique relatif maximal : 4,38e-11. Le retour par parcours inverse retrouve le déplacement froid à 5,43e-15 m près. Ce parcours inverse vérifie la réversibilité mécanique ; il ne calcule pas un refroidissement.

Le demi-pas d'interpolation ne change pas la coordonnée d'arrêt à la précision de recherche. Le panneau raffiné donne 64,436101 s (écart d'environ 0,217 %), les 320 fibres donnent 64,576366 s. Les déplacements, réactions et énergies ont aussi été comparés à une coordonnée commune.

## Transfert et énergie

Les profils V11K proviennent des températures aux centres de 64 cellules. Une interpolation linéaire avec prolongement unilatéral vers les faces est remise à l'échelle pour conserver la moyenne FV. Une correction multiplicative des températures des fibres de béton conserve la moyenne et le gradient linéaire équivalent M1/I en respectant la quadrature V11H. Les armatures reçoivent la température du profil continu à leurs positions.

La correction conserve les zones initialement froides. Son maximum dans les fibres est 0,0847 K. Les écarts de température aux surfaces V11K et l'écart de moment absolu dû à la quadrature sont enregistrés. La reconstruction est qualifiée pour ce chauffage positif ; elle n'est pas un remappeur général chauffage/refroidissement mixte.

Le coupon thermique est homogène ; le panneau remplace 0,2 % de la section par des armatures avec leur propre capacité thermique. La différence d'enthalpie est donc un **écart déclaré**, pas un bilan thermodynamique couplé fermé. Il n'y a pas de rétroaction vers la conduction. Le travail thermoélastique reste séparé de la chaleur sensible.

## Tentatives conservées

- 001 : les contrôles initiaux passaient, mais la relecture a détecté un sous-dépassement de 0,02 K sous la référence froide causé par la correction additive de moyenne. Tentative rejetée scientifiquement.
- 002 : correction multiplicative et 33 contrôles PASS ; conservée comme intermédiaire avant enrichissement de l'audit et de la documentation.
- 003 : version publiée, 33 contrôles et 25 audits PASS.

## Fichiers à consulter sans relancer l'historique

- `wtc1_simulation_v8/data/v11l_profile_panel.json` : configuration et critères.
- `wtc1_simulation_v8/scripts/v11l_profile_panel.py` : adaptateur et continuation.
- `wtc1_simulation_v8/scripts/run_v11l_profile_panel.py` : calculs, comparaisons et tests.
- `wtc1_simulation_v8/scripts/audit_v11l_profile_panel.py` : audit indépendant ; option `--read-only` pour relire les sorties déjà auditées.
- Dans le dossier final : `results_v11l.json`, `panel_runs.json`, `comparisons.json`, `section_controls.json`, `numerical_audit.json`, `release_audit.json`, `offline_manifest.json`, `source_manifest.json`, `rapport_v11l.md`.

## V11M — étape suivante bornée

Résoudre et sauvegarder finement les premières minutes thermiques, particulièrement entre 45 et 90 s, pour mesurer séparément la sensibilité de la coordonnée du premier garde-fou :

1. au pas du solveur thermique et à la fréquence de sauvegarde ;
2. au maillage thermique en profondeur ;
3. à la reconstruction des températures près des surfaces.

Utiliser V11K comme contrôle sauvegardé et ses équations constantes comme référence. Créer une nouvelle itération sans modifier V11K/V11L. Le demi-pas d'interpolation V11L ne remplace pas une étude de convergence du calcul thermique. Maintenir les contrôles froids, le suivi des réactions et les bilans d'énergie. Examiner l'écart de capacité thermique composite avant toute affirmation de couplage thermodynamique fermé.

## Limites permanentes

Le palier est `synthetique_non_WTC`. Une température imposée n'est pas un incendie calculé. Propriétés froides constantes, pas de fissuration chaude ni modification d'historique endommagé. La localisation en flexion après fracture complète reste non validée. Le garde-fou n'est pas une température critique réelle, une preuve de rupture, de sécurité ou de survie. Aucun impact, effondrement global, retour thermodynamique ou changement Blender n'est calculé ici. Blender reste une visualisation ; crédit énergétique global nul.
