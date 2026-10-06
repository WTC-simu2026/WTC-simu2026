# WTC-simu2026

**Construction progressive d'une simulation exploratoire du WTC 1 : impact d'un Boeing 767, incendies et réponse structurelle, jusqu'à un éventuel effondrement ou son arrêt.**

Le projet teste des mécanismes, des hypothèses explicites et des plages de paramètres. Aucun résultat final n'est présupposé. Il s'agit d'une recherche personnelle reproductible, assistée par Codex, dont les modèles, calculs, essais rejetés et limites sont publiés pour être examinés et améliorés.

*English: an open, incremental WTC 1 research harness. Current results concern limited verification models; they do not establish the cause or reproduce the full historical collapse.*

## Où en est la simulation ?

Instantané du **6 octobre 2026** : AIRCRAFT-A08 et AIRCRAFT-A09 terminées comme contrôles limités ; prochaine étape AIRCRAFT-A10. **Neuf itérations de la branche avion entier**, aucune calibration sur les dommages NIST.

Les moteurs sont couplés au modèle mécanique du 767, avec **960 ou 3 840 triangles de coque et 56 liaisons**, deux budgets hypothétiques de 4 500 kg. A08 ajoute les historiques des pièces/inerties et corrige le contrôle du centre de masse A07 selon la répartition nodale native ; aucune masse ou force modifiée. Deux maillages à même surface facettée sont comparés. A09 exécute neuf contrôles du premier contact, avec formulations de raideur et variantes RBE3 déclarées avant calcul.

**Bilan local d’énergie et critères spatiaux échoués, interprétation de rotation non qualifiée.** À environ 0,4 ms, résidu du maillage fin −36,07 kJ au réglage de base ; −69,62 et −65,17 kJ avec les facteurs de contact effectivement réduits. Le facteur 0,1 est inactif dans ce contrôle. La variante RBE3 est activée par le Starter, conserve les impulsions/énergies globales sauvegardées mais présente des différences internes. Aucun canal suspect ajouté pour compenser le déficit ; aucun réglage choisi pour atteindre un résultat attendu.

Les nacelles sont touchées en premier ; les carters fan/core ne sont pas encore directement heurtés. Ces scènes ne constituent pas la traversée historique complète : contact extérieur limité aux moteurs, absence de planchers/noyau, rotors et fragmentation. Géométrie interne, matériaux et attaches restent des hypothèses. Le contrat de fracture à historique maximal demeure analytique ; la loi native refusée A06 n’est pas transférée.

Tous les échecs et premières erreurs des lecteurs sont conservés avec leurs corrections documentées. Publication = intégrité et reproductibilité des fichiers, sans nouveau calcul scientifique. V11F/V11R préservés ; température imposée distincte d’un incendie calculé ; Blender reste une visualisation. **Ni impact historique ni effondrement réel validés.**


## Ce qui est publié

- `harness/` : état scientifique, registre des expériences, références, contrôles et passations.
- `wtc1_simulation_v8/scripts/` et `data/` : code des calculs et configurations numériques.
- `wtc1_simulation_v8/output/`, dossiers CalculiX et OpenRadioss : résultats, rapports, bilans et diagnostics, y compris essais rejetés.
- `wtc1_3d_v4/` : scripts de visualisation, paramètres, audits et modèles/rendus dans les archives de résultats.
- `outputs/` : calculs exploratoires antérieurs et audits complémentaires. Leurs affirmations se lisent avec leurs propres limites ; leur présence n'est pas une validation.
- `publication/` : inventaire complet, empreintes SHA-256, règles de publication, licences tierces et liste motivée des fichiers externes non redistribués.

Inventaire courant : **6,818 fichiers scientifiques dans Git**, **9,307 sorties dans 64 archives**.

Restaurer les 57 anciennes archives des releases précédentes, puis les 7 archives [A08+A09](https://github.com/WTC-simu2026/WTC-simu2026/releases/tag/snapshot-2026-10-06-aircraft-a08-a09). Manifestes, SHA-256 et URL conservés ; aucune ancienne archive reconstruite ou remplacée.

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

AIRCRAFT-A10 : isoler le premier contact dans un témoin élastique sans redistribution RBE3, avec un bilan analytique et des conventions de sortie explicites. Identifier les inerties natives de coque et la signification du canal RKE, puis vérifier les options de contact et le pas de temps avant transfert vers l’avion. Ne pas ajuster Stfac aux dégâts attendus. Rupture/écrasement à historique et énergie contrôlés, rotors, autocontact/fragments, planchers/noyau et conditions AA11 restent à traiter. Prochaine publication après deux itérations vérifiées A10+A11.


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
