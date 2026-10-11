# WTC-simu2026

**Construction progressive d'une simulation exploratoire du WTC 1 : impact d'un Boeing 767, incendies et réponse structurelle, jusqu'à un éventuel effondrement ou son arrêt.**

Le projet teste des mécanismes, des hypothèses explicites et des plages de paramètres. Aucun résultat final n'est présupposé. Il s'agit d'une recherche personnelle reproductible, assistée par Codex, dont les modèles, calculs, essais rejetés et limites sont publiés pour être examinés et améliorés.

*English: an open, incremental WTC 1 research harness. Current results concern limited verification models; they do not establish the cause or reproduce the full historical collapse.*

## Où en est la simulation ?

Instantané du **11 octobre2026** : **AIRCRAFT-A29 terminée**, prochaine étape **AIRCRAFT-A30**. Le registre compte148entrées. A28+A29 ajoutent39calculs natifs complets de témoins isolés. Rapports, configurations, résultats, scripts et critères échoués sont conservés.

A28 explique une composante numérique de l'écart de flexion: la formule ASQBI et les propriétés déclarées prédisent six historiques A27sans ajustement. Le changement de défaut Icpre n'est pas appliqué dans les pièces TYPE22. La variante HSEPH garde les échecs de flexion et échoue aussi au bilan du cisaillement transverse avec Ashear5/6. Aucun terme ne répare artificiellement l'énergie.

A29 teste une branche volumique TYPE6avec quatre éléments géométriques dans l'épaisseur. La carte LAW25source, conservée, échoue à la référence3D même avec le bon repère. La nouvelle branche explicite LAW12passe **ses15contrôles**: six modes affines, mouvements libres, masse/inertie physiques, moment cinétique, traction, flexion et raffinements. Les modules,densitéetnu12source sont inchangés; **nu23=nu31=0,25sont des hypothèses transverses nouvelles**, sans équivalence automatique de LAW25ni mesure historique de rupture. Le montage entier n'est pas modifié.

Les [rapports A28](wtc1_simulation_v8/output/aircraft_a28/rapport_aircraft_a28.md) et [A29](wtc1_simulation_v8/output/aircraft_a29/rapport_aircraft_a29.md) distinguent observations, références, hypothèses et limites. Les erreurs de préparation et de lecture sont documentées; les essais arrêtés au Starter et les deux calculs A29échoués sont gardés. Aucune ancienne exécution relancée, compensation de masse/inertie ou RKE inventée.

La vidéo3D des **dix premières secondes physiques** reste incomplète: le meilleur calcul entier A20couvre **20millisecondes physiques**. A30qualifiera le cœur et son assemblage avec les peaux avant les24racines/144ancres courbes. Les propriétés et ruptures historiques, la façade, la gravité, l'intérieur porteur et les contacts de fragments restent ouverts. Nouveau départ entier intact seulement après bilans et estimation du coût. Aucun dommage connu comme cible. Cette publication confirme l'intégrité des fichiers, sans validation historique de l'impact ou de l'effondrement.


## Ce qui est publié

- `harness/` : état scientifique, registre des expériences, références, contrôles et passations.
- `wtc1_simulation_v8/scripts/` et `data/` : code des calculs et configurations numériques.
- `wtc1_simulation_v8/output/`, dossiers CalculiX et OpenRadioss : résultats, rapports, bilans et diagnostics, y compris essais rejetés.
- `wtc1_3d_v4/` : scripts de visualisation, paramètres, audits et modèles/rendus dans les archives de résultats.
- `outputs/` : calculs exploratoires antérieurs et audits complémentaires. Leurs affirmations se lisent avec leurs propres limites ; leur présence n'est pas une validation.
- `publication/` : inventaire complet, empreintes SHA-256, règles de publication, licences tierces et liste motivée des fichiers externes non redistribués.

Inventaire courant : **12,692 fichiers scientifiques dans Git**, **20,049 sorties dans 112 archives**.

Restaurer les 111 anciennes archives des releases précédentes, puis les 1 archives [A28+A29](https://github.com/WTC-simu2026/WTC-simu2026/releases/tag/snapshot-2026-10-11-aircraft-a28-a29). Manifestes, SHA-256 et URL conservés ; aucune ancienne archive reconstruite ou remplacée.

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

A30 : qualifier séparément le cœur LAW28 et un sandwich conformal peau/cœur à faces partagées, à partir des témoins volumiques A29. Préserver masse, inertie physique et matériaux déclarés, documenter les hypothèses transverses nouvelles, vérifier mouvements libres, travail/énergie et modes élastiques indépendants avec raffinements. Les anciens Spot5ne sont pas remplacés implicitement. Ensuite24racines/144ancres courbes A25et nouveau départ entier intact après estimation du coût. Objectif10secondes physiques incomplet, meilleur entier20ms; pas de prolongation A21, aucune rupture historique qualifiée, aucun dommage connu comme cible. Prochaine publication après A30+A31vérifiées.

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
