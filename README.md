# WTC-simu2026

**Construction progressive d'une simulation exploratoire du WTC 1 : impact d'un Boeing 767, incendies et réponse structurelle, jusqu'à un éventuel effondrement ou son arrêt.**

Le projet teste des mécanismes, des hypothèses explicites et des plages de paramètres. Aucun résultat final n'est présupposé. Il s'agit d'une recherche personnelle reproductible, assistée par Codex, dont les modèles, calculs, essais rejetés et limites sont publiés pour être examinés et améliorés.

*English: an open, incremental WTC 1 research harness. Current results concern limited verification models; they do not establish the cause or reproduce the full historical collapse.*

## Où en est la simulation ?

Instantané du **11 octobre2026** : **AIRCRAFT-A31 terminée**, prochaine étape **AIRCRAFT-A32**. Le registre compte150entrées. A30+A31 ajoutent18calculs natifs complets, quatre tentatives implicites échouées et des analyses en cache. Configurations, scripts, résultats et critères échoués conservés.

A30 vérifie le sandwich volumique à faces communes, de masse0,2214g: mêmes peaux LAW12explicites et cœur LAW28source, mouvements libres, invariants physiques, champs élastiques et raffinements. Le collage parfait et les coefficients transverses restent des hypothèses. Les champs imposés à tous les nœuds ne suffisent pas à qualifier le transfert de charge.

A31 impose seulement les faces extérieures et laisse tous les nœuds intérieurs libres. CisaillementsXZ/YZ, traction et compression normales sur deux maillages, réactions, travail, déplacements, énergie et raffinements sont comparés à une référence3D indépendante hétérogène. Le périmètre fin **passe**. Les neuf ensembles individuels comptent9réussites; les bilans complets9/9. Toutes les hypothèses matérielles et limites restent explicites.

La correspondance des24racines/144ancres courbes conserve faces physiques, repères et candidats géométriques; aucun volume ou budget de prise plate n'est supposé. Le binaire installé échoue aux deux sondes implicites compactes avec **MUMPSrequired**; les deux erreurs de lecture initiales sont conservées. Aucun solveur modifié ou composant installé. Un addendum relit les canaux plastiques A30manquants en cache, sans réécriture des preuves A30scellées.

Les [rapports A30](wtc1_simulation_v8/output/aircraft_a30/rapport_aircraft_a30.md) et [A31](wtc1_simulation_v8/output/aircraft_a31/rapport_aircraft_a31.md) séparent faits, références, archives, hypothèses, résultats dérivés et lacunes. Échecs précédents conservés, aucune ancienne exécution relancée, compensation de masse/inertie ou RKEinventée. Le libellé officiel REACforce est confronté à l'observation d'impulsions de ce binaire, avec les deux interprétations testées.

La vidéo3D des **dix premières secondes physiques** reste incomplète: meilleur entier A20=**20millisecondes physiques**. Son coût extrapolé est d'environ6,90jours, estimation indicative sans garantie. Les attaches réelles et une voie de calcul efficace à masse physique inchangée doivent être testées avant nouveau départ entier. Propriétés/ruptures historiques, façade, gravité, intérieur porteur et contacts de fragments restent ouverts. Aucun dommage connu comme cible. La publication confirme l'intégrité des fichiers, sans validation historique de l'impact ou de l'effondrement.


## Ce qui est publié

- `harness/` : état scientifique, registre des expériences, références, contrôles et passations.
- `wtc1_simulation_v8/scripts/` et `data/` : code des calculs et configurations numériques.
- `wtc1_simulation_v8/output/`, dossiers CalculiX et OpenRadioss : résultats, rapports, bilans et diagnostics, y compris essais rejetés.
- `wtc1_3d_v4/` : scripts de visualisation, paramètres, audits et modèles/rendus dans les archives de résultats.
- `outputs/` : calculs exploratoires antérieurs et audits complémentaires. Leurs affirmations se lisent avec leurs propres limites ; leur présence n'est pas une validation.
- `publication/` : inventaire complet, empreintes SHA-256, règles de publication, licences tierces et liste motivée des fichiers externes non redistribués.

Inventaire courant : **13,116 fichiers scientifiques dans Git**, **20,344 sorties dans 115 archives**.

Restaurer les 112 anciennes archives des releases précédentes, puis les 3 archives [A30+A31](https://github.com/WTC-simu2026/WTC-simu2026/releases/tag/snapshot-2026-10-11-aircraft-a30-a31). Manifestes, SHA-256 et URL conservés ; aucune ancienne archive reconstruite ou remplacée.

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

AIRCRAFT-A32 : le périmètre élastique du sandwich à intérieur libre passe; préparer les24racines/144ancres courbes réellement inventoriées dans A25, leurs repères, prises et budgets physiques avant un contrôle natif représentatif. Le coût de10secondes doit être évalué sur la discrétisation réelle; tester une formulation efficace à masse physique inchangée avec référence indépendante si nécessaire. Le binaire installé échoue aux deux sondes implicites avec MUMPSrequired; aucune installation ni modification du solveur effectuée. Les cartes LAW12, coefficients transverses et collage parfait restent des hypothèses explicites; résistances, décollement et rupture historiques non identifiés. Aucun faux ajout de RKE, correction de densité ou ajustement aux dégâts connus. Nouveau départ entier après critères locaux, bilans et estimation du coût. Meilleur entierA20=20ms; objectif vidéo3D10secondes physiques incomplet. Publication A30+A31 après vérification, déjà autorisée; cadence suivante A32+A33.

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
