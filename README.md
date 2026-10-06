# WTC-simu2026

**Construction progressive d'une simulation exploratoire du WTC 1 : impact d'un Boeing 767, incendies et réponse structurelle, jusqu'à un éventuel effondrement ou son arrêt.**

Le projet teste des mécanismes, des hypothèses explicites et des plages de paramètres. Aucun résultat final n'est présupposé. Il s'agit d'une recherche personnelle reproductible, assistée par Codex, dont les modèles, calculs, essais rejetés et limites sont publiés pour être examinés et améliorés.

*English: an open, incremental WTC 1 research harness. Current results concern limited verification models; they do not establish the cause or reproduce the full historical collapse.*

## Où en est la simulation ?

Instantané du **6 octobre 2026** : AIRCRAFT-A06 et AIRCRAFT-A07 terminées comme investigations limitées ; prochaine étape AIRCRAFT-A08.

Les moteurs appartiennent désormais au modèle mécanique couplé du 767 : **960 triangles de coque, 56 liaisons**, deux budgets de 4 500 kg sans double comptage. Cinq départs intacts A07 sont conservés : vol libre, début du contact par le nez, trois contrôles limités au contact initial des nacelles. Le vol libre passe ses critères ; demi-pas moteur : impulsion 0,1354 %, énergie générée 0,0591 %, dans les limites annoncées.

**Bilan local d’énergie échoué, fortes déformations plastiques, convergence spatiale moteur non testée.** Écart supplémentaire de centre de masse 0,0203 mm conservé contre le seuil strict, lié aux centroïdes natifs des nacelles coniques et non expliqué complètement. Les carters internes ne sont pas encore directement heurtés à 0,8 ms, pales/disques/spin/écrasement/fragments et autocontact moteur absents. Profils internes, matériaux et attaches restent des hypothèses.

A06 refuse le transfert de la rupture ORTHENERG au radôme : énergie totale dépendante de la longueur et dommage supplémentaire à la recharge au même pic. A07 localise la plus forte perte A06 entre 1,640568 et 1,660712 ms depuis ses sorties sauvegardées, sans cause établie ni ancien calcul relancé. Un contrat de rupture analytique avec énergie totale et historique maximal est conservé, sans implémentation native qualifiée. Aucun résultat de dégâts NIST utilisé comme cible.

Sources primaires EASA/GE/Boeing distinguées des hypothèses. Ces contrôles et leur publication ne valident **ni l’impact historique, ni un incendie calculé, ni un effondrement réel**. V11F froid, branches différées et toutes les limites anciennes restent préservés.


## Ce qui est publié

- `harness/` : état scientifique, registre des expériences, références, contrôles et passations.
- `wtc1_simulation_v8/scripts/` et `data/` : code des calculs et configurations numériques.
- `wtc1_simulation_v8/output/`, dossiers CalculiX et OpenRadioss : résultats, rapports, bilans et diagnostics, y compris essais rejetés.
- `wtc1_3d_v4/` : scripts de visualisation, paramètres, audits et modèles/rendus dans les archives de résultats.
- `outputs/` : calculs exploratoires antérieurs et audits complémentaires. Leurs affirmations se lisent avec leurs propres limites ; leur présence n'est pas une validation.
- `publication/` : inventaire complet, empreintes SHA-256, règles de publication, licences tierces et liste motivée des fichiers externes non redistribués.

Inventaire courant : **6,446 fichiers scientifiques dans Git**, **9,012 sorties dans 57 archives**.

Restaurer les 53 anciennes archives des releases précédentes, puis les 4 archives [A06+A07](https://github.com/WTC-simu2026/WTC-simu2026/releases/tag/snapshot-2026-10-06-aircraft-a06-a07). Manifestes, SHA-256 et URL conservés ; aucune ancienne archive reconstruite ou remplacée.

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

AIRCRAFT-A08 : poursuivre les moteurs dans l’avion entier par un contact segmenté et des historiques locaux de masse, énergie, impulsion et efforts. Expliquer ou borner le déficit de contact et l’écart du premier moment, puis comparer un maillage moteur affiné à masse et géométrie constantes avant un horizon prolongé ou la fragmentation. Les carters, pales et assemblages réels restent à identifier ; aucune calibration sur des dégâts attendus. Le contrat énergétique du radôme reste analytique tant qu’une implémentation native et son historique ne sont pas vérifiés. Prochaine publication après deux nouvelles itérations vérifiées A08+A09.


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
