# WTC-simu2026

**Construction progressive d'une simulation exploratoire du WTC 1 : impact d'un Boeing 767, incendies et réponse structurelle, jusqu'à un éventuel effondrement ou son arrêt.**

Le projet teste des mécanismes, des hypothèses explicites et des plages de paramètres. Aucun résultat final n'est présupposé. Il s'agit d'une recherche personnelle reproductible, assistée par Codex, dont les modèles, calculs, essais rejetés et limites sont publiés pour être examinés et améliorés.

*English: an open, incremental WTC 1 research harness. Current results concern limited verification models; they do not establish the cause or reproduce the full historical collapse.*

## Où en est la simulation ?

Instantané du **5 octobre 2026** : **AIRCRAFT-A03 — premier contact de l'avion entier avec une façade représentative**, prochaine étape **AIRCRAFT-A04**. Registre : **122 entrées**. A02 et A03 sont deux itérations d'assemblage/calcul de l'avion complet, avec leurs essais et diagnostics conservés.

Le Boeing paramétrique est maintenant exécuté dans OpenRadioss : 2860 nœuds structuraux + 368 masses/RBE3, 6538 coques triangulaires et 4600 poutres. A02 conserve la translation libre aux facteurs de pas 0,8/0,4 ; **43/49 critères littéraux passent**, avec échecs CG de 1,204527 mm, masse ajoutée apparente et horodatage final. Ces échecs restent visibles, sans correction de masse ajustée.

A03 ajoute une bande de façade de **59 colonnes × 3 étages**, 31792 nœuds et 31986 quadrilatères. Trois calculs nouveaux : contact désactivé et deux contacts avec pas divisé par deux. Tous terminent normalement, sans erreur ni avertissement ; chaque cas sauvegarde 20 états de 35020 nœuds. Le premier contact apparaît vers **0,226 ms** sous les conditions déclarées (-200,5,2)m/s, attitude nulle, **hypothétiques et non attribuées à AA11**. L'impulsion varie de **0,112 %** quand le pas est réduit de moitié.

**La réponse élastique est déjà dépassée vers 0,275 ms** : contraintes de coque jusqu'à 2,47 GPa pour la peau et 2,34 GPa pour l'acier. Ce sont des extrapolations du modèle intact, pas des contraintes physiques après rupture. Le bilan global laisse ~49,6 kJ de résidu : 0,00203 % de l'énergie initiale, mais ~16,6 % des énergies mobilisées par ce court contact. **Bilan local et impact physique non qualifiés.** Le dernier état est vers 0,475 ms et l'histoire vers 0,495 ms ; le critère de fin exacte reste non vérifié. Les premiers faux échecs de connectivité du convertisseur (triangles paddés) et leur audit corrigé sont conservés.

Le nez reste une fermeture aluminium hypothétique, sans radome composite reconstruit. Les moteurs sont des masses/attaches équivalentes sans surfaces de contact. Les dimensions nominales de façade dépendent d'entrées NIST déjà documentées ; **aucun résultat de dégâts NIST n'est une cible**, aucun résultat attendu n'est imposé. Structure interne, sections, assemblages et répartition du vide restent hypothétiques ; 53,187 t du vide ne reçoivent aucune raideur cachée.

![Premier contact, états mécaniques sauvegardés et limites élastiques](wtc1_simulation_v8/output/aircraft_a03/cached_review/A03_premier_contact.png)

Lire les [résultats A02](wtc1_simulation_v8/output/aircraft_a02/rapport_aircraft_a02.md), le [rapport A03](wtc1_simulation_v8/output/aircraft_a03/rapport_aircraft_a03.md), la [vérification d'intégrité A03](wtc1_simulation_v8/output/aircraft_a03/publication_verification.json) et la [passation vers A04](harness/handoffs/WTC1_AIRCRAFT_A03_HANDOFF.md). V11F froid, V11R/V11S, tous les échecs antérieurs et I02I-M différérée sont conservés. Pas d'incendie ni d'effondrement calculé. Tests numériques et dessin ne valident pas l'événement réel.

## Ce qui est publié

- `harness/` : état scientifique, registre des expériences, références, contrôles et passations.
- `wtc1_simulation_v8/scripts/` et `data/` : code des calculs et configurations numériques.
- `wtc1_simulation_v8/output/`, dossiers CalculiX et OpenRadioss : résultats, rapports, bilans et diagnostics, y compris essais rejetés.
- `wtc1_3d_v4/` : scripts de visualisation, paramètres, audits et modèles/rendus dans les archives de résultats.
- `outputs/` : calculs exploratoires antérieurs et audits complémentaires. Leurs affirmations se lisent avec leurs propres limites ; leur présence n'est pas une validation.
- `publication/` : inventaire complet, empreintes SHA-256, règles de publication, licences tierces et liste motivée des fichiers externes non redistribués.

Inventaire courant : **5,569 fichiers scientifiques dans Git**, **7,524 sorties dans 46 archives**.

Restaurer les 45 anciennes archives des releases A à L+A01, puis les 1 archives [A02+A03](https://github.com/WTC-simu2026/WTC-simu2026/releases/tag/snapshot-2026-10-05-aircraft-a02-a03). Manifestes, SHA-256 et URL conservés ; aucune ancienne archive reconstruite ou remplacée.

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

A04 : poursuivre le premier contact de l'avion entier avec une plasticité métallique explicite et des paramètres indépendants, dans un nouveau départ intact à t=0. Traiter la limite du nez/radome, les contraintes de poutres/fibres, le bilan local des énergies/amortissements et l'horodatage final. Conserver A03 et ses limites ; ne pas changer arbitrairement l'historique d'un matériau endommagé. Aucun ajustement vers NIST. Prochaine paire après A04+A05 vérifiées.

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
