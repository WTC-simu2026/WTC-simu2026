# IMPACT-I02A — premier contact d'une section d'aile structurée

Date : 12 septembre 2026. Branche prioritaire : premier contact avion-façade. La branche thermique reste V11R terminée/V11S différée ; le contrôle froid V11F est conservé. Aucun ancien calcul n'a été relancé.

## Résultat livré

IMPACT-I02A remplace le caisson creux générique I01 par une section 3D contenant deux peaux, deux longerons, quatre nervures et des raidisseurs en Z. Trois cas OpenRadioss ont terminé normalement : vol libre, contact nominal et pas de temps divisé par deux. Les 17 contrôles numériques pré-déclarés passent. L'impulsion du cas nominal à 1,195058 ms vaut **4378,67 N·s** ; le demi-pas donne **4377,54 N·s**, soit **0,0258 %** d'écart. Le contrôle I01 de masse presque identique donne 6016,60 N·s : la topologie change donc de 27,22 % la réponse de ce modèle réduit.

Ce résultat **ne dit pas si une aile réelle se brise ou reste intacte**. La rupture et l'érosion sont désactivées, les jonctions sont parfaites et les déformations plastiques finales dépassent largement les allongements statiques de référence. C'est un témoin supérieur de connectivité, utile pour préparer une vraie étude de rupture, pas une simulation qualifiée du Boeing 767 complet ni du WTC1 réel.

Livrables principaux :

- animation exacte des 25 états sauvegardés : `wtc1_3d_v4/renders/impact_i02a/IMPACT_I02A_solver_states.gif` ;
- scène 3D : `wtc1_3d_v4/output/impact_i02a/IMPACT_I02A_SOLVER_STATES.blend` ;
- synthèse calcul : `wtc1_simulation_v8/output/impact_i02a_structured_wing/synthese_impact_i02a.png` ;
- audits : `campaign_audit.json`, `animation_export_audit.json`, `wtc1_3d_v4/output/impact_i02a/blender_audit.json` et `animation_audit.json`.

## 1. Faits directement observés dans les sorties

- Les trois moteurs OpenRadioss finissent normalement, sans avertissement Starter dans les cas acceptés, sans pénétration initiale signalée, sans ajout significatif de masse et sans élément érodé.
- Le témoin sans contact conserve exactement son énergie dans l'historique et sa vitesse finale s'écarte de la valeur imposée de 1,01e-7 en relatif.
- Cas nominal : erreur énergétique absolue maximale 1,9754 %, énergie numérique des pièces maximale 0,2409 % de l'énergie cinétique initiale, erreur impulsion-contact/variation de quantité de mouvement de l'aile 0,01464 %, erreur réaction d'appui/variation de quantité de mouvement totale 0,00867 %.
- Cas demi-pas : valeurs correspondantes 1,9749 %, 0,2412 %, 0,00736 % et 0,00426 %.
- La première impulsion de contact supérieure à 1 N·s apparaît vers 0,22 ms. La masse de la section est 175,48644 kg et son énergie cinétique initiale 3,440953 MJ.
- À la fin du cas nominal, la vitesse axiale massique moyenne de la section vaut -173,0823 m/s ; l'énergie cinétique globale vaut 2,847529 MJ et l'énergie interne 541,5921 kJ, dont 472,8472 kJ dans la section d'aile.
- Le premier essai `FREE_M050` est conservé mais rejeté : sept avertissements provenaient d'un champ coque Istrain obsolète. Les trois cas suffixés `_R1` corrigent ce champ sans changer les propriétés physiques déclarées.

## 2. Résultats du modèle officiel réutilisés

Le [NIST NCSTAR 1-2B](https://nvlpubs.nist.gov/nistpubs/Legacy/NCSTAR/ncstar1-2bv1.pdf) décrit, pour son modèle de petite section d'aile, quatre nervures de hauteur uniforme, un longeron avant, un longeron arrière, des raidisseurs en Z et deux peaux. Il indique une peau supposée de 0,1 in et donne comme dimensions typiques d'un raidisseur environ 1 in pour les semelles, 2 in pour l'âme et 1/8 in d'épaisseur. Il décrit aussi des liaisons par rivets et des interfaces de type tiebreak dans ses propres modèles.

Le même rapport précise que NIST n'a pas effectué d'essais de matériau spécifiques sur l'avion et a construit les courbes 2024/7075 à partir de références publiques. Dans son calcul officiel raffiné de composant à 442 mph, il rapporte la déchirure des longerons, nervures et peaux et environ 43 % d'énergie cinétique résiduelle pour les débris d'aile, tandis que les colonnes ne sont pas complètement sectionnées. C'est un **résultat du modèle NIST**, pas une observation directe, et I02A ne cherche pas à le reproduire : la rupture est ici supprimée.

## 3. Affirmations des archives locales

Aucune nouvelle affirmation d'archive n'est transformée en paramètre mécanique. Les vidéos Evidence1/2 ne sont pas réanalysées dans ce lot. Une apparence de continuité, de disparition ou de pénétration dans une vidéo compressée ne mesure ni les contraintes, ni les ruptures internes, ni la masse transmise.

## 4. Hypothèses, propriétés et unités

Système d'unités : g, mm, ms, MPa. Une unité de force vaut 1 N, une unité d'impulsion 0,001 N·s et une unité d'énergie 0,001 J. La vitesse 443 mph est convertie par 0,44704 en **198,03072 m/s**.

| Élément | Valeurs utilisées | Statut épistémique |
|---|---|---|
| Enveloppe de section | 3,0 m de portée × 2,0 m de corde × 0,4 m d'épaisseur | Héritée de I01, entièrement hypothétique ; pas la géométrie Boeing entre nervures 14–18 |
| Peaux | 2,54 mm | Hypothèse NIST explicitement publiée pour son modèle simplifié |
| Longerons et nervures | 3,175 mm | Hypothèse pilote, égale à l'épaisseur typique du raidisseur ; non sourcée pour ces pièces |
| Raidisseur en Z idéalisé | âme 50,8 mm, semelle libre 25,4 mm, épaisseur 3,175 mm | Dimensions typiques NIST ; la peau coïncidente fournit l'autre semelle |
| Nombre de raidisseurs | 10 par peau | Interprétation de la figure NIST ; le texte « ten z-stringers » peut aussi signifier dix au total, donc une sensibilité 5/par peau reste obligatoire |
| Peau, proxy 2024-T3 clad | rho 2780 kg/m³ ; E 73,1 GPa ; nu 0,33 ; limite 310,264 MPa ; élasto-plastique parfait | Valeurs statiques typiques du manuel USAF/NAVAIR TO 1-1A-1, pas une carte Boeing de production |
| Internes, proxy 7075-T6 | rho 2810 kg/m³ ; E 71,7 GPa ; nu 0,33 ; limite 503,32 MPa ; élasto-plastique parfait | Affectation approximative ; pas de carte matière as-built |
| Façade | 3 colonnes représentatives et une allège, géométrie I01 | Pas le calendrier exact de tôles du panneau WTC1 frappé |

Le manuel [USAF/NAVAIR TO 1-1A-1](https://everyspec.com/USAF/USAF-Tech-Manuals/download.php?spec=TO_1-1A1-A_15JAN2016.056663.pdf), tableau 4-4, donne aussi des résistances ultimes/allongements typiques : 448,16 MPa/18 % pour 2024-T3 clad et 572,264 MPa/11 % pour 7075-T6. Ces deux limites **ne sont pas utilisées comme critères de rupture** dans I02A.

Toutes les intersections peau-longeron-nervure-raidisseur emploient des nœuds fusionnés. Cela représente une liaison parfaite et indestructible, pas les rivets de l'aile. Le contact est TYPE7 unilatéral, sans frottement, sans auto-contact ni contact arête-arête. Les appuis haut/bas de la façade sont bloqués ; aucun plancher, noyau, chargement gravitaire ou souplesse globale de la tour n'est présent.

## 5. Résultats dérivés et sensibilité

| Grandeur au temps commun 1,195058 ms | I02A nominal | I02A demi-pas | I01 caisson fermé |
|---|---:|---:|---:|
| Impulsion de contact, N·s | 4378,6703 | 4377,5390 | 6016,6042 |
| Écart nominal/demi-pas | 0,02584 % | — | — |
| Masse, kg | 175,48644 | 175,48644 | 172,8 |
| Variation I02A/I01 de l'impulsion | -27,2236 % | — | — |

La très faible sensibilité au pas de temps qualifie ce paramètre numérique dans le domaine testé. Elle ne qualifie ni le maillage spatial, ni le contact en plis, ni la loi matière, ni la rupture. L'écart de 27 % à masse presque constante démontre seulement que la topologie interne et les épaisseurs choisies comptent fortement ; il ne mesure pas l'impact réel.

La déformation plastique équivalente maximale nominale atteint 0,0514 dans les colonnes, 0,0050 dans l'allège, 2,2586 dans les peaux, 2,7484 dans les longerons, 0,9312 dans les nervures, 0,2408 dans les âmes de raidisseurs et 0,4678 dans leurs semelles. Le demi-pas change le maximum par pièce d'au plus 1,221 %. Les valeurs supérieures à 1 sont possibles numériquement avec une loi sans dommage, mais elles sont très au-delà des allongements statiques typiques cités : **les formes tardives ne sont pas une prédiction physique d'une aile intacte**.

## 6. Transfert Blender vérifié

Le fichier Blender contient 25 formes, une par état OpenRadioss de 0 à 1,2 ms, 21 920 sommets et 22 074 faces coque. La réouverture indépendante retrouve exactement la connectivité, les identifiants de pièce et toutes les coordonnées transformées mm→m ; erreur maximale mesurée **0 m** dans la précision stockée. L'interpolation est constante. Aucun corps rigide, modificateur mécanique, moteur physique, fracture ou amplification de déplacement n'est actif.

Le GIF étire les 1,2 ms physiques sur 5 s et présente chaque état exact pendant 0,2 s. Il n'invente aucun état intermédiaire. Le rouge signale uniquement epsilon plastique équivalente > 0,20, seuil d'affichage arbitraire. Blender est donc relié aux états mécaniques sauvegardés, mais reste un visualiseur et ne répare aucune limite du modèle.

## 7. Ce qui est établi, non établi, et suite

Établi : une section structurée non érodante peut être calculée de façon stable sur 1,2 ms dans ce montage ; ses bilans d'énergie, de quantité de mouvement et de réactions satisfont les seuils déclarés ; la topologie modifie matériellement l'impulsion par rapport au caisson I01 ; le transfert 3D est exact.

Non établi : géométrie/matériaux Boeing as-built, tenue ou rupture des rivets, fragmentation, interaction complète aile-fuselage-moteurs-carburant, panneau exact de façade, dommages intérieurs, incendie, effondrement, ni correspondance causale avec une vidéo. I02A ne peut ni confirmer une « aile intacte », ni démontrer une projection, ni valider ou invalider à lui seul le récit global.

Suite IMPACT-I02B : conserver I01 et I02A comme témoins sans rupture ; construire d'abord un coupon peau-raidisseur/rivet ou une interface tiebreak avec énergie de séparation explicite, puis une petite section rompable. Balayer au minimum 5/10 raidisseurs par peau et des épaisseurs de longeron/nervure basses/base/hautes. Exiger objectivité de l'énergie dissipée et sensibilité 50→25 mm avant tout modèle plus large. Ne pas régler une rupture pour imiter une silhouette vidéo.

## Reproductibilité

Configuration : `wtc1_simulation_v8/data/impact_i02a_structured_wing.json`. Calcul : `run_impact_i02a.py`. Extraction : `export_impact_i02a.py`. Audit : `audit_impact_i02a.py`. Synthèse : `plot_impact_i02a.py`. Blender : `build_impact_i02a.py`, `verify_impact_i02a_blend.py`, `encode_impact_i02a_gif.py`. Solveur OpenRadioss 20260728, Blender 5.2.0 LTS, graine 9112001, aucun tirage. Temps moteur accepté : environ 103 s, 125 s et 252 s ; aucun calcul de plusieurs heures.

