# WTC-simu2026

**Construction progressive d'une simulation exploratoire du WTC 1 : impact d'un Boeing 767, incendies et réponse structurelle, jusqu'à un éventuel effondrement ou son arrêt.**

Le projet teste des mécanismes, des hypothèses explicites et des plages de paramètres. Aucun résultat final n'est présupposé. Il s'agit d'une recherche personnelle reproductible, assistée par Codex, dont les modèles, calculs, essais rejetés et limites sont publiés pour être examinés et améliorés.

*English: an open, incremental WTC 1 research harness. Current results concern limited verification models; they do not establish the cause or reproduce the full historical collapse.*

## Où en est la simulation ?

Instantané du **14 octobre 2026** : **AIRCRAFT-A73 terminée**, prochaine **AIRCRAFT-A74**, registre **192 entrées**. Objectif dix secondes physiques puis vidéo 3D incomplet.

**A72 : proposition concrète de contexte CHECK explicite.** La garde TT0 ratée A71 est conservée. La source avance TT avant CALL IMP_CHKM ; le correctif propose IMP_CHK>0, en conservant IDYNA2/IQSTAT0/R2exact0 et un diagnostic explicite, et retire l’inclusion COM08 devenue inutile. Quatorze critères de portée passent ; aucun moteur modifié en A72. Cinq lectures scalaires sont préparées, avec offsets typés figés et bornes à vérifier dans le futur binaire. La revue statique ne présume aucune valeur native ni qualification physique.

**A73 : neuvième moteur isolé, autorisé distinctement, appliqué exactement et compilé.** Build en 301.832s sur six CPU, plafond1h, sans GPU ni installation. Les sources/moteurs antérieurs sont conservés ; différence exacte appliquée fuzz0 dans un nouveau workspace puis démontée. Six Engine sur unCPU/plafond180s, zéro Starter, budget entièrement consommé. Le Starter positif propre A71 est réutilisé par empreintes, sans répétition.

**Le contrôle logiciel de la nouvelle garde passe.** Les cinq contextes et R2 sont mesurés directement dans l’enfant, en lecture seule, aux points d’arrêt matériels existants. Aucun scalaire inventé ou instruction/état mécanique modifié. La dynamique libre passe : True, 23 critères aux seuils A67 conservés, TH terminal1.0ms ; aucun crédit entier donné aux témoins. Les anciennes erreurs TT0 A71 et le premier échec d’observation A69 ne sont pas réécrits.

| Contrôle | IDYNA | IQSTAT | IMP_CHK | NCYCLE | TT natif(ms) | R2 |
|---|---:|---:|---:|---:|---:|---:|
| FREE_INITIAL_ZERO_CHECK | 2 | 0 | 1 | 1 | 1.0000625 | 0.0 |
| STATIC_INITIAL_ZERO_CHECK | 0 | 0 | 1 | 1 | 1.0000625 | 0.0 |
| STATIC_POSITIVE_LOAD_CHECK | 0 | 0 | 1 | 1 | 1.0000625 | 4.0 |
| WHOLE_ORIGINAL_CHECK | 2 | 0 | 1 | 1 | 0.001 | 0.0 |
| WHOLE_PAIRED_CHECK | 2 | 0 | 1 | 1 | 0.001 | 0.0 |

**Les scènes entières restent bloquées.** WHOLE_ORIGINAL_CHECK : 0 erreurs/107396 avertissements, 5 TYPE25 ignorés ; WHOLE_PAIRED_CHECK : 0 erreurs/107396 avertissements, 5 TYPE25 ignorés. Les avertissements de préconditionnement et cinq contacts ignorés restent des critères échoués, sans substitution silencieuse ni force ou RKE de compensation. A52nonintégrée, inerties/matériaux/contacts/bilans entiers non qualifiés, aucun prolongement dynamique entier. Toutes les sorties, tentatives ratées, versions, budgets et archives sont conservés. Le prochain audit en lecture seule doit utiliser les résultats A73 et les audits existants ; toute nouvelle modification/compilation ou lot natif nécessite une proposition concrète et un accord distinct.

Les [rapports A72](wtc1_simulation_v8/output/aircraft_a72/rapport_aircraft_a72.md) et [A73](wtc1_simulation_v8/output/aircraft_a73/rapport_aircraft_a73.md) séparent les six catégories de preuve. **Meilleur impact entier : 0,0200001220703125 s.** Dix secondes et vidéo 3D ne sont pas produites ; aucune extrapolation visuelle fabriquée ni ajustement à des dégâts connus. Publication et CI attestent l’intégrité, pas la physique de l’impact réel.


## Ce qui est publié

- `harness/` : état scientifique, registre des expériences, références, contrôles et passations.
- `wtc1_simulation_v8/scripts/` et `data/` : code des calculs et configurations numériques.
- `wtc1_simulation_v8/output/`, dossiers CalculiX et OpenRadioss : résultats, rapports, bilans et diagnostics, y compris essais rejetés.
- `wtc1_3d_v4/` : scripts de visualisation, paramètres, audits et modèles/rendus dans les archives de résultats.
- `outputs/` : calculs exploratoires antérieurs et audits complémentaires. Leurs affirmations se lisent avec leurs propres limites ; leur présence n'est pas une validation.
- `publication/` : inventaire complet, empreintes SHA-256, règles de publication, licences tierces et liste motivée des fichiers externes non redistribués.

Inventaire courant : **19,038 fichiers scientifiques dans Git**, **41,423 sorties dans 141 archives**.

Restaurer les 140 anciennes archives des releases précédentes, puis les 1 archives [A72+A73](https://github.com/WTC-simu2026/WTC-simu2026/releases/tag/snapshot-2026-10-14-aircraft-a72-a73). Manifestes, SHA-256 et URL conservés ; aucune ancienne archive reconstruite ou remplacée.

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

AIRCRAFT-A74 : préparer en lecture seule la prochaine étape à partir des résultats natifs A73, après publication A72+A73 vérifiée. Utiliser les cinq paramètres natifs, R2 et les avertissements effectivement mesurés ; conserver A71 gardeTT0 échouée, anciennes sorties, contacts/budgets et tous les critères physiques échoués. Si la garde CHECK passe, traiter le contrat des cinq TYPE25 ignorés et des avertissements de préconditionnement avant toute intégration/prolongation entière ; réutiliser les audits existants, aucune substitution silencieuse. A73 neuf moteurs isolés au total, six Engine/zéro Starter autorisés entièrement consommés. Toute nouvelle modification de logiciel/compilation ou lot natif requiert une proposition concrète et un accord distinct. Pas de GPU, installation, RKE de compensation, calibrage aux dégâts connus ni crédit de témoins. Meilleur impact entier0,0200001220703125s ; objectif dix secondes physiques puis vidéo3D incomplet.

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
