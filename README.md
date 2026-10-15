# WTC-simu2026

**Construction progressive d'une simulation exploratoire du WTC 1 : impact d'un Boeing 767, incendies et réponse structurelle, jusqu'à un éventuel effondrement ou son arrêt.**

Le projet teste des mécanismes, des hypothèses explicites et des plages de paramètres. Aucun résultat final n'est présupposé. Il s'agit d'une recherche personnelle reproductible, assistée par Codex, dont les modèles, calculs, essais rejetés et limites sont publiés pour être examinés et améliorés.

*English: an open, incremental WTC 1 research harness. Current results concern limited verification models; they do not establish the cause or reproduce the full historical collapse.*

## Où en est la simulation ?

Instantané du **15 octobre 2026** : **AIRCRAFT-A83 terminée**, prochaine **AIRCRAFT-A84**, registre **202 entrées**. **Les dix secondes physiques et la vidéo3D restent à produire.**

**A82 prépare l’observation du premier refus Newton sans relancer un solveur.** L’examen du chemin source épinglé relie un refus, la restauration du temps/cycle, l’ajustement du pas et l’arrêt lorsque son minimum est atteint. Le message générique A81 ne fournit pas la cause du refus initial. Une carte ajoute uniquement /IMPL/PRINT/NONLIN/-1 ; les dix contrôles de portée passent, tous les blocs préexistants, trois tolérances, chargements, bornes de pas, horizon et binaires restent identiques. Le restart initial propre A81 est copié à l’identique, sans nouveau Starter. L’accord A83 reçu ultérieurement et la publication A80+A81 sont vérifiés avant lancement.

**A83 consomme son unique Engine distinctement autorisé.** UnCPU, plafond180s, zéro Starter, correctif, compilation, GPU, installation ou prolongement d’impact entier. Engine4,774s, code2 sans dépassement. La sortie confirme NPRINT−1, trois tolérances1e−11, minimum/maximum0,000125ms. Les avertissementsPARITH/ON etISOLID0 restent conservés.

**L’impression révèle31lignes non linéaires et des critères non finis.** À l’itération0, déplacement0, force1, énergie0. À1 : déplacement1, force0, énergieInfinity. De2à30 : déplacementNaN, force0, énergieInfinity. Le maximum d’itérations est atteint ; demande de reprise avec nouveau pas, puis MESSAGE79/ISTOP−2. Les chaînes imprimées et numéros de ligne sont conservés dans JSON strict et CSV. Un ratio de force imprimé0 ne prouve pas un résidu brut exactement nul.

**L’observation est partielle et la trajectoire reste échouée.** Les numérateurs/dénominateurs bruts et le temps/cycle tenté ne sont pas imprimés. Le premier temps tenté0,000125ms est une inférence, jamais un état sauvegardé ou une mesure native directe. Aucun diagnostic unique de division par zéro n’est revendiqué à partir des seuls ratios. L’acceptation complète de l’observation reste refusée, même si les nouvelles valeurs identifient les critères à examiner.

**Un seul état TH réel et une animation initiale à0ms existent.** Compression, rupture, refermeture, impulsions de plateau, travail de fracture et peuplementUSR restent non mesurés. Le seul Engine A83 est consommé sans réessai ; A81 et tous les anciens budgets restent consommés. Aucun critère neutralisé, pas abaissé après coup, RKE inventé, temps interpolé ou ajustement aux dégâts connus. Anciennes sorties, échecs et107391avertissements A73 conservés ; aucune archive historique ou vidéo source réanalysée.

**A84 doit examiner les normalisations et références au premier pas imposé en lecture seule.** Préparer une proposition concrète avant une nouvelle exécution ou une modification du moteur. Aucun correctif n’est autorisé par le lot A83.

Les [rapports A82](wtc1_simulation_v8/output/aircraft_a82/rapport_aircraft_a82.md) et [A83](wtc1_simulation_v8/output/aircraft_a83/rapport_aircraft_a83.md) séparent les six catégories de preuve. **Meilleur impact entier0,0200001220703125s.** Publication/CI attestent l’intégrité, pas la validation physique de l’impact réel.


## Ce qui est publié

- `harness/` : état scientifique, registre des expériences, références, contrôles et passations.
- `wtc1_simulation_v8/scripts/` et `data/` : code des calculs et configurations numériques.
- `wtc1_simulation_v8/output/`, dossiers CalculiX et OpenRadioss : résultats, rapports, bilans et diagnostics, y compris essais rejetés.
- `wtc1_3d_v4/` : scripts de visualisation, paramètres, audits et modèles/rendus dans les archives de résultats.
- `outputs/` : calculs exploratoires antérieurs et audits complémentaires. Leurs affirmations se lisent avec leurs propres limites ; leur présence n'est pas une validation.
- `publication/` : inventaire complet, empreintes SHA-256, règles de publication, licences tierces et liste motivée des fichiers externes non redistribués.

Inventaire courant : **19,403 fichiers scientifiques dans Git**, **41,447 sorties dans 146 archives**.

Restaurer les 145 anciennes archives des releases précédentes, puis les 1 archives [A82+A83](https://github.com/WTC-simu2026/WTC-simu2026/releases/tag/snapshot-2026-10-15-aircraft-a82-a83). Manifestes, SHA-256 et URL conservés ; aucune ancienne archive reconstruite ou remplacée.

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

AIRCRAFT-A84 : après publication A82+A83 vérifiée, examiner en lecture seule les normalisations des critères Newton de déplacement et énergie et les références au premier pas imposé. A83 imprime31lignes, itérations0à30 : force normalisée0 dès1, énergie Infinity de1à30, déplacement NaN de2à30, puis maximum d’itérations et limite de pas79/ISTOP−2. Numérateurs/dénominateurs bruts et temps/cycle tenté ne sont pas imprimés ; aucune cause unique encore prouvée. Préparer une proposition concrète avant toute nouvelle exécution ou modification du moteur. Le seul Engine A83 est consommé, zéro Starter ; aucun réessai. Ne pas neutraliser les critères, abaisser silencieusement le minimum ou attribuer une trajectoire à l’état initial. Compression, rupture et refermeture restent non mesurées. Conserver anciennes sorties, budgets, 107391avertissements et critères échoués. Meilleur impact entier0,0200001220703125s ; dix secondes physiques puis vidéo3D incomplètes.


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
