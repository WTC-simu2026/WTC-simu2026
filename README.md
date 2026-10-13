# WTC-simu2026

**Construction progressive d'une simulation exploratoire du WTC 1 : impact d'un Boeing 767, incendies et réponse structurelle, jusqu'à un éventuel effondrement ou son arrêt.**

Le projet teste des mécanismes, des hypothèses explicites et des plages de paramètres. Aucun résultat final n'est présupposé. Il s'agit d'une recherche personnelle reproductible, assistée par Codex, dont les modèles, calculs, essais rejetés et limites sont publiés pour être examinés et améliorés.

*English: an open, incremental WTC 1 research harness. Current results concern limited verification models; they do not establish the cause or reproduce the full historical collapse.*

## Où en est la simulation ?

Instantané du **13 octobre 2026** : **AIRCRAFT-A57 terminée**, prochaine étape **AIRCRAFT-A58**. Le registre compte **176 entrées**. Les deux itérations conservent les anciens moteurs, budgets et critères échoués ; la vidéo des dix secondes physiques demeure incomplète.

A56 compile le correctif du tampon temporaire dans un quatrième moteur isolé. Il ne résout pas la corruption : sept arrêts cohésifs implicites avant le premier pas, parmi17Engine nouveaux, aucun Starter. Les contrôles natifs de graphe/attaches, quatre témoins explicites et deuxTYPE7 passent dans leur domaine. Une mesure de740appels lit le tampon **d'origine** ELBUF_STR%GBUF%SMSTR : demande0, double8octets, bornes1..0, capacité0. Son pointeur est exactement SAV transmis à SRCOORK. La proposition initiale ciblait une copie temporaire ; son échec est conservé.

A57 applique le nouveau correctif original explicitement autorisé dans **un cinquième moteur séparé**, avec les correctifs antérieurs conservés. Source figée3d75ff13d1946f6d28a43920eac4fa2aae41b27a, compilation plafonnée1h/sixCPU, sans GPU ni installation. Seule nouvelle différence : allocbuf_auto.F réserve au moins21*NEL valeurs au TYPE43 sans changer largeurs de redémarrage, offsets ni nombre de valeurs restaurées. Les sources dérivées/patch/binaire AGPL restent hors du manifeste MIT ; scripts propres, sorties et empreintes sont conservés.

Les mesures et critères A57 sont enregistrés séparément : **17 nouveaux Engine**, aucun ancien moteur rejoué, contrôles plafonnés180s/unCPU. **Capacité native originale21/NEL1 et pointeur SAV exact, en-tête mémoire intact ; les quatre témoins implicites restent àT=0 avecSTOP volume nul etUSER BREAK. Graphe/attaches, quatre témoins explicites et deuxTYPE7 passent dans leur domaine, physique entière toujours non qualifiée.**


Les [rapports A56](wtc1_simulation_v8/output/aircraft_a56/rapport_aircraft_a56.md) et [A57](wtc1_simulation_v8/output/aircraft_a57/rapport_aircraft_a57.md) séparent les six catégories de preuve. Le CHECK entier échoué et les cinqTYPE25 ignorés ne sont pas annulés par la correction d'un tampon. A52 n'est pas intégré, les travaux/inerties et la couverture énergétique entière restent manquants. Aucune masse compensatoire, RKE inventée ou cible de dégâtsNIST. Sources historiques et anciennes archives restent intactes.

Meilleur impact entierA20 : **0,0200001220703125seconde**. Aucun temps des témoins isolés n'est crédité à l'impact entier. Aucune vidéo de dix secondes fabriquée par extrapolation ou ralenti ; publication/intégrité ne signifie ni validation physique ni validation historique.


## Ce qui est publié

- `harness/` : état scientifique, registre des expériences, références, contrôles et passations.
- `wtc1_simulation_v8/scripts/` et `data/` : code des calculs et configurations numériques.
- `wtc1_simulation_v8/output/`, dossiers CalculiX et OpenRadioss : résultats, rapports, bilans et diagnostics, y compris essais rejetés.
- `wtc1_3d_v4/` : scripts de visualisation, paramètres, audits et modèles/rendus dans les archives de résultats.
- `outputs/` : calculs exploratoires antérieurs et audits complémentaires. Leurs affirmations se lisent avec leurs propres limites ; leur présence n'est pas une validation.
- `publication/` : inventaire complet, empreintes SHA-256, règles de publication, licences tierces et liste motivée des fichiers externes non redistribués.

Inventaire courant : **17,525 fichiers scientifiques dans Git**, **34,776 sorties dans 133 archives**.

Restaurer les 131 anciennes archives des releases précédentes, puis les 2 archives [A56+A57](https://github.com/WTC-simu2026/WTC-simu2026/releases/tag/snapshot-2026-10-13-aircraft-a56-a57). Manifestes, SHA-256 et URL conservés ; aucune ancienne archive reconstruite ou remplacée.

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

AIRCRAFT-A58 : moteur A57 compilé et contrôlé, SHA25634eb01b358869b4acd34a6204ec29083b95530d62ff6d7f2c9e43d20a90ef528, a57_original_type43_scratch_candidate ; accords A53 graphe/A55 temporaire/A56 original tous distincts enregistrés. Capacité native originale21 pourNEL1, pointeur identique àSAV, en-tête NODREAC0x31 intact au retour ; corruption observée levée dans ce témoin. Dix-sept nouveaux Engine code0/NORMAL, aucun Starter ; cela ne qualifie pas la réponse chargée : quatre témoins implicites restentT=0, STOP volume nul puisUSER BREAK, CSV vides, échec de lecteur conservé. CHECK cohésif isolé5erreurs/unvolume, solide ordinaire1erreur de matrice ; entier15erreurs/624volumes/cinqTYPE25 ignorés. Graphe256opérations,3024attaches exactes, quatre témoins explicites et deuxTYPE7/bilans etdemi-pas passent,600champs sous règle de précision préexistante. Prochaine étape : examiner et vérifier la chaîne géométrie/tangente implicite du TYPE43/LAW117 et les contacts entiers avant de proposer un traitement de surface. Les sources déjà ciblées S8ZKE3→S8ZDERICT3→SCHKJAB3 montrent un jacobien volumique ; MMATS/MMSTIFS nécessitent audit de compatibilité. Ne pas supprimer le STOP, inventer une épaisseur pour le contourner ou déclarer NORMAL comme réponse physique. Inspections et nouveaux contrôles de cas bornés avec le même binaire sont autorisés ; toute nouvelle modification du logiciel exige une proposition concrète et un accord distinct. A52 reste non intégré ; budgets, anciennes sorties et échecs conservés, zéroRKE compensatoire. Meilleur impact entierA20=0,0200001220703125s, objectif1 dix secondes physiques puis vidéo3D incomplet. Cadence A56+A57 à publier/vérifier ; ne pas rejouer les anciens Engine.

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
