# WTC-simu2026

**Construction progressive d'une simulation exploratoire du WTC 1 : impact d'un Boeing 767, incendies et réponse structurelle, jusqu'à un éventuel effondrement ou son arrêt.**

Le projet teste des mécanismes, des hypothèses explicites et des plages de paramètres. Aucun résultat final n'est présupposé. Il s'agit d'une recherche personnelle reproductible, assistée par Codex, dont les modèles, calculs, essais rejetés et limites sont publiés pour être examinés et améliorés.

*English: an open, incremental WTC 1 research harness. Current results concern limited verification models; they do not establish the cause or reproduce the full historical collapse.*

## Où en est la simulation ?

Instantané du **4 octobre 2026** : **IMPACT-I02I-I terminée comme campagne bornée avec quatre échecs de signe brut**, prochaine étape **IMPACT-I02I-J**. Le registre contient 116 entrées. Les mentions V8H/V11H sont historiques.

H vérifie quatre états neufs : contrôles élastiques libres à 25/12,5 ns (champs bruts ≤1 %) puis séparation normale libre à 50/25 ns et mouvement ensuite sans force. 122/122 critères de cas, 14/14 comparaisons et 9/9 références. I ajoute quatre états neufs d'arrêt et retour sans séparation : **170/174 critères**, 16/16 comparaisons et 16/16 références. Les quatre échecs concernent IE−U légèrement négatif ; ils restent échoués. Le diagnostic est compatible avec l'arrondi, sans preuve de l'algorithme interne ni changement de seuil. Ces témoins restent numériques, sans calibration physique.

Lire les [rapports H](wtc1_simulation_v8/output/impact_i02i_free_fracture/rapport_impact_i02i_free_fracture.md) et [I](wtc1_simulation_v8/output/impact_i02i_free_return/rapport_impact_i02i_free_return.md), la [vérification d'intégrité I](wtc1_simulation_v8/output/impact_i02i_free_return/publication_verification.json) et la [passation J](harness/handoffs/WTC1_IMPACT_I02I_I_HANDOFF.md). Les cinq échecs OFF/FX F, les huit diagnostics historiques G et les sensibilités/couvertures E restent ouverts. V11F et V11R → V11S sont conservés. Impact complet Boeing/façade, incendie et effondrement réel non qualifiés.

## Ce qui est publié

- `harness/` : état scientifique, registre des expériences, références, contrôles et passations.
- `wtc1_simulation_v8/scripts/` et `data/` : code des calculs et configurations numériques.
- `wtc1_simulation_v8/output/`, dossiers CalculiX et OpenRadioss : résultats, rapports, bilans et diagnostics, y compris essais rejetés.
- `wtc1_3d_v4/` : scripts de visualisation, paramètres, audits et modèles/rendus dans les archives de résultats.
- `outputs/` : calculs exploratoires antérieurs et audits complémentaires. Leurs affirmations se lisent avec leurs propres limites ; leur présence n'est pas une validation.
- `publication/` : inventaire complet, empreintes SHA-256, règles de publication, licences tierces et liste motivée des fichiers externes non redistribués.

Inventaire courant : **5,209 fichiers scientifiques dans Git**, **7,392 sorties dans 43 archives**.

Restaurer les 23 archives [A](https://github.com/WTC-simu2026/WTC-simu2026/releases/tag/snapshot-2026-10-01-impact-i02i-a), les 4 archives [B+C](https://github.com/WTC-simu2026/WTC-simu2026/releases/tag/snapshot-2026-10-03-impact-i02i-c), les 14 archives [D+E](https://github.com/WTC-simu2026/WTC-simu2026/releases/tag/snapshot-2026-10-03-impact-i02i-e), l'archive [F+G](https://github.com/WTC-simu2026/WTC-simu2026/releases/tag/snapshot-2026-10-04-impact-i02i-g), puis les 1 archives [H+I](https://github.com/WTC-simu2026/WTC-simu2026/releases/tag/snapshot-2026-10-04-impact-i02i-i). Les manifestes conservent les SHA-256 et URL ; les anciennes archives ne sont pas remplacées.

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

IMPACT-I02I-J : établir la précision des sorties binaires T01/CSV sauvegardées et examiner IE−U sans relancer les anciens calculs. Conserver les quatre échecs I et toutes les limites E/F/G. Toute nouvelle mesure de précision doit être pré-déclarée ; aucun clipping, déphasage ou substitution de propriété sur état endommagé. Les modes mixtes libres et la calibration physique restent différés, ainsi que Gf15/60.

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
