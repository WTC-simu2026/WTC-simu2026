# IMPACT-I02G — éprouvette M(T) 2024-T3 à fissure explicite

## Résultat exécutif

I02G reproduit la géométrie nominale M(T) publiée (76,2 × 300 × 2,3 mm, fissure centrale totale 25,4 mm, orientation L-T) et exécute huit cas OpenRadioss retenus. La tôle est élastique parfaitement plastique et la fissure suit une ligne cohésive prescrite sans masse. Aucun paramètre n'a été ajusté après calcul pour viser les comparateurs NASA.

Les contrôles de masse, d'énergie, de quasi-staticité et de travail de section passent. Le contrôle sans propagation reste fermé. L'écart élastique entre les mailles 5,08 et 2,54 mm vaut 0.988 %. À maille fine, l'inclinaison interne de 5° change le seuil de première séparation de 0.252 %, donc le contrôle d'orientation passe.

En revanche, le seuil Gf=30 passe de 147.943 MPa à 185.081 MPa lorsque la maille passe de 5,08 à 2,54 mm : l'écart relatif de 20.07 % échoue au critère de 10 %. La maille fine ne propage que de 1,27 mm par côté, sous le minimum de 2,3 mm fixé avant comparaison CTOA. I02G n'est donc pas une validation de fissuration 2024-T3.

## 1. Faits directement observés ou transcrits

- NASA CR-191523 décrit une éprouvette M(T) 2024-T3 de 2,3 mm d'épaisseur, 76,2 mm de largeur, 300 mm de longueur et une fissure/entaille centrale totale de 25,4 mm, chargée en déplacement en orientation L-T.
- Le document situe approximativement le début de déchirure stable vers 200 MPa pour les faibles contraintes de préfissuration et vers 230 MPa pour les fortes contraintes de préfissuration.
- Les Figures 6 et 7 montrent un CTOA de surface qui se rapproche d'environ 6° après une extension de l'ordre d'une épaisseur ; les valeurs proches de l'amorçage sont plus fortes et dispersées.

Source locale en lecture seule : `wtc1_simulation_v8/input/impact_i02f_sources/NASA_CR_191523_2024T3_CTOA.pdf`, SHA-256 `27d91f70b8816927b22f980ae7decb528837abfb19c04335a538ebaa7e6af156`.

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
| Gf=15 N/mm | 147.865 | 2.54 | 2.773° |
| Gf=30 N/mm | 147.943 | 2.54 | 3.023° |
| Gf=60 N/mm | 216.267 | 2.54 | 5.804° |


Le cas grossier Gf=60 donne 216.267 MPa et 5.804° au premier pas, proches des domaines publiés. Cette concordance porte sur un seul saut discret de 2,54 mm et ne survit pas encore à une démonstration de convergence : elle reste un comparateur, pas une calibration ni une preuve.

Le résidu énergétique maximal des cas retenus vaut 0.1033 %, l'erreur maximale entre le travail externe et l'intégrale force-de-section/déplacement vaut 0.0013 %, et le rapport énergie cinétique/énergie interne au pic reste sous 0.0056 %. La force publiée dans les résultats est la somme des `FY` de la section cohésive ; la somme brute des `REACY` nodaux du grip n'a pas fermé le bilan de travail et n'est pas utilisée.

## 6. Contradictions, échecs et informations manquantes

- ÉCHEC : sensibilité du seuil Gf=30 à la maille = 20.07 % > 10 %.
- ÉCHEC : la maille fine atteint seulement Δa=1.27 mm par côté ; aucun CTOA fin n'est comparé au domaine stabilisé après 2,3 mm.
- La tentative 20° a été arrêtée au plafond de 600 s car le mappage comprimait certains éléments ; elle est conservée comme tentative rejetée. La variante 5° termine et passe le contrôle d'orientation.
- Le seuil d'adoucissement et la séparation complète ne sont pas le même événement. Les tableaux les conservent séparément.
- Les courbes contrainte-déformation post-élastiques, les surfaces triaxialité/Lode/vitesse, la longueur interne physique et une énergie de rupture mesurée 2024-T3 restent absentes.
- La localisation en flexion après fracture complète reste non validée.

## Portée

I02G vérifie une éprouvette numérique bornée. Il ne qualifie ni une aile de Boeing 767, ni la façade du WTC1, ni une pénétration historique. Une température imposée n'est pas un incendie calculé. Le contrôle froid V11F et la branche thermique V11R sont préservés. Blender reste une visualisation tant qu'il n'est pas alimenté par des états mécaniques validés.

## Suite IMPACT-I02H

Remplacer les sauts nodaux de la ligne cohésive par une formulation permettant une propagation plus régulière ou une zone cohésive mieux résolue, avec une troisième maille locale économiquement bornée. Identifier une courbe plastique 2024-T3 et des données de ténacité/énergie compatibles avec l'épaisseur et l'orientation ; conserver 200/230 MPa et ~6° comme comparateurs indépendants. Ne transférer vers une deuxième zone I02E qu'après passage de la convergence du seuil et obtention d'au moins deux états CTOA fins au-delà de Δa=2,3 mm.
