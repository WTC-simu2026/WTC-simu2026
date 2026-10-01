# Harnais WTC 1

Ce dossier transforme l'espace de travail existant en environnement de recherche reproductible. La conversation Codex reste dans sa tâche actuelle ; son état utile est condensé dans `state.json` afin qu'une future reprise n'ait pas besoin de relire tout l'historique.

## Organisation

- `state.json` : point de reprise scientifique et technique.
- `sources.json` : racines de sources et politique de lecture seule.
- `experiments/registry.jsonl` : registre append-only des itérations validées.
- `snapshots/source_hashes.json` : empreintes des principales sources officielles.
- `tools/Test-WtcHarness.ps1` : contrôle rapide du harnais et des livrables.
- `logs/` : journaux techniques futurs ; jamais les documents sources.

## Utilisation

Avant une itération importante :

```powershell
pwsh -NoProfile -File .\harness\tools\Test-WtcHarness.ps1
```

Après validation, ajouter au registre l'identifiant de l'expérience, son script, ses paramètres, ses entrées et ses sorties. Ne pas remplacer une ligne antérieure.

## Ce que ce harnais ne fait pas

Il n'ajoute ni précision physique, ni puissance de calcul, ni données manquantes. Il améliore la traçabilité, la répétabilité, la sécurité des archives et la continuité entre les itérations.
