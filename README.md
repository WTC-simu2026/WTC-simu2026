# WTC-simu2026

**Construction progressive d'une simulation exploratoire du WTC 1 : impact d'un Boeing 767, incendies et réponse structurelle, jusqu'à un éventuel effondrement ou son arrêt.**

Le projet teste des mécanismes, des hypothèses explicites et des plages de paramètres. Aucun résultat final n'est présupposé. Il s'agit d'une recherche personnelle reproductible, assistée par Codex, dont les modèles, calculs, essais rejetés et limites sont publiés pour être examinés et améliorés.

*English: an open, incremental WTC 1 research harness. Current results concern limited verification models; they do not establish the cause or reproduce the full historical collapse.*

## Où en est la simulation ?

Instantané du **15 octobre 2026** : **AIRCRAFT-A79 terminée**, prochaine **AIRCRAFT-A80**, registre **198 entrées**. **Objectif dix secondes physiques puis vidéo 3D incomplet.** Cette paire apporte une observation des contacts initiaux, sans nouvelle durée d’impact.

**A78 : audit géométrique depuis les sorties A77 conservées.** L’auto-contact du radôme possède 432 pièces, 1296 facettes et 3024 nœuds. Le graphe de surface, fondé sur les identités de nœuds, contient 432 composantes et 340 groupes de coordonnées écrites identiques entre composantes. Les 676 numéros distincts portant les erreurs A77 figurent tous dans ces groupes. Les contraintes TYPE2 sont hors de ce graphe : aucune déconnexion mécanique ou déficience de rang n’en est déduite. Aucun solveur rejoué pendant cet audit.

**A79 : l’unique observation Starter autorisée est terminée en 32,6006743 s**, sur un CPU, sous plafond de 180 s, sans dépassement. L’ajout de `/IOFLAG Ipri5` et les noms de cas sont les seuls changements apportés à une copie du modèle original A77 ; les cartes physiques et contacts restent identiques. Logiciels inchangés, zéro Engine, correctif logiciel, compilation, GPU ou installation. Le code retour est 2 et aucun état initial propre n’est qualifié.

**Les paires réellement imprimées sont maintenant vérifiées.** Les 4430 tuples uniques associent chacun un secondaire et les quatre sommets d’un segment natif, retrouvés dans une facette déclarée avec le même ordre. Les 48171 coordonnées natives imprimées concordent avec l’entrée à la précision disponible, avec écart maximal nul ; les 1296 segments et 3024 secondaires sont contrôlés. Les 916 paires avec ERROR612 concernent 676 secondaires distincts. Toutes ont une coïncidence exacte avec un sommet principal portant un autre numéro ; aucune de leurs facettes quadrilatérales n’est dégénérée. Mais huit autres paires présentent aussi une coïncidence exacte sans ERROR612 : la seule égalité des coordonnées ne suffit donc pas à établir une règle causale. La présence imprimée des 432 liaisons TYPE2 ne qualifie pas leur dynamique.

**Observation réussie, préparation physique toujours échouée.** Les 916 erreurs restent présentes et la sortie détaillée contient deux avertissements, contre un prévu : WARNING1164 liste 3514 autres pénétrations ; WARNING343 compte 4430 pénétrations sur 1968 secondaires, soit 916 + 3514. L’avertissement supplémentaire et la prévision initiale sont conservés. La séquence des numéros fautifs reste identique à A77. La source logicielle figée éclaire l’impression détaillée sans être assimilée au binaire Windows. Masse 191273837,9425 g et ADMAS 100368522,1367 g conservées ; cela ne qualifie pas les tenseurs redistribués ou les inerties natives.

**L’unique Starter A79 est consommé, aucun Engine n’est autorisé ou exécuté.** Les anciens budgets, sorties et critères échoués restent conservés, notamment A75/A77 et les 107391 avertissements A73. Aucun temps manquant extrapolé, terme RKE inventé ou ajustement aux dégâts connus. Aucune archive historique ou vidéo source réanalysée.

**A80 doit préparer en lecture seule une stratégie de contact pour les jointures cohésives initialement coïncidentes**, à partir des paires A79. Préserver les nœuds séparés nécessaires à la rupture et les contacts après ouverture et refermeture ; ne pas forcer le passage par fusion, déplacement de coordonnées, réduction du gap ou désactivation globale. Vérifier les chemins sources et définir des témoins distinctifs avant de présenter un correctif concret. Aucun correctif n’est encore prêt ; tout nouveau lot natif ou changement logiciel reste hors du lot A79 consommé.

Les [rapports A78](wtc1_simulation_v8/output/aircraft_a78/rapport_aircraft_a78.md) et [A79](wtc1_simulation_v8/output/aircraft_a79/rapport_aircraft_a79.md) séparent les six catégories de preuve. **Meilleur impact entier : 0,0200001220703125 s.** Les dix secondes physiques puis la vidéo 3D restent à produire. Publication et CI attestent l’intégrité des artefacts, pas la validation physique de l’impact réel.


## Ce qui est publié

- `harness/` : état scientifique, registre des expériences, références, contrôles et passations.
- `wtc1_simulation_v8/scripts/` et `data/` : code des calculs et configurations numériques.
- `wtc1_simulation_v8/output/`, dossiers CalculiX et OpenRadioss : résultats, rapports, bilans et diagnostics, y compris essais rejetés.
- `wtc1_3d_v4/` : scripts de visualisation, paramètres, audits et modèles/rendus dans les archives de résultats.
- `outputs/` : calculs exploratoires antérieurs et audits complémentaires. Leurs affirmations se lisent avec leurs propres limites ; leur présence n'est pas une validation.
- `publication/` : inventaire complet, empreintes SHA-256, règles de publication, licences tierces et liste motivée des fichiers externes non redistribués.

Inventaire courant : **19,247 fichiers scientifiques dans Git**, **41,437 sorties dans 144 archives**.

Restaurer les 143 anciennes archives des releases précédentes, puis les 1 archives [A78+A79](https://github.com/WTC-simu2026/WTC-simu2026/releases/tag/snapshot-2026-10-15-aircraft-a78-a79). Manifestes, SHA-256 et URL conservés ; aucune ancienne archive reconstruite ou remplacée.

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

AIRCRAFT-A80 : après publication A78+A79 vérifiée, préparer en lecture seule une stratégie de contact pour les jointures cohésives initialement coïncidentes, à partir des paires réelles A79. Préserver les nœuds séparés voulus pour la rupture et les contacts après ouverture/refermeture ; ne pas fusionner les nœuds, réduire le gap, déplacer les coordonnées ou désactiver globalement le contact pour forcer une préparation propre. Écarter toute simple copie Inacti1000 entre TYPE25 et TYPE7. Définir des témoins distinctifs et vérifier les chemins sources avant de présenter un correctif concret. A79 consomme son unique Starter ; zéro Engine autorisé ou exécuté. Aucun autre lot natif/correctif logiciel ou compilation couvert par cet accord. Les916erreurs et deux avertissements A79 restent échoués, dont1164 supplémentaire dû à la sortie détaillée, sans modifier la prévision originale d’un avertissement. Conserver moteurs, sorties, budgets, critères échoués et107391avertissements A73. Meilleur impact entier0,0200001220703125s ; objectif dix secondes physiques puis vidéo3D incomplet.


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
