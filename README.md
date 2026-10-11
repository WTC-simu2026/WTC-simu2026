# WTC-simu2026

**Construction progressive d'une simulation exploratoire du WTC 1 : impact d'un Boeing 767, incendies et réponse structurelle, jusqu'à un éventuel effondrement ou son arrêt.**

Le projet teste des mécanismes, des hypothèses explicites et des plages de paramètres. Aucun résultat final n'est présupposé. Il s'agit d'une recherche personnelle reproductible, assistée par Codex, dont les modèles, calculs, essais rejetés et limites sont publiés pour être examinés et améliorés.

*English: an open, incremental WTC 1 research harness. Current results concern limited verification models; they do not establish the cause or reproduce the full historical collapse.*

## Où en est la simulation ?

Instantané du **11 octobre 2026** : **AIRCRAFT-A33 terminée**, prochaine étape **AIRCRAFT-A34**. Le registre compte **152 entrées**. A32+A33 ajoutent **38 calculs natifs complets** : **29 ensembles individuels passent, neuf échouent et les 38 bilans énergétiques passent**. Tous les résultats, configurations, scripts et critères échoués sont conservés.

A32 compare deux formulations volumiques efficaces à une cellule géométrique dans l’épaisseur, avec même carte LAW12 explicite et masse physique 0,0915 g. Mouvements libres, champs affines et membrane passent. Quatre flexions échouent à leur référence Cxx initiale. Une référence indépendante séparée à faces chargées et intérieur libre révèle une relaxation transverse admissible et une sensibilité du maillage conventionnel; ses raffinements jusqu’à 192×192×16 atteignent 0,65% dans le plan et 0,34% dans l’épaisseur. L’écart natif subsiste; aucun ancien critère remplacé et aucune qualification de flexion accordée.

A33 donne aux peaux des nœuds intérieurs physiquement libres avec deux ou quatre cellules dans l’épaisseur. Huit calculs et 24 échantillons de champs natifs : trois ensembles réussis, cinq échoués, dont le témoin négatif à une cellule. Les bilans, impulsions, travaux aux faces et raffinements passent. Quatre cellules ramènent l’erreur énergétique sous 1%, mais le champ intérieur aux bords reste hors du seuil déclaré. L’accord énergétique seul ne qualifie pas la mécanique ou l’insertion dans l’avion.

Les [rapports A32](wtc1_simulation_v8/output/aircraft_a32/rapport_aircraft_a32.md) et [A33](wtc1_simulation_v8/output/aircraft_a33/rapport_aircraft_a33.md) séparent faits, références, archives, hypothèses, résultats dérivés et lacunes. Au total, 114 échantillons de champs natifs contrôlés, aucun ancien solveur relancé et aucune compensation de masse/inertie, densité modifiée ou RKE inventé. Les coefficients transverses et seuils élastiques LAW12 restent des hypothèses, sans résistance ou rupture historique identifiée. Les prises courbes, collage, décollement et contacts restent à qualifier.

Une proposition en lecture seule décrit une version séparée du solveur avec MUMPS, car le binaire installé refuse les sondes implicites A31. Outils manquants et source candidate figée sont inventoriés. Aucune installation, compilation ou modification logicielle effectuée; ces actions supplémentaires demandent un accord explicite et leur réussite ne garantit pas dix secondes d’impact. Les sources tierces et leurs licences restent exclues de la redistribution; références et empreintes conservées.

La vidéo 3D des **dix premières secondes physiques** reste incomplète : meilleur entier A20 = **20 millisecondes physiques**. Les aperçus ralentis ne remplissent pas cet objectif. Aucun nouvel impact entier ou prolongement balistique inventé. Aucun dommage connu comme cible. La publication vérifie l’intégrité des fichiers, sans validation historique de l’impact ou de l’effondrement.


## Ce qui est publié

- `harness/` : état scientifique, registre des expériences, références, contrôles et passations.
- `wtc1_simulation_v8/scripts/` et `data/` : code des calculs et configurations numériques.
- `wtc1_simulation_v8/output/`, dossiers CalculiX et OpenRadioss : résultats, rapports, bilans et diagnostics, y compris essais rejetés.
- `wtc1_3d_v4/` : scripts de visualisation, paramètres, audits et modèles/rendus dans les archives de résultats.
- `outputs/` : calculs exploratoires antérieurs et audits complémentaires. Leurs affirmations se lisent avec leurs propres limites ; leur présence n'est pas une validation.
- `publication/` : inventaire complet, empreintes SHA-256, règles de publication, licences tierces et liste motivée des fichiers externes non redistribués.

Inventaire courant : **13,787 fichiers scientifiques dans Git**, **20,818 sorties dans 116 archives**.

Restaurer les 115 anciennes archives des releases précédentes, puis les 1 archives [A32+A33](https://github.com/WTC-simu2026/WTC-simu2026/releases/tag/snapshot-2026-10-11-aircraft-a32-a33). Manifestes, SHA-256 et URL conservés ; aucune ancienne archive reconstruite ou remplacée.

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

AIRCRAFT-A34 : conserver les défauts de relaxation aux bords A33, étudier leur raffinement géométrique et l’opérateur discret avant une prise courbe ou insertion entière. La référence indépendante A32 à faces prescrites et intérieur libre passe ses contrôles; A33Z4passe l’énergie mais pas le champ intérieur. Une compilation séparée avec MUMPS est proposée dans aircraft_a33/native_build_preflight, soumise à accord explicite Jeremy pour installation/compilation; ne pas l’exécuter sans cet accord. Après accord, déclarer configuration/source/version et contrôles avant construction et nouveaux calculs; aucune compatibilité de reprise Windows/Linux présumée. Sans cet accord, les diagnostics et contrôles mécaniques du binaire actuel peuvent continuer. Aucun ajout de masse/densité, RKE inventé ou dommage connu comme cible. Capacités, décollement et rupture historiques non identifiés; LAW12reste un témoin élastique hypothétique. Meilleur entier A20=20ms; vidéo3D10secondes physiques incomplète. Publication A32+A33 après vérification; cadence suivante A34+A35.

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
