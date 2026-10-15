# WTC-simu2026

**Construction progressive d'une simulation exploratoire du WTC 1 : impact d'un Boeing 767, incendies et réponse structurelle, jusqu'à un éventuel effondrement ou son arrêt.**

Le projet teste des mécanismes, des hypothèses explicites et des plages de paramètres. Aucun résultat final n'est présupposé. Il s'agit d'une recherche personnelle reproductible, assistée par Codex, dont les modèles, calculs, essais rejetés et limites sont publiés pour être examinés et améliorés.

*English: an open, incremental WTC 1 research harness. Current results concern limited verification models; they do not establish the cause or reproduce the full historical collapse.*

## Où en est la simulation ?

Instantané du **15 octobre 2026** : **AIRCRAFT-A89 terminée**, prochaine **AIRCRAFT-A90**, registre **208 entrées**. **Les dix secondes physiques et la vidéo3D restent à produire.**

**A88 prépare une observation ciblée du second essai avec le moteur A87 inchangé.** Les deux régressions A87 sont conservées à l’identique, mais le coupon n’a qu’un pas accepté. Les positions typées des modes,NCYCLE/TT sont calculées depuis cinq déclarations source épinglées et bornées par les symboles du binaire exact. Treize contrôles source/observateur, cinq du lanceur et dix contrôles finaux passent statiquement ; aucun Engine pendant la préparation. L’ancienne place de CHECK conditionnelle n’est pas réaffectée.

**A89 consomme son unique Engine distinctement autorisé après publication A86+A87 vérifiée.** UnCPU/plafond180s, mêmes cartes/restart initial, zéro Starter/correctif/compilation/GPU/installation/extension entière. Dix-neuf arrêts matériels, lecture seule des données et configuration des registres matériels de débogage seulement. Les points sont désactivés après le critère2 du second essai, puis le moteur termine lui-même. Lecteur code0, Engine code2 sans signal : observation réussie, trajectoire physique échouée. Les anciens libellés consoleA85 sont cosmétiques ; configuration et répertoire A89 sont explicites et conservés.

**Le second essai est maintenant observé avec son cycle/temps natifs.** NCYCLE2,TT0,00025ms ; IDYNA2,IQSTAT0,INSOLV1,NITOL123,ISPRB0,IDTC1,ILAST0,NFXVEL4,NINTER0,IRODDL0,NSPMD1,NTHREAD1,IMCONV0,ICONT0,NDDL8. F libre contient huit zéros exacts,DE0=1e−20,EIMP0,R02=1. U2=DU2=0 aux retours natifs. Au critère2 :URNaN,RR0,ERInfinity ; arrêt79/ISTOP−2.

**La condition sur toute la correction brute exclut les quatre mouvements imposés.** Les seules composantesDD non nulles sont les quatreZ supérieurs imposés,−1,90288107842e−9mm chacune ; D vaut−1,328447181728e−8mm sur cesZ. ALL(DD brut==0) est donc faux malgré une norme libre nulle. R2=0 est reconstruit depuisF nul etIRIKS0 depuisIDTC1 selon le code ; ces deux variables locales n’ont pas été directement lues. Les autres paramètres sont observés. Les dix contrôles de transcription/portée A89 passent.

**A90 doit préparer un contrôle exact de la correction projetée/condensée.** Il ne suffit pas de supprimer la conditionDD ou de tester seulement son carré : un petit non-zéro libre dont le carré sous-déborde doit rester bloquant. Aucun nouveau correctif moteur n’est appliqué ou compilé par A89, aucune tolérance changée. Un nouvel accord distinct sera nécessaire pour une nouvelle modification ou un autre lot.

**Deux états sauvegardés seulement, dernier0,000125ms.** Le temps tenté0,00025ms n’est pas un état accepté. Rupture, plateaux et refermeture non atteints ; aucun crédit nouveau sur l’impact entier. L’unique Engine A89 est consommé, sans réessai. Anciennes sorties, budgets, critères échoués, cinqTYPE25 ignorés et107391avertissements restent conservés ; aucune archive historique ou vidéo réanalysée, aucun RKE inventé ou ajustement aux dégâts connus.

Les [rapports A88](wtc1_simulation_v8/output/aircraft_a88/rapport_aircraft_a88.md) et [A89](wtc1_simulation_v8/output/aircraft_a89/rapport_aircraft_a89.md) séparent les six catégories de preuve. **Meilleur impact entier0,0200001220703125s.** Publication/CI attestent l’intégrité, pas la validation physique de l’impact réel.


## Ce qui est publié

- `harness/` : état scientifique, registre des expériences, références, contrôles et passations.
- `wtc1_simulation_v8/scripts/` et `data/` : code des calculs et configurations numériques.
- `wtc1_simulation_v8/output/`, dossiers CalculiX et OpenRadioss : résultats, rapports, bilans et diagnostics, y compris essais rejetés.
- `wtc1_3d_v4/` : scripts de visualisation, paramètres, audits et modèles/rendus dans les archives de résultats.
- `outputs/` : calculs exploratoires antérieurs et audits complémentaires. Leurs affirmations se lisent avec leurs propres limites ; leur présence n'est pas une validation.
- `publication/` : inventaire complet, empreintes SHA-256, règles de publication, licences tierces et liste motivée des fichiers externes non redistribués.

Inventaire courant : **19,677 fichiers scientifiques dans Git**, **41,871 sorties dans 149 archives**.

Restaurer les 148 anciennes archives des releases précédentes, puis les 1 archives [A88+A89](https://github.com/WTC-simu2026/WTC-simu2026/releases/tag/snapshot-2026-10-15-aircraft-a88-a89). Manifestes, SHA-256 et URL conservés ; aucune ancienne archive reconstruite ou remplacée.

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

AIRCRAFT-A90 : après publication A88+A89 vérifiée, préparer en lecture seule une garde de correction nulle sur coordonnées libres projetées/condensées. A89 observeNCYCLE2/TT0,00025ms, tous modes admissibles, forces libres0,EIMP0,DE0=1e−20,U2=DU2=0 mais quatreDD Z imposés−1,90288107842e−9mm ; ALLDD brut exclut ce cas alors que la projection native est nulle. Ne pas supprimer la garde de correction : vérifier exactement son vecteur projeté pour rejeter un petit non-zéro dont le carré sous-déborde. Aucun nouveau correctif appliqué/compilé ; accord distinct requis. Un EngineA89consommé, aucun réessai, CHECK A87 inutilisé non réaffecté. Conserver toutes sorties, critères échoués, budgets et contacts bloquants. Meilleur impact entier0,0200001220703125s ; dix secondes physiques puis vidéo3D incomplètes.


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
