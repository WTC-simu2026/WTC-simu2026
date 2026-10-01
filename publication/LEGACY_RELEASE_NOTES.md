# Diagnostics numériques historiques et helpers

Complément de l'instantané IMPACT-I02I-A, sans changement de l'état scientifique. Le [premier instantané](https://github.com/WTC-simu2026/WTC-simu2026/releases/tag/snapshot-2026-10-01-impact-i02i-a) inclut désormais ces diagnostics dans une seule release.

1214 fichiers supplémentaires (1.20 Go originaux) sont conservés : anciens préflights, essais interrompus, tentatives rejetées et brouillons des étapes V8/V10/V11. Les scripts, configurations et rapports courts sont dans Git ; les autres fichiers sont dans 2 ZIP supplémentaires. Il peut y avoir des copies identiques de résultats finaux : leurs chemins historiques et leurs octets sont conservés.

Ces sorties temporaires ne sont pas promues en calculs validés. Les rapports finaux, le registre et `harness/state.json` restent les points de référence. Aucun ancien calcul n'a été relancé.

Télécharger aussi les 21 ZIP du premier instantané dans le même dossier, puis exécuter `python tools/restore_release_assets.py --archives CHEMIN_VERS_LES_ZIP` et `python tools/verify_public_snapshot.py --full`. Le manifeste de la branche `main` contient les empreintes ; les 23 ZIP sont regroupés dans une même release.

Le code propre au projet reste MIT ; les licences amont déjà indiquées sont conservées. Les sources documentaires, vidéos, images d'archive et caches d'extraction ne sont pas intégrés à ce complément. Les helpers historiques conservent leurs prérequis locaux et ne doivent pas être exécutés sans adapter leurs chemins et respecter la lecture seule des sources.
