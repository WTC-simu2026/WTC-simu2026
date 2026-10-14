# WTC-simu2026

**Construction progressive d'une simulation exploratoire du WTC 1 : impact d'un Boeing 767, incendies et réponse structurelle, jusqu'à un éventuel effondrement ou son arrêt.**

Le projet teste des mécanismes, des hypothèses explicites et des plages de paramètres. Aucun résultat final n'est présupposé. Il s'agit d'une recherche personnelle reproductible, assistée par Codex, dont les modèles, calculs, essais rejetés et limites sont publiés pour être examinés et améliorés.

*English: an open, incremental WTC 1 research harness. Current results concern limited verification models; they do not establish the cause or reproduce the full historical collapse.*

## Où en est la simulation ?

Instantané du **14 octobre 2026** : **AIRCRAFT-A67 terminée**, prochaine **AIRCRAFT-A68**, registre **186 entrées**. L’objectif dix secondes physiques puis vidéo 3D reste incomplet.

**A66 : audit et proposition exacte d’aire courante.** Les 624 surfaces entières TYPE43/LAW117 emploient Ismstr4 ; la branche A62 traite Ismstr1 avec une aire de référence VOL. Ismstr4 utilise les aires courantes. Géométrie et prototype propres vérifiés : 52 contrôles passent, sans nouveau calcul natif. Branche Ismstr1 préservée exactement, tentatives de préparation échouées conservées.

**A67 : correctif A66 appliqué après accord humain distinct et compilé dans le septième moteur isolé.** Première compilation en 291,077 s, six CPU, plafond une heure, sans GPU ni installation ; Starter inchangé. Les huit Engine autorisés sur un CPU/plafond 180 s sont exécutés, aucun contrôle restant. **Six témoins locaux, 137 critères et deux comparaisons demi-pas passent**, plus le travail complet aux quatre points de quadrature, analysé sans recalcul natif. Cinq variantes à translations supérieures libres qualifient leurs bilans dans le domaine élastique déclaré ; le témoin d’aire évolutive 100→110 mm² qualifie seulement Y libre, X étant prescrit. La comparaison temporelle conserve le seuil 1,01e-5 J : KE 5,47014241452e-6 J, IE 5,49140000000e-6 J. Les TH atteignent réellement 1 ms ; aucun temps de témoin crédité à l’impact entier.

**Les deux CHECK entiers échouent encore.** Les 624 STOP de volume observés en A65 ne sont plus présents, sans géométrie/épaisseur fictive. Chaque scène affiche une erreur de chargement implicite et 107396 avertissements : 107391 directions de connexion possible (107166 rotations et 225 translations), plus cinq TYPE25 ignorés. NORMAL/code0 n’est pas un passage. Les compteurs ne prouvent pas encore une déconnexion géométrique, et la valeur R2 du chargement n’est pas imprimée. Les cartes contiennent déjà /IMPL/DYNA/2. Anciennes cartes/initialisations vérifiées identiques ; A52 non intégrée, aucun impact entier prolongé.

**A68 : audit de sources et des rôles des nœuds en lecture seule.** Suivre DIAG_M, LB/R2 et les contacts ignorés avant de préparer une intervention précise. Aucun nouveau lot natif, nouveau correctif ou nouvelle compilation couvert par l’accord A67. Les archives restent en lecture seule, toutes les anciennes sorties et tous les critères échoués sont préservés. Aucune force fictive, aucun ajustement aux dégâts connus, aucun terme RKE compensateur ni modification de budgets.

Les [rapports A66](wtc1_simulation_v8/output/aircraft_a66/rapport_aircraft_a66.md) et [A67](wtc1_simulation_v8/output/aircraft_a67/rapport_aircraft_a67.md) séparent les six catégories de preuve. La matrice demeure une matrice d’itération, pas un jacobien exact ; dommage général, retour arrière, grandes rotations dynamiques, inerties et bilans locaux entiers restent non qualifiés. **Meilleur impact entier : 0,0200001220703125 s.** Aucune vidéo ne fabrique les secondes manquantes. Publication et CI vérifient l’intégrité des livrables, sans valider la physique de l’impact réel.


## Ce qui est publié

- `harness/` : état scientifique, registre des expériences, références, contrôles et passations.
- `wtc1_simulation_v8/scripts/` et `data/` : code des calculs et configurations numériques.
- `wtc1_simulation_v8/output/`, dossiers CalculiX et OpenRadioss : résultats, rapports, bilans et diagnostics, y compris essais rejetés.
- `wtc1_3d_v4/` : scripts de visualisation, paramètres, audits et modèles/rendus dans les archives de résultats.
- `outputs/` : calculs exploratoires antérieurs et audits complémentaires. Leurs affirmations se lisent avec leurs propres limites ; leur présence n'est pas une validation.
- `publication/` : inventaire complet, empreintes SHA-256, règles de publication, licences tierces et liste motivée des fichiers externes non redistribués.

Inventaire courant : **18,484 fichiers scientifiques dans Git**, **40,971 sorties dans 138 archives**.

Restaurer les 137 anciennes archives des releases précédentes, puis les 1 archives [A66+A67](https://github.com/WTC-simu2026/WTC-simu2026/releases/tag/snapshot-2026-10-14-aircraft-a66-a67). Manifestes, SHA-256 et URL conservés ; aucune ancienne archive reconstruite ou remplacée.

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

AIRCRAFT-A68 : audit borné en lecture seule des deux nouveaux CHECK A67 et des sources figées du même moteur. Tracer la création/normalisation de DIAG_M, la branche de chargement LB/R2 et le rôle des 75 nœuds de translation signalés ; examiner séparément les cinq contacts TYPE25 ignorés et leur équivalence mécanique éventuelle. Réutiliser les sorties A67, sans nouveau Starter/Engine ni modification/compilation. /IMPL/DYNA/2 est déjà présent dans les cartes. Ne pas ajouter de force fictive, masquer les messages, changer RREF ou les seuils sans preuve et protocole déclaré. A67 est compilée ; les huit Engine autorisés sont consommés. Six témoins locaux passent dans leur domaine déclaré, dont aire évolutive limitée à Y libre. Les deux CHECK entiers échouent chacun : une erreur de chargement implicite, 107391 avertissements de connexion possible et cinq TYPE25 ignorés ; les 624 STOP de volume sont résolus. A52 reste non intégrée, aucun impact entier prolongé. Toute nouvelle modification/compilation ou nouveau lot natif nécessite une proposition concrète et un accord distinct. Préserver budgets, sorties, échecs et bilans sans RKE compensateur. Meilleur impact entier 0,0200001220703125 s ; dix secondes physiques et vidéo 3D restent incomplètes.

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
