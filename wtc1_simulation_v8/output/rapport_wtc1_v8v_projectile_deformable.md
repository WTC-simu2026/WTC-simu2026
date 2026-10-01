# WTC 1 — V8V : projectile moteur/capotage minimal déformable

## Résultat

La matrice V8V s'est exécutée sans modifier les archives sources, `C:\OpenRadioss`, `System32` ni les artefacts V8U. Le contrôle de régression V8U par empreintes et métriques est **PASS**. Le portail V8V pré-déclaré est **FAIL: energy_error, baseline_projectile_remaining_mass, medium_to_fine_contact_impulse**.

Ce verdict concerne uniquement un projectile équivalent à deux parties déformables, deux interfaces `/INTER/TYPE7` et un panneau de façade simplifié de trois colonnes par trois étages. Il ne valide ni un JT9D réel, ni l'impact global du vol AA11, ni l'incendie, l'initiation ou la propagation de l'effondrement, ni Blender comme solveur physique, ni une hypothèse d'explosif ou de thermite.

## 1. Faits directement documentés

- NIST décrit les panneaux préfabriqués de façade comme des assemblages de trois colonnes par trois étages, avec colonnes caisson nominales de 14 pouces, entraxe de 40 pouces et allèges de 52 pouces.
- Un acier périphérique spécifié à 60 ksi et une plaque voisine de 5/16 pouce sont documentés près des étages 97–100. Ces données voisines ne constituent pas le bordereau exact du panneau 124 au niveau 96.
- Le registre V8S attribue 20 100 lb aux deux moteurs avec capotages ; V8V conserve exactement la moitié comme masse cible du projectile équivalent.
- La documentation officielle Radioss définit TYPE7 comme un contact nœud-segment déformable et expose, par `/TH/INTER` et `/TH/PART`, les forces de contact, quantités de mouvement, masses, énergies et éléments érodés utilisés ici.

## 2. Résultats d'un modèle officiel utilisés seulement comme contexte

- Les pertes de vitesse de moteur de 56 à 74 mph proviennent de sous-modèles NIST. Elles ne sont pas des observations directes et ne sont pas un portail V8V, car la géométrie et les lois du projectile V8V ne sont pas celles du modèle NIST.

## 3. Hypothèses propres à V8V

- Le noyau moteur est une boîte fermée en coques d'acier équivalent ; le capotage est une boîte ouverte à l'arrière en coques d'aluminium équivalent. Ce ne sont pas des géométries JT9D.
- Les épaisseurs uniformes du projectile sont recalées sur 3 600,0 kg pour le noyau et 958,603 kg pour le capotage. Elles représentent une masse équivalente, pas des épaisseurs réelles.
- Les résistances, déformations de rupture et liaisons du projectile sont des hypothèses de qualification. Le contact est sans frottement et le contact arête-arête TYPE11 n'est pas inclus.
- La façade étendue correspond à l'échelle trois colonnes par trois étages, mais ses soudures, boulons, plaques d'épissure, planchers et sièges de fermes restent absents.

## 4. Résultats dérivés

| Cas | Maille façade (mm) | Maille projectile (mm) | Facteur pas | Fils | Impulsion (kN·s) | Écart bilan qdm | Éléments projectile érodés | Masse projectile restante | Erreur énergie (%) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| M100_P100_DT090_T1 | 100 | 100 | 0.90 | 1 | 139.191 | 0.389% | 344 | 96.294% | -1.584 |
| M050_P050_DT090_T1 | 50 | 50 | 0.90 | 1 | 59.533 | 0.026% | 3894 | 32.291% | 286.586 |
| M025_P025_DT090_T1 | 25 | 25 | 0.90 | 1 | 41.540 | 1.122% | 16339 | 19.529% | 142749.484 |
| M050_P050_DT045_T1 | 50 | 50 | 0.45 | 1 | 65.679 | 0.017% | 4106 | 33.177% | 283.892 |
| M050_P050_DT090_T4 | 50 | 50 | 0.90 | 4 | 59.533 | 0.026% | 3894 | 32.291% | 286.586 |
| M050_P050_DT090_FLO_T1 | 50 | 50 | 0.90 | 1 | 66.054 | 0.041% | 5052 | 17.160% | 276.303 |
| M050_P050_DT090_FHI_T1 | 50 | 50 | 0.90 | 1 | 59.749 | 0.176% | 2641 | 56.538% | 291.041 |

- Écart moyen-fin d'impulsion : **43.316%** (seuil 10 %).
- Écart au demi-pas d'impulsion : **9.358%** (seuil 10 %).
- Répétabilité 1/4 fils de l'impulsion : **0.000%** (seuil 1 %).
- Maximum de l'écart entre la variation du canal cumulatif FNZ et la variation de quantité de mouvement : **1.122%** (seuil 5 %).
- Ordre d'érosion rupture basse / nominale / haute : **5052 / 3894 / 2641**, portail **PASS**.
- Le premier enregistrement des cas 50 et 25 mm, à 0,0207 et 0,0203 ms, précède l'impact de façade : le canal FNZ de façade y est encore nul, mais l'énergie élastique de contact vaut déjà respectivement **2,112 × 10^11** et **2,789 × 10^13** unités solveur. Le cas 100 mm reste nul au premier enregistrement. Cette croissance pré-impact, fortement dépendante du maillage, localise l'instabilité dans l'initialisation du contact interne noyau-capotage plutôt que dans la façade.
- Les cas 50 et 25 mm terminent normalement au sens informatique, mais leur énergie finale et les vitesses de fragments sont non physiques. Leur bon bilan d'impulsion FNZ-quantité de mouvement ne compense pas cet échec énergétique.

## 5. Contradictions, inconnues et décision

- Le bordereau exact des plaques du panneau 124 au niveau 96 reste **inconnu** dans le jeu local gelé ; aucune archive n'a été rescannée pour V8V.
- La géométrie, les matériaux, les assemblages et les lois de rupture à grande vitesse du JT9D restent **non qualifiés**.
- TYPE7 ne qualifie pas à lui seul le contact arête-arête, la fragmentation tridimensionnelle, les ailes, le carburant ou le fuselage.
- L'interface d'auto-contact du projectile doit être isolée en vol libre, instrumentée séparément et corrigée avant de répéter le contact de façade ; aucune impulsion V8V à 50 ou 25 mm ne peut être utilisée comme résultat physique.
- Le portail global impact WTC 1, le couplage thermique et la dynamique Blender restent **fermés**, indépendamment du verdict numérique V8V.

La suite doit conserver V8U et V8V comme régressions. Un passage à une sous-structure plus globale n'est autorisé que si les portails d'impulsion, de pas de temps, de quantité de mouvement, d'énergie, de répétabilité et de rupture ci-dessus sont tous satisfaits ; sinon l'itération suivante doit corriger uniquement les échecs identifiés.
