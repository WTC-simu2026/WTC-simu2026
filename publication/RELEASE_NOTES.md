# Instantané AIRCRAFT-A46+AIRCRAFT-A47 — 12 octobre 2026

Instantané du **12 octobre 2026** : **AIRCRAFT-A47 terminée**, prochaine étape **AIRCRAFT-A48**. Le registre compte **166 entrées**. Les coques de façade isolées sont testées sous charge, avec les erreurs de préparation et les critères de sortie échoués conservés.

A46 copie quatre coques et neuf nœuds de la façade A20, sans changer matériaux, propriétés, épaisseur ou coordonnées. Les deux CHECK, libre et bord fixé, atteignent leur compte rendu mais signalent **1erreur de chargement chacun et27/21avertissements de rotation**. Une terminaison normale ne suffit pas à une qualification mécanique. La panne entière ASSEMC_KIJ A45 n’est pas reproduite.

A47 introduit traction et flexion à faible déformation avec un nœud intérieur libre. Une **erreur d’encodage de la nouvelle charge** est détectée : amplitude placée dans Ascale_x temps au lieu de Fscale_y déplacement. Les tentatives Linux et un nouveau contrôle Windows sur le même état sont conservés ; leur arrêt à0,010ms avec valeurs infinies n’est pas présenté comme succès malgré NORMAL/code0. La correction dans des dossiers distincts rétablit exactement les paramètres pré-déclarés. Aucun matériau, masse, formulation, appui ou critère n’est ajusté à un résultat connu.

Les **quatre calculs corrigés** passent énergie, masse, déplacements, plasticité nulle, épaisseur, absence d’érosion, efforts et moments sur leurs histoires réellement enregistrées. Écarts relatifs d’énergie à l’élasticité indépendante : **5,35e-6en traction et3,65e-6en flexion**. Les comparaisons explicite/implicite passent jusqu’à leur support commun **11,999ms**, sans décalage ou extrapolation. **L’ensemble original reste échoué** : deux histoires implicites n’enregistrent pas le dernier échantillon12ms ; la dernière animation de flexion implicite est11,5002ms. Ces limites restent explicites. Les pas implicites se réduisent ; aucune accélération10s n’est déduite du panneau.

Les journaux montrent **deux threads Starter et un thread Engine**. Un addendum A47 corrige le libellé antérieur trop général d’un thread par processus ; anciens rapports conservés. A47 comprend cinq préparations et neuf Engine nouveaux ; aucune installation, compilation ou ancienne dynamique relancée. Les binaires, bibliothèques et sources tierces brutes restent exclus.

Les [rapports A46](wtc1_simulation_v8/output/aircraft_a46/rapport_aircraft_a46.md) et [A47](wtc1_simulation_v8/output/aircraft_a47/rapport_aircraft_a47.md) séparent les six catégories de preuve. Le prochain contrôle cible les couplages et degrés actifs du graphe entier, une famille à la fois. Les cinq TYPE25 ignorés, A40 chargé/croissance, A34 peaux et A36 raffinement restent ouverts ou échoués.

La vidéo3D des **dix premières secondes physiques** reste incomplète : meilleur impact entier A20 = **0,0200001220703125seconde**. Les temps de panneau ne sont jamais crédités à l’impact entier. L’intégrité de publication ne valide pas la physique ou l’événement historique.

Archives antérieures et critères échoués conservés.


1 archives complémentaires ; 124 archives précédentes conservées. Sources externes exclues, scripts et résultats propres sous MIT. Vérification de publication sans relancer les solveurs.
