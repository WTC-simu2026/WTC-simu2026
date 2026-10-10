# AIRCRAFT-A22 — attache finie et préparation des matériaux

21 nouveaux contrôles natifs d'une attache mécanique finie sont conservés. Tous les contrôles d'implémentation: **non réussis**. L'attache et la fracture physiques restent non qualifiées. Le dernier aperçu A20 couvre20ms physiques; la vidéo des10premières secondes reste incomplète.

## 1. Faits directement observés ou transcrits

Graine1102047, zéro tirage. Six offsets réels de la première racine A20, chacun subdivisé en4 puis8segments, diamètre circulaire déclaré0,5mm. Translation prescrite, trois rotations prescrites90°, translation libre, trois rotations libres et traction axiale élastique indépendante, soit18contrôles. Trois nouveaux mouvements libres à10rad/ms, au lieu de0,1, rendent l'énergie10000fois plus grande et observable au-dessus du seuil absolu inchangé. Un thread CPU, aucun GPU ni mise à l'échelle de masse. Histoires natives en unités g/mm/ms converties explicitement en J. Les champs de nœuds sont sélectionnés par le titre du groupe, sans supposer qu'ils précèdent PART. Aucun ancien solveur relancé.

La première entrée de translation libre w0 est refusée par26avertissements100217: la seconde ligne requise INIVEL, tempsinitial0/capteur0, avait été omise. Aucun Engine exécuté sur cette entrée. L'erreur, les entrées et le refus restent conservés; une nouvelle copie w1 corrige seulement le format. Les quatre calculs w0 terminés sont réutilisés sans répétition.

La mise à jour GitHub A14–A21 est publiée avant la déclaration A22. Elle contient7917fichiers nouveaux ou actualisés,21archives complémentaires lossless, tous les critères échoués et l'aperçu A20. La vérification distante des tailles, SHA256, auteurs, arbres Git et contrôles automatiques confirme l'intégrité; elle ne qualifie pas la physique. Conservation locale vérifiée de15790fichiers antérieurs, 56.998Go.

## 2. Résultats d'un modèle officiel

La documentation primaire décrit les [poutres finies TYPE3](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/prop_type3_beam_starter_r.htm) et leur [masse répartie aux nœuds](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/beam_elements_r.htm). Les recommandations de longueur et de section sont vérifiées dans les configurations; elles ne constituent pas une qualification du connecteur.

La pagePDF100 du document NIST NCSTAR1-3D (pageimprimée66) donne des paramètres estimés d'écrouissage Voce pour les aciers de façade. La pagePDF101 précise que epsilon_max est la déformation vraie au maximum de traction et au début de striction. Ces pages ont été rendues et vérifiées visuellement. Les dix familles préparées couvrent un début de striction0,070–0,259; ce n'est pas une plage de rupture. L'élasticité de205GPa et les coefficients en ksi, convertis en MPa avec6,894757293168361, restent des candidats de source, sans affectation à la façade du calcul. Les corrections de nuance et de taux, la rupture après striction et sa régularisation restent ouvertes. [Source primaire](https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=101021).

## 3. Affirmations provenant des archives locales

Aucune nouvelle analyse de photographie, vidéo historique ou archive. Lecture seule du PDF de matériau déjà présent dans work/official_sources; son SHA256 est conservé. Réemploi de l'inspection NASA A21, du cœur LAW28 et du sandwich Spot5 p3 A20 réussis. Aucun résultat de dommage NIST ou observé utilisé comme cible.

## 4. Hypothèses propres au modèle

Le diamètre0,5mm, les six connexions ponctuelles et la capacité sont des hypothèses de prototype. Matériau LAW2/1 hérité: rho0,00278g/mm³, E73100MPa, nu0,33, seuil324MPa, écrouissage nul et fracture absente. La capacité axiale élastique par brin est63.617251N; elle ne représente pas une fixation historique mesurée. Les calculs isolés ne changent pas l'avion. Une insertion future ajouterait explicitement **0.334061255g** aux24racines, sans ADMAS ni compensation de densité.

Les inerties de centre de ligne discret et de cylindres continus sont calculées indépendamment. La contribution de section physique est utilisée comme référence analytique, jamais ajoutée artificiellement au bilan natif. Les mouvements prescrits constituent une référence de cinématique et non une preuve de transmission à la peau de l'avion.

## 5. Résultats dérivés

| Contrôle | Segments/brin | Résidu énergétique maximal(J) | Résultat |
|---|---:|---:|---|
| TRANSLATION_X | 4 | 1e-09 | réussi |
| ROTATION_X | 4 | 3.041901e-10 | **échoué**: independent_physical_KE |
| ROTATION_Y | 4 | 6.375467e-10 | **échoué**: independent_physical_KE |
| ROTATION_Z | 4 | 3.998372e-10 | **échoué**: independent_physical_KE |
| FREE_TRANSLATION | 4 | 0 | réussi |
| FREE_ROTATION_X | 4 | 8.7977241e-14 | réussi |
| FREE_ROTATION_Y | 4 | 1.0262422e-14 | réussi |
| FREE_ROTATION_Z | 4 | 7.909028e-14 | réussi |
| AXIAL | 4 | 9.85017e-11 | réussi |
| TRANSLATION_X | 8 | 1e-09 | réussi |
| ROTATION_X | 8 | 4.954323e-10 | réussi |
| ROTATION_Y | 8 | 1.2511107e-09 | **échoué**: independent_physical_KE |
| ROTATION_Z | 8 | 7.665594e-10 | réussi |
| FREE_TRANSLATION | 8 | 0 | réussi |
| FREE_ROTATION_X | 8 | 6.4772087e-14 | réussi |
| FREE_ROTATION_Y | 8 | 1.007176e-14 | réussi |
| FREE_ROTATION_Z | 8 | 7.998316e-14 | réussi |
| AXIAL | 8 | 9.69646e-11 | réussi |
| FREE_ROTATION_X | 8 | 1.50622e-09 | réussi |
| FREE_ROTATION_Y | 8 | 1.28646e-07 | **échoué**: independent_initial_KE |
| FREE_ROTATION_Z | 8 | 9.9228e-08 | réussi |

Tous les seuils sont pré-déclarés. Les21bilans énergétiques natifs passent. Les trois rotations prescrites échouent à l'inertie physique sur4segments. Sur8segments,X etZ passent, maisY garde un écart de14,37% sur le pic cinétique; la nouvelle rotation libreY confirme un écart d'énergie initiale au-dessus du seuil absolu. Le contrôle axial conserve la réponse analytique élastique et les translations conservent leur masse et leur mouvement.

L'audit en cache des six rotations sépare les canaux natifs: la contribution RKE correspond à une inertie identique surXYZ de0,002480230g·mm² pour4segments et0,000783173g·mm² pour8segments. Les cylindres indépendants donnent0,000219535/0,000429749/0,000220667g·mm² pour la seule section physique. Le raffinement réduit l'écart scalaire sans qualifierY. Ce sont des diagnostics des champs natifs; aucun terme n'est ajouté au bilan, aucun seuil élargi, aucune densité ajustée. Le défaut local entier A21 n'est pas expliqué par ce seul témoin. Les mouvements libres à0,1rad/ms ont une énergie enY inférieure au seuil absolu; leur réussite littérale est conservée mais ne qualifie pas l'inertie.

Les fichiers natifs, les entrées, le script utilisé, les champs convertis, les masses, les inerties et chaque échec sont conservés. Voir connector_review.json, native_inertia_audit.json et les review.json individuels. Dix courbes d'écrouissage acier sont préparées uniquement comme candidats bornés avant striction, dans steel_hardening_candidates.json; aucune n'est insérée dans le solveur entier. La conversion en déformation plastique au début de striction comporte une hypothèse explicite de contrainte d'ingénieur au pic, à confirmer avant emploi.

## 6. Contradictions et informations manquantes

Les contrôles de cinématique, d'énergie et de matériau sont distincts. La transmission à une peau réelle, les surfaces de contact/bearing, la capacité en cisaillement et arrachement, les modes de rupture et le budget de masse de l'attache restent à vérifier. Aucun contrôle isolé ne prouve la cause complète du déficit A21. Les limites matérielles et le bilan local de l'avion entier restent échoués. Les données NASA d'un essai ATR42 à9,14m/s ne mesurent pas la fracture AA11 à200m/s. La correspondance des nuances d'acier, l'écrouissage de l'aluminium, le taux, la triaxialité, la maille et l'énergie de rupture restent nécessaires. Gravité, intérieur porteur et contact des fragments n'ont pas été ajoutés par ces témoins.

AIRCRAFT-A23 : reprendre les témoins finis A22, sans relancer les anciens calculs. Lire connector_review.json, native_inertia_audit.json, les énergies et les champs natifs de chaque cas, ainsi que material_preparation.json. Les poutres sont une hypothèse de connecteur, pas une attache historique identifiée. Aucune RKE reconstruite ni compensation de masse. Réutiliser le cœur et Spot5 p3 A20 réussis. A22 conserve les21bilans natifs mais l’inertie physique échoue enY sur8segments et sur le mouvement libre observable. Le champ RKE révèle une inertie scalaire identique enXYZ,0,000783173g·mm² contre une section physique enY0,000429749; cela ne prouve pas la cause du déficit entier A21. Comparer un connecteur volumique à degrés de liberté de translation et une référence indépendante, avec géométrie et budget déclarés, avant insertion. Si tous les contrôles d’implémentation passent, vérifier ensuite la transmission à une peau réelle et sa dynamique libre avant un départ intact entier; la masse de24racines serait explicitement ajoutée,0,334061g, pas masquée. Le tableau acier3-13 donne des paramètres d’écrouissage estimés et un début de striction, pas une fracture. Les courbes préparées sont des candidats non insérés; vérifier la conversion et la correspondance des nuances, puis témoins élastique/plastique, décharge, taux, maille et rupture énergétique. NASA ATR42 à9,14m/s reste un autre modèle, pas la rupture AA11 à200m/s. Les bilans local et matériaux A21 restent échoués. Gravité, intérieur porteur et contact des fragments à compléter avant10s. Objectif vidéo3D10secondes physiques incomplet; le MP4/GIF A20 couvre20ms. A14–A21 publiés et vérifiés; A22 seule locale, prochaine publication après A23 vérifiée.
