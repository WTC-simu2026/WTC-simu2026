# WTC-simu2026

**Construction progressive d'une simulation exploratoire du WTC 1 : impact d'un Boeing 767, incendies et réponse structurelle, jusqu'à un éventuel effondrement ou son arrêt.**

Le projet teste des mécanismes, des hypothèses explicites et des plages de paramètres. Aucun résultat final n'est présupposé. Il s'agit d'une recherche personnelle reproductible, assistée par Codex, dont les modèles, calculs, essais rejetés et limites sont publiés pour être examinés et améliorés.

*English: an open, incremental WTC 1 research harness. Current results concern limited verification models; they do not establish the cause or reproduce the full historical collapse.*

## Où en est la simulation ?

Instantané du **12 octobre 2026** : **AIRCRAFT-A47 terminée**, prochaine étape **AIRCRAFT-A48**. Le registre compte **166 entrées**. Les coques de façade isolées sont testées sous charge, avec les erreurs de préparation et les critères de sortie échoués conservés.

A46 copie quatre coques et neuf nœuds de la façade A20, sans changer matériaux, propriétés, épaisseur ou coordonnées. Les deux CHECK, libre et bord fixé, atteignent leur compte rendu mais signalent **1erreur de chargement chacun et27/21avertissements de rotation**. Une terminaison normale ne suffit pas à une qualification mécanique. La panne entière ASSEMC_KIJ A45 n’est pas reproduite.

A47 introduit traction et flexion à faible déformation avec un nœud intérieur libre. Une **erreur d’encodage de la nouvelle charge** est détectée : amplitude placée dans Ascale_x temps au lieu de Fscale_y déplacement. Les tentatives Linux et un nouveau contrôle Windows sur le même état sont conservés ; leur arrêt à0,010ms avec valeurs infinies n’est pas présenté comme succès malgré NORMAL/code0. La correction dans des dossiers distincts rétablit exactement les paramètres pré-déclarés. Aucun matériau, masse, formulation, appui ou critère n’est ajusté à un résultat connu.

Les **quatre calculs corrigés** passent énergie, masse, déplacements, plasticité nulle, épaisseur, absence d’érosion, efforts et moments sur leurs histoires réellement enregistrées. Écarts relatifs d’énergie à l’élasticité indépendante : **5,35e-6en traction et3,65e-6en flexion**. Les comparaisons explicite/implicite passent jusqu’à leur support commun **11,999ms**, sans décalage ou extrapolation. **L’ensemble original reste échoué** : deux histoires implicites n’enregistrent pas le dernier échantillon12ms ; la dernière animation de flexion implicite est11,5002ms. Ces limites restent explicites. Les pas implicites se réduisent ; aucune accélération10s n’est déduite du panneau.

Les journaux montrent **deux threads Starter et un thread Engine**. Un addendum A47 corrige le libellé antérieur trop général d’un thread par processus ; anciens rapports conservés. A47 comprend cinq préparations et neuf Engine nouveaux ; aucune installation, compilation ou ancienne dynamique relancée. Les binaires, bibliothèques et sources tierces brutes restent exclus.

Les [rapports A46](wtc1_simulation_v8/output/aircraft_a46/rapport_aircraft_a46.md) et [A47](wtc1_simulation_v8/output/aircraft_a47/rapport_aircraft_a47.md) séparent les six catégories de preuve. Le prochain contrôle cible les couplages et degrés actifs du graphe entier, une famille à la fois. Les cinq TYPE25 ignorés, A40 chargé/croissance, A34 peaux et A36 raffinement restent ouverts ou échoués.

La vidéo3D des **dix premières secondes physiques** reste incomplète : meilleur impact entier A20 = **0,0200001220703125seconde**. Les temps de panneau ne sont jamais crédités à l’impact entier. L’intégrité de publication ne valide pas la physique ou l’événement historique.


## Ce qui est publié

- `harness/` : état scientifique, registre des expériences, références, contrôles et passations.
- `wtc1_simulation_v8/scripts/` et `data/` : code des calculs et configurations numériques.
- `wtc1_simulation_v8/output/`, dossiers CalculiX et OpenRadioss : résultats, rapports, bilans et diagnostics, y compris essais rejetés.
- `wtc1_3d_v4/` : scripts de visualisation, paramètres, audits et modèles/rendus dans les archives de résultats.
- `outputs/` : calculs exploratoires antérieurs et audits complémentaires. Leurs affirmations se lisent avec leurs propres limites ; leur présence n'est pas une validation.
- `publication/` : inventaire complet, empreintes SHA-256, règles de publication, licences tierces et liste motivée des fichiers externes non redistribués.

Inventaire courant : **16,046 fichiers scientifiques dans Git**, **28,482 sorties dans 125 archives**.

Restaurer les 124 anciennes archives des releases précédentes, puis les 1 archives [A46+A47](https://github.com/WTC-simu2026/WTC-simu2026/releases/tag/snapshot-2026-10-12-aircraft-a46-a47). Manifestes, SHA-256 et URL conservés ; aucune ancienne archive reconstruite ou remplacée.

## Consulter et vérifier sans relancer les solveurs

```powershell
git clone https://github.com/WTC-simu2026/WTC-simu2026.git
cd WTC-simu2026
python tools/verify_public_snapshot.py
```

Ce contrôle vérifie les fichiers présents dans Git, l'état, le registre et les empreintes de l'instantané. Il annonce séparément les fichiers de release qui restent à télécharger. Il vérifie l'intégrité de la publication, pas la physique du WTC.

Pour restaurer et vérifier toutes les sorties brutes, télécharger les ZIP de la release, puis utiliser :

```powershell
python tools/restore_release_assets.py --archives CHEMIN_VERS_LES_ZIP
python tools/verify_public_snapshot.py --full
```

Le restaurateur vérifie chaque archive puis chaque fichier ; il refuse d'écraser un fichier différent. Ces outils utilisent uniquement la bibliothèque standard Python.

## Reproduire ou poursuivre les calculs

Voir [REPRODUCIBILITY.md](REPRODUCIBILITY.md). La base Python utilise NumPy et Pillow ; certains scripts demandent aussi pandas, matplotlib, pypdf ou pdfplumber. OpenRadioss, CalculiX, Blender et ParaView sont des logiciels séparés, à obtenir auprès de leurs projets respectifs.

**La lecture et la vérification des résultats sont portables ; la relance de toutes les itérations ne l'est pas encore.** Des scripts historiques conservent des chemins Windows et des dépendances locales. Les configurations et journaux originaux sont préservés, et cette limite est explicite. Aucun solveur n'est relancé par le contrôle de publication.

## Prochaine étape

AIRCRAFT-A48 : conserver les quatre témoins chargés corrigés A47 en cache, sans les refaire. L’amplitude était écrite dans Ascale_x temps ; la correction vers Fscale_y rétablit exactement les paramètres pré-déclarés, sans ajustement physique. Les contrôles mécaniques traction/flexion et leurs comparaisons passent sur les histoires réellement communes jusqu’à11,999ms ; la demande de dernier échantillon12ms reste échouée pour les deux implicites, dernière animation de flexion11,5002ms. Ne pas réétiqueter ces gates en succès, ni injecter/extrapoler les champs. Les coques seules peuvent répondre mécaniquement en explicite et MUMPS ; les avertissements de rotations CHECK A46 ne démontrent donc pas une absence de flexion. Cibler maintenant le graphe entier qui avorte dans ASSEMC_KIJ : pré-déclarer des petits assemblages coque/solide/RBE3/TYPE2 issus des données entières, en introduisant une seule famille à la fois, puis évaluer la topologie et les degrés actifs avant variante entière. Ne pas modifier silencieusement masse, inertie, résistances, formulation ou TYPE25. Les cinq TYPE25 ignorés restent une incompatibilité indépendante. Les pas implicites A47 se réduisent ; aucune accélération10s ni reprise chargée validée n’en découle. A40 chargé/croissance, A34 peaux et A36 raffinement restent échoués. Meilleur impact entierA20=0,0200001220703125s ; dix secondes physiques3D puisMP4/GIF restent actives et incomplètes. Publier A46+A47 avec tous les échecs, selon autorisation existante, puis avancer A48.

## Discipline de preuve

Chaque rapport distingue observations/transcriptions, résultats de modèles officiels, affirmations des archives, hypothèses du projet, résultats dérivés et informations manquantes. Les données NIST utilisées comme entrées ou références ne deviennent pas des observations indépendantes.

- La localisation en flexion après fracture complète n'est pas validée.
- Une température imposée n'est pas un incendie calculé.
- Des tests numériques réussis ne valident pas à eux seuls l'effondrement réel.
- Une fraction de champs synthétiques n'est pas une probabilité de l'événement historique.
- Blender reste une visualisation tant que son animation n'est pas reliée à des états mécaniques vérifiés.

## Licence et contributions

Les travaux propres au projet sont proposés sous [licence MIT](LICENSE). Les composants tiers et leurs dérivés explicitement identifiés gardent leurs licences : notamment GPL-2.0 pour le modèle graphique B762, CC-BY-4.0 pour le jeu SHPB S355 et CC-BY-NC-4.0 pour le cas officiel TWISBEAM. La licence MIT ne remplace aucune de ces licences. Voir [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

Les contributions sont bienvenues : corrections de calcul, contrôles indépendants, sources primaires, portabilité ou visualisation. Indiquer la question testée, les unités, les hypothèses, le coût et le critère qui accepterait ou rejetterait le résultat. Conserver les anciennes itérations et publier les échecs utiles. Voir [CONTRIBUTING.md](CONTRIBUTING.md).
