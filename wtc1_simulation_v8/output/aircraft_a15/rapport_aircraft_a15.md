# AIRCRAFT-A15 — lancement de l'avion complet contre la façade

**Le prototype complet a réellement été lancé dans OpenRadioss contre une façade déformable, sans trajectoire imposée.** Un essai atteint **10.000361400 ms ≈0,01s**, contre0,4ms dans A11. L'essai au demi-pas est arrêté au plafond de coût déclaré600s ; ses données disponibles vont jusqu'à **6.240026 ms**. Cet essai incomplet reste incomplet. Aucun ancien solveur relancé, aucune cible de dommages NIST utilisée.

Le déplacement maximal de façade dans les états échantillonnés atteint **394.812 mm**. L'impulsion X principale vaut **-48.114390 kN·s** au dernier historique9,990103ms. Le nez transmet l'effort ; nacelles, fan et core n'ont pas encore de contact. Les bilans déclarés du cas achevé passent, mais **les limites matérielles échouent**. Cette avance est une expérience exploratoire, pas une reconstruction qualifiée de l'impact historique.

## 1. Faits directement observés ou transcrits

Deux Starter sans erreur ni avertissement. IMPACT_10_DT50 termine normalement ; l'observateur lit son état final sans modifier les sorties principales. IMPACT_10_DT25 porte explicitement TIMEOUT dans le journal et un fichier retained_failure conservé ; pas d'observateur, pas de fin réelle certifiée. Sa dernière image stockée est à6.200158596ms ; son dernier historique n'est pas un timestamp de fin.

Les1000 lignes principales du cas achevé et les625 lignes disponibles du cas incomplet sont vérifiées, tous canaux, contre les records binaires natifs. Le premier record de l'observateur confirme la fin et les énergies. Contact FNX/FNY/FNZ et REAC des appuis sont des **impulsions cumulatives**, converties N·ms→0,001N·s, sans réintégration. Les REAC et contacts de l'observateur sont exclus de tous les bilans de transfert car leurs cumuls repartent à zéro.

Lecture des temps corrigée et tracée : le convertisseur VTK affiche six chiffres significatifs ;10,000361ms est affiché10,0004ms. Le premier audit rejetait cette image avec une tolérance absolue trop fine. Le script antérieur et son journal d'échec sont conservés. Le lecteur utilise maintenant le temps float32 du fichier natif FASTMAGI10, vérifie l'accord avec la précision affichée du convertisseur, puis les coordonnées, IDs et vitesses. Aucun solveur ni seuil physique relancé ou modifié pour cette correction.

Ce sont des observations sur des fichiers numériques, aucune nouvelle observation historique.

## 2. Résultats d'un modèle officiel

Aucun résultat officiel de dommages, de pénétration, de trajectoire ou d'effondrement n'est utilisé comme cible. Les sorties nouvelles sont celles d'OpenRadioss v20260728-win64, empreintes et arguments enregistrés dans execution_summary.json. La façade représentative hérite d'entrées nominales NIST des branches précédentes ; sa géométrie et ses sections ne constituent donc pas un modèle historique entièrement indépendant. Cette dépendance d'entrée est distincte d'un ajustement aux résultats NIST.

La documentation primaire TYPE25 déjà copiée et épinglée dans A14 décrit le contact nœuds/surface. Les références Boeing/CF6 et sandwich sont celles du manifeste A11, avec leurs réserves d'attribution et leurs conversions originales. Aucune propriété nouvelle n'est attribuée à l'avion réel dans A15.

## 3. Affirmations provenant des archives locales

Aucune vidéo, photographie ou PDF source nouvellement inspecté ou modifié. **8795 fichiers antérieurs**, **39.520 Go**, recontrôlés intégralement par SHA-256 sans différence. Les archives et work/official_sources restent en lecture seule. V11F/V11R, les rapports A11-A14 et leurs critères échoués restent intacts.

Le module Boeing parallèle v2 n'est pas intégré : ses défauts d'inertie/dynamique libre restent ouverts. Le prototype principal déjà exécutable est celui utilisé ici. La dernière publication distante vérifiée reste A12+A13 ; A14+A15 devient la paire locale à publier selon la cadence, aucune publication externe réalisée par ce script.

## 4. Hypothèses propres au modèle

Configuration aircraft_a15_predeclaration.json épinglée avant calcul, graine1102040, zéro tirage. Deux départs neufs de l'avion intact ; aucun dommage réinjecté ni continuation cachée. La demande directe de Jeremy de lancer l'avion change le programme A15 auparavant limité à des témoins locaux : l'exécution exploratoire est autorisée, **la qualification A14 et ses échecs ne sont pas réécrits**.

Géométrie, matériaux, masse, RBE3, assemblages, conditions aux limites et vitesse hérités exactement de A11/NOSE_04_DT05 ; cartes NODE/MAT/PROP/SHELL/SH3N/BEAM/ADMAS/RBE3/BCS/INIVEL comparées à l'identique.37228 nœuds, dont5436 d'avion et31792 de façade ;10378 triangles d'avion,4464 poutres,31986 quadrilatères de façade. Façade de trois étages représentatifs, environ59,3m×10,97m, **944 nœuds de bord fixes et intérieur déformable**. Masse native avion **121962.861144 kg**, ensemble **191273.837943 kg**. Il s'agit de la masse du prototype ; les conditions historiques AA11 ne sont pas établies.

Vitesse initiale[-200,5,2]m/s, façade initiale X=−50mm, nez X=0, gap5mm. Quatre contacts extérieurs passent de TYPE7 à TYPE25 canonique : surfaces[0,1003], groupes secondaires1100/1101/1102/1103 conservés, mode3, Stfac1 et Istf4, pas de pondération par aire. L'auto-contact TYPE7 du radôme est conservé ; auto-contact global de l'avion absent. La pénalité est une option numérique non qualifiée spatialement, pas une raideur physique identifiée.

Radôme sandwich0,5/8/0,5mm, LAW25+TYPE51/TYPE19 élastique avec plafonds de rupture numériques très élevés : ni rupture, ni écrasement d'âme, ni délamination. Matériaux métalliques plastiques hérités, sans rupture ni érosion ; assemblages idéaux et paramètres approximatifs. Le carburant n'est pas résolu ; pas de feu ni d'intérieur de tour. Aucune masse ajoutée ou nouvelle mise à l'échelle de masse, aucun pilotage de pénétration.

Deux facteurs de pas stable0,5/0,25, durée demandée10ms chacun, deux threads CPU, zéro GPU, plafond600s par principal. Le premier prend502.42s ; le demi-pas dépasse ce plafond. Ce plafond est un choix de coût, pas une instabilité ni une réussite scientifique. TH tous0,01ms ; animations natives tous0,1ms ;96 sondes nodales déclarées, toutes les masses/vitesses/positions conservées dans les animations. Vérification détaillée du cas achevé sur **21 états régulièrement échantillonnés tous≈0,5ms**, premier et dernier inclus ; toutes les images brutes restent conservées. Les maxima matériels et de déplacements rapportés sont des maxima **échantillonnés**, pas une certification de chaque image.

Unités d'origine g/mm/ms/MPa/N/N·mm ; g→0,001kg, mm→0,001m, ms→0,001s, N·mm→0,001J et N·ms→0,001N·s. mm/ms=m/s. Ledger : KE+rotation globale+IE+hourglass+spring+contact élastique/frottement/amortissement−travail externe, chaque terme une fois. Travail plastique inclus dans IE ; aucun RKE reconstruit ou par pièce ajouté.

Seuils A11 conservés : masse relative10⁻⁶ ; résidu global≤0,5% KE initiale ; local≤5% énergie hors translation+1000J au-dessus1000J ; quantité de mouvement≤10N·s+2% max impulsion ; comparaison demi-pas≤5% d'impulsion et10% d'énergie hors translation ; déformation plastique de diagnostic≤0,1 ; ratio de résistance des peaux du radôme≤1. Ces résistances sont des références sandwich, pas des résistances AA11 identifiées. L'avion entier n'est pas qualifié par les témoins plans A14.

## 5. Résultats dérivés

| Cas | Temps ms / rôle | Impulsion X N·s | Énergie hors translation MJ | Résidu kJ | Échecs conservés |
|---|---|---:|---:|---:|---|
| IMPACT_10_DT50 | 10.000361400, fin observée | -48114.390 | 7.646173 | -170.756942 | metal_material_domain; beam_material_domain; radome_face_reference_domain |
| IMPACT_10_DT25 | 6.240026, dernier historique seulement | -17590.680 | 2.661747 | -18.253300 | plafond600s ; fin10ms non atteinte |

Le cas complet démarre le contact AIRFRAME vers **0.2303436 ms**, résolution de l'historique0,01ms. Les trois autres impulsions sont nulles. KE initiale **2.441026 GJ** ; travail plastique final **3.043175 MJ**. Résidu énergétique maximal **172.453700 kJ**, soit **0.007065%** de KE initiale. Écarts maximaux de quantité de mouvement globale/appuis **8.111217 N·s**, façade/contact **7.352519 N·s**, sous les seuils déclarés. Masses nodales décodées indépendamment, constantes dans les états contrôlés ; appuis fixes, masse ajoutée nulle, érosion absente et travail externe nul.

Le maximum de ratio local résidu/énergie est61,398453% au tout début : à0,3002859ms, G=1239,169J et R=−760,831J. Le critère déclaré autorise1061,958J à cet instant avec sa marge1000J. Le contrôle local passe **avec cette marge** ; cela ne signifie pas une erreur relative inférieure à5% à chaque instant. Le budget natif n'est pas corrigé a posteriori.

À **6.240026 ms**, la comparaison donne Δimpulsion **0.0067538%**, Δénergie hors translation **0.0027101%**. Les deux critères passent sur cette **fenêtre commune seulement**. Aucune convergence temporelle jusqu'à10ms n'est revendiquée ; aucune convergence spatiale nouvelle calculée.

Déplacement de façade complet échantillonné **394.812mm** ; dernier état du cas incomplet **114.151mm à6.200159ms**. Déformations plastiques maximales des coques **0.519221**, des poutres sondées **0.382445**, au-delà du seuil0,1. Le premier état échantillonné dépassant la résistance de référence du radôme est à **1.000176ms**, ratio **1.129026** ; le précédent, vers0,500321ms, est sous le seuil. Ratio maximal **9.914325**. Ce diagnostic ne constitue ni une mesure du matériau réel, ni un instant de rupture ; la loi du modèle maintient ces peaux intactes.

Visualisation HTML : **21 états natifs ×1**, aucune interpolation géométrique ni trajectoire Blender, lecture artificiellement ralentie. Données comprimées avec retour exact, syntaxe JavaScript vérifiée. PNG des bilans et de la géométrie inspectés visuellement ; rendu interactif non certifié. Vue10ms hors domaine matériel destinée au diagnostic. Précision des coordonnées imprimées : écart maximal0.055714mm, consigné plutôt que corrigé.

## 6. Contradictions et informations manquantes

L'avion complet a bien évolué sous contact avec la façade, mais à10ms seuls le nez et l'avant interagissent ; ce n'est ni une traversée complète, ni les premières secondes. Des bilans numériques et une comparaison temporelle courte réussis coexistent avec des matériaux hors domaine et une absence de rupture. Une ressemblance visuelle ne prouve aucun mécanisme historique.

Les résistances/énergies de rupture du sandwich réel, écrasement de l'âme, séparation des assemblages, fragmentation, auto-contact global, carburant, géométrie/sections de façade et conditions réelles d'impact restent à documenter et qualifier. Le demi-pas demandé10ms demeure incomplet, même si ses données disponibles sont cohérentes. Les anciennes qualifications A11-A14 restent échouées et distinctes de ces nouveaux résultats. Aucune cause unique de tout déficit énergétique ancien n'est prouvée par A15.

AIRCRAFT-A16 : partir de l'impact couplé A15 et de ses sorties enregistrées. Priorité à une loi mécanique de dommage/rupture du radôme, puis de l'avant métallique et de la façade, avec propriétés et plages indépendantes des dommages historiques. Le premier état échantillonné du radôme hors résistance de référence est vers1ms ; allonger seulement le modèle sans rupture produit des formes hors domaine. Déclarer les paramètres et dissipation, signaler les données manquantes plutôt que les inventer, vérifier une seule famille de contrôles mécaniques nécessaires puis revenir au contact avion/façade avec une durée et un coût réalistes. Réutiliser les sorties A15 ; ne pas relancer les anciens solveurs. Le demi-pas n'est comparé que jusqu'à6,240026ms, pas jusqu'à10ms ; prévoir un plafond de coût cohérent si sa fin est nécessaire. Convergence spatiale, géométrie/masse/conditions historiques, auto-contact global, carburant et assemblages restent à qualifier. Garder les échecs A11-A14 et les limites A15 ; aucun réglage pour retrouver NIST, une perforation ou une trajectoire connue. Le module parallèle n'est pas intégré. Premières secondes et chaîne d'effondrement non calculées. Publication A14+A15 due selon la cadence enregistrée, à préparer et vérifier séparément.

Livrables : rapport, configuration épinglée, scripts/générateurs, campaign_review.json, scientific_assessment.json, execution_summary.json, historiques et états SI, journaux d'échecs, manifeste, preuve de préservation et handoff. Le contrôle d'intégrité des **sorties disponibles** passe ; l'ensemble des objectifs de deux calculs achevés et la qualification scientifique globale restent échoués.
