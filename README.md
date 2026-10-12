# WTC-simu2026

**Construction progressive d'une simulation exploratoire du WTC 1 : impact d'un Boeing 767, incendies et réponse structurelle, jusqu'à un éventuel effondrement ou son arrêt.**

Le projet teste des mécanismes, des hypothèses explicites et des plages de paramètres. Aucun résultat final n'est présupposé. Il s'agit d'une recherche personnelle reproductible, assistée par Codex, dont les modèles, calculs, essais rejetés et limites sont publiés pour être examinés et améliorés.

*English: an open, incremental WTC 1 research harness. Current results concern limited verification models; they do not establish the cause or reproduce the full historical collapse.*

## Où en est la simulation ?

Instantané du **12 octobre 2026** : **AIRCRAFT-A41 terminée**, prochaine étape **AIRCRAFT-A42**. Le registre compte **160 entrées**. A40+A41 ajoutent **quatorze témoins dynamiques**, dont **treize terminaisons normales**, **huit ensembles physiques réussis** dans leurs domaines déclarés, et **un contrôle CHECK simple réussi**. Les autres critères et premières lectures échoués sont conservés.

A40 qualifie le mouvement libre implicite et sa reprise native complète avec MUMPS/Newmark **à pas constant**, au pas initial et au demi-pas, en utilisant un plancher explicite de normalisation de force. Masses, matériaux, vitesses, paramètres physiques et seuils de conservation restent inchangés. La croissance adaptative échoue : pendant une croissance1,5, la trajectoire utilise temporairement une vitesse publiée voisine deV0/1,5 puis garde un décalage de déplacement. Les deux contacts déjà chargés repris depuis l’explicite restent hors énergie et convergence. Quatre reprises A37 vérifiées sont réutilisées sans recalculer les phases explicites ; les quatre jonctions passent.

A41 démarre le même **contact TYPE7 directement en implicite**, depuis une géométrie séparée. La source figée montre que les vitesses nodales publiées sont des vitesses sécantes, différentes des vitesses instantanées Newmark pendant l’accélération. Leur interprétation est vérifiée par les incréments de déplacement, la grille des cycles, les compteurs natifs de KE et de momentum. Aucun coefficient ajusté, terme RKE nouveau, injection dans les états ou patch de logiciel. Les cinq pas directs terminent : le plus grossier échoue, les quatre suivants passent les budgets physiques. La paire **6,25ns/3,125ns** passe les écarts de KE, énergie interne et contact élastique, sous le seuil originel0,5%KE0+10⁻⁷J. Les bornes de format six chiffres/float32 sont examinées séparément, avec les lectures littérales initiales conservées.

Le **CHECK simple** écrit son compte rendu puis termine normalement. L’avortement entier A37, avant ce compte rendu, reste à diagnostiquer dans sa lecture/données/complexité. Il n’est pas attribué automatiquement aux cinq TYPE25, qui ne figurent pas parmi les contacts implicites documentés. Le TYPE7 du cube ne les remplace pas dans l’avion. A42 doit traiter cette compatibilité entière avant un nouveau pilote. Les reprises chargées et la croissance A40 restent non qualifiées ; peaux A34 et raffinement A36 restent échoués séparément.

Les [rapports A40](wtc1_simulation_v8/output/aircraft_a40/rapport_aircraft_a40.md) et [A41](wtc1_simulation_v8/output/aircraft_a41/rapport_aircraft_a41.md) séparent faits, références, archives, hypothèses, résultats et lacunes. Compilation A35 terminée39,29min ; aucune nouvelle installation, compilation, modification de solveur, compensation de masse/densité/inertie ou matériau. Binaires, bibliothèques et sources tierces ne sont pas redistribués. Les propriétés de résistance/rupture et l’impact entier ne sont pas qualifiés par ces cubes.

La vidéo3D des **dix premières secondes physiques** reste incomplète : meilleur impact entier A20 = **20millisecondes physiques**. Aucun temps de cube ou de contrôle n’est crédité à l’impact entier ; aucun coût10s extrapolé depuis ces petits témoins. Aucun dommage historique connu comme cible. L’intégrité des archives et du dépôt n’est pas une validation physique ou historique de l’impact ou de l’effondrement.


## Ce qui est publié

- `harness/` : état scientifique, registre des expériences, références, contrôles et passations.
- `wtc1_simulation_v8/scripts/` et `data/` : code des calculs et configurations numériques.
- `wtc1_simulation_v8/output/`, dossiers CalculiX et OpenRadioss : résultats, rapports, bilans et diagnostics, y compris essais rejetés.
- `wtc1_3d_v4/` : scripts de visualisation, paramètres, audits et modèles/rendus dans les archives de résultats.
- `outputs/` : calculs exploratoires antérieurs et audits complémentaires. Leurs affirmations se lisent avec leurs propres limites ; leur présence n'est pas une validation.
- `publication/` : inventaire complet, empreintes SHA-256, règles de publication, licences tierces et liste motivée des fichiers externes non redistribués.

Inventaire courant : **15,486 fichiers scientifiques dans Git**, **26,215 sorties dans 121 archives**.

Restaurer les 120 anciennes archives des releases précédentes, puis les 1 archives [A40+A41](https://github.com/WTC-simu2026/WTC-simu2026/releases/tag/snapshot-2026-10-12-aircraft-a40-a41). Manifestes, SHA-256 et URL conservés ; aucune ancienne archive reconstruite ou remplacée.

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

AIRCRAFT-A42 : reprendre le contact direct implicite qualifié A41 à pas fixes6,25e-6/3,125e-6ms, sans recalculer ces témoins. La vitesse nodale publiée est une vitesse sécante; la reconstruction Newmark àγ.5/β.25 avec tous les cycles est vérifiée par déplacement, KE et momentum natifs. Les comparaisons de KE/IE/contact au demi-pas passent. Garder les diagnostics instantanés et les critères de format initiaux échoués. Le CHECK simple réussit avec compte rendu; l’avortement entier A37 est donc à diagnostiquer dans sa préparation/lecture/complexité, sans attribution automatique aux cinq TYPE25 non documentés pour l’implicite. Inspecter les fichiers et sources en cache pour localiser l’étape d’arrêt, puis déclarer une vérification bornée qui change une seule famille de données à la fois; conserver masse, matériaux, géométrie et anciens résultats. Toute variante de contact entière doit être déclarée, justifiée et comparée, jamais substituée silencieusement. Pas de pilotage/coût10s déduit du cube. La reprise chargée E→I et la croissance de pas A40 restent échouées; ne pas les utiliser. Peaux A34 et raffinement A36 restent non qualifiés. Compilation A35 terminée39,29min; aucune nouvelle compilation/installation ou modification de logiciel. Meilleur impact entier A20=20ms; dix secondes physiques3D puis vidéo/GIF incomplètes. Publier A40+A41 maintenant après intégrité des deux, selon autorisation/cadence.

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
