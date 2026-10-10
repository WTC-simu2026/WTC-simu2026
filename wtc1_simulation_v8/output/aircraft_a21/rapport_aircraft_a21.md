# AIRCRAFT-A21 — précision temporelle et transfert des attaches

Un nouvel impact intact atteint **12.000055313 ms physiques**, avec un pas deux fois plus fin et les mêmes entrées mécaniques qu’A20. L'impulsion finale varie de **0.9987%**, l'énergie générée de **0.2580%**. Le bilan local échoue encore. Les attaches ont un défaut de rotation reproductible sur témoins; aucune correction complète n'est qualifiée. **La vidéo de10 secondes physiques reste à produire.** Le dernier MP4/GIF conservé A20 couvre20 ms et son ralenti ne vaut pas10 secondes simulées.

## 1. Faits directement observés ou transcrits

Graine1102046, zéro tirage. Analyse des données A20 en cache, déclarations immuables avant les nouveaux témoins et le nouveau solveur. Un seul nouveau cas entier, HALF_DT_12: pas0,25 au lieu de0,5, horizon12 ms au lieu de20 ms; aucun redémarrage depuis l'état final invalide A20. Vitesse[-200;5;2]m/s, masses, géométrie, matériaux, attaches, contacts, appuis, intervalles de sorties identiques. Starter confirme masse, CG et inertie strictement identiques. Les deux avertissements de voisinage1166/343 restent présents et le contrôle zéro avertissement reste faux.

Calcul entier sur2threads CPU: **2103.846s**, soit 35.06min. Fin native et observateur terminal enregistrés; tous les champs CSV confrontés aux données binaires, sans relancer l'ancien solveur. Coordonnées et vitesses confrontées à un second lecteur sur4états natifs. Tous les champs d'énergie de peau conservés sont examinés.

Dans A20, 1001lignes brutes confirment le défaut: l'impression CSV peut déplacer le résidu de 814.216J au maximum, contre un excès de contrôle de 158921.901J au contact du fuselage. La quantification binaire de KE vaut262,144J à l'énergie initiale≈2,441GJ. Les seuils restent5% de l'énergie générée +1000J lorsque celle-ci dépasse1000J.

L'énergie négative A20 se trouve dans la peau supérieure, facette111, élément70981: -3.937582362J à15.000173569ms. Il est encore intact et son champ de dommage est nul. Aire initiale34730.103103mm², déformée34715.889729mm². Cela localise le défaut et ne prouve ni une cause ni une énergie physique négative. Onze états conservés contiennent cet élément négatif.

## 2. Résultats d'un modèle officiel

Aucun dommage NIST ou historique n'a servi de cible. La documentation primaire décrit les [RBE2 à inertie scalaire](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/rbe2_starter_r.htm) et les [liaisons TYPE2 avec hiérarchie](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/inter_type2_starter_r.htm). La hiérarchie TYPE2 testée est refusée par le binaire556, malgré les niveaux explicites et les champs lus correctement; sa compatibilité n'est pas qualifiée. Le passage de Spot5 à Spot2 échoue également au bilan du témoin de référence. Il ne remplace pas les contrôles Spot5 p3 A20 réussis.

Le modèle NASA d'un essai ATR42 à9,14m/s utilise des propriétés estimées depuis MIL-HDBK-5H. Le tableau1 de la pagePDF5, vérifié visuellement, donne pour2024-T3 E66,33GPa, seuil243MPa, module d'écrouissage826,7MPa et déformation ultime14,63%; pour7075-T6 E71,02GPa, seuil360MPa, écrouissage1001,8MPa et déformation ultime4,49%. Ce sont des paramètres du modèle d'un autre avion, pas des mesures de fracture d'AA11 à200m/s. Aucune valeur n'est adoptée silencieusement; conversions conservées dans material_reference_assessment.json. [Publication NASA originale](https://ntrs.nasa.gov/api/citations/20040086484/downloads/20040086484.pdf).

## 3. Affirmations provenant des archives locales

Aucune nouvelle archive, photographie ou vidéo historique analysée. Réemploi en lecture seule des sources et sorties A20. Acquisition séparée du PDF primaire NASA et de la documentation des contraintes; manifestes SHA256. La première autre URL NASA n'a pas fourni un document accepté par le contrôle d'acquisition; aucun paramètre n'en est tiré. Conservation vérifiée de **13998 fichiers antérieurs**, 53.794Go. A12+A13 publiés restent intacts, A14 àA21 locaux.

## 4. Hypothèses propres au modèle

Le modèle entier garde ses limites: cœur LAW28 fini mais sans densification ni G mesuré, peaux et joints à seuils déclarés hypothétiques,24attaches de racine RBE2 idéales, matériaux métalliques parfaitement plastiques sans fracture finie, absence de gravité, d'intérieur porteur et de contact complet des fragments. Les témoins sont des contrôles d'implémentation et ne prouvent pas les propriétés de l'assemblage historique.

Les témoins de masse ponctuelle utilisent les six offsets réels de la première racine et des masses connues indépendantes; ils ne modifient pas la masse de l'avion. La référence structurale ajoute une peau de fuselage10×10mm d'épaisseur2,54mm, matériau hérité. Les variantes TYPE2 de bord, puis sandwich/cœur/peau/racine, sont déclarées et archivées séparément. Aucune extrapolation refusée ou mise à l'échelle de masse n'est cachée. Aucun terme RKE n'est inventé pour fermer un bilan.

## 5. Résultats dérivés

La translation de l'attache transmet correctement masse, mouvement et impulsion. Les rotations de la géométrie ponctuelle sont justes, mais le total énergétique natif omet l'énergie attendue; l'inertie sphérique est216,75g·mm² contre2,60441g·mm² autour deY pour les masses ponctuelles connues. Avec une peau de fuselage et une référence cinématique indépendante identique, la référence conserve son énergie et les trois RBE2 échouent:

| Axe | Pic référence(J) | Pic RBE2(J) | Écart maximal(J) | Bilan RBE2 |
|---|---:|---:|---:|---|
| X | 0.41338908 | 0.11104408 | 0.302345 | **échoué** |
| Y | 0.22062368 | 0.20904736 | 0.01157632 | **échoué** |
| Z | 0.41182388 | 0.11104408 | 0.3007798 | **échoué** |

La comparaison TYPE2 n'a pas abouti à une attache qualifiée: recherche améliorée laisse4points hors bord; recherche ancienne les lie mais avertit et les variantes échouent à des contrôles d'énergie et d'inertie. Le contrôle de masse ajoutée exactement nulle échoue sur un champ de7,1×10⁻¹⁵g, alors que la masse globale est constante et le seuil relatif A21 pré-déclaré passe. L'échec brut reste conservé dans l'addendum de précision, sans modifier la masse ni les seuils. Les interfaces imbriquées refusent le démarrage556. Les témoins de référence Spot2 ont eux-mêmes un résidu de≈0,142122J, malgré une IE quasi nulle et des mouvements corrects. Le lecteur CSV met PART avant NODE; un addendum vérifie les21histoires mixtes en sélectionnant les titres de groupes. Les premiers contrôles de mouvement erronés restent conservés; les énergies globales nommées et le diagnostic entier n'étaient pas affectés.

Les refus initiaux sont distingués des défauts physiques: témoin sans PART1114, points de bord1079/86, omission de6courbes de matériau126 corrigée dans une copie, hiérarchie556, double comptage du résumé d'avertissements corrigé sans relancer Starter. Les anciens fichiers et résultats faux ne sont pas écrasés.

Sur le cas entier, avant10ms, l'excès maximal du contrôle local passe de2039.890J à1308.150J. Le nombre de lignes brutes en échec passe de77 à52. Dès le contact du fuselage, le pas fin ne répare pas le bilan: excès maximal171968.502J, résidu-257093.976J pour1682509.480J générés à10.920016289ms. Le pas de temps seul n'explique pas le défaut.

À la fin: énergie générée3623000.200J, résidu-148465.528J. Au temps commun11,98007ms, l'impulsion varie de0.998673%; l'énergie à12ms varie de0.257972%. Ces deux contrôles de demi-pas passent. Erreurs de quantité de mouvement globale/appuis36.333832N·s et façade/contact5.784322N·s, sous le seuil inchangé. Les réussites globales ne remplacent pas le contrôle local.

Plasticité maximale échantillonnée: métal0.476483, façade0.172335, poutres0.344678, au-delà du seuil diagnostique0,1. Minimum d'énergie de peau sauvegardée-0.673370449J. À12ms,1065peaux,607cœurs et605joints sont supprimés nativement. Les états sont finis et leur connectivité est conservée, sans rendre intact un élément supprimé.

| Contrôle entier A21 | Résultat |
|---|---|
| native_binary_CSV | réussi |
| native_normal_termination | réussi |
| requested_12ms_horizon | réussi |
| native_physical_mass | réussi |
| no_scaled_or_added_mass | réussi |
| identical_A20_Starter_mechanics | réussi |
| identical_A20_mass_CG_inertia | réussi |
| strict_zero_warnings | **échoué** |
| no_external_work | réussi |
| global_energy | réussi |
| native_local_energy | **échoué** |
| printed_CSV_local_energy | **échoué** |
| global_support_momentum | réussi |
| facade_contact_momentum | réussi |
| halfdt_end_impulse | réussi |
| halfdt_end_generated | réussi |
| sampled_native_geometry_finite | réussi |
| sampled_connectivity | réussi |
| supports_fixed | réussi |
| metal_material_domain | **échoué** |
| facade_material_domain | **échoué** |
| beam_material_domain | **échoué** |
| saved_skin_elements_IE_nonnegative | **échoué** |
| sampled_core_elements_IE_nonnegative | réussi |

## 6. Contradictions et informations manquantes

La cause complète du résidu entier n'est pas isolée. Le transfert d'inertie et l'énergie des attaches exigent une correction contrôlée; les témoins faux ne sont pas une solution prête à insérer. La déformation temporelle converge sur certains indicateurs alors que le bilan local reste faux. Les paramètres d'écrouissage, rupture ductile, dépendance au taux, état de contrainte et longueur de maille restent à définir pour le métal et la façade. La petite variation d'aire de l'élément négatif n'établit pas sa cause. Une rotation correcte n'est pas une conservation d'énergie ni une validation physique.

AIRCRAFT-A22 : objectif vidéo3D de10 secondes physiques incomplet. Lire le rapport A21, r0/HALF_DT_12/review.json, native_precision_review.json, root_structural_review.json, control_channel_audit.json et cached_skin_negative_localization.json. A21 est un nouveau départ intact de12ms, mêmes entrées mécaniques A20, pas0,25 contre0,5. Impulsion et énergie finale convergent mais le bilan local reste faux au nez et au contact du fuselage. Ne pas relancer A20/A21 ou leurs témoins. Réutiliser les contrôles cœur LAW28 et sandwich TYPE2 Spot5 p3 A20 réussis; ne pas remplacer sans preuve Spot5 par Spot2. Les témoins de rotation RBE2 échouent avec ou sans peau de fuselage; aucune cause complète du déficit entier n’est prouvée. Les TYPE2 testés à la racine ne sont pas qualifiés: extrapolation de bord, énergie/inertie ou hiérarchie556. Les prototypes Spot2, même en référence sans nouvelle racine, échouent au bilan de rotation; cela ne remet pas silencieusement à zéro les réussites Spot5 p3. Priorité: comparer une attache mécanique finie, avec masse et inertie explicites, à un témoin indépendant de translation/rotation et dynamique libre. Pré-déclarer géométrie, capacité et incertitudes; conserver le budget initial ou annoncer explicitement toute masse ajoutée, sans ajuster ADMAS/densité pour fermer un bilan. Seulement après réussite des témoins, construire un départ intact et vérifier bilan local, matériaux et contact avant extension. Préparer en parallèle une rupture métallique/acier à partir de références et plages déclarées, sans cible de dommage. La référence NASA ATR42 à9,14m/s est une source de modèle différente, pas une mesure de fracture AA11 à200m/s. Ne pas prolonger les états invalides vers100ms,1s ou10s et ne pas inventer une RKE. Gravité, intérieur porteur et contacts des fragments restent nécessaires. Le lecteur CSV place les champs PART avant NODE: sélectionner les titres de groupes. Les erreurs de génération/lecture et tous les témoins refusés sont conservés. Le MP4/GIF A20 demeure le dernier aperçu:20ms physiques ralentis. A12+A13 sont déjà publiés; A14 àA21 restent locaux, sans nouvelle autorisation externe.
