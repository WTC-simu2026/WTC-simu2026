# WTC-simu2026

**Construction progressive d'une simulation exploratoire du WTC 1 : impact d'un Boeing 767, incendies et réponse structurelle, jusqu'à un éventuel effondrement ou son arrêt.**

Le projet teste des mécanismes, des hypothèses explicites et des plages de paramètres. Aucun résultat final n'est présupposé. Il s'agit d'une recherche personnelle reproductible, assistée par Codex, dont les modèles, calculs, essais rejetés et limites sont publiés pour être examinés et améliorés.

*English: an open, incremental WTC 1 research harness. Current results concern limited verification models; they do not establish the cause or reproduce the full historical collapse.*

## Où en est la simulation ?

Instantané du **15 octobre 2026** : **AIRCRAFT-A81 terminée**, prochaine **AIRCRAFT-A82**, registre **200 entrées**. **Les dix secondes physiques et la vidéo3D restent à produire.**

**A80 classe les4430paires initiales sans modifier la scène.** 2910paires relient des facettes de même peau partageant un joint cohésif d’arête direct, dont toutes les916erreursA79 ;1520partagent seulement un sommet relié par des chemins de deux ou trois joints. Les624joints et leurs raccords sont présents. Le refusR0 d’identité avec A20 sur144hôtes réaffectés reste conservé ; R1 contrôle les chemins actuellement écrits aux racines, présence/topologie uniquement. Aucune exclusion de contact ou équivalence mécanique n’est déduite.

**Une attente jusqu’à sortie du gap0,5mm n’est pas retenue sans contrôle cohésif.** Sous les hypothèses de modeI pur et d’évolution linéaire, les paramètres actuels donnent une rupture vers0,22222mm. Une ouverture0,3mm puis refermeture pourrait donc rompre un joint avant l’armement géométrique envisagé. Il s’agit d’un résultat dérivé conditionnel, pas d’une propriété mesurée de l’avion. Un développement transversal Starter/Engine n’est pas présenté comme un petit correctif prêt.

**A81 exécute le témoin distinctement autorisé, avec logiciels inchangés.** Un Starter puis un Engine sur unCPU, plafond180s chacun, sans GPU, installation, correctif, compilation ou prolongement entier. Coupon8nœuds/100mm²/8g instrumentaux ; cartesLAW117/TYPE43 actuelles, compression−0,05mm, ouverture0,3mm, refermeture−0,05mm prévues sur0,65ms. Les préparations et contrôles indépendants restent statiques. La publication A78+A79 a été vérifiée avant déclaration.

**Le Starter passe ; l’Engine échoue avant toute trajectoire sauvegardée.** Préparation6,945s, code0, zéro erreur/zéro avertissement et paramètres natifs confirmés, masse8g/ADMAS8g. Engine4,955s, code2 sans dépassement, MESSAGE79/ISTOP−2 sur la limite de pas minimale égale au pas initial0,000125ms. Les avertissementsPARITH etISOLID0 sont conservés. Une factorisation MUMPS sans pivot négatif ne qualifie pas la convergence non linéaire.

**Un seul état TH et une animation initiale à0ms existent.** Le lecteur Python du schémaTH3040 a été vérifié contre8001lignes/99colonnes du CSV natif A67 sauvegardé, sans convertisseur ni solveur relancé. Le CSV A81 est la transcription de son unique état réel. Les impulsions des plateaux, dommage, travail de fracture, rupture et compression après refermeture restent non mesurés ; les zéros initiauxUSR ne prouvent pas leur peuplement. Le refus de lectureR0 TN/TT est conservé, corrigé avant lancement par un préfixe exact, sans changement d’entrée physique.

**Les deux places A81 sont consommées.** Aucun réessai ou abaissement de pas après coup, aucun temps manquant interpolé, RKE inventé ou ajustement aux dégâts connus. La tolérance énergétiqueA67 de1e−7J à énergie initiale nulle reste conservée sans faux succès d’un historique à0ms. Anciennes sorties, budgets, critères échoués et107391avertissements A73 restent conservés. Aucune archive historique ou vidéo source réanalysée.

**A82 doit observer les critères du premier essai Newton avant toute modification.** Préparer une impression non linéaire détaillée, réutiliser l’état initial propre A81, conserver chargement, bornes de pas, tolérances et moteur. L’observation nouvelle demande un accord distinct et ne constitue pas un prolongement de l’impact entier.

Les [rapports A80](wtc1_simulation_v8/output/aircraft_a80/rapport_aircraft_a80.md) et [A81](wtc1_simulation_v8/output/aircraft_a81/rapport_aircraft_a81.md) séparent les six catégories de preuve. **Meilleur impact entier0,0200001220703125s.** Publication/CI attestent l’intégrité, pas la validation physique de l’impact réel.


## Ce qui est publié

- `harness/` : état scientifique, registre des expériences, références, contrôles et passations.
- `wtc1_simulation_v8/scripts/` et `data/` : code des calculs et configurations numériques.
- `wtc1_simulation_v8/output/`, dossiers CalculiX et OpenRadioss : résultats, rapports, bilans et diagnostics, y compris essais rejetés.
- `wtc1_3d_v4/` : scripts de visualisation, paramètres, audits et modèles/rendus dans les archives de résultats.
- `outputs/` : calculs exploratoires antérieurs et audits complémentaires. Leurs affirmations se lisent avec leurs propres limites ; leur présence n'est pas une validation.
- `publication/` : inventaire complet, empreintes SHA-256, règles de publication, licences tierces et liste motivée des fichiers externes non redistribués.

Inventaire courant : **19,347 fichiers scientifiques dans Git**, **41,443 sorties dans 145 archives**.

Restaurer les 144 anciennes archives des releases précédentes, puis les 1 archives [A80+A81](https://github.com/WTC-simu2026/WTC-simu2026/releases/tag/snapshot-2026-10-15-aircraft-a80-a81). Manifestes, SHA-256 et URL conservés ; aucune ancienne archive reconstruite ou remplacée.

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

AIRCRAFT-A82 : après publication A80+A81 vérifiée, diagnostiquer en lecture seule l’arrêt au premier pas imposé A81, message79/ISTOP−2, sans rupture ni refermeture observées. Préparer une observation des critères de convergence au premier essai, avec impression nonlinéaire détaillée et restart initial A81 réutilisé, sans modifier le chargement, les tolérances, le minimum/maximum de pas, le moteur ou les paramètres physiques. Toute nouvelle exécution nécessite une proposition concrète et accord distinct : les1Starter+1Engine A81 sont consommés. Ne pas abaisser silencieusement le pas minimum ni compter l’état initial comme trajectoire. Les impulsions de plateau, USR, dégâts, compression après rupture et retour en contact restent non mesurés. Conserver erreurs, avertissements, refus R0, limites et budgets antérieurs. Meilleur impact entier0,0200001220703125s ; dix secondes physiques puis vidéo3D incomplètes.


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
