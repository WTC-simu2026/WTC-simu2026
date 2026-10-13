# WTC-simu2026

**Construction progressive d'une simulation exploratoire du WTC 1 : impact d'un Boeing 767, incendies et réponse structurelle, jusqu'à un éventuel effondrement ou son arrêt.**

Le projet teste des mécanismes, des hypothèses explicites et des plages de paramètres. Aucun résultat final n'est présupposé. Il s'agit d'une recherche personnelle reproductible, assistée par Codex, dont les modèles, calculs, essais rejetés et limites sont publiés pour être examinés et améliorés.

*English: an open, incremental WTC 1 research harness. Current results concern limited verification models; they do not establish the cause or reproduce the full historical collapse.*

## Où en est la simulation ?

Instantané du **13 octobre 2026** : **AIRCRAFT-A63 terminée**, prochaine étape **AIRCRAFT-A64**, registre **182entrées**. Les dix secondes physiques d’impact et leur vidéo3D restent incomplètes.

**A62 : sixième moteur isolé compilé**, autorisation humaine A61 sauvegardée. Différence approuvée appliquée exactement, puis déclarations d’interface Fortran réparées seulement ; équations exécutables du helper inchangées. Échecs R0/R1 conservés, R2 réussit dans le même plafond initial1h/CPU6/sansGPU/installation. Binaire **d36015d6238b5216ae7c5c4cbd909abb5c3cd7b25f724e6ef2faebc4814a4235**. Sources/caches/anciens moteurs préservés ; sources/différences/binaireAGPL hors des archives MIT.

Dix nouveaux Engine A62 CPU1/plafond180s : au repos, témoin normal et journal Newton échouent àT0 par rapports NaN/Infinity, résidu de force0 puis limite de pas. Le STOP volume nul est franchi. Trois variantes avec petite vitesseY libre initiale terminent à1ms, tractions/travail/G/rechargement/demi-pas concordants. Les conventions KE/P et somme de toutes les REAC sous mouvements imposés restent **non qualifiées**, leurs critères échoués et analyses initiales conservés ; aucune compensation de masse/RKE. Trois régressions explicites : **297canaux égaux bit à bit** aux A60 ; deux TYPE7/MUMPS et demi-pas passent le lecteur source/énergie/momentum A45, avec les échecs bruts antérieurs archivés.

**A63 : deux derniers Engine du lot autorisé**, sans compilation ou patch. Oscillateur surfacique élastique libre, aucune trajectoire imposée, deux Starter propres, CPU1/plafond180s. **44contrôles par cas passent** : solution Newmark discrète exacte, énergie physique, quantité de mouvement/impulsion des seuls supports, canaux natifs, masse8g et masse ajoutée0. Maximum résidu énergie8,82e-9J, impulsion1,10e-8Ns ; erreur de déplacement analytique7,24e-10mm.

**La comparaison demi-pas échoue** : KE/IE diffèrent jusqu’à0,00034846J, tolérance conservée1,01e-5J. Le composé global resteFALSE. Conservation algébrique et solution discrète exacte ne prouvent pas la convergence en temps. La dispersion analytique propose0,000125/0,0000625ms pour les futurs témoins ; matériau/masse/géométrie inchangés, aucune adaptation aux dégâts historiques. Ce pas instrumental n’est pas transposé à l’avion.

**Les12contrôles autorisés sont consommés.** [A64 préparée](wtc1_simulation_v8/output/aircraft_a64_preparation/proposition_etape_a64.md), non exécutée à cet instantané : deux essais plus fins puis, si tous les critères passent, deux CHECK entiers avec les anciennes entrées exactes. Nouveau budget maximum4/CPU1/cap180s, sanscompilation/GPU/installation, soumis à un accord distinct. Aucun impact entier prolongé.

Les [rapports A62](wtc1_simulation_v8/output/aircraft_a62/rapport_aircraft_a62.md) et [A63](wtc1_simulation_v8/output/aircraft_a63/rapport_aircraft_a63.md) séparent les six catégories de preuve. Archives/anciennes sorties/critères échoués préservés. Ancien CHECK15erreurs/624volumes/cinqTYPE25 ignorés, A52nonintégré ; domaines matériaux et bilans locaux entiers restent ouverts. **Meilleur impact entier :0,0200001220703125s**, aucun temps de témoin crédité à l’impact. Aucune vidéo produite en inventant les secondes manquantes. Intégrité de publication distincte de la validation physique.


## Ce qui est publié

- `harness/` : état scientifique, registre des expériences, références, contrôles et passations.
- `wtc1_simulation_v8/scripts/` et `data/` : code des calculs et configurations numériques.
- `wtc1_simulation_v8/output/`, dossiers CalculiX et OpenRadioss : résultats, rapports, bilans et diagnostics, y compris essais rejetés.
- `wtc1_3d_v4/` : scripts de visualisation, paramètres, audits et modèles/rendus dans les archives de résultats.
- `outputs/` : calculs exploratoires antérieurs et audits complémentaires. Leurs affirmations se lisent avec leurs propres limites ; leur présence n'est pas une validation.
- `publication/` : inventaire complet, empreintes SHA-256, règles de publication, licences tierces et liste motivée des fichiers externes non redistribués.

Inventaire courant : **18,087 fichiers scientifiques dans Git**, **38,891 sorties dans 136 archives**.

Restaurer les 135 anciennes archives des releases précédentes, puis les 1 archives [A62+A63](https://github.com/WTC-simu2026/WTC-simu2026/releases/tag/snapshot-2026-10-13-aircraft-a62-a63). Manifestes, SHA-256 et URL conservés ; aucune ancienne archive reconstruite ou remplacée.

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

AIRCRAFT-A64 : douze Engine autorisés A61 consommés au total A62(10)+A63(2). Ne pas dépasser ce budget sans nouvel accord. Préparer puis demander un accord pour deux témoins libres raffinés dt0,000125/0,0000625ms, CPU1/cap180s chacun, sur le moteur A62 inchangé, sans compilation/GPU/installation ; si leurs critères passent, deux CHECK entiers bornés original/paireA53 avec les mêmes entrées, aucune extension dynamique. A63 chaque trajectoire libre concorde avec la solution Newmark discrète exacte et les bilans physiques K/P/support/IE ; maxrésidu énergie8,82e-9J, impulsion1,10e-8Ns. Mais comparaison demi-pas0,001/0,0005ms échoue : différence KE/IE~0,00034846J >tol1,01e-5J. Échec conservé ; dispersion temporelle théorique explique le déphasage, pas de modification du seuil. Le nouveau pas proposé vient de l’erreur du modèle analytique prédeclared, sans ajuster matériau/masse ni dégâts ; ne pas le transposer à l’avion puisque les masses instrumentales sont artificielles. A62 : correctif surfacique compilé, sixième moteur SHAd36015d6238b5216ae7c5c4cbd909abb5c3cd7b25f724e6ef2faebc4814a4235. Démarrage au repos NaN/Infinity et observables imposés KE/P restent échoués/non qualifiés ; les variantes chargées passent traction/travail, pas une qualification entière. Trois régressions explicites297canaux bits identiques, deux TYPE7/MUMPS source énergie/momentum et demi-pas passent, échecs bruts conservés. CHECK entiercached15erreurs/624volumes/cinqTYPE25 ignorés, A52nonintégré ; aucun nouveau CHECK ni extension. Budgets/anciennes sorties et critères préservés, aucun RKE compensateur. Meilleur impact entier0,0200001220703125s ; objectif dix secondes physiques puis vidéo3D incomplet. PublicationA62+A63 à vérifier, prochaine cadenceA64+A65. Toute future modification/compilation moteur supplémentaire demande un accord distinct sur une proposition concrète.

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
