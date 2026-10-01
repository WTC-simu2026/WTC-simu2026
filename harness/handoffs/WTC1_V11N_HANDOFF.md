# WTC1 — passation V11N vers V11O

Lire `AGENTS.md`, `harness/state.json`, puis cette passation. L’état local prévaut sur les anciennes mentions V8H/V11H. Exécuter `harness/tools/Test-WtcHarness.ps1` avant/après toute modification importante. Sources et anciennes itérations en lecture seule ; aucune nouvelle analyse d’archive nécessaire ici.

## V11N achevée sur éprouvettes, raccord initial non validé

Sorties : `wtc1_simulation_v8/output/v11n_positive_transfer/`. 13 fichiers publiés identiques à la tentative 002, audit final relu : **74/74 contrôles, 448/448 audits**. Empreinte numérique : `a642bcc89419f0fff5555128f7b989350931f4041fd618096033c15ae69e94fe`.

- Trois historiques V11M réutilisés : `C64_S640`, `C128_S640`, `C256_S640`. Aucun recalcul de conduction ni ancien pilote complet relancé ; contrôle froid V11F conservé par empreintes, références de section V11H comparées.
- Deux reconstructions × trois historiques × 641 instants × trois résolutions de fibres : **11 538 combinaisons**, dont 11 526 supportées et 12 explicitement rejetées.
- **320 et 640 fibres supportent tous les 640 instants positifs** des deux reconstructions et trois maillages thermiques testés. Cela ne qualifie pas tout instant arbitrairement proche de zéro.
- 60 éprouvettes de section libre/entièrement empêchée avec cycles d’amplitude synthétiques. **6 dépassent la résistance froide en traction** : leur bilan est une identité algébrique, pas une validation matérielle élastique. Pas de nouveau chemin du panneau, de nouveau garde-fou ou de fissuration chaude.

## Méthode et résultats

La reconstruction `surface_cell_conservative` respecte chaque moyenne de cellule et les températures de surface sauvegardées. Les faces internes valent la moyenne des cellules adjacentes limitée à deux fois la plus petite. Des rampes symétriques encadrent un plateau dont l’intégrale est fixée par la moyenne. Elle reste positive ; les champs affines restent affines. Sa forme sous-maille est une hypothèse numérique, pas un champ exact de conduction.

La projection positive est une pondération exponentielle des températures brutes : `T_i=n*m0*softmax(log(raw_i)+beta*eta_i)`. Les zéros restent nuls. Beta impose le barycentre thermique ; les cibles hors du support des fibres positives sont rejetées. On conserve la moyenne et le **gradient équivalent**, selon la convention V11L, et non le moment absolu exact : l’écart de quadrature est enregistré. Les armatures échantillonnent le profil continu sans correction.

Erreurs maximales : moyenne 1,78e-15 K ; gradient équivalent 3,32e-13 K ; moyenne par cellule 1,07e-13 K ; faces 0 K. Résidu énergétique relatif maximal des cycles 1,48e-15 ; retour énergétique 0 J/m. Propriétés et historiques endommagés inchangés. Les propriétés de fibres effectivement utilisées sont dans `section_inventory.json`.

Exemple à 256 cellules, 640 fibres, profil à 90 s : section empêchée, énergie 15,506861 J/m, travail thermique identique, réactions +107 050,803 N et −5 383,835 N·m. Enthalpie composite 1 340 696,235 J/m ; écart composite moins coupon brut −2 540,657 J/m. Section libre : énergie 10,443994 J/m mais traction/ft20=1,17290, donc hors du domaine physique élastique revendicable. Ce n’est pas une rupture calculée.

## Les 12 rejets et le problème initial

- 9 rejets correspondent à **t=0**, nouvelle reconstruction × trois maillages × trois nombres de fibres. Les cellules ont une moyenne thermique nulle, mais la surface sans masse a déjà un incrément algébrique de 7,098210 K, 3,593311 K ou 1,807872 K (64/128/256 cellules). Un champ continu non négatif de moyenne nulle ne peut satisfaire cette face positive.
- 3 rejets à t=0,140625 s concernent 160 fibres : ancienne reconstruction à 256 cellules ; nouvelle reconstruction à 128 et 256 cellules. Les barycentres sont inaccessibles. Raffiner à 320 résout ces cas sauvegardés.

Aucune température n’a été tronquée, aucun seuil relâché, aucune face initiale remplacée silencieusement et aucune chaleur fictive ajoutée. Le contrôle séparé tout-froid ne résout pas le raccord initial du champ imposé.

## V11O — prochaine étape bornée

Définir et qualifier le raccord entre état froid, surface algébrique sans masse et transfert positif aux premières fractions de seconde. Distinguer état avant le palier, limite après le palier et premier pas sauvegardé ; ne pas faire passer une convention d’initialisation pour une donnée physique. Vérifier faisabilité de projection, continuité/limites des charges, réactions et énergie. Réutiliser les historiques V11M et les résultats V11N.

Ensuite seulement, intégrer le transfert qualifié au panneau élastique : contrôle froid V11F, comparaison avec les chemins V11M acceptés, raffinement croisé thermique/fibres/longitudinal et arrêt au garde-fou. Ne pas prétendre que le seul succès sur les instants sauvegardés résout ce raccord ou une histoire continue.

## Fichiers et reproductibilité

Configuration : `wtc1_simulation_v8/data/v11n_positive_transfer.json`. Scripts dans `wtc1_simulation_v8/scripts/` : `v11n_positive_transfer.py`, `run_v11n_positive_transfer.py`, `audit_v11n_positive_transfer.py`, `package_v11n_positive_transfer.py`.

Lire d’abord `results_v11n.json`, `rapport_v11n.md`, puis `projection_sweep.json` pour les rejets précis, `selected_details.json` pour les champs complets sélectionnés, `section_coupons.json` pour contraintes/travaux/réactions et `reconstruction_checks.json` pour les 3 846 reconstructions. L’audit indépendant reconstruit tous les instants, reprend les pondérations positives et vérifie les champs détaillés ainsi que les bilans de section sans importer le modèle testé.

Audit sans écriture : `python wtc1_simulation_v8/scripts/audit_v11n_positive_transfer.py --output wtc1_simulation_v8/output/v11n_positive_transfer --read-only`. Utiliser `OPENBLAS_NUM_THREADS=1` et `PYTHONDONTWRITEBYTECODE=1`.

Tentative 001 : calcul physique/numérique, 25,60 s CPU, 74 contrôles et premier audit de 447 vérifications. Entrées figées dans `input_snapshot/`. Tentative 002 : données numériques identiques, audit étendu à tous les instants (448 vérifications), reconditionnement sans relancer les éprouvettes. Conserver ces tentatives : leurs empreintes participent à la provenance.

## Limites permanentes

Exposition synthétique non WTC ; aucun incendie calculé, aucune conclusion historique. Bilans de chaleur sensible et de travail thermoélastique séparés, écart composite explicite, premier principe couplé non fermé. Pas de fissuration chaude, de dynamique globale ni d’effondrement validé. Localisation en flexion après fracture complète non validée. Blender inchangé, toujours une visualisation ; crédit énergétique global nul.
