# WTC-simu2026

**Construction progressive d'une simulation exploratoire du WTC 1 : impact d'un Boeing 767, incendies et réponse structurelle, jusqu'à un éventuel effondrement ou son arrêt.**

Le projet teste des mécanismes, des hypothèses explicites et des plages de paramètres. Aucun résultat final n'est présupposé. Il s'agit d'une recherche personnelle reproductible, assistée par Codex, dont les modèles, calculs, essais rejetés et limites sont publiés pour être examinés et améliorés.

*English: an open, incremental WTC 1 research harness. Current results concern limited verification models; they do not establish the cause or reproduce the full historical collapse.*

## Où en est la simulation ?

Instantané du **5 octobre 2026** : **AIRCRAFT-A05 — nez arrondi et sandwich composite de référence dans l’avion entier**, prochaine étape **AIRCRAFT-A06**. Registre : **124 entrées historiques**, dont **cinq itérations de l’avion entier A01–A05**. Ce compteur ne mesure pas la fidélité physique.

**A04 ajoute la plasticité métallique.** Le premier travail plastique apparaît vers 0,2401 ms. Quatre variantes sans écrouissage sont arrêtées après300 s vers1,63 ms : la fermeture plate hypothétique du nez devient dégénérée. Une variante H=0,02E atteint2 ms mais ses grandes déformations restent non qualifiées ; elle n’est pas choisie simplement parce qu’elle termine. Les essais arrêtés, les premières interprétations et les corrections d’audit sont conservés.

**A05 remplace ce nez par une surface arrondie et un sandwich élastique explicite.** Neuf départs intacts : contrôle libre, forme métallique seule, composite avec/sans autocontact, demi-pas, gap selon épaisseur, deux épaisseurs de face et maillage affiné. Tous les cas retenus ont Starter sans erreur/avertissement et Engine normal : huit contacts atteignent2 ms, contrôle libre0,6 ms. Les masses sont recalculées sans compensation ; les sources Hexcel et Boeing ne sont pas une reconstruction de la fabrication du radôme767.

**Les limites restent visibles.** La réduction du pas donne0,39547 % d’écart d’impulsion et0,15931 % d’énergie générée, dans les seuils annoncés. Le maillage affiné, à géométrie et masse identiques, donne14,34646 %/43,25002 % : convergence spatiale en échec. La référence de résistance du sandwich nominal est dépassée dès l’état0,60045 ms. Tous les contacts échouent le bilan énergétique local ; nominal : résidu−78,642 kJ pour283,168 kJ générés, ~27,77 %. L’autocontact est présent mais inactif sur cette fenêtre, donc non validé après pliage. Rupture, écrasement de l’âme et délaminage restent absents. Une nouvelle observation des listings révèle de l’amortissement numérique métallique natif malgré des zéros d’entrée ; son effet sur le bilan reste à mesurer.

![Avion entier et comparaison mécanique des deux maillages de nez](wtc1_simulation_v8/output/aircraft_a05/cached_review/summary_aircraft_a05.png)

Conditions de test propres au modèle : v=(-200,5,2)m/s, attitude nulle, façade représentative59 colonnes×3 étages. Ailes et moteurs n’ont pas encore atteint la façade ; les moteurs restent des masses/attaches sans surfaces de contact. Dimensions nominales de façade héritées de sources NIST, dépendance déclarée ; **aucune sortie de dégâts NIST n’est une cible et aucun résultat attendu n’est imposé**. Incendie et effondrement non calculés. V11F froid, V11R/V11S différée, A02/A03 et leurs échecs sont conservés. Blender et les tests numériques ne valident pas l’événement réel.

Lire le [rapport A04](wtc1_simulation_v8/output/aircraft_a04/rapport_aircraft_a04.md), le [rapport A05](wtc1_simulation_v8/output/aircraft_a05/rapport_aircraft_a05.md), la [relecture autoritative A05](wtc1_simulation_v8/output/aircraft_a05/cached_review/review.json), la [vérification d’intégrité](wtc1_simulation_v8/output/aircraft_a05/publication_verification.json) et la [passation vers A06](harness/handoffs/WTC1_AIRCRAFT_A05_HANDOFF.md). La publication conserve les sorties, reprises, binaires, scripts, configurations, tentatives et critères échoués ; elle ne relance aucun solveur ancien.


## Ce qui est publié

- `harness/` : état scientifique, registre des expériences, références, contrôles et passations.
- `wtc1_simulation_v8/scripts/` et `data/` : code des calculs et configurations numériques.
- `wtc1_simulation_v8/output/`, dossiers CalculiX et OpenRadioss : résultats, rapports, bilans et diagnostics, y compris essais rejetés.
- `wtc1_3d_v4/` : scripts de visualisation, paramètres, audits et modèles/rendus dans les archives de résultats.
- `outputs/` : calculs exploratoires antérieurs et audits complémentaires. Leurs affirmations se lisent avec leurs propres limites ; leur présence n'est pas une validation.
- `publication/` : inventaire complet, empreintes SHA-256, règles de publication, licences tierces et liste motivée des fichiers externes non redistribués.

Inventaire courant : **6,084 fichiers scientifiques dans Git**, **7,976 sorties dans 53 archives**.

Restaurer les 46 anciennes archives des releases précédentes, puis les 7 archives [A04+A05](https://github.com/WTC-simu2026/WTC-simu2026/releases/tag/snapshot-2026-10-05-aircraft-a04-a05). Manifestes, SHA-256 et URL conservés ; aucune ancienne archive reconstruite ou remplacée.

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

**A06 : traiter le radôme au-delà de sa limite élastique**, avec endommagement/rupture et énergie explicites issus de références indépendantes ou de plages annoncées. Vérifier un mécanisme simple avant son transfert dans un nouveau départ intact de l’avion entier ; examiner aussi la sensibilité spatiale/contact et l’amortissement natif métallique. Ne pas ajuster résistances, énergie, maillage ou érosion à un résultat NIST. Les moteurs géométriques et leur contact restent un domaine manquant. Préserver V11F et la branche thermique différée. Prochaine mise à jour après deux nouvelles itérations vérifiées, A06+A07 si la route locale reste inchangée.


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
