# WTC-simu2026

**Construction progressive d'une simulation exploratoire du WTC 1 : impact d'un Boeing 767, incendies et réponse structurelle, jusqu'à un éventuel effondrement ou son arrêt.**

Le projet teste des mécanismes, des hypothèses explicites et des plages de paramètres. Aucun résultat final n'est présupposé. Il s'agit d'une recherche personnelle reproductible, assistée par Codex, dont les modèles, calculs, essais rejetés et limites sont publiés pour être examinés et améliorés.

*English: an open, incremental WTC 1 research harness. Current results concern limited verification models; they do not establish the cause or reproduce the full historical collapse.*

## Où en est la simulation ?

Instantané du **13 octobre 2026** : **AIRCRAFT-A59 terminée**, prochaine étape **AIRCRAFT-A60**. Le registre compte **178 entrées**. A58 précise la chaîne native du blocage géométrique ; A59 prépare un prototype propre de résidu/rigidité surfacique. **La vidéo des dix secondes physiques reste incomplète.**

Le moteur A57 précédemment publié conserve ses corrections autorisées et le passage du témoin mémoire : capacité21 et pointeurSAV exact, en-têteNODREAC intact. **Aucun nouveau correctif, installation ou compilation A58/A59.** A58 lance un seul nouveau Engine instrumenté, CPU1/cap180s, sansGPU. Ordre observé : **SUSER43**, puis **S8ZKE3(TYPE43/LAW117,NEL1,ISMSTR1,JHBE0)**, **S8ZDERICT3**, **SCHKJAB3(DET0,OFF1,élément1)**. La face possède100mm² et hauteur0. L'hypothèse « volume avant toute surface » est rejetée et conservée. Code0/NORMAL suivi deUSER BREAK etSTOP volume nul àT=0 : aucune réponse chargée.

Sept routines sources figées sont auditées en lecture seule, avec empreintes et lignes ; sources brutesAGPL exclues. DansMMATS inspecté, pas de branche spécifique117, sans extrapoler cette absence à tout le programme. SIGEPS117 n'est pas directement instrumentée ; son appel est appuyé par la brancheSUSER43 et le matériau du cas. Retirer le contrôle de volume ne constituerait pas un traitement cohésif correct.

A59 n'exécute **aucun Engine/Starter**. Un prototype propre passe **112contrôles** : équilibre, intégrale surfacique fermée, rang12 et translations nulles, tangente active par différences finies, adoucissement négatif, covariance3D des forces/matrices, traction/travail/rechargement sur les quatre témoins natifsA57 réutilisés avec empreintes, sans les rejouer. CPU1, sansGPU, plafond120s, résultats en moins d'une seconde. Seuils physiquesA17 inchangés, aucune masse, matériau ouRKE compensatoire.

**Domaine limité** : plans rectangulaires en repère de référence fixe, matrice élastique3axes et tangente active en modes purs à adoucissement linéaire. Les directions passives gardent le dommage gelé. Modes mixtesLAW117, repères mobiles, tangente géométrique, état d'essai/retour arrièreNewton et connexion au moteur **non qualifiés**. STIFM deSUSER43 est une surestimation pour le pas explicite, pas une tangente implicite cohérente. Le prototype n'est pas prêt à être intégré à l'impact entier.

Les [rapports A58](wtc1_simulation_v8/output/aircraft_a58/rapport_aircraft_a58.md) et [A59](wtc1_simulation_v8/output/aircraft_a59/rapport_aircraft_a59.md) séparent les six catégories de preuve. Archives, anciennes sorties et hypothèses rejetées conservées. CHECK entier15erreurs/624volumes/cinqTYPE25 ignorés, A52 non intégré, couverture locale et domaines de matériau restent échoués ou manquants. Aucun dégât connu utilisé comme cible.

Meilleur impact entierA20 : **0,0200001220703125seconde**. L'ancienne projection linéaire6,89479jours pour10s est un ordre de grandeur historique, pas une ETA actuelle. Aucune prolongation de l'ancien état hors domaine ; aucun temps des témoins/prototype crédité comme impact. Aucune vidéo fabriquée par extrapolation ou ralenti. Intégrité de publication et physique restent distinctes.


## Ce qui est publié

- `harness/` : état scientifique, registre des expériences, références, contrôles et passations.
- `wtc1_simulation_v8/scripts/` et `data/` : code des calculs et configurations numériques.
- `wtc1_simulation_v8/output/`, dossiers CalculiX et OpenRadioss : résultats, rapports, bilans et diagnostics, y compris essais rejetés.
- `wtc1_3d_v4/` : scripts de visualisation, paramètres, audits et modèles/rendus dans les archives de résultats.
- `outputs/` : calculs exploratoires antérieurs et audits complémentaires. Leurs affirmations se lisent avec leurs propres limites ; leur présence n'est pas une validation.
- `publication/` : inventaire complet, empreintes SHA-256, règles de publication, licences tierces et liste motivée des fichiers externes non redistribués.

Inventaire courant : **17,580 fichiers scientifiques dans Git**, **34,781 sorties dans 134 archives**.

Restaurer les 133 anciennes archives des releases précédentes, puis les 1 archives [A58+A59](https://github.com/WTC-simu2026/WTC-simu2026/releases/tag/snapshot-2026-10-13-aircraft-a58-a59). Manifestes, SHA-256 et URL conservés ; aucune ancienne archive reconstruite ou remplacée.

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

AIRCRAFT-A60 : prototype propre de surface A59 disponible dans surface_aircraft_a59.py,112contrôles passent dans le domaine déclaré. Compléter et qualifier les modes mixtes selon SIGEPS117, états d’essai et validation/retour arrière de Newton, repères mobiles et tangente géométrique avant une différence moteur concrète. Le noyau A59 couvre plans rectangulaires, matrice élastique3axes et tangente ACTIVE de modes purs normaux/cisaillement à adoucissementlinéaire. Les directions passives gardent le dommage gelé ; cela ne qualifie pas le couplage mixte de LAW117. 112tests :équilibre,intégralefermée, rang12 et translationsnulles, différencesfinies de tangente, adoucissement négatif, rotations de repère3D, quatre témoinsnatifsA57 réutilisés sans rerun, travail et rechargement. SUSER43 décritSTIFM comme surestimation pour le pas explicite ; ne pas l’assimiler à une tangente implicite cohérente. Aucun patch moteur proposé/appliqué ou compilationA59, zéro nouveau Engine/Starter ; toute future modification/compilation moteur exige un accord explicite distinct après proposition concrète. Moteur A57 conservé34eb01b358869b4acd34a6204ec29083b95530d62ff6d7f2c9e43d20a90ef528 ; mémoire du témoin corrigée, mais STOP de jacobienvolumiqueTYPE43 reste. A58ordre natif surface puis rigidité volumique connu, ne pas le rejouer. CHECKentier15erreurs/624volumes/cinqTYPE25 ignorés, A52nonintégré, budgets/critèreséchoués conservés. Meilleur impact entierA20=0,0200001220703125s ; ne pas prolonger cet état horsdomaine vers10s. Coût historiqueA20=1191,4197075s pour20ms, projection linéaire6,89479jours pour10s est seulement un ordre de grandeur ancien, pas une ETA ni une autorisation d’extension. A20 ne modélisait pas gravité/intérieurporteur et ses critèreslocaux/matériaux échouaient ; aucune extrapolation de ces lacunes à une nouvelle scène sans inspection. Objectif1 dix secondes physiques puis vidéo3D incomplet, aucun crédit des témoins ou prototype. PublicationA58+A59 à vérifier, ensuite cadenceA60+A61. Aucun ancien solver rejoué.

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
