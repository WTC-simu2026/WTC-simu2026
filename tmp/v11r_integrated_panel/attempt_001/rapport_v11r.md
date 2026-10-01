# V11R — panneau intégré : thermique, gravité, ferme, dalle et liaisons

## Résultat du jalon

16 configurations, 7288 états engagés ; 16 chemins avec chauffage engagé. 13 configurations satisfont les tolérances de travail/énergie sur leur domaine engagé. PASS des contrôles ne signifie pas que tous les objectifs physiques sont atteints.

| Cas | Charge relative | Dernier temps (s) | États chauffés | Arrêt | Bilan énergie |
|---|---:|---:|---:|---|---|
| REF_G025 | 0.25 | 60.609375 | 431 | STOP_HEATING_ELASTIC_GUARD | PASS |
| THERM_N64 | 0.25 | 60.75 | 432 | STOP_HEATING_ELASTIC_GUARD | PASS |
| THERM_N128 | 0.25 | 60.75 | 432 | STOP_HEATING_ELASTIC_GUARD | PASS |
| THERM_N512 | 0.25 | 60.609375 | 431 | STOP_HEATING_ELASTIC_GUARD | PASS |
| TIME_S160 | 0.25 | 60.75 | 108 | STOP_HEATING_ELASTIC_GUARD | NON QUALIFIÉ |
| TIME_S320 | 0.25 | 60.75 | 216 | STOP_HEATING_ELASTIC_GUARD | NON QUALIFIÉ |
| TIME_S1280 | 0.25 | 60.6796875 | 863 | STOP_HEATING_ELASTIC_GUARD | PASS |
| MESH_2 | 0.25 | 61.171875 | 435 | STOP_HEATING_ELASTIC_GUARD | PASS |
| MESH_8 | 0.25 | 60.46875 | 430 | STOP_HEATING_ELASTIC_GUARD | PASS |
| GRAVITY_0 | 0.0 | 62.859375 | 447 | STOP_HEATING_ELASTIC_GUARD | PASS |
| GRAVITY_050 | 0.5 | 58.359375 | 415 | STOP_HEATING_ELASTIC_GUARD | PASS |
| GRAVITY_100 | 1.0 | 53.4375 | 380 | STOP_HEATING_ELASTIC_GUARD | PASS |
| LOCAL_G025 | 0.25 | 90.0 | 640 | REACHED_SOURCE_END | PASS |
| LOCAL_G100 | 1.0 | 90.0 | 640 | REACHED_SOURCE_END | PASS |
| TIE_SOFT | 0.25 | 60.609375 | 431 | STOP_HEATING_ELASTIC_GUARD | NON QUALIFIÉ |
| TIE_STIFF | 0.25 | 60.609375 | 431 | STOP_HEATING_ELASTIC_GUARD | PASS |

## 1. Faits observés dans les fichiers

V11P fournit les profils résolus ; V11Q a qualifié le transfert de section. V11R assemble ces intégrales dans le panneau V11F/I : dalle-poutre, ferme, sièges, contact compressif, attaches verticales en traction et attaches horizontales. Les sources sauvegardées ne sont pas recalculées.

## 2. Modèles officiels

Les capacités et dimensions documentées héritées restent référencées par les configurations V11A/C/D. Aucun nouveau résultat officiel, incendie ni champ de dommages importé. Le panneau équivalent n’est pas un étage as-built complet.

## 3. Archives locales

Aucune archive rescannée, vidéo analysée ou source modifiée.

## 4. Hypothèses et unités

One-way thermal-to-mechanical coupling. Reuse V11P saved nodal temperatures, exact concrete m0,m1,m2 and discrete reinforcement temperatures, into the inherited small-displacement V11F/I truss/slab panel. All 80 psf reference weight is applied once on the slab, multiplied by the declared gravity factor. Truss, seats and ties remain at 20 C. No damage or artificial stiffness; unilateral contact and tension ties retain reversible piecewise-linear laws.

Central quarter of the longitudinal span receives the saved through-depth profile, elsewhere deltaT=0; boundaries align with steel-panel and slab-element boundaries. This is a declared spatial exposure sensitivity with no lateral conduction, not a room-fire solution. Area-weight the sensible heat. Uniform and local cases are not calibrated to WTC.

Gravité : charge de référence 80 psf, appliquée une seule fois à la dalle ; facteurs 0, 0,25, 0,5 et 1 pré-déclarés. Maillage de dalle : 2/4/8 éléments par travée de ferme, topologie métallique et stations de connexion fixes. Sensibilité de raideur des attaches verticales : 1e7/1e8/1e9 N/m par connecteur équivalent, hypothèses non mesurées.

Dalle : largeur 2,032 m, épaisseur 0,11049 m, béton E=2500 ksi, alpha=1e-5/K ; armatures E=200 GPa, alpha=1,2e-5/K, fraction0,002. Sections planes et petits déplacements, propriétés constantes, forces N, moments N·m, déplacement m, rotation rad, énergie de panneau J. Les profils nodaux et le carré de température sont intégrés exactement dans l’épaisseur ; deux points de Gauss par élément dans la longueur.

Kq−f fournit les résultants N/M de section. L’assemblage Bᵀ(Kq−f), les forces de ferme/contact/attaches et le vecteur de gravité sont équilibrés sur tous les degrés de liberté. Les réactions de sol proviennent des ressorts d’appui ; leur déplacement côté sol est nul. Le travail de gravité et le travail thermique sont calculés séparément de la chaleur sensible.

Retain Uslab+Usprings, external gravity work and exact section endpoint thermal work separately from sensible heat. Work trapezoids can have an active-set crossing defect; report the defect and qualification independently. Do not interpret it as dissipation or repair it by defining work from energy. Only numerically qualified paths can support later visual/mechanical claims. No coupled first-law closure or collapse energy credit.

Solve each trial from the previous accepted displacement; check every element endpoint and longitudinal Gauss section at every thermal depth knot and rebar layer plus all member/seat/tie capacities. First trial above0.9 is saved separately and not committed. Stop also if support directions have no declared capacity. Never adjust gravity or strength after a rejection. Cold preload may itself stop; no heating then. No interpolation of thermal time or guard crossing.

## 5. Résultats dérivés et contrôles

Le contrôle froid compare le nouveau panneau à la ligne V11F COLD_R02 déjà sauvegardée à g=0,25. L’inertie continue modifie légèrement la raideur par rapport aux fibres au milieu des bandes ; cold_comparison.json conserve les écarts. Aucun historique froid endommagé ni ancienne matrice n’est réécrit.

Chaque premier essai refusé est conservé avec son déplacement, ses forces et sa raison, sans engagement. Une direction d’appui sans capacité déclarée constitue un arrêt de qualification, pas une rupture démontrée. Les comparaisons emploient uniquement les temps effectivement sauvegardés et engagés des deux cas ; aucun instant inventé.

## 6. Limites et décisions

Chauffage de la dalle seulement ; ferme et connexions froides, pas d’isolant, humidité, feu de compartiment, géométrie non linéaire, fissuration chaude ou dynamique globale. Les gradients localisés sont une sensibilité sans conduction longitudinale. Une absence de rupture avant l’arrêt ne prouve pas la stabilité du WTC. Localisation en flexion après fracture complète non validée. Blender et ses anciennes animations inchangés.

La priorité suivante est déterminée par les motifs d’arrêt de ce panneau intégré, pas par une nouvelle série de coupons. Les limites refusées restent visibles ; aucun réglage postérieur de charge ou de capacité ne sert à forcer un résultat.

## Suite

Traiter en priorité le premier blocage du panneau intégré identifié dans la synthèse V11R. Ne pas repartir des coupons ni refaire les calculs qualifiés. Compléter seulement la loi ou le contrôle manquant (direction d’appui, domaine fissuré ou bilan de changement de contact selon résultats) avec hypothèses explicites ; préserver la charge nominale comme témoin et la séparation des bilans. Transfert visuel limité aux états mécaniques effectivement qualifiés.

Calcul CPU : 49.78 s ; graine11018 sans tirage. 84/84 contrôles de campagne.
