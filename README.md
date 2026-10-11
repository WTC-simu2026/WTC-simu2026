# WTC-simu2026

**Construction progressive d'une simulation exploratoire du WTC 1 : impact d'un Boeing 767, incendies et réponse structurelle, jusqu'à un éventuel effondrement ou son arrêt.**

Le projet teste des mécanismes, des hypothèses explicites et des plages de paramètres. Aucun résultat final n'est présupposé. Il s'agit d'une recherche personnelle reproductible, assistée par Codex, dont les modèles, calculs, essais rejetés et limites sont publiés pour être examinés et améliorés.

*English: an open, incremental WTC 1 research harness. Current results concern limited verification models; they do not establish the cause or reproduce the full historical collapse.*

## Où en est la simulation ?

Instantané du **11 octobre 2026** : **AIRCRAFT-A35 terminée**, prochaine étape **AIRCRAFT-A36**. Le registre compte **154 entrées**. A34+A35 ajoutent **neuf calculs natifs terminés** : **un ensemble individuel passe, huit échouent et les neuf bilans énergétiques passent**. Les configurations, scripts, tentatives échouées et limites sont conservés.

A34 affine les peaux LAW12 avec 48 cellules dans le plan et quatre ou huit dans l’épaisseur, à masse physique inchangée de 0,0915 g. Le mouvement libre passe. L’énergie et les raffinements temporels/spatiaux passent, mais les trois champs intérieurs en flexion restent hors du seuil indépendant. Un accord énergétique ne suffit pas pour insérer cette mécanique dans l’avion.

A35 réalise la compilation séparée avec MUMPS explicitement autorisée, en **39,29 minutes**, sous l’heure prévue. Les dépendances minimales ont été installées dans Ubuntu WSL. Le moteur et le lecteur sont compilés; le préparateur Linux échoue à la liaison sur cinq fonctions manquantes. Le solveur Windows est conservé. La source OpenRadioss est figée au commit bad6688602d770e019b75773d2d5a48b4f9bd918, sans modification du code physique suivi; les métadonnées de dépendances et l’interface H3D locale sont documentées. La compilation complète et H3D restent non qualifiés. Les binaires, bibliothèques, archives de compilation et sources tierces ne sont pas redistribués.

Cinq nouveaux calculs du moteur Linux ont été préparés par le préparateur Windows : explicite, demi-pas explicite, PCG, MUMPS et demi-pas MUMPS. Les journaux confirment l’exécution implicite et MUMPS 5.6.2. Cette compatibilité est mesurée seulement sur un cube élastique de 1 mm durant 50 microsecondes. Les cinq bilans, masses et quinze champs passent. L’énergie implicite et explicite diffère d’environ 0,00384 % à temps commun, avec un pas implicite 100 fois plus grand. Ce rapport ne prédit pas le coût de l’impact entier. Les cinq références indépendantes échouent encore : environ 3,19 % d’écart énergétique et 2,49×10⁻⁵ mm de déplacement, au-delà des seuils conservés.

Un lecteur associait les réactions au mauvais ordre de nœuds. La correction par identifiants est vérifiée sur les sorties en cache, sans relancer les solveurs ni changer les critères : impulsions et travaux explicites passent. Les trois transferts implicites échouent encore. Aucun facteur empirique n’est ajouté pour fermer ces écarts. Cinq premières tentatives de lancement, échouées avant le moteur Linux, restent conservées séparément.

Les [rapports A34](wtc1_simulation_v8/output/aircraft_a34/rapport_aircraft_a34.md) et [A35](wtc1_simulation_v8/output/aircraft_a35/rapport_aircraft_a35.md) séparent faits, références, archives, hypothèses, résultats dérivés et lacunes. **27 échantillons de champs natifs** sont contrôlés. Aucun changement des budgets de masse/inertie, aucune densité compensatrice, aucun RKE inventé et aucun dommage connu comme cible. La résistance, la rupture, les prises courbes, les contacts et la transition explicite–implicite restent à qualifier.

La vidéo 3D des **dix premières secondes physiques** reste incomplète : meilleur impact entier A20 = **20 millisecondes physiques**. Aucun nouvel impact entier ni prolongement balistique inventé. La publication vérifie l’intégrité des fichiers, sans validation historique de l’impact ou de l’effondrement.


## Ce qui est publié

- `harness/` : état scientifique, registre des expériences, références, contrôles et passations.
- `wtc1_simulation_v8/scripts/` et `data/` : code des calculs et configurations numériques.
- `wtc1_simulation_v8/output/`, dossiers CalculiX et OpenRadioss : résultats, rapports, bilans et diagnostics, y compris essais rejetés.
- `wtc1_3d_v4/` : scripts de visualisation, paramètres, audits et modèles/rendus dans les archives de résultats.
- `outputs/` : calculs exploratoires antérieurs et audits complémentaires. Leurs affirmations se lisent avec leurs propres limites ; leur présence n'est pas une validation.
- `publication/` : inventaire complet, empreintes SHA-256, règles de publication, licences tierces et liste motivée des fichiers externes non redistribués.

Inventaire courant : **14,215 fichiers scientifiques dans Git**, **20,943 sorties dans 118 archives**.

Restaurer les 116 anciennes archives des releases précédentes, puis les 2 archives [A34+A35](https://github.com/WTC-simu2026/WTC-simu2026/releases/tag/snapshot-2026-10-11-aircraft-a34-a35). Manifestes, SHA-256 et URL conservés ; aucune ancienne archive reconstruite ou remplacée.

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

AIRCRAFT-A36 : qualifier le moteur implicite effectivement disponible avant extension entière. Contrôler les mêmes données physiques avec un nouveau témoin du moteur Windows et une référence conventionnelle raffinée pour distinguer écart de formulation/référence et compatibilité du nouveau moteur. Lire dans les sources épinglées le stockage des réactions implicites et le relier à momentum/travail par un témoin distinct; ne pas appliquer un facteur ajusté aux résultats. Vérifier ensuite une transition explicite→implicite avec états fraîchement calculés et mêmes bilans avant un impact entier borné. Le préparateur Windows est inchangé; le préparateur Linux a échoué à cinq interfaces et reste incomplet. La compilation autorisée A35 est terminée en moins d’une heure, sans prolongation de ce budget. Conserver A34, les échecs A35, masse/densité/inertie, sources et seuils. La comparaison mécanique Isolid18/24 préparée reste différée. Objectif : dix secondes physiques 3D puis vidéo/GIF; meilleur entier A20=20ms, objectif incomplet, aucun dommage connu comme cible. Publication A34+A35 après vérification d’intégrité, sans redistribution des binaires ni sources tierces.

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
