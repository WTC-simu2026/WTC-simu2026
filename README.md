# WTC-simu2026

**Construction progressive d'une simulation exploratoire du WTC 1 : impact d'un Boeing 767, incendies et réponse structurelle, jusqu'à un éventuel effondrement ou son arrêt.**

Le projet teste des mécanismes, des hypothèses explicites et des plages de paramètres. Aucun résultat final n'est présupposé. Il s'agit d'une recherche personnelle reproductible, assistée par Codex, dont les modèles, calculs, essais rejetés et limites sont publiés pour être examinés et améliorés.

*English: an open, incremental WTC 1 research harness. Current results concern limited verification models; they do not establish the cause or reproduce the full historical collapse.*

## Où en est la simulation ?

Instantané du **14 octobre 2026** : **AIRCRAFT-A77 terminée**, prochaine **AIRCRAFT-A78**, registre **196 entrées**. Objectif dix secondes physiques puis vidéo3D incomplet.

**A76 : audit en lecture seule et proposition exacte de filtrage local.** Les nouvelles sorties A75 sont réutilisées sans solveur rejoué. Dix fichiers de sources Starter en cache expliquent la distinction entre1000 imprimé et0 opérationnel, le message614 d’IBAG et l’ordre des lignes précédant612. L’identité de ces sources avec le binaire Windows n’est pas supposée. Les916lignes de coordonnées impossibles précèdent les916messages et portent le même numéro ; l’ancienne association suivante du lecteur A75 est conservée. La table d’impacts séparée est lue :23520possibles pour2,0 pour101–104. Le lecteur propre corrigé continue de rejeter les vraies erreurs et avertissements.

**Deux variantes concrètes sont proposées puis autorisées distinctement.** Exactement six champs par modèle : IBAG2→0 sur cinq TYPE7, Irem_gap1→2 uniquement sur l’auto-contact2. Vingt-deux critères de portée passent ; coordonnées, masse/matière/inertie, groupes/surfaces, TH, gaps0,5/5mm et tous les autres paramètres restent identiques, hors noms de cas. Aucune désactivation globale ou Inacti1/2/3/5/6. Le filtre est une hypothèse non qualifiée et ne présume aucune équivalence dynamique TYPE25/TYPE7. Préparation source R0 au chemin de helper absent conservée ; R1 réutilise les trois copies correctes et lit le quatrième au vrai chemin.

**A77 : IBAG est corrigé, le filtre local reste inefficace.** Les deux nouveaux Starter CPU1/plafond180s échouent avec916erreurs612 et1avertissement343 chacun, sans dépassement. Les dix614 ont disparu. Le nouveau Irem_gap2 est réellement imprimé, mais la séquence des916numéros de nœuds reste identique àA75 ;23520candidats et4430pénétrations initiales concernant1968nœuds de l’auto-contact2 restent. Les paramètres des cinq TYPE7 et les tables sont lus, sans état initial valide produit. Masse191273837,9425g et ADMAS100368522,1367g conservées ; aucun tenseur redistribué ou inertie native inférés.

**Les deux EngineCHECK conditionnels sont omis.** Deux Starter autorisés entièrement consommés, zéro Engine ; deux places CHECK conditionnellement inutilisées non réaffectées. Moteur A73 inchangé, aucun correctif/compilation/GPU/installation, aucun impact entier prolongé. Le pilote R0 non exécuté est conservé ; R1 corrige deux noms d’artefacts avant déclaration, sans changer les entrées ou budgets.

**La prochaine étape est géométrique.** A78 doit cartographier les numéros imprimés vers les faces/connexions et préparer une mesure des paires initiales si elles manquent. Ne pas rejouer les anciens diagnostics, désactiver le contact, réduire le gap ou déplacer des nœuds pour forcer un passage. Anciennes TYPE25 ignorées,107391 avertissements de préconditionnement A73, gardeTT0 ratéeA71, Irem_gap2 ratéA77, sorties et budgets restent conservés. Toute nouvelle exécution ou modification logicielle demande une proposition concrète et accord distinct.

Les [rapports A76](wtc1_simulation_v8/output/aircraft_a76/rapport_aircraft_a76.md) et [A77](wtc1_simulation_v8/output/aircraft_a77/rapport_aircraft_a77.md) séparent les six catégories de preuve. **Meilleur impact entier :0,0200001220703125s.** Dix secondes et vidéo3D incomplètes, aucun temps manquant extrapolé ni ajustement aux dégâts connus. Publication et CI attestent l’intégrité, pas la physique de l’impact réel.


## Ce qui est publié

- `harness/` : état scientifique, registre des expériences, références, contrôles et passations.
- `wtc1_simulation_v8/scripts/` et `data/` : code des calculs et configurations numériques.
- `wtc1_simulation_v8/output/`, dossiers CalculiX et OpenRadioss : résultats, rapports, bilans et diagnostics, y compris essais rejetés.
- `wtc1_3d_v4/` : scripts de visualisation, paramètres, audits et modèles/rendus dans les archives de résultats.
- `outputs/` : calculs exploratoires antérieurs et audits complémentaires. Leurs affirmations se lisent avec leurs propres limites ; leur présence n'est pas une validation.
- `publication/` : inventaire complet, empreintes SHA-256, règles de publication, licences tierces et liste motivée des fichiers externes non redistribués.

Inventaire courant : **19,194 fichiers scientifiques dans Git**, **41,433 sorties dans 143 archives**.

Restaurer les 142 anciennes archives des releases précédentes, puis les 1 archives [A76+A77](https://github.com/WTC-simu2026/WTC-simu2026/releases/tag/snapshot-2026-10-14-aircraft-a76-a77). Manifestes, SHA-256 et URL conservés ; aucune ancienne archive reconstruite ou remplacée.

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

AIRCRAFT-A78 : audit géométrique/topologique en lecture seule des contacts initiaux A77, après publication A76+A77 vérifiée. IBAG0 supprime les dix614, mais Irem_gap2 natif confirmé ne résout aucune des916erreurs612 de l’auto-contact2 ;23520candidats et4430pénétrations initiales restent. Deux Starter autorisés consommés, zéro Engine ; deux CHECK conditionnellement inutilisés non réaffectés. Cartographier les numéros effectivement imprimés vers les faces/connexions du modèle et préparer une mesure de paires initiales si elles manquent, sans rejouer les anciens diagnostics. Ne pas désactiver globalement le contact, réduire le gap ou déplacer les nœuds pour forcer un passage. Moteur A73 inchangé ; tout nouveau lot natif/correctif/compilation nécessite une proposition et accord distinct. Préserver A75, Irem_gap2 raté, anciennes sorties, budgets et critères échoués. Les107391 avertissements et budgets physiques entiers restent bloquants. Meilleur impact entier0,0200001220703125s ; dix secondes physiques puis vidéo3D incomplètes.

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
