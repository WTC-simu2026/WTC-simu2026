# WTC 1 - V8R : audit de circulation à capacités bornées

## Conclusion

V8R ferme la liberté mathématique illimitée de V8Q et teste **70 combinaisons exactes** de circulation avec intervalles de charge, capacités d'arêtes et capacités externes. Le meilleur cas borné ne satisfait que **0 étage(s) sur 7**. Un cas diagnostique laissant ouverts les chemins internes et externes inconnus en satisfait **7 sur 7**.

La porte froide reste **FAIL** : aucune combinaison V8L/V8M bornée ne couvre simultanément les sept étages, les affectations as-built des poutres et assemblages restent absentes, et les chemins internes/externes non publiés demeurent déterminants. Ce résultat ne démontre ni que les données NIST sont truquées, ni qu'une démolition a eu lieu ; il montre précisément quelle capacité manque dans le modèle réduit.

## 1. Faits et résultats officiels utilisés

- Les intervalles avant/après impact et les sommes des Floors 93-99 viennent de la numérisation V8P des sorties NIST.
- Les 17 arêtes `nist_moment_only` sont une transcription du sous-réseau de poutres de moment du modèle officiel.
- Le graphe orthogonal de 79 arêtes est une reconstruction contrainte par figures, pas le Book 5 as-built.
- NIST indique que son noyau Case B isolé ne capturait pas les transferts via planchers, façades et hat truss.

## 2. Affirmations des archives locales

Aucune nouvelle affirmation provenant des vidéos, affiches ou archives militantes n'est utilisée dans les équations V8R. Les archives originales sont restées en lecture seule.

## 3. Hypothèses de capacité

1. Les profils 12WF65, 14WF136 et 14WF228 encadrent les poutres, mais leur affectation réelle aux arêtes n'est pas connue.
2. Les forces d'arête sont plafonnées soit à l'écoulement, soit juste avant la rotation de rupture de 0,02 rad de la loi V8L.
3. Les arêtes retirées par la figure de dommage V8L au Floor 96 ont une capacité nulle.
4. Les ports externes emploient uniquement la composante verticale calculée par V8M pour 2, 5, 12 ou 25 in. Les limites 44/94 kip ne sont jamais posées directement comme ressorts verticaux.
5. Le signe symétrique des ports est une borne optimiste ; la compatibilité directionnelle réelle n'est pas reconstruite.
6. Le Floor 93 ne reçoit aucune capacité V8L/V8M extrapolée dans l'audit principal.

## 4. Meilleur cas borné

- Arêtes : `orthogonal_upper_prefracture`.
- Ports : `intact_full_drop25`.
- Étages faisables : **0/7**.

| Étage | Variation totale officielle (kip) | Capacité externe symétrique (kip) | Condition nette | Circulation | Déficit (kip) |
|---:|---:|---:|---:|---:|---:|
| 93 | -555 | 0.0 | non | FAIL | 4285.6 |
| 94 | -352 | 252.8 | non | FAIL | 2633.7 |
| 95 | -53 | 252.8 | oui | FAIL | 2955.3 |
| 96 | +261 | 252.8 | non | FAIL | 3458.0 |
| 97 | +399 | 252.8 | non | FAIL | 1896.8 |
| 98 | +400 | 252.8 | non | FAIL | 1271.6 |
| 99 | +398 | 252.8 | non | FAIL | 969.6 |

Les transferts internes peuvent redistribuer la charge entre colonnes, mais ils ne peuvent pas changer la somme du noyau. La différence totale avant/après doit nécessairement passer par un port externe. Cette condition de coupe explique une grande partie des échecs avant même les détails locaux.

## 5. Sensibilité : multiplicateur commun minimal des arêtes et de V8M à 25 in

La table suivante multiplie simultanément les arêtes orthogonales supérieures juste avant rupture et les ports V8M à 25 in. Pour le Floor 93 seulement, les deux enveloppes sont extrapolées comme sensibilité et ne deviennent pas des données as-built.

| Étage | Multiplicateur minimal | Extrapolation Floor 93 |
|---:|---:|---:|
| 93 | 3.500 | oui, sensibilité seulement |
| 94 | 4.189 | non |
| 95 | 4.325 | non |
| 96 | 8.152 | non |
| 97 | 2.990 | non |
| 98 | 2.363 | non |
| 99 | 1.939 | non |

Un multiplicateur supérieur à 1 signifie que l'ensemble arêtes plus ports, à leurs enveloppes préenregistrées, reste insuffisant pour trouver un état dans tous les intervalles.

## 6. Dix meilleures combinaisons bornées

| Arêtes | Ports | Étages faisables |
|---|---|---:|
| moment_lower_yield | intact_full_drop25 | 0/7 |
| moment_upper_prefracture | intact_full_drop25 | 0/7 |
| orthogonal_lower_yield | intact_full_drop25 | 0/7 |
| orthogonal_middle_yield | intact_full_drop25 | 0/7 |
| orthogonal_upper_yield | intact_full_drop25 | 0/7 |
| orthogonal_upper_prefracture | intact_full_drop25 | 0/7 |
| moment_lower_yield | damage_informed_drop25 | 0/7 |
| moment_upper_prefracture | damage_informed_drop25 | 0/7 |
| orthogonal_lower_yield | damage_informed_drop25 | 0/7 |
| orthogonal_middle_yield | damage_informed_drop25 | 0/7 |

## 7. Portes de décision

- Un cas borné cartographié couvre les sept étages : **FAIL**.
- Affectations as-built complètes : **FAIL**.
- Le cas complet exige un chemin interne ou externe inconnu : **OUI**.
- Porte froide globale : **FAIL**.
- Thermique et Blender : **NON AUTORISÉS**.

## 8. Contradictions et informations manquantes

- V8R ne trouve pas de contradiction algébrique avec les intervalles NIST : l'ouverture conjointe des chemins internes et externes inconnus peut restaurer une solution.
- En revanche, les seules enveloppes bornées V8L/V8M documentées dans le harnais ne reproduisent pas les sept états simultanément.
- Le profil exact de chaque poutre, les connexions Book 6, la dalle composite, le diaphragme complet, les liaisons aux façades et leur réponse transitoire restent manquants.
- Le choix optimal n'est pas une preuve de capacité réelle : même le cas supérieur utilise des profils proxy et une distribution uniforme des capacités de face.
- Aucune conclusion sur des explosifs ou la thermite n'est permise par ce test de capacité.

## 9. Impact de l'avion : jalon conservé

La reconstitution d'impact reste obligatoire dans la feuille de route. Elle devra utiliser la masse, la vitesse, l'assiette, l'angle, les étages d'impact et la géométrie officielle, puis comparer les dommages de façade et de noyau. Les images de sortie de la façade opposée devront distinguer le fuselage des moteurs, du train, du carburant et des fragments. Blender ne sera utilisé que pour visualiser une dynamique calculée ailleurs.
