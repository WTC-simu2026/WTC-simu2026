# WTC-simu2026

**Construction progressive d'une simulation exploratoire du WTC 1 : impact d'un Boeing 767, incendies et réponse structurelle, jusqu'à un éventuel effondrement ou son arrêt.**

Le projet teste des mécanismes, des hypothèses explicites et des plages de paramètres. Aucun résultat final n'est présupposé. Il s'agit d'une recherche personnelle reproductible, assistée par Codex, dont les modèles, calculs, essais rejetés et limites sont publiés pour être examinés et améliorés.

*English: an open, incremental WTC 1 research harness. Current results concern limited verification models; they do not establish the cause or reproduce the full historical collapse.*

## Où en est la simulation ?

Instantané du **5 octobre 2026** : **AIRCRAFT-A01 terminée comme premier assemblage paramétrique de l'avion entier**, prochaine étape **AIRCRAFT-A02**. Registre : **120 entrées**. Avant cette étape :119,dont22 dans la branche impact; les12 dernières I02I-A à L étaient des diagnostics locaux.

La priorité a été recentrée sur l'avion complet et les conditions d'entrée, sans ajuster le modèle pour rejoindre NIST. A01 assemble fuselage,deux ailes/caisson central,longerons,nervures,raidisseurs,empennages et deux moteurs/pylônes équivalents; les dimensions externes viennent des plans primaires Boeing. Les sources Boeing restent en lecture seule et ne sont pas redistribuées comme logiciel libre. La structure interne,les épaisseurs et les masses détaillées sont encore hypothétiques.

Neuf scénarios de carburant,charge,épaisseur et répartition du vide :**66/66** contrôles de construction,**4/4** contrôles des masses exportées,**6/6** contrôles de géométrie/conversion. La première sortie r0 conserve neuf échecs de symétrie : le découpage a été corrigé en miroir, sans modifier les seuils. Toutes les versions sont conservées. Nominal :122,159t,dont19,972t de structure explicite,9t de moteurs équivalents et53,187t de vide non résolu,plus30t carburant et10t de charge. La réserve non résolue représente64,7% du vide et ne reçoit aucune raideur cachée. Ni masse niCG historiques ne sont établis. Aucun impact calculé en A01.

![Avion entier - géométrie et masses hypothétiques](wtc1_simulation_v8/output/aircraft_a01/verification_r2/preview_corrected/B767_assemblage_A01.png)

Lire le [rapport A01](wtc1_simulation_v8/output/aircraft_a01/rapport_aircraft_a01.md), le [modèle 3D GLB](wtc1_simulation_v8/output/aircraft_a01/verification_r2/B767_airframe_A01.glb), la [vérification](wtc1_simulation_v8/output/aircraft_a01/publication_verification.json) et la [passation A02](harness/handoffs/WTC1_AIRCRAFT_A01_HANDOFF.md). L conserve les cinq échecs OFF/FX, les réserves et les diagnostics I/J : son bilan numérique conditionnel n'identifie pas une fracture physique. Le [rapport L](wtc1_simulation_v8/output/impact_i02i_deletion_ledger/rapport_impact_i02i_deletion_ledger.md) est aussi publié. I02I-M est différée par ce recentrage, son plan conservé. V11F/V11R/V11S et toutes les limites antérieures restent ouvertes.

**Aucun résultat NIST ne sert de cible dans le nouveau constructeur.** Les comparaisons de dommages auront lieu après gel des conditions; un écart restera visible. Maillage intact élastique et masses vérifiés pour ces hypothèses seulement; transfert au solveur,vol libre,résistance d'impact et rupture encore à vérifier. Aucun incendie ou effondrement historique validé.

## Ce qui est publié

- `harness/` : état scientifique, registre des expériences, références, contrôles et passations.
- `wtc1_simulation_v8/scripts/` et `data/` : code des calculs et configurations numériques.
- `wtc1_simulation_v8/output/`, dossiers CalculiX et OpenRadioss : résultats, rapports, bilans et diagnostics, y compris essais rejetés.
- `wtc1_3d_v4/` : scripts de visualisation, paramètres, audits et modèles/rendus dans les archives de résultats.
- `outputs/` : calculs exploratoires antérieurs et audits complémentaires. Leurs affirmations se lisent avec leurs propres limites ; leur présence n'est pas une validation.
- `publication/` : inventaire complet, empreintes SHA-256, règles de publication, licences tierces et liste motivée des fichiers externes non redistribués.

Inventaire courant : **5,430 fichiers scientifiques dans Git**, **7,413 sorties dans 45 archives**.

Restaurer les44 anciennes archives des releases A à J+K, puis les 1 archives [L+A01](https://github.com/WTC-simu2026/WTC-simu2026/releases/tag/snapshot-2026-10-05-aircraft-a01). Manifestes,SHA-256 et URL conservés; aucune ancienne archive reconstruite ou remplacée.

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

AIRCRAFT-A02 : transfert cohérent des masses et inerties au solveur et vol libre intact court; préciser les données de structure/moteur qui dominent les inconnues. Puis impact limité de l'avion entier sur façade représentative, avec vitesse/attitude et sensibilités déclarées avant comparaison des dégâts. Aucune adaptation pour faire coïncider les résultats NIST. I02I-M est différée et ne sera reprise automatiquement qu'en présence d'un blocage concret de sa loi. La priorité reste l'assemblage complet.

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
