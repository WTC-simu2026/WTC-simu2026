# WTC-simu2026

**Construction progressive d'une simulation exploratoire du WTC 1 : impact d'un Boeing 767, incendies et réponse structurelle, jusqu'à un éventuel effondrement ou son arrêt.**

Le projet teste des mécanismes, des hypothèses explicites et des plages de paramètres. Aucun résultat final n'est présupposé. Il s'agit d'une recherche personnelle reproductible, assistée par Codex, dont les modèles, calculs, essais rejetés et limites sont publiés pour être examinés et améliorés.

*English: an open, incremental WTC 1 research harness. Current results concern limited verification models; they do not establish the cause or reproduce the full historical collapse.*

## Où en est la simulation ?

Instantané du **11 octobre 2026** : **AIRCRAFT-A37 terminée**, prochaine étape **AIRCRAFT-A38**. Le registre compte **156 entrées**. A36+A37 ajoutent **19 témoins natifs terminés**, dont **12 ensembles individuels réussis et sept échoués**, avec leurs configurations, scripts et limites conservés.

A36 teste le raffinement indépendant et natif ainsi qu’un budget de réactions implicites tiré des sources figées du moteur. Le résidu TH et l’inertie physique des nœuds imposés expliquent séparément impulsion et travail dans les témoins élastiques, sans facteur empirique, ajout de masse ou RKE inventé. Les onze bilans et33champs passent; les critères de raffinement indépendant N8→N16 et natif N4→N8 échouent. Une première translation garde un écart de quantité de mouvement globale, puis deux nouvelles translations plus observables passent les budgets. Les échecs initiaux restent conservés.

A37 teste de vraies reprises complètes entre phases du même moteur Linux : mouvement libre et collision élastique fermée. Huit témoins,14phases dynamiques et trois observateurs d’un cycle terminent. Les empreintes des reprises, les six jonctions au même instant et les champs natifs contrôlés passent. Les deux contrôles explicites passent. Les six voies implicites échouent : vitesse libre finale opposée et triple, énergie cinétique neuf fois initiale; la collision active échoue au bilan énergétique et au demi-pas. Le départ implicite direct échoue aussi. La continuité d’un fichier de reprise ne valide donc pas la dynamique qui suit. Les huit premières préparations de contact échouées et les diagnostics d’observation initiaux sont conservés.

Le contrôle implicite du modèle avion–façade entier, aux cartes physiques A20 inchangées, avorte avant son compte rendu. Sa cause n’est pas identifiée. La documentation liste les contacts implicites TYPE5/7/10/11; les cinq TYPE25 du modèle entier ne figurent pas dans cette liste. Ce fait documentaire ne suffit pas à attribuer l’avortement au TYPE25. Aucun remplacement silencieux ni nouvelle dynamique entière.

Les [rapports A36](wtc1_simulation_v8/output/aircraft_a36/rapport_aircraft_a36.md) et [A37](wtc1_simulation_v8/output/aircraft_a37/rapport_aircraft_a37.md) séparent faits, références, archives, hypothèses, résultats dérivés et lacunes. La compilation séparée A35, terminée en39,29min sous l’heure autorisée, n’est pas prolongée; le préparateur Linux reste incomplet. Binaires, bibliothèques et sources tierces ne sont pas redistribués. Aucun changement des budgets de masse/inertie ou de matériaux de l’avion, aucune densité compensatrice et aucun dommage connu comme cible.

La vidéo3D des **dix premières secondes physiques** reste incomplète : meilleur impact entier A20 = **20millisecondes physiques**. Aucun temps de contrôle ou d’observateur n’est crédité à l’impact entier; aucun prolongement balistique inventé. La publication vérifie l’intégrité des fichiers, sans validation physique ou historique de l’impact ou de l’effondrement.


## Ce qui est publié

- `harness/` : état scientifique, registre des expériences, références, contrôles et passations.
- `wtc1_simulation_v8/scripts/` et `data/` : code des calculs et configurations numériques.
- `wtc1_simulation_v8/output/`, dossiers CalculiX et OpenRadioss : résultats, rapports, bilans et diagnostics, y compris essais rejetés.
- `wtc1_3d_v4/` : scripts de visualisation, paramètres, audits et modèles/rendus dans les archives de résultats.
- `outputs/` : calculs exploratoires antérieurs et audits complémentaires. Leurs affirmations se lisent avec leurs propres limites ; leur présence n'est pas une validation.
- `publication/` : inventaire complet, empreintes SHA-256, règles de publication, licences tierces et liste motivée des fichiers externes non redistribués.

Inventaire courant : **14,875 fichiers scientifiques dans Git**, **21,833 sorties dans 119 archives**.

Restaurer les 118 anciennes archives des releases précédentes, puis les 1 archives [A36+A37](https://github.com/WTC-simu2026/WTC-simu2026/releases/tag/snapshot-2026-10-11-aircraft-a36-a37). Manifestes, SHA-256 et URL conservés ; aucune ancienne archive reconstruite ou remplacée.

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

AIRCRAFT-A38 : reprendre les états et diagnostics A37, sans répéter les campagnes. La copie complète des reprises natives et les champs à la jonction passent dans les témoins libres et en contact; les deux contrôles explicites passent. Les six voies implicites échouent aux budgets : vitesse libre finale -3 fois la vitesse initiale et KE9 fois initiale, contact actif hors énergie et demi-pas. Départ implicite direct échoue aussi; ne pas attribuer ces effets au seul fichier de reprise. Tester une cause d’initialisation à la fois, dont AUTOSPC par défaut et l’initialisation Newmark, avec le même moteur figé, mêmes masses/matériaux/velocités et référence libre exacte. Arrêter une branche si les budgets échouent. Le contrôle entier /IMPL/CHECK a avorté avant son compte rendu; cause non identifiée. Les cinq contacts TYPE25 ne figurent pas parmi les contacts implicites documentés; ne pas les remplacer silencieusement. Aucun coût entier ni dix secondes ne doit être projeté depuis ces cubes. A34 mécanique des peaux et raffinement A36 restent échoués séparément. Compilation A35 terminée; aucune nouvelle installation/compilation engagée. Préserver tous les échecs. Meilleur impact entier A20=20ms; objectif dix secondes physiques 3D puis vidéo/GIF toujours incomplet. A36+A37 prêtes pour publication autorisée après leur intégrité.

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
