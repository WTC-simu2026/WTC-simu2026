# WTC-simu2026

**Construction progressive d'une simulation exploratoire du WTC 1 : impact d'un Boeing 767, incendies et réponse structurelle, jusqu'à un éventuel effondrement ou son arrêt.**

Le projet teste des mécanismes, des hypothèses explicites et des plages de paramètres. Aucun résultat final n'est présupposé. Il s'agit d'une recherche personnelle reproductible, assistée par Codex, dont les modèles, calculs, essais rejetés et limites sont publiés pour être examinés et améliorés.

*English: an open, incremental WTC 1 research harness. Current results concern limited verification models; they do not establish the cause or reproduce the full historical collapse.*

## Où en est la simulation ?

Instantané du **7 octobre 2026**, mis à jour jusqu’à **AIRCRAFT-A11**. Suite : **AIRCRAFT-A12**. Onze itérations de la branche avion/contact, dont dix comportant l’avion entier ; A10 est un témoin isolé. Cette publication conserve les critères échoués et ne qualifie ni l’impact historique, ni l’écrasement, ni l’effondrement réel.

A10 isole le contact élastique sans RBE3 : le témoin contraint ferme ses bilans à Stfac1 avec réduction du pas, tandis que des contacts plus souples conservent des pertes. Les inerties natives initiales des quads, triangles et poutres reproduisent le RKE global initial, mais les canaux RKE par pièce restent non qualifiés. REAC brut est une impulsion cumulée dans le build testé.

A11 remet la façade représentative devant le nez et active le contact des surfaces extérieures de l’avion couplé, avec les mêmes masses, matériaux et assemblages. Le premier contact du nez apparaît vers **0,225 ms**, avant les ailes et moteurs. Trois pas de temps sont comparés sur **0,4 ms = 0,0004 s** ; le déficit énergétique local persiste malgré des impulsions proches. Ce critère échoué bloque le prolongement déclaré à 1 ms. Les premières secondes, la rupture, la délamination et la traversée historique ne sont pas calculées ou qualifiées.

La vue hors ligne utilise les états natifs, avec déplacement ×1 et temps physique en millisecondes ; elle reste une visualisation. Les données d’entrée représentatives de façade héritent de sources NIST, sans utiliser les dégâts observés ou les sorties NIST comme cibles de réglage. Archives et anciennes itérations restent inchangées. V11F/V11R préservées ; V11S/I02I-M différées.


## Ce qui est publié

- `harness/` : état scientifique, registre des expériences, références, contrôles et passations.
- `wtc1_simulation_v8/scripts/` et `data/` : code des calculs et configurations numériques.
- `wtc1_simulation_v8/output/`, dossiers CalculiX et OpenRadioss : résultats, rapports, bilans et diagnostics, y compris essais rejetés.
- `wtc1_3d_v4/` : scripts de visualisation, paramètres, audits et modèles/rendus dans les archives de résultats.
- `outputs/` : calculs exploratoires antérieurs et audits complémentaires. Leurs affirmations se lisent avec leurs propres limites ; leur présence n'est pas une validation.
- `publication/` : inventaire complet, empreintes SHA-256, règles de publication, licences tierces et liste motivée des fichiers externes non redistribués.

Inventaire courant : **7,254 fichiers scientifiques dans Git**, **9,644 sorties dans 69 archives**.

Restaurer les 64 anciennes archives des releases précédentes, puis les 5 archives [A10+A11](https://github.com/WTC-simu2026/WTC-simu2026/releases/tag/snapshot-2026-10-07-aircraft-a10-a11). Manifestes, SHA-256 et URL conservés ; aucune ancienne archive reconstruite ou remplacée.

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

AIRCRAFT-A12 : isoler le contact du nez/radôme sans redistribution RBE3, vérifier les inerties et le bilan natif LAW25/TYPE19, comparer à un témoin élastique simple et à une formulation de contact déclarée, puis compléter le contrôle spatial. Réutiliser A10/A11 et conserver chaque échec. Ne pas prolonger comme impact qualifié tant que le bilan local ne ferme pas. Examiner le module mécanique Boeing parallèle lorsqu’il est réellement livré, avec un contrôle explicite des masses, assemblages et paramètres hypothétiques.


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
