# WTC-simu2026

**Construction progressive d'une simulation exploratoire du WTC 1 : impact d'un Boeing 767, incendies et réponse structurelle, jusqu'à un éventuel effondrement ou son arrêt.**

Le projet teste des mécanismes, des hypothèses explicites et des plages de paramètres. Aucun résultat final n'est présupposé. Il s'agit d'une recherche personnelle reproductible, assistée par Codex, dont les modèles, calculs, essais rejetés et limites sont publiés pour être examinés et améliorés.

*English: an open, incremental WTC 1 research harness. Current results concern limited verification models; they do not establish the cause or reproduce the full historical collapse.*

## Où en est la simulation ?

Instantané du **11 octobre 2026** : **AIRCRAFT-A39 terminée**, prochaine étape **AIRCRAFT-A40**. Le registre compte **158 entrées**. A38+A39 ajoutent **dix témoins natifs déclarés**, dont **sept dynamiques terminées**, **une branche arrêtée sur critère échoué** et **deux moteurs Windows indisponibles avant avance**. Aucun ensemble complet ne qualifie le démarrage implicite. Configurations, limites et échecs sont conservés.

A38 change séparément les contraintes automatiques, le solveur linéaire, l’intégrateur puis le critère de convergence. Le défaut libre reste présent dans les voies ordinaires : vitesse finale opposée et triple, KE neuf fois initiale. Dix fichiers de reprise conservent le compteur des27vitesses initiales ; cela ne démontre pas une compatibilité binaire générale. La source figée révèle un retour sur petit résidu absolu avant les critères choisis. Une tolérance plus stricte engage la résolution initiale, puis le journal annonce−75% d’énergie et le calcul est arrêté. Ses douze animations partielles gardent toutefois les vitesses nodales initiales, avec un décalage de déplacement d’environ0,000293mm, hors du seuil0,00002mm.

A39 précise cette contradiction par une **nouvelle lecture du fichier d’historique partiel A38**, copié sans modifier l’original ni relancer un solveur : aux douze instants enregistrés, **KE nodale et KE globale du fichier concordent à0,05564031J**, le **bilan énergétique complet passe**, momentum, masse, absence d’ADMAS et travail externe passent. Le−75% du journal n’est donc pas assimilé à une perte physique ou une KE enregistrée fausse. Son origine reste inconnue. Le déplacement et la terminaison complète restent échoués/absents ; aucun décalage artificiel de temps ou facteur empirique ne corrige ces sorties.

Les deux contrôles PCG avec un préparateur et un moteur Windows cohérents s’arrêtent avec **MUMPSrequired àt0**, limitation déjà connue sur les anciennes sondes implicites et confirmée ici pour le cube libre. Ils ne permettent aucune comparaison de dynamique Windows–Linux. Leur journal affiche2processus HMPP malgré1déclaré : écart conservé, aucune avance physique. Il faudra vérifier explicitement le nombre de threads pour un prochain calcul Windows.

Les [rapports A38](wtc1_simulation_v8/output/aircraft_a38/rapport_aircraft_a38.md) et [A39](wtc1_simulation_v8/output/aircraft_a39/rapport_aircraft_a39.md) séparent faits, sources, archives, hypothèses, résultats et lacunes. La prochaine expérience raffinera le **premier pas** puis testera sa **croissance adaptative**, à critères physiques et entrées inchangés. Transition/contact et demi-pas restent requis après une voie libre complète réussie. Peaux A34, raffinement A36 et compatibilité implicite entière ne sont pas qualifiés. La compilation A35 reste terminée39,29min ; préparateur Linux incomplet, aucune nouvelle compilation/installation. Binaires et sources tierces exclus de cette publication.

La vidéo3D des **dix premières secondes physiques** reste incomplète : meilleur impact entier A20 = **20millisecondes physiques**. Aucun cube, temps de contrôle ou aperçu ralenti n’est crédité à l’impact entier. Aucune modification de masse, densité compensatrice, matériau, inertie, état initial ou résultat historique utilisé comme cible. L’intégrité de publication ne constitue pas une validation physique ou historique de l’impact ou de l’effondrement.


## Ce qui est publié

- `harness/` : état scientifique, registre des expériences, références, contrôles et passations.
- `wtc1_simulation_v8/scripts/` et `data/` : code des calculs et configurations numériques.
- `wtc1_simulation_v8/output/`, dossiers CalculiX et OpenRadioss : résultats, rapports, bilans et diagnostics, y compris essais rejetés.
- `wtc1_3d_v4/` : scripts de visualisation, paramètres, audits et modèles/rendus dans les archives de résultats.
- `outputs/` : calculs exploratoires antérieurs et audits complémentaires. Leurs affirmations se lisent avec leurs propres limites ; leur présence n'est pas une validation.
- `publication/` : inventaire complet, empreintes SHA-256, règles de publication, licences tierces et liste motivée des fichiers externes non redistribués.

Inventaire courant : **15,126 fichiers scientifiques dans Git**, **21,995 sorties dans 120 archives**.

Restaurer les 119 anciennes archives des releases précédentes, puis les 1 archives [A38+A39](https://github.com/WTC-simu2026/WTC-simu2026/releases/tag/snapshot-2026-10-11-aircraft-a38-a39). Manifestes, SHA-256 et URL conservés ; aucune ancienne archive reconstruite ou remplacée.

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

AIRCRAFT-A40 : reprendre les douze historiques partiels Linux stricts A38 relus en A39 sans répétition. Vitesse, KE nodale et globale, bilan énergétique complet, momentum physique/global, masse et travail passent aux instants enregistrés; seul le déplacement garde environ0,000293mm de décalage et la terminaison complète manque. Le -75% est une ligne de journal, pas la KE globale du fichier TH; sa cause d’affichage reste inconnue. Déclarer un raffinement du tout premier pas, avec tolérances1e-11 et croissance adaptative vers le pas maximal initial, selon /IMPL/DTINI et /IMPL/DT/1. Garder les seuils physiques, masses, matériaux, vitesses et état initial; ne pas appliquer un décalage artificiel de temps/position ou facteur de KE. Tester le mouvement libre exact jusqu’au terme puis au demi-pas; seulement après succès, déclarer transition complète et contact actif. Aucun calcul entier ni coût10s extrapolé depuis ce cube. Le contrôle Windows PCG est indisponible : MUMPS requis avant avance, limitation connue A33 confirmée en A39. Ses départs affichent2HMPP malgré1déclaré; vérifier explicitement -nt1 avant tout nouveau calcul Windows. Compilation A35 terminée39,29min, aucune nouvelle compilation ou installation. Peaux A34, raffinement A36 et compatibilité implicite entière restent échoués/incomplets. Meilleur impact entier A20=20ms, objectif10s physiques 3D puis vidéo/GIF incomplet. Publier A38+A39 maintenant après vérification, selon autorisation et cadence.

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
