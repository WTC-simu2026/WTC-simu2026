# WTC-simu2026

**Construction progressive d'une simulation exploratoire du WTC 1 : impact d'un Boeing 767, incendies et réponse structurelle, jusqu'à un éventuel effondrement ou son arrêt.**

Le projet teste des mécanismes, des hypothèses explicites et des plages de paramètres. Aucun résultat final n'est présupposé. Il s'agit d'une recherche personnelle reproductible, assistée par Codex, dont les modèles, calculs, essais rejetés et limites sont publiés pour être examinés et améliorés.

*English: an open, incremental WTC 1 research harness. Current results concern limited verification models; they do not establish the cause or reproduce the full historical collapse.*

## Où en est la simulation ?

Instantané du **15 octobre 2026** : **AIRCRAFT-A87 terminée**, prochaine **AIRCRAFT-A88**, registre **206 entrées**. **Les dix secondes physiques et la vidéo3D restent à produire.**

**A86 prépare une garde pour les deux critères relatifs exactement nuls.** Le cas A85 mesuraitDE0=1e−20,EIMP=0,U2=DU2=0, force libre et correctionDD exactement nulles. La proposition définit les ratios à0 dans ce seul sous-espace dégénéré, sous restrictions explicites : Newmark non quasi-statique, Newton modifié, critères123, mouvement imposé, aucune interface générale/rotation, un domaine/un thread, itération>=2. Le chemin non nul et CRIT_ITE restent textuellement conservés ; les tolérances ne changent pas. L’itération1 garde sonInfinity possible. Les86cas mathématiques et16contrôles finaux de portée passent statiquement, sans constituer une validation Fortran native.

**A87 applique le diff exact après accord distinct et publication A84+A85 vérifiée.** Dixième moteur isolé, sourceNL_SOLV seule nouvellement modifiée, recette et correctifs A73 conservés. Compilation309,388s sur sixCPU, dans le plafond1h, sans GPU, installation ou Starter compilé. Nouveau binaireSHA2569e72f04411158c9b48f67968eff3fe01f741aca5cb5bd3201985cdbaf75e27cd ; neuf anciens moteurs conservés.

**Les deux régressions du nouveau binaire passent sans relâcher leurs seuils.** FREE_Ismstr4 etAREA_EVOLUTION_FREE_Y atteignent1ms. Pour chaque cas,8001lignes/99colonnes décodées sont identiques valeur par valeur aux binaires A67 sauvegardés. L’analyse mécanique A67 est reprise sur les nouvelles sorties, avec ses seuils et portées d’origine. La portéeY à aire variable reste distincte d’une qualification globale du mouvementX imposé. Aucun ancien solveur n’est rejoué ; aucun convertisseur natif lancé.

**La boucle A81 franchit son premier pas, puis s’arrête au suivant.** Le marqueur de garde apparaît une fois à l’itération2 du premier essai. Un cycle1 à0,000125ms et deux états TH réels, dont un à temps positif, existent. Dernier temps binaire0,0001250000059371814ms : c’est une durée locale du coupon, aucun crédit sur l’impact entier. Au second essai,Infinity/NaN persistent et l’Engine s’arrête à nouveau au maximum30 puis79/ISTOP−2. La condition précise qui exclut ce second cas n’a pas été lue nativement et ne sera pas déduite sans preuve.

**La qualification locale reste échouée.** Ni plateau de compression, rupture, refermeture ou force après rupture n’est atteint. Les premiers champs natifs non nuls sont conservés, sans qualifier leur sémantique de dommage. Le résidu énergétique sur les deux états vaut au maximum1,39045e−12J pour le seuil1e−7J conservé ; cette fenêtre initiale ne valide pas la boucle0,65ms ni le travail indépendant des réactions. DifférenceKE reconstruite/native1,82489e−12J sur cette seule fenêtre. Aucun RKE ajouté ou seuil augmenté après coup.

**Trois Engine sont consommés sur quatre maximum, zéro Starter.** UnCPU/plafond180s chacun, zéro GPU/installation/extension entière. La quatrième place de CHECK était conditionnelle aux critères locaux ; elle reste inutilisée et n’est pas réaffectée. Les cinqTYPE25 ignorés et107391avertissements restent bloquants. Anciennes sorties, sources, budgets et critères échoués sont conservés. Aucune archive historique ou vidéo source réanalysée.

**A88 doit exploiter les nouveaux états en lecture seule et préciser le refus du second essai.** La garde du premier pas, les deux régressions et une trajectoire complète sont trois niveaux de preuve distincts. Aucun nouveau calcul automatique ou modification du moteur n’est couvert par la place conditionnelle restante.

Les [rapports A86](wtc1_simulation_v8/output/aircraft_a86/rapport_aircraft_a86.md) et [A87](wtc1_simulation_v8/output/aircraft_a87/rapport_aircraft_a87.md) séparent les six catégories de preuve. **Meilleur impact entier0,0200001220703125s.** Publication/CI attestent l’intégrité, pas la validation physique de l’impact réel.


## Ce qui est publié

- `harness/` : état scientifique, registre des expériences, références, contrôles et passations.
- `wtc1_simulation_v8/scripts/` et `data/` : code des calculs et configurations numériques.
- `wtc1_simulation_v8/output/`, dossiers CalculiX et OpenRadioss : résultats, rapports, bilans et diagnostics, y compris essais rejetés.
- `wtc1_3d_v4/` : scripts de visualisation, paramètres, audits et modèles/rendus dans les archives de résultats.
- `outputs/` : calculs exploratoires antérieurs et audits complémentaires. Leurs affirmations se lisent avec leurs propres limites ; leur présence n'est pas une validation.
- `publication/` : inventaire complet, empreintes SHA-256, règles de publication, licences tierces et liste motivée des fichiers externes non redistribués.

Inventaire courant : **19,618 fichiers scientifiques dans Git**, **41,867 sorties dans 148 archives**.

Restaurer les 147 anciennes archives des releases précédentes, puis les 1 archives [A86+A87](https://github.com/WTC-simu2026/WTC-simu2026/releases/tag/snapshot-2026-10-15-aircraft-a86-a87). Manifestes, SHA-256 et URL conservés ; aucune ancienne archive reconstruite ou remplacée.

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

AIRCRAFT-A88 : après publication A86+A87 vérifiée, analyser en lecture seule les nouveaux états A87 sauvegardés et leurs critères encore échoués. Distinguer la garde numérique des cas nuls, les régressions à seuils inchangés, le parcours commandé du coupon et ses qualifications physiques. Ne pas confondre durée locale en millisecondes et impact avion entier. Rechercher les valeurs de réaction, énergie et champs réellement disponibles avant une nouvelle proposition ; ne pas rejouer les diagnostics vérifiés. Aucun nouveau lancement automatique : les places utilisées A87 sont consommées et le CHECK conditionnel inutilisé ne devient pas un crédit générique. Toute autre modification du moteur ou exécution hors lot demande une proposition et un accord distinct. Conserver tolérances, budgets physiques, sources, sorties, critères échoués, cinqTYPE25 ignorés et107391avertissements. Meilleur impact entier0,0200001220703125s ; dix secondes physiques puis vidéo3D incomplètes.


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
