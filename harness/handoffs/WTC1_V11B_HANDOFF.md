# Reprise WTC1 après V11B

État autoritatif : `harness/state.json`. Lire AGENTS.md et l'état, puis lancer `harness/tools/Test-WtcHarness.ps1` depuis le dossier actif. Archives et copies officielles en lecture seule. Les anciennes itérations sont immuables.

## Demande actuelle

Jeremy veut une structure initialement debout, un Boeing767 lancé avec les conditions d'impact documentées, puis des dommages et incendies calculés, sans résultat d'effondrement prédéfini. Il accepte les hypothèses exploratoires et ne demande pas une reconstitution scientifique complète avant toute exécution. Ne pas remplacer les sous-modèles manquants par une animation scénarisée. Ne pas bloquer tout calcul sur une nouvelle liste documentaire.

Il envisage ensuite WTC2 par réutilisation : garder des moteurs communs mais des fichiers de tour et d'événement distincts. La recherche primaire parallèle a confirmé le noyau E–O de WTC1 versus N–S de WTC2 (NCSTAR1-1 p8), des modifications structurelles propres (1-2A tableau2-1 p13) et des conditions d'impact différentes. Les coordonnées, angles et vitesses ont des incertitudes. Estimation vidéo UA175 542±24mph et valeur de cas de base officiel546mph (1-2B vol2 tableau9-2) ne sont pas interchangeables. Aucun modèle WTC2 n'a été créé.

## V11B terminée

Répertoire : `wtc1_simulation_v8/output/v11b_initialization_mass/`.

- Rapport `rapport_v11b_depart_masse.md`, résumé `results_v11b.json`, figure `synthese_v11b_depart_masse.png`.
- `comparison_cases.csv` : 732 scénarios (729 grille +3 nommés).
- `variant_summaries.csv` : 2196 scénarios-variantes ; `outcome_transitions.csv` : migrations de résultats.
- `detailed_energy_mass_momentum_ledger.csv`, `detailed_motion_timeline.csv` : trois scénarios nommés + GRID-0119 dans les trois variantes.
- `corrected_driver.json` : interface étiquetée non appliquée à Blender.
- `scenario_inputs.json`, `initiation_cache_audit.json`, `source_manifest.json`, `numerical_audit.json`, `offline_manifest.json`, `release_audit.json`.

Configuration : `data/v11b_initialization_mass_predeclaration.json`.
Mécanique pure : `scripts/v11b_propagation.py`.
Runner : `scripts/run_v11b_initialization_mass.py`.
Ces chemins sont dans `wtc1_simulation_v8/`.

Exécution CPU Python3.14.3 : environ2,9s, répétition comprise. Aucun GPU, Blender, nouveau logiciel ou accès à l'archive. Le runner refuse un dossier existant ; pour tests, choisir un nouveau sous-dossier de `tmp/v11b_initialization_mass/`. Ne pas relancer le main V10Y ni écraser la version livrée.

## Corrections et conventions

V10Y commençait à t=0 après f·h de chute supposée avec v=sqrt(2gfh). V11B part à x=v=K=0 et compte le temps et le travail résistant dès le premier parcours. À l'étage i, ce parcours vaut f·h, contre F=R_i/h, donc travail fR_i.

Conserver la masse initiale V10Y : M0=(110−i+α)m, α=0,5. Ne pas remplacer α par1−f : fraction de parcours et fraction de masse sont deux hypothèses indépendantes héritées. Après le premier parcours, accréter (1−α)m ; puis les masses entières des étages i−1…1. Le total final en cas de progression vaut110m et non109,5m.

« Masse du bloc » = masse affectée/capturée, y compris quand sa vitesse est nulle. Bloc + non-accrétée =110m dans la version corrigée. Les diagnostics incomplets conservent un troisième compte de masse omise pour montrer ce qui était exclu.

Mouvement : a=g−F/M, v−²=v0²+2ad, dt=2d/(v0+v−). Si arrêt, x=K0/(F−Mg), dt=−v0/a. Un arrêt exactement à la frontière n'entraîne aucune accrétion ni perte de choc.

Capture : v+=Mv−/(M+μ), perte=½Mμ/(M+μ)·v−². Bilans de masse, énergie et impulsion séparés. Kfinal=Wg−WR−pertes, K0=0, travail de la première chute compté une seule fois.

Sans départ : quand v0=0 et F≥Mg, accélération réalisée0, réaction mobiliséeMg, capacité disponibleF conservée. Le champ `potential_acceleration_at_full_resistance_capacity_m_s2` peut être négatif mais n'est pas une accélération effectivement produite. Le seuil thermique franchi reste distinct du départ : aucune vitesse n'est imposée pour franchir cette incompatibilité entre lois simplifiées.

À la limite basse : conserver vitesse et énergie non nulles. Pas de contact avec la fondation, pas de débris stabilisés. Après arrêt, températures/résistances figées au seuil ; aucun chauffage ultérieur ou redémarrage calculé.

## Comparaison contrôlée

Les scénarios, paramètres et moments/niveaux des seuils sont inchangés. Les conditions thermiques identiques sont mises en cache par quintuplet impact/température/réserve/redistribution/pénalité, pas recalculées732fois. Les fonctions historiques sont importées sans exécuter leur main ; leur propagation retrouve les résumés CSV gelés.

Grille729 :

| Variante | Sans seuil | Seuil sans départ | Mouvement puis arrêt | Frontière basse |
|---|---:|---:|---:|---:|
| Temps seul (même résultat que V10Y) |297|0|144|288|
| + résistance initiale, masse encore incomplète |297|90|73|269|
| V11B + masse complète |297|90|54|288|

La résistance initiale arrête19 cas anciennement progressants ; la demi-masse ajoutée rétablit leur progression dans cette loi. Les90 sans-départ étaient auparavant classés arrêtés après la chute supposée. Les comptes de grille ne sont pas des probabilités historiques ; « sans départ » ne démontre pas la stabilité de la tour réelle.

GRID-0119 reste sélectionné uniquement parce qu'il alimentait déjà le film. Pas de nouvelle sélection/calibration chronologique. Seuil5810s, étage96 inchangés. Durée14,126338666s (temps initial absent) →15,048151389s depuis repos. Masse finale350400000→352000000kg (352000tonnes, pas352millions de tonnes). Vitesse finale43,290415107m/s, Kfinal329,834567070GJ. Scénario central19,500577636s et266,893873256GJ ; vulnérable14,466832225s et386,659334695GJ ; résistant sans seuil.

## Vérification

75/75 tests, dont57 tests analytiques/mécaniques et18 contrôles d'ensemble. Résidu max relatif énergie7,2092e−16, impulsion1,5167e−16, masse0. Relecture indépendante des équations puis des2196sorties. Contrôle indépendant à deux étages : g10,h=m1,α=f0,5,R0 → masse2, Wg12,5J, pertes6,875J, Kfinal5,625J, temps0,632455532s.

Empreinte numérique : `858489bd44df431332edb3f2648a071a786cfd8424d56b32610ca1bb1eb06a73`. Vérification séparée :15sorties,9entrées/protégés,3fichiers code/configuration. Deux brouillons graphiques sont conservés : attempt01 courbe dépassant l'axe ; attempt02 titre d'axe chevauchant une graduation. Sortie finale revue, courbes interpolées selon l'accélération constante et axes lisibles.

## Prochaine V11C

Construire un panneau de plancher à partir de V11A, avec appuis déformables, dalle/treillis et liaisons explicites, puis valider sa réponse froide avant températures/déplacements imposés et couplage spatial. Pas de nouveau calcul d'effondrement imposé par des sièges fictivement forts ou faibles.

V11A fournit déjà329tronçons des47colonnes du noyau et553poutres candidates aux étages93–99, trois profils de poutres hypothétiques, quinze détails d'appuis et192variantes de travée. Sa géométrie Warren, ses profils de poutres, le lien parfait de dalle et ses paramètres béton restent des hypothèses. Le modèle de dalle ne résout ni flexion, ni knuckles/goujons, ni rupture réelle des liaisons. Module d'acier limité20–600°C. Voir son handoff sans relire toute l'histoire.

Ne pas convertir une somme de capacités de force ou de travaux de ressorts isolés en énergie d'effondrement. V11B reste une pile1D uniforme de402,336m, distincte du master hétérogène416,9664m. Impact et incendie restent encore des références dépendantes du NIST, pas les sorties d'un767 virtuellement lancé et d'un feu résolu. V10Z reste intacte et affiche l'ancien pilote ; ne pas présenter le film comme déjà mis à jour.
