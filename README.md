# WTC-simu2026

**Construction progressive d'une simulation exploratoire du WTC 1 : impact d'un Boeing 767, incendies et réponse structurelle, jusqu'à un éventuel effondrement ou son arrêt.**

Le projet teste des mécanismes, des hypothèses explicites et des plages de paramètres. Aucun résultat final n'est présupposé. Il s'agit d'une recherche personnelle reproductible, assistée par Codex, dont les modèles, calculs, essais rejetés et limites sont publiés pour être examinés et améliorés.

*English: an open, incremental WTC 1 research harness. Current results concern limited verification models; they do not establish the cause or reproduce the full historical collapse.*

## Où en est la simulation ?

Instantané du **15 octobre 2026** : **AIRCRAFT-A85 terminée**, prochaine **AIRCRAFT-A86**, registre **204 entrées**. **Les dix secondes physiques et la vidéo3D restent à produire.**

**A84 localise les normalisations en lecture seule.** La source épinglée définitRE=DE0/EIMP etRU=LS3*sqrt(DU2/U2), avec plancherDE0=1e−20 pour les très petits incréments. PRODUT_UHP forme une norme après projection/condensation sur les inconnues libres. Des dénominateurs nuls étaient une hypothèse compatible à vérifier. Les16contrôles source/observateur et8contrôles du lanceur passent statiquement ; aucun moteur n’est exécuté pendant cette préparation.

**Un addendum corrige l’interprétation de la ligne0 A83.** Le même en-tête visuel recouvre à0 les grandeurs initiales sqrt(U2),sqrt(R02),EIMP ; les lignes positives impriment les ratiosRU,RR,RE. Les chaînes transcrites A83 sont exactes ; leur appellation générale de ratios était trop large pour0. Le rapport d’origine reste conservé et la correction est explicitement ajoutée dans A84. Infinity/NaN aux itérations positives restent observés.

**A85 exécute son unique Engine distinctement autorisé après vérification A82+A83.** UnCPU, plafond180s, zéro Starter, correctif, compilation, GPU, installation ou prolongement entier. Carte A83, restart initial propre A81 et tous critères/paramètres inchangés. Durée5,004s avec lancement,0,641s dans l’observateur. Celui-ci retourne0 et l’Engine2 sans signal terminal : la réussite de mesure ne vaut pas convergence. Onze arrêts matériels bornés, lectures seules des données, aucune instruction ou donnée numérique modifiée ; désactivation après le critère2, puis arrêt propre du moteur.

**Les valeurs natives confirment les deux divisions dégénérées.** Aux critères1et2 : DE0=1e−20,EIMP=0,R02=1 et les huit composantesF libres exactement0 ; ER=+Infinity. À2 : U2=DU2=0 au retour natif,LS3=1 etUR=NaN. Les24composantes de correctionDD sont nulles, tandis que D contient−1,90288107842e−9mm sur les quatreZ supérieurs imposés. La norme libre peut donc être nulle malgré le mouvement imposé. Les opérandes consommés établissent1e−20/0 et0/0 dans ce cas précis ; leDE brut antérieur au plancher n’est pas capturé.

**Les16contrôles de transcription et portée A85 passent ; la physique reste échouée.** Le carré du résidu recalculé depuisF est étiqueté dérivé, jamais assimilé à une lecture de la variable localeR2. Le temps/cycle global n’a pas été observé ni promis. EIMP est une variable d’algorithme, pas l’énergie physique totale. Un seul état TH réel et une animation initiale à0ms ; maximum30 puis MESSAGE79/ISTOP−2, avertissementsPARITH/ON etISOLID0 conservés. Compression, rupture, refermeture, plateaux, travail de fracture et peuplementUSR restent non mesurés.

**A86 doit préparer un traitement borné des cas exactement nuls.** Définir gardes et témoins adverses pour conserver les critères non nuls, les déséquilibres et l’énergie indépendante. Aucun correctif moteur appliqué ou compilé. Le seul EngineA85 est consommé sans remplacement ; anciennes sorties, budgets, critères échoués et107391avertissements A73 restent conservés. Aucun RKE inventé, temps interpolé, ajustement aux dégâts connus ou archive historique réanalysée.

Les [rapports A84](wtc1_simulation_v8/output/aircraft_a84/rapport_aircraft_a84.md) et [A85](wtc1_simulation_v8/output/aircraft_a85/rapport_aircraft_a85.md) séparent les six catégories de preuve. **Meilleur impact entier0,0200001220703125s.** Publication/CI attestent l’intégrité, pas la validation physique de l’impact réel.


## Ce qui est publié

- `harness/` : état scientifique, registre des expériences, références, contrôles et passations.
- `wtc1_simulation_v8/scripts/` et `data/` : code des calculs et configurations numériques.
- `wtc1_simulation_v8/output/`, dossiers CalculiX et OpenRadioss : résultats, rapports, bilans et diagnostics, y compris essais rejetés.
- `wtc1_3d_v4/` : scripts de visualisation, paramètres, audits et modèles/rendus dans les archives de résultats.
- `outputs/` : calculs exploratoires antérieurs et audits complémentaires. Leurs affirmations se lisent avec leurs propres limites ; leur présence n'est pas une validation.
- `publication/` : inventaire complet, empreintes SHA-256, règles de publication, licences tierces et liste motivée des fichiers externes non redistribués.

Inventaire courant : **19,463 fichiers scientifiques dans Git**, **41,450 sorties dans 147 archives**.

Restaurer les 146 anciennes archives des releases précédentes, puis les 1 archives [A84+A85](https://github.com/WTC-simu2026/WTC-simu2026/releases/tag/snapshot-2026-10-15-aircraft-a84-a85). Manifestes, SHA-256 et URL conservés ; aucune ancienne archive reconstruite ou remplacée.

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

AIRCRAFT-A86 : après publication A84+A85 vérifiée, préparer une réponse précise aux critères relatifs dégénérés observés, en lecture seule. A85 mesureDE0=1e−20,EIMP=0,RE=Infinity ; U2=DU2=0,LS3=1,RU=NaN à2 ; les huit composantesF libres sont exactement0. Le mouvement normal imposé existe dansD mais ne contribue pas à la norme des inconnues libres. Proposer un traitement borné des cas exactement nuls, sans neutraliser les critères non nuls ni masquer un déséquilibre ; définir témoins adverses et vérifications énergétiques avant accord distinct. Aucun correctif moteur appliqué ou compilé. Le seul EngineA85 est consommé, zéro Starter, aucun réessai. Les captures natives s’arrêtent à2 ; la suite est seulement imprimée. Compression, rupture et refermeture restent non mesurées ; tous échecs, anciennes sorties et budgets conservés. Meilleur impact entier0,0200001220703125s ; dix secondes physiques puis vidéo3D incomplètes.


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
