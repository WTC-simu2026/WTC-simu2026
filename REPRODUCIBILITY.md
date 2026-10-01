# Vérification et reproduction

## 1. Vérifier l'instantané public

Python 3.10 ou plus suffit aux outils de publication, sans bibliothèque supplémentaire :

```powershell
python tools/verify_public_snapshot.py
python tools/restore_release_assets.py --archives CHEMIN_VERS_LES_ZIP
python tools/verify_public_snapshot.py --full
```

Le mode normal vérifie seulement les fichiers Git ; le mode `--full` exige également tous les fichiers de résultats fournis en release. Les exclusions documentaires ne deviennent pas des échecs de l'intégrité publique. Le contrôle affiche ce qu'il a réellement vérifié.

## 2. Lire une expérience

Partir de `harness/state.json` et de la passation correspondante. Une ligne de `harness/experiments/registry.jsonl` pointe vers la configuration, le rapport et les sorties. Lire la configuration avant les résultats, notamment les unités, sources, graines et critères. Les tentatives rejetées et les contrôles négatifs sont conservés.

La passation courante est `harness/handoffs/WTC1_IMPACT_I02I_A_HANDOFF.md`. Le dernier audit final est `wtc1_simulation_v8/output/impact_i02i_material/verification_r4/summary_i02i_material.json`. Ne pas confondre les audits intermédiaires rejetés avec cet audit final.

## 3. Environnement des calculs

La dernière étape a été exécutée sous Windows avec Python 3.14.3, NumPy 2.4.6, Pillow 12.2.0 et le runtime OpenRadioss Windows `v20260728-win64`. Les autres étapes décrivent leur propre environnement dans leurs journaux ; ces versions ne prouvent pas à elles seules la compatibilité de tous les calculs historiques.

`requirements.txt` donne les dépendances Python de base ; `requirements-optional.txt` liste les bibliothèques utilisées par certaines extractions/figures. Les outils de vérification publique n'en ont pas besoin. `bpy` et `mathutils` proviennent de Blender ; `vtkmodules` provient de ParaView/VTK dans les visualisations concernées.

OpenRadioss est à obtenir depuis [ses releases](https://github.com/OpenRadioss/OpenRadioss/releases), CalculiX depuis [son site](https://www.calculix.de/), Blender depuis [blender.org](https://www.blender.org/download/) et ParaView depuis [paraview.org](https://www.paraview.org/download/). Les bibliothèques et exécutables installés ne sont pas inclus dans la release de ce projet.

Les configurations historiques précisent les empreintes des exécutables utilisés et les chemins attendus. La V8T documente la création d'un dossier runtime isolé pour éviter une ancienne DLL OpenMP système ; ne pas modifier le système pour contourner cette difficulté. Certaines itérations utilisent des chemins tels que `C:/Python314`, `C:/OpenRadioss` ou une installation Blender locale : leur adaptation doit être faite dans une **nouvelle configuration**, avec versions et empreintes enregistrées.

## 4. Contrôles historiques et limites de portabilité

`harness/tools/Test-WtcHarness.ps1` est conservé tel quel. Ce contrôle local attend notamment une configuration Codex privée, des PDF de `work/official_sources/`, des archives locales et le runtime installé. **Il n'est pas le contrôle d'un clone public incomplet.** Utiliser le vérificateur public ci-dessus pour ce dernier.

De même, `complete_impact_i02i_material.py --verify` vérifie des empreintes locales dont certaines références documentaires sont externes au dépôt. Ce script est publié comme partie de la chaîne historique, sans promettre qu'il passe avant restauration des prérequis concernés. Son exécution ne doit pas enregistrer à nouveau une itération déjà enregistrée.

Le premier instantané apporte une intégrité vérifiable et les calculs conservés. Il reste à rendre la relance générale portable, à automatiser l'acquisition des sources autorisées et à vérifier cette relance dans un environnement propre. Ne pas qualifier cette relance complète de vérifiée avant ce travail.

## 5. Nouvelle expérience

Ne pas écraser une ancienne sortie. Créer un identifiant et une configuration avec unités, sources, graines, coût et critères pré-déclarés. Conserver le script, les journaux, les résultats et le rapport. Contrôler l'énergie et l'historique d'un matériau endommagé avant toute modification de propriétés. Actualiser le registre, l'état et la passation seulement après vérification.

Annoncer toute campagne susceptible de durer plusieurs heures. Un calcul en cache vérifié est préférable à une relance inutile. Une étape mécanique validée sur un cas réduit conserve sa portée réduite.
