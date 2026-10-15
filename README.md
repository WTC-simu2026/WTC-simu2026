# WTC-simu2026

**Construction progressive d'une simulation exploratoire du WTC 1 : impact d'un Boeing 767, incendies et réponse structurelle, jusqu'à un éventuel effondrement ou son arrêt.**

Le projet teste des mécanismes, des hypothèses explicites et des plages de paramètres. Aucun résultat final n'est présupposé. Il s'agit d'une recherche personnelle reproductible, assistée par Codex, dont les modèles, calculs, essais rejetés et limites sont publiés pour être examinés et améliorés.

*English: an open, incremental WTC 1 research harness. Current results concern limited verification models; they do not establish the cause or reproduce the full historical collapse.*

## Où en est la simulation ?

Instantané du **15 octobre 2026** : **AIRCRAFT-A91 terminée**, prochaine **AIRCRAFT-A92**, registre **210 entrées**. **Les dix secondes physiques d’impact entier et la vidéo 3D restent à produire.**

**A90 prépare une garde de correction libre exactement nulle.** La projection reprend IMP_SETB puis CONDENS_B ; chaque composante projetée doit être exactement nulle, avec rejet des D/DD non finis. Les restrictions A86, les tolérances et le traitement non dégénéré restent conservés. Les 105 contrôles mathématiques et la revue de portée sont statiques ; l’application et la compilation sont réalisées uniquement par A91 après son accord explicite distinct. La première dérivation du lanceur, rejetée avant toute exécution, reste archivée.

**A91 compile le onzième moteur isolé en 320,630 s, six CPU, dans le plafond d’une heure.** Zéro Starter, GPU, installation ou prolongement dynamique entier. Les dix anciens moteurs, sorties et critères échoués sont conservés. Le lot utilise trois Engine sur quatre maximum, un CPU et 180 s chacun. Les deux régressions reproduisent exactement les canaux binaires sauvegardés et passent leurs contrôles mécaniques aux seuils d’origine : mouvement libre et aire courante avec Y libre, dans leurs portées respectives.

**Le témoin original de compression–rupture–refermeture termine normalement et sauvegarde 5 201 états jusqu’à 0,65 ms.** Le blocage numérique au second essai est levé : 5 200 marqueurs de garde. Cette durée locale n’est pas une durée d’impact entier. Un problème de sérialisation JSON d’un booléen NumPy a interrompu le premier export d’analyse ; le fichier partiel et l’exception sont conservés, puis l’analyse est récupérée sur les mêmes sorties sans aucun calcul natif supplémentaire ni changement des formules ou seuils.

**La qualification physique reste échouée.** Le plateau initial de compression donne environ 22 000,007 N en valeur absolue, mais celui après rupture et refermeture donne 0 N. Le résidu énergétique calculé vaut au maximum 6,15396457e−5 J pour le seuil inchangé 1e−7 J ; la différence entre énergie cinétique nodale reconstruite et native atteint 3,86075989e−5 J. La précision des sorties et la reconstruction doivent être examinées avant d’attribuer cet écart à la mécanique. La population/sémantique des champs USR et la fermeture indépendante par travail des réactions restent non certifiées. Aucun RKE inventé et aucun seuil relâché.

**Le CHECK entier conditionnel reste inutilisé**, sans réaffectation de sa place. Aucun impact entier prolongé ; cinq contacts TYPE25 ignorés et 107 391 avertissements restent bloquants. A92 doit lire les nouveaux états et les sources exactes pour expliquer la perte de compression après rupture, puis examiner les champs et le bilan indépendant. Une nouvelle modification du moteur ou un autre lot natif exigera une proposition et un accord distinct. Aucune archive historique ni vidéo réanalysée, aucune adaptation aux dégâts connus.

Les [rapports A90](wtc1_simulation_v8/output/aircraft_a90/rapport_aircraft_a90.md) et [A91](wtc1_simulation_v8/output/aircraft_a91/rapport_aircraft_a91.md) séparent les six catégories de preuve. **Meilleur impact entier : 0,0200001220703125 s.** Publication et CI vérifient l’intégrité des fichiers, pas la physique de l’impact réel.


## Ce qui est publié

- `harness/` : état scientifique, registre des expériences, références, contrôles et passations.
- `wtc1_simulation_v8/scripts/` et `data/` : code des calculs et configurations numériques.
- `wtc1_simulation_v8/output/`, dossiers CalculiX et OpenRadioss : résultats, rapports, bilans et diagnostics, y compris essais rejetés.
- `wtc1_3d_v4/` : scripts de visualisation, paramètres, audits et modèles/rendus dans les archives de résultats.
- `outputs/` : calculs exploratoires antérieurs et audits complémentaires. Leurs affirmations se lisent avec leurs propres limites ; leur présence n'est pas une validation.
- `publication/` : inventaire complet, empreintes SHA-256, règles de publication, licences tierces et liste motivée des fichiers externes non redistribués.

Inventaire courant : **24,050 fichiers scientifiques dans Git**, **43,287 sorties dans 150 archives**.

Restaurer les 149 anciennes archives des releases précédentes, puis les 1 archives [A90+A91](https://github.com/WTC-simu2026/WTC-simu2026/releases/tag/snapshot-2026-10-15-aircraft-a90-a91). Manifestes, SHA-256 et URL conservés ; aucune ancienne archive reconstruite ou remplacée.

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

AIRCRAFT-A92 : après publication A90+A91 vérifiée, analyser en lecture seule les nouveaux états A91 sauvegardés et leurs critères encore échoués. Distinguer la garde numérique des cas nuls, les régressions à seuils inchangés, le parcours commandé du coupon et ses qualifications physiques. Ne pas confondre durée locale en millisecondes et impact avion entier. Le coupon atteint0,65ms mais ne transmet plus de compression après refermeture ; tracer les états de suppression et les champs TH dans les sources exactes, puis examiner le bilan indépendant des réactions et sa précision. Ne pas rejouer les diagnostics vérifiés. Aucun nouveau lancement automatique : les places utilisées A91 sont consommées et le CHECK conditionnel inutilisé ne devient pas un crédit générique. Toute autre modification du moteur ou exécution hors lot demande une proposition et un accord distinct. Conserver tolérances, budgets physiques, sources, sorties, critères échoués, cinqTYPE25 ignorés et107391avertissements. Meilleur impact entier0,0200001220703125s ; dix secondes physiques puis vidéo3D incomplètes.


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
