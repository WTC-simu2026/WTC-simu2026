# WTC1 — passation V11M vers V11N

Lire `AGENTS.md`, `harness/state.json`, puis cette passation. L’état local prévaut sur les anciennes reprises V8H/V11H. Exécuter `harness/tools/Test-WtcHarness.ps1` depuis la racine avant/après les modifications importantes. Sources et anciennes itérations en lecture seule.

## V11M achevée, qualification mécanique partielle

Sorties : `wtc1_simulation_v8/output/v11m_early_thermal/`. 17 fichiers publiés identiques à `tmp/v11m_early_thermal/attempt_003`, puis audit final relu : **53/53 contrôles, 101/101 audits**. Ce PASS valide les sorties bornées et la déclaration des rejets, pas tous les transferts prévus.

- Six historiques de conduction sur 0–90 s, sauvegardés à chaque pas : 64 cellules × 80/160/320/640 pas ; 128 et 256 cellules × 640 pas.
- Dix chemins mécaniques acceptés, 845 états ; quatre transferts rejetés avant d’être crédités. Contrôle V11F préservé ; V11F/H/I/K/L vérifiés par empreintes, anciens pilotes complets non relancés.
- Empreinte numérique : `2a48908a974fe79b717b21df7b5a796a3c6dc78d2995a9d437520b6b316d2123`.
- Panneau inchangé : 4 subdivisions, 160 fibres béton + 2 couches d’armatures, précharge 0,25 gravité. Treillis et assemblages froids. Aucun historique de dommage modifié.

## Résultats utiles

À 64 cellules, pas thermique 0,140625 s et profils transférés toutes les 1,125 s : garde-fou DCR=0,9 à **61,473404 s**. Avec tous les profils : **61,471234 s** (écart 0,003530 %). V11L donnait 64,576253 s ; à nouveau pas thermique mais profils espacés de 45 s : 64,253572 s. La fréquence de sauvegarde avait donc un effet distinct du pas de calcul.

Dernière division par deux du pas thermique : changement du garde-fou 0,105140 %. Le diagnostic des sondes de face ne change pas ce garde-fou à 64 cellules : la traction intérieure du béton gouverne. Aucun de ces nombres n’est un temps de rupture du WTC.

Référence : U=272,419238 J ; Wext=95,390435 J ; Wth=177,028803 J ; réaction verticale=35 239,800130 N. Résidu énergétique mécanique relatif maximal 3,834e-11 ; équilibre 3,777e-9. Coupon étendu : 16 976 354,328 J ; composite : 16 942 780,515 J ; écart −33 573,814 J, non compensé.

Conduction seule, 128→256 cellules à 90 s : différence de température de surface haute −0,025177 K ; changement d’enthalpie 0,030400 %. La comparaison mécanique en profondeur reste **indéterminée**, pas validée.

## Rejet à traiter en priorité

La correction héritée des fibres `T*(1+a+b*y/h)` conserve moyenne et gradient équivalent, mais peut produire une queue négative. À la première entrée mécanique planifiée de 1,125 s : minimum proposé −2,57e-10 K pour 128 cellules et −2,61e-8 K pour 256 cellules, sous le seuil inchangé −1e-10 K. Les variantes FACE correspondantes sont aussi rejetées. Aucun temps de garde-fou ne leur est attribué.

Les diagnostics de **tous** les pas thermiques montrent un problème plus fondamental à 256 cellules, t=0,140625 s : barycentre thermique cible eta=0,497007140334, au-delà de la fibre extrême eta=0,496875. Sur ces 160 fibres fixes, aucune température non négative ne peut alors conserver simultanément les deux moments demandés. Cela ne signifie pas qu’un champ physique positif est impossible : c’est une incompatibilité de quadrature/transfert. Le minimum proposé est alors environ −0,006398 K, jamais engagé en mécanique.

Ne pas tronquer les températures négatives, relâcher le seuil ou modifier les propriétés pour faire passer ces cas. Une projection positive seule ne résout pas un moment cible hors du support des fibres.

## Reprise V11N

1. Réutiliser les six historiques V11M : aucune nécessité de recalculer la conduction.
2. Qualifier sur des coupons la projection positive conservant les moments ; vérifier explicitement sa faisabilité sur le support discret. Raffiner/adapter les fibres si nécessaire, puis comparer les réponses et énergies avec les chemins acceptés V11M et le contrôle froid V11F.
3. Traiter ensuite les faces dans une reconstruction continue conservative, avec contrôle des très premiers instants et de la quadrature. FACE dans V11M ne remplace que les sondes sans volume : ce n’est pas cette reconstruction.
4. Croiser les raffinements thermiques/mécaniques avant toute fissuration chaude ; garder les bilans de chaleur sensible et de travail thermoélastique séparés.

## Fichiers et essais conservés

Configuration : `wtc1_simulation_v8/data/v11m_early_thermal.json` ; scripts : `v11m_early_thermal.py`, `run_v11m_early_thermal.py`, `audit_v11m_early_thermal.py` dans `wtc1_simulation_v8/scripts/`.

Dans les sorties finales, lire d’abord `results_v11m.json`, `rapport_v11m.md`, `rejected_transfers.json`, puis au besoin `mapping_diagnostics.json`, `comparisons.json`, `panel_runs.json` et le fichier thermique exact `C*_S*.json`. Audit sans écriture : `python wtc1_simulation_v8/scripts/audit_v11m_early_thermal.py --output wtc1_simulation_v8/output/v11m_early_thermal --read-only`. Utiliser `OPENBLAS_NUM_THREADS=1` et `PYTHONDONTWRITEBYTECODE=1`.

Tentative 001 : arrêt scientifique sur positivité, six historiques et quatre chemins conservés, entrées figées dans `input_snapshot/`. Tentative 002 : dix chemins et quatre rejets déclarés ; 52/53 contrôles, contrôle d’identité perturbé de 1,4e-10 DCR par un nouveau solveur Newton. Son premier audit avait aussi une erreur de conversion liste/tableau. Entrées conservées. Tentative 003 : même calcul physique en cache, identité comparée au **même déplacement sauvegardé**, audit corrigé ; aucun seuil relâché. Production depuis le cache : 5,35 s. Les tentatives/cache sont référencées par empreintes : les conserver.

## Limites permanentes

Exposition `synthetique_non_WTC`, constantes génériques héritées, pas d’incendie calculé ni de calibration à l’événement réel. Transfert thermique unidirectionnel, différence de capacité thermique du composite explicite, pas de premier principe couplé fermé. Pas de fissuration chaude, de flambement géométrique, de dynamique globale ni d’effondrement validé. Localisation en flexion après fracture complète non validée. Blender inchangé, toujours une visualisation ; crédit énergétique global nul.
