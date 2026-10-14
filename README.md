# WTC-simu2026

**Construction progressive d'une simulation exploratoire du WTC 1 : impact d'un Boeing 767, incendies et réponse structurelle, jusqu'à un éventuel effondrement ou son arrêt.**

Le projet teste des mécanismes, des hypothèses explicites et des plages de paramètres. Aucun résultat final n'est présupposé. Il s'agit d'une recherche personnelle reproductible, assistée par Codex, dont les modèles, calculs, essais rejetés et limites sont publiés pour être examinés et améliorés.

*English: an open, incremental WTC 1 research harness. Current results concern limited verification models; they do not establish the cause or reproduce the full historical collapse.*

## Où en est la simulation ?

Instantané du **14 octobre 2026** : **AIRCRAFT-A69 terminée**, prochaine **AIRCRAFT-A70**, registre **188 entrées**. Objectif dix secondes physiques puis vidéo 3D incomplet.

**A68 : audit en lecture seule des nouveaux CHECK A67.** Huit sources logicielles figées expliquent la chaîne : le contrôle de connexion porte sur un tableau réutilisé comme préconditionneur après LIN_SOLV, avec des coefficients issus d’inverses approchés. Ses faibles valeurs ne sont pas, à elles seules, une preuve de déconnexion. Les 75 nœuds de translation signalés ont tous des incidences d’éléments : 74 au fuselage, un à l’aile. Cela ne démontre pas le rang complet des contraintes. Les cinq TYPE25 restent ignorés et bloquants. Aucun Engine, Starter, correctif ou compilation en A68.

**A69 : trois Engine sur un CPU/plafond 180 s, après accord humain distinct.** Moteur A67 inchangé, sans Starter, GPU, installation ni compilation. **La première observation originale échoue** : le lecteur propre tentait de lire l’adresse inutilisée d’un tableau de taille zéro. Échec compté et conservé, aucune valeur native R2 attribuée à l’original. Une version R1 du lecteur traite correctement un tableau vide ; seules les deux observations restantes sont exécutées, sans répétition ni remise à zéro du budget.

**Deux observations complètes : R2 vaut exactement zéro**, et LB est entièrement nul, dans la scène appariée et le témoin libre CHECK. Ce témoin conserve sa dynamique libre A67 qualifiée jusqu’à 1 ms. Il affiche pourtant l’erreur native de chargement, car le contrôle exige un résidu strictement positif. Dans la scène appariée, la diagonale assemblée dynamique/contraintes est positive, comprise entre 1,13727e7 et 1,14438e18 ; les coefficients après préconditionnement vont de 8,73833e-19 à 8,79297e-8. Les 107391 valeurs signalées concordent avec ce tableau transformé. La positivité dynamique ne prouve pas la validité des seules liaisons statiques. La correspondance complète entre équations libres réduites et les deux diagonales n’est pas reconstruite sans IKC ; aucune correspondance inventée.

**La scène entière reste refusée** : une erreur de chargement, 107391 avertissements de connexion possible et cinq TYPE25 ignorés. L’observation originale reste incomplète ; deux mesures réussies ne deviennent pas trois réussites. Tous les anciens critères, sorties et budgets restent conservés. A52 non intégrée, aucun impact entier prolongé, aucune force fictive ou compensation RKE.

**A70 : préparer le correctif limité au contrôle du résidu initial dynamique nul**, en préservant les anciens CHECK refusés et la distinction entre admissibilité numérique et qualification physique. Toute nouvelle modification/compilation du moteur nécessite un accord humain distinct. Les cinq contacts requièrent encore une variante déclarée et contrôlée, sans substitution silencieuse.

Les [rapports A68](wtc1_simulation_v8/output/aircraft_a68/rapport_aircraft_a68.md) et [A69](wtc1_simulation_v8/output/aircraft_a69/rapport_aircraft_a69.md) séparent les six catégories de preuve. Sources privées AGPL et binaires exclus des livrables MIT. **Meilleur impact entier : 0,0200001220703125 s.** Aucune seconde manquante fabriquée dans une vidéo. Publication et CI attestent l’intégrité, pas la validité physique de l’impact réel.


## Ce qui est publié

- `harness/` : état scientifique, registre des expériences, références, contrôles et passations.
- `wtc1_simulation_v8/scripts/` et `data/` : code des calculs et configurations numériques.
- `wtc1_simulation_v8/output/`, dossiers CalculiX et OpenRadioss : résultats, rapports, bilans et diagnostics, y compris essais rejetés.
- `wtc1_3d_v4/` : scripts de visualisation, paramètres, audits et modèles/rendus dans les archives de résultats.
- `outputs/` : calculs exploratoires antérieurs et audits complémentaires. Leurs affirmations se lisent avec leurs propres limites ; leur présence n'est pas une validation.
- `publication/` : inventaire complet, empreintes SHA-256, règles de publication, licences tierces et liste motivée des fichiers externes non redistribués.

Inventaire courant : **18,579 fichiers scientifiques dans Git**, **40,979 sorties dans 139 archives**.

Restaurer les 138 anciennes archives des releases précédentes, puis les 1 archives [A68+A69](https://github.com/WTC-simu2026/WTC-simu2026/releases/tag/snapshot-2026-10-14-aircraft-a68-a69). Manifestes, SHA-256 et URL conservés ; aucune ancienne archive reconstruite ou remplacée.

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

AIRCRAFT-A70 : préparer en lecture seule le correctif précis de classification du résidu initial dynamique nul dans IMP_CHKM, à partir de R2=0 directement mesuré dans le témoin libre et la scène appariée. Préserver les anciens CHECK refusés ; distinguer cette admissibilité numérique de la qualification physique entière. Conserver les 107391 avertissements de préconditionnement et les cinq TYPE25 bloquants, sans substitution silencieuse ni fausse force. A69 : trois Engine consommés, aucun Starter, moteur A67 inchangé ; première observation originale échouée sur le lecteur de tableau vide, deux restantes complètes après correction propre du lecteur, aucune répétition. Aucun crédit d’impact entier. Nouveau correctif/compilation et lot natif exigent une proposition concrète et un nouvel accord distinct. Meilleur impact entier 0,0200001220703125 s ; dix secondes physiques et vidéo 3D incomplètes.

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
