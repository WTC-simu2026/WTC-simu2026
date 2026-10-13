# WTC-simu2026

**Construction progressive d'une simulation exploratoire du WTC 1 : impact d'un Boeing 767, incendies et réponse structurelle, jusqu'à un éventuel effondrement ou son arrêt.**

Le projet teste des mécanismes, des hypothèses explicites et des plages de paramètres. Aucun résultat final n'est présupposé. Il s'agit d'une recherche personnelle reproductible, assistée par Codex, dont les modèles, calculs, essais rejetés et limites sont publiés pour être examinés et améliorés.

*English: an open, incremental WTC 1 research harness. Current results concern limited verification models; they do not establish the cause or reproduce the full historical collapse.*

## Où en est la simulation ?

Instantané du **13 octobre 2026** : **AIRCRAFT-A61 terminée**, prochaine étape **AIRCRAFT-A62**. Registre **180 entrées**. Les dix secondes physiques d’impact et leur vidéo3D restent incomplètes.

**A60 : six nouveaux témoins explicites** mixtes, non proportionnels et compression après dommage, CPU1/sansGPU, chacun plafonné180s, Starter sans erreur/avertissement puis Engine A57 normal. Traction dans les trois directions, travail/énergie, demi-pas et aire×4 passent les seuils A17 conservés. Erreur maximale relative de traction0,000891.22contrôles propres de dérivée complète et état d’essai passent ; dérivée mixte généralement non symétrique, incompatible avec l’insertion directe dans un assemblage triangulaire symétrique.

L’historique natif0,9999ms reste inchangé. Ses contrôles de fin initialement échoués et l’égalité stricte échouée du champ à1,00001ms sont conservés. Une analyse séparée après calcul vérifie la fin effective à1ms dans un pas déclaré, avec les champs sauvegardés, sans modifier durée/pas ni seuil mécanique. Aucun temps de témoin ajouté à la couverture entière.

**A61 : aucun nouveau Starter/Engine**,44contrôles propres d’une matrice surfacique symétrique d’itération : équilibre, aires uniformes/nonuniformes, rang12, translations nulles, rotation3D, reconstruction triangulaire, neuf équilibres à résidu mixte complet avec états validés gelés. L’échec R0 bit à bit reste archivé ; R1 utilise la tolérance matricielle1e-12 déjà déclarée. Une différence exacte de s8zke3.F est préparée : branche TYPE43+LAW117+Ismstr1, quatre aires natives de référence, normale courante ; les forces et états SUSER43/SIGEPS117 restent calculés nativement. Cette matrice est une approximation d’itération, pas une tangente cohérente.

**Correctif non appliqué/non compilé dans cette paire.** [Proposition A61](wtc1_simulation_v8/output/aircraft_a61/proposition_correctif_surface_implicite.md). Accord distinct reçu pour la future A62 : sixième moteur isolé, plafond compilation1h/CPU6/sansGPU/sansinstallation, jusqu’à12contrôles CPU1/plafond180s chacun. Les cinq moteurs antérieurs et trois correctifs déjà autorisés sont conservés. Grande rotation, convergence implicite native et restauration des états Newton restent non qualifiées ; un échec bloquera l’intégration entière. Source/différence bruteAGPL hors des archives publiques MIT.

Les [rapports A60](wtc1_simulation_v8/output/aircraft_a60/rapport_aircraft_a60.md) et [A61](wtc1_simulation_v8/output/aircraft_a61/rapport_aircraft_a61.md) séparent les six catégories de preuve. Aucun budget de masse/matériau, termeRKE ou seuil physique changé, aucun dégât connu ciblé. Archives/anciennes sorties/échecs conservés ; aucun ancien solver rejoué.

CHECK entier15erreurs/624volumes/cinqTYPE25 ignorés ; A52 non intégré, domaines matériaux/bilans locaux échoués conservés. **Meilleur impact entier :0,0200001220703125s**, sans prolongation de l’ancien état hors domaine. Aucune vidéo obtenue par interpolation des secondes manquantes. Intégrité de publication et validation physique restent distinctes.


## Ce qui est publié

- `harness/` : état scientifique, registre des expériences, références, contrôles et passations.
- `wtc1_simulation_v8/scripts/` et `data/` : code des calculs et configurations numériques.
- `wtc1_simulation_v8/output/`, dossiers CalculiX et OpenRadioss : résultats, rapports, bilans et diagnostics, y compris essais rejetés.
- `wtc1_3d_v4/` : scripts de visualisation, paramètres, audits et modèles/rendus dans les archives de résultats.
- `outputs/` : calculs exploratoires antérieurs et audits complémentaires. Leurs affirmations se lisent avec leurs propres limites ; leur présence n'est pas une validation.
- `publication/` : inventaire complet, empreintes SHA-256, règles de publication, licences tierces et liste motivée des fichiers externes non redistribués.

Inventaire courant : **17,749 fichiers scientifiques dans Git**, **36,025 sorties dans 135 archives**.

Restaurer les 134 anciennes archives des releases précédentes, puis les 1 archives [A60+A61](https://github.com/WTC-simu2026/WTC-simu2026/releases/tag/snapshot-2026-10-13-aircraft-a60-a61). Manifestes, SHA-256 et URL conservés ; aucune ancienne archive reconstruite ou remplacée.

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

AIRCRAFT-A62 : correctif A61 prêt, NON appliqué/NON compilé. Proposition : wtc1_simulation_v8/output/aircraft_a61/proposition_correctif_surface_implicite.md. Demander un accord humain explicite distinct pour la différence exacte de s8zke3.F, sixième moteur isolé, compilation cap1h/CPU6/sansGPU/sansinstallation et au maximum12 Engine CPU1/cap180s. SHA patch1c2c9b74239d75883234057d2ae0f1e28d0dd017abb5fa99aa8deaad89b3a3b8 ; source proposée53a6d683bff4e2f3124ac98d2743f74777107890031b5e407af489859407f35e. Branche TYPE43+LAW117+Ismstr1, quatre aires natives de référence et normale courante, matrice symétrique élastique d’itération, forces/loi/histoire natives inchangées ; pas une tangente exacte. 44 contrôles propres A61 passent ; neuf équilibres mixtes à résidu complet avec état validé gelé. Échec bit à bit R0 archivé, R1 applique la tolérance matricielle1e-12 déjà déclarée. A60 six témoins explicites nouveaux et22contrôles de dérivée passent, pas de nouveau solver A61. Retour arrière des états natifs, convergence et grandes rotations restent non qualifiés et conditionnent les contrôles. Ne pas seulement ignorer le STOP volume, changer SYM ou inventer une épaisseur. Ne pas intégrer au modèle entier avant contrôles locaux natifs. Moteur A57inchangé SHA34eb01b358869b4acd34a6204ec29083b95530d62ff6d7f2c9e43d20a90ef528. Anciennes cinq sorties/moteurs, budgets et critères échoués préservés. CHECK entier15erreurs/624volumes/cinqTYPE25 ignorés, A52nonintégré. Meilleur impact entierA20=0,0200001220703125s, aucun crédit physique A60/A61. Objectif dix secondes physiques puis vidéo3D incomplet. PublicationA60+A61 à vérifier, prochaine cadenceA62+A63. Aucun diagnostic ancien à rejouer sans une nouvelle question.

Accord humain distinct reçu pour ce correctif exact, enregistré dans wtc1_simulation_v8/data/aircraft_a62_authorization.json. Application/compilation A62 non encore exécutées à cet instantané.

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
