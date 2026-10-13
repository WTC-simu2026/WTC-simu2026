# WTC-simu2026

**Construction progressive d'une simulation exploratoire du WTC 1 : impact d'un Boeing 767, incendies et réponse structurelle, jusqu'à un éventuel effondrement ou son arrêt.**

Le projet teste des mécanismes, des hypothèses explicites et des plages de paramètres. Aucun résultat final n'est présupposé. Il s'agit d'une recherche personnelle reproductible, assistée par Codex, dont les modèles, calculs, essais rejetés et limites sont publiés pour être examinés et améliorés.

*English: an open, incremental WTC 1 research harness. Current results concern limited verification models; they do not establish the cause or reproduce the full historical collapse.*

## Où en est la simulation ?

Instantané du **13 octobre 2026** : **AIRCRAFT-A51 terminée**, prochaine étape **AIRCRAFT-A52**. Le registre compte **170 entrées**. Le démarrage natif de la copie à chaînes rigides composées est comparé à la référence, puis les messages de contraintes sont classés depuis les appels réels du moteur.

A50 exécute un nouvel Engine explicite de trois cycles, un threadCPU, en17,858s. Les cinqTYPE25sont conservés. Deux histoires0/10ns et trois animations0/10/20ns correspondent à la référence A45 à la précision enregistrée : masses, énergies, impulsionsXYZ, coordonnées, déplacements et vitesses. La comparaison brute de topologie reste échouée :384extrémités de traits rigides changent, exactement comme les144relations A49. Un audit distinct confirme chaque changement pré-déclaré et l’identité des éléments physiques et autres traits. Les sorties originales sont conservées, aucun ancien solveur relancé.

Le compteur natifADDED MASS=**0,0002019107g**est minuscule mais non nul, identique à A45. Il n’est pas confondu avec les ADMAS non structurelles prescrites. Cette fenêtre20ns sans charge significative ne qualifie pas l’inertie en rotation ou les travaux locaux. La source précise que **CHECKforceISOLV1/IPREC5/ILINE1 puisIKPAT1**, indépendamment du mot-clé de solveur demandé ; ce contrôle n’est pas une dynamique MUMPS qualifiée. Changer seulement le solveur dansCHECKserait neutralisé. Les blocs absents de PUT_KIJ ne sont pas ajoutés.

A51 réemploie l’état natif à temps zéro. L’export texte arrondi échoue à0,05mm ; le lecteur natif vérifie les **48171nœuds**, erreur maximale **0,00167415mm**, sous le seuil inchangé0,003mm. Les302correspondances capturées directement sont confirmées. Les réparations de lecteurs sont conservées dans des fichiers distincts, sans modifier moteur ou physique.

**Une interprétation initiale des messages est rejetée** : les appels TYPE2/RBE2 transmettent ITAB(N), donc les nombres imprimés sont déjà les labels d’entrée. La classification corrigée conserve l’ancienne tentative comme erreur explicite. Les15directions suspectes appartiennent aux racines99/103/107/109/111/119. Les49370messages forment20483paires ordonnées par famille : **37165TYPE2entre ensembles distincts**,11831avec une interface commune,374RBE2. Aucune double contrainte secondaire déclarée ;96interfaces ont des parents de surface potentiellement dépendants. Les groupes de surface ne sont pas assimilés aux facettes ou poids natifs réellement sélectionnés.

La sourceIND_KINE_K laisseNMC2à zéro et traite les couples secondaires à l’intérieur de chaque TYPE2avantRBE2. Une interaction de deuxTYPE2au travers du même noyau constitue une **hypothèse à tester**, aucune cause complète n’est déclarée prouvée. Le prochain reproducer copie une facette complète avec ses peaux, noyau3D, cellules cohésives et deuxTYPE2originaux. Tout regroupement doit conserver facettes, coefficients et déports natifs avant transfert entier.

Les [rapports A50](wtc1_simulation_v8/output/aircraft_a50/rapport_aircraft_a50.md) et [A51](wtc1_simulation_v8/output/aircraft_a51/rapport_aircraft_a51.md) séparent les six catégories de preuve. A51 n’exécute aucun nouveau solveur. Aucun patch logiciel, installation, compilation, masse compensatoire ou ajustement aux dégâts historiques. A49 garde15erreurs mécaniques et cinqTYPE25ignorés en implicite ; A40 chargé/croissance, A34 peaux et A36 raffinement restent échoués.

La vidéo3D des **dix premières secondes physiques** reste incomplète : meilleur impact entier A20 = **0,0200001220703125seconde**. Aucun temps de diagnostic ou de panneau n’est crédité à l’impact entier. L’intégrité de publication ne valide pas la physique ni l’événement historique.


## Ce qui est publié

- `harness/` : état scientifique, registre des expériences, références, contrôles et passations.
- `wtc1_simulation_v8/scripts/` et `data/` : code des calculs et configurations numériques.
- `wtc1_simulation_v8/output/`, dossiers CalculiX et OpenRadioss : résultats, rapports, bilans et diagnostics, y compris essais rejetés.
- `wtc1_3d_v4/` : scripts de visualisation, paramètres, audits et modèles/rendus dans les archives de résultats.
- `outputs/` : calculs exploratoires antérieurs et audits complémentaires. Leurs affirmations se lisent avec leurs propres limites ; leur présence n'est pas une validation.
- `publication/` : inventaire complet, empreintes SHA-256, règles de publication, licences tierces et liste motivée des fichiers externes non redistribués.

Inventaire courant : **16,434 fichiers scientifiques dans Git**, **28,543 sorties dans 128 archives**.

Restaurer les 127 anciennes archives des releases précédentes, puis les 1 archives [A50+A51](https://github.com/WTC-simu2026/WTC-simu2026/releases/tag/snapshot-2026-10-13-aircraft-a50-a51). Manifestes, SHA-256 et URL conservés ; aucune ancienne archive reconstruite ou remplacée.

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

AIRCRAFT-A52 : créer un reproducer complet de la dernière facette216, à partir de l’entrée réelle A20/A49 : deux faces de peau, noyau3D, cellules cohésives et RBE2déportés, deux TYPE2originaux16430/16431. A51 corrige les labels du listing : les appels PRINT_WKIJ reçoiventITAB(N), donc les nombres imprimés sont déjà des labels originaux ; les anciennes classifications inverses sont rejetées et conservées. Les15directions suspectes appartiennent aux racines99/103/107/109/111/119. Les49370messages sont répartis en20483paires ordonnées ;37165TYPE2 relient des ensembles TYPE2distincts,11831ontau moins un TYPE2commun ;374sontRBE2. Aucune double contrainte secondaire,96interfaces ont des parents potentiellement dépendants. La sourceIND_KINE_K laisseNMC2=0 et construit les couples secondaires à l’intérieur de chaque TYPE2 avantRBE2. Tester l’interaction réelle de deux TYPE2au travers du même noyau, absente des petits reproducer A49. Comparer ensuite une variante groupée seulement si les facettes principales, coefficients natifs et déports restent équivalents ; ne pas assimiler un groupe de surface potentiel aux vrais poids. Aucun changement entier implicite, ajout de masse/inertie, patch logiciel ou ajustement historique. Coordonnées natives48171nœuds vérifiées au seuil0,003mm : erreur0,00167415mm ; la sortie texte arrondie0,05mm reste rejetée. Les302correspondances natives sont confirmées ; aucun nouveau Engine enA51. CHECKforcéPCG/IPREC5, contactsTYPE25ignorés et15erreurs restent ouverts. A40 chargé/croissance, A34 peaux et A36 raffinement échoués. Meilleur impact entierA20=0,0200001220703125s ; dix secondes physiques3D puisMP4/GIF actives et incomplètes. Publier A50+A51 puis poursuivre A52.

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
