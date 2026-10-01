# Instantané public du 1er octobre 2026

IMPACT-I02I-A terminée ; prochaine IMPACT-I02I-B. Branche thermique V11R/V11S et contrôle froid V11F préservés.

Cette préversion de recherche contient 4132 fichiers scientifiques versionnés et 7095 fichiers de résultats bruts, répartis dans 23 archives ZIP. Les sorties représentent 18.33 Go d'origine, compressés en 6.69 Go. Les octets de chaque résultat ont été contrôlés après décompression par SHA-256 ; la republication conserve exactement leurs flux compressés. Les tentatives rejetées et diagnostics historiques sont conservés.

Lire le README et les rapports avant d'interpréter les figures. Les tests de traction homogène ne qualifient pas la propagation de fracture ni l'événement réel. Une température imposée n'est pas un incendie calculé ; Blender garde sa portée de visualisation.

## Restaurer les résultats

Télécharger tous les fichiers `results-*.zip` de cette release et, si souhaité, `SHA256SUMS.txt`, puis cloner le dépôt et exécuter :

```powershell
python tools/restore_release_assets.py --archives CHEMIN_VERS_LES_ZIP
python tools/verify_public_snapshot.py --full
```

Les ZIP conservent leurs chemins relatifs. Le restaurateur vérifie les empreintes et refuse d'écraser des fichiers différents. Le manifeste `publication/snapshot_manifest.json` fournit les tailles et SHA-256 de chaque fichier et de chaque archive. Le contrôle automatique GitHub vérifie les fichiers versionnés, sans télécharger les archives et sans lancer de solveur.

Code propre au projet : MIT. Modèle B762 et conversions : GPL-2.0. Données SHPB S355 : CC-BY-4.0. Exemple officiel TWISBEAM : CC-BY-NC-4.0 ; sa restriction non commerciale est conservée. Les licences complètes accompagnent le dépôt et les archives concernées. Les exécutables et documents/médias tiers hors périmètre de redistribution restent externes, avec références et exclusions documentées.

La relance générale de toutes les anciennes itérations reste partiellement dépendante de chemins Windows et de sources externes ; elle n'est pas présentée comme vérifiée dans un environnement propre.
