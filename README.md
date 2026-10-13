# WTC-simu2026

**Construction progressive d'une simulation exploratoire du WTC 1 : impact d'un Boeing 767, incendies et réponse structurelle, jusqu'à un éventuel effondrement ou son arrêt.**

Le projet teste des mécanismes, des hypothèses explicites et des plages de paramètres. Aucun résultat final n'est présupposé. Il s'agit d'une recherche personnelle reproductible, assistée par Codex, dont les modèles, calculs, essais rejetés et limites sont publiés pour être examinés et améliorés.

*English: an open, incremental WTC 1 research harness. Current results concern limited verification models; they do not establish the cause or reproduce the full historical collapse.*

## Où en est la simulation ?

Instantané du **13 octobre 2026** : **AIRCRAFT-A55 terminée**, prochaine étape **AIRCRAFT-A56**, nouveau correctif mémoire explicitement autorisé. Le registre compte **174 entrées**. Le moteur A54 corrige le rangement du graphe ; A55 observe une corruption mémoire avant le premier pas cohésif implicite. Les dix secondes physiques et leur vidéo3D restent incomplètes.

A54 compile le correctif exact A53 autorisé dans un troisième moteur isolé, sans remplacer les anciens. Une première garde sur les fins de ligne arrête la préparation avant compilation, conservée ; R1 vérifie puis copie le fichier proposé exact. Compilation248,771s, total474,160s dans le plafond1h, sixCPU, sans GPU ni installation. Dix nouveaux Engine, aucun Starter, caps180s/unCPU. Les deux CHECK référence et candidat A52 terminent sans messages de connectivité manquante, et les3024attaches natives correspondent exactement. L'oracle observe256opérations,140doublons et116vrais nouveaux voisins : tous les ensembles avant/après passent. L'ancienne sonde auxiliaire sans appels et l'hypothèse de compteur final3 échouée restent conservées.

Le CHECK entier conserve **15erreurs,624messages de volume et5TYPE25 ignorés**. Les624éléments signalés sont LAW117/TYPE43, faces positives, hauteur nulle ; cela ne supprime aucun critère échoué. Quatre témoins cohésifs explicites et deux témoins TYPE7/MUMPS passent leurs bilans physiques et demi-pas ;600champs passent la règle de précision déjà établie, échecs littéraux conservés. Une analyse de contact initialement sans métadonnée est réparée dans un résultat distinct sans relancer le moteur. A52 reste non intégré.

A55 utilise le même binaire intact,16nouveaux Engine et10lancements Starter dont4échecs de configuration conservés et6préparations propres. Quinze Engine cohésifs s'arrêtent code3 àNC=0/T=0 ; le solide ordinaire termine mais garde1erreur de matrice définie positive. Libérer des déplacements non chargés ou retirer les sorties nodales ne résout pas l'arrêt. Une surveillance native établit l'écritureSRCOORK+0x4488 qui remplace un en-tête malloc0x31 par0, puis free échoue. Le contexte est TYPE43/NEL1/ISMSTR1 ; les observations incomplètes restent conservées.

SRCOORK déclareSAV(NEL,21), transmis commeSMSTR, alors que l'allocation temporaire dépend deNEL*G_SMSTR. L'insuffisance de capacité est une **inférence du contrat source**, la capacité native n'a pas été lue. La proposition ne change que ce tampon temporaire TYPE43 ;48contrôles arithmétiques passent, aucun contrôle compilé revendiqué. Le nouvel accord reçu couvre un quatrième moteur isolé,1h/sixCPU puis témoins bornés180s, sans GPU ni installation. **Aucun nouveau correctif appliqué ni compilation A56 à la date de cet instantané.** Les sources dérivées et patch AGPL restent hors du manifeste MIT.

Les [rapports A54](wtc1_simulation_v8/output/aircraft_a54/rapport_aircraft_a54.md) et [A55](wtc1_simulation_v8/output/aircraft_a55/rapport_aircraft_a55.md) séparent les six catégories de preuve. Archives, anciennes sorties, moteurs et critères échoués préservés. Aucune masse compensatoire, RKE inventée ou cible de dégâtsNIST. La suppression d'un défaut mémoire ne qualifiera ni les contacts entiers ni la cohésion implicite chargée.

Meilleur impact entierA20 : **0,0200001220703125seconde**. Aucun diagnostic n'est crédité comme durée physique supplémentaire ; aucune vidéo de dix secondes fabriquée par extrapolation. L'intégrité de publication ne valide pas la physique ni l'événement historique.


## Ce qui est publié

- `harness/` : état scientifique, registre des expériences, références, contrôles et passations.
- `wtc1_simulation_v8/scripts/` et `data/` : code des calculs et configurations numériques.
- `wtc1_simulation_v8/output/`, dossiers CalculiX et OpenRadioss : résultats, rapports, bilans et diagnostics, y compris essais rejetés.
- `wtc1_3d_v4/` : scripts de visualisation, paramètres, audits et modèles/rendus dans les archives de résultats.
- `outputs/` : calculs exploratoires antérieurs et audits complémentaires. Leurs affirmations se lisent avec leurs propres limites ; leur présence n'est pas une validation.
- `publication/` : inventaire complet, empreintes SHA-256, règles de publication, licences tierces et liste motivée des fichiers externes non redistribués.

Inventaire courant : **16,992 fichiers scientifiques dans Git**, **30,653 sorties dans 131 archives**.

Restaurer les 130 anciennes archives des releases précédentes, puis les 1 archives [A54+A55](https://github.com/WTC-simu2026/WTC-simu2026/releases/tag/snapshot-2026-10-13-aircraft-a54-a55). Manifestes, SHA-256 et URL conservés ; aucune ancienne archive reconstruite ou remplacée.

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

AIRCRAFT-A56 : accord explicite reÃ§u le13octobre pour le nouveau correctif A55 du tampon SMSTR temporaire TYPE43, patch a0d52993240ac373a726185b2a3400d447bd947a59aa483b7f60e45c2bdc8503, source alloc_elbuf_imp.F seulement ; prÃ©server le correctif de graphe A53, source figÃ©e3d75ff13d1946f6d28a43920eac4fa2aae41b27a. Compiler un quatriÃ¨me moteur isolÃ© a56_type43_scratch_candidate, une heure maximum/sixCPU/sansGPU ni installation, puis contrÃ´les natifs capacitÃ©/mÃ©moire et cohÃ©sion implicite chargÃ©e, graphe/CHECK et rÃ©gressions explicites/TYPE7 avec critÃ¨res inchangÃ©s et180s par processus. A55 :16Engine,10Starter dont4Ã©checs de configuration conservÃ©s, aucun temps physique chargÃ© ; corruption malloc directement Ã©crite par SRCOORK surTYPE43, insuffisance de capacitÃ© infÃ©rÃ©e du contrat SAV(NEL,21) et allocation NEL*G_SMSTR ; capacitÃ© native G_SMSTR non lue. La suppression de la corruption ne qualifiera pas les lois, les15erreurs CHECK entiÃ¨res ni les5TYPE25 ignorÃ©s. Le contrÃ´le solide ordinaire termine mais conserve1erreur de matrice dÃ©finie positive. A52 non intÃ©grÃ©, budgets et tous Ã©checs conservÃ©s, aucune RKE compensatoire. Meilleur impact entier A20=0,0200001220703125s ; objectif1 dix secondes physiques puis vidÃ©o3D toujours incomplet. Publication A54+A55 Ã  vÃ©rifier avant remise Ã  zÃ©ro de la cadence.

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
