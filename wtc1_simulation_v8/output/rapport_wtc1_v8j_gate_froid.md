# WTC 1 - V8J : gate froid et audit du chemin de charge manquant

## Resultat principal

V8J reproduit le cas post-impact entierement froid de V8I sans changer sa resistance. Le premier echec n'est pas une surcharge globale : au niveau 96, sept aretes du proxy poutre+dalle se rompent et isolent les colonnes 503, 504, 505 et 604, deja retirees comme appuis verticaux dans le damage set Case B. Cette composante conserve une charge de **3256 kip**, soit **9.5 %** de la demande noyau de 34 429 kip, mais ne possede plus d'appui survivant dans le graphe V8I.

Ce diagnostic invalide une interpretation precedente trop simple : V8I ne dit pas que le noyau reel etait globalement trop faible a froid. Il dit que la topologie nearest-four du sous-modele ne contient pas le chemin reel qui a redistribue cette charge. Le gate froid reste donc **non valide** et aucune transition thermique ni animation Blender n'est autorisee a partir de ce reseau.

## Faits et sorties officielles

- NIST donne environ 16 kip de charge de service par siege supportant une paire de fermes; a 20 C, les capacites verticales des sieges exterieurs publies vont de 94 a 207 kip.
- NIST rapporte 38 poteaux sur 59 severes ou lourdement endommages sur la facade nord, ainsi que de graves dommages aux planchers nord entre les colonnes 112 et 145 sur les niveaux 94 a 98.
- Immediatement apres impact, le changement de charge du noyau publie est +400 kip aux niveaux 98 et 105. Le differentiel est donc nul : le hat truss redistribue les charges de facade, mais NIST ne montre pas a cet instant de delestage net supplementaire du noyau entre ces deux niveaux.
- A 80 min, NIST montre au contraire un transfert thermique net d'environ 6 748 kip du noyau vers les facades; l'outrigger E atteint un DCR de 0,97. Ce resultat tardif ne peut pas etre credite au cas froid sans double comptage.

## Observations provenant des archives locales

- L'inventaire en lecture seule de `FloorTrussSystems-20260813T183023Z-1-001.zip` contient 522 fichiers, tous images ou videos; il ne contient aucun fichier de modele ou de mesures tabulaires.
- Une recherche par noms de fichiers dans le depot local n'a pas trouve WTCAB, Drawing Book 5/6, BeamSched, C32T1 ni de fichier de solveur structurel avec les extensions testees. Cette recherche ne prouve pas que ces donnees sont absentes de toute archive compressee non inspectee.

## Resultats derives du sous-modele

| Cas de dalle | Demande froide maximale encore stable | Deficit par rapport a 34 429 kip |
|---|---:|---:|
| no_slab_v8h_reference | 11940 kip | 22489 kip |
| high_ratio_full_area | 11954 kip | 22475 kip |
| cold_upper_envelope | 11954 kip | 22475 kip |

La valeur maximale stable est un seuil du proxy, pas une capacite as-built. Dans le cas froid superieur, la rupture du cut-set isole exactement quatre noeuds sans appui; le chargement isole vaut 3256 kip.

## Ecran de capacite des sieges de plancher

| Detail de siege exterieur | Capacite par paire a 20 C | Paires requises | 31 paires, face intacte | 11 paires, proxy nord endommage |
|---|---:|---:|---:|---:|
| #1013 | 94 kip | 35 | 2914 kip (echoue) | 1034 kip (echoue) |
| #1111 | 94 kip | 35 | 2914 kip (echoue) | 1034 kip (echoue) |
| #1212 | 111 kip | 30 | 3441 kip (passe) | 1221 kip (echoue) |
| #1311 | 94 kip | 35 | 2914 kip (echoue) | 1034 kip (echoue) |
| #1313 | 94 kip | 35 | 2914 kip (echoue) | 1034 kip (echoue) |
| #1411 | 140 kip | 24 | 4340 kip (passe) | 1540 kip (echoue) |
| #1511 | 193 kip | 17 | 5983 kip (passe) | 2123 kip (echoue) |
| #1611 | 207 kip | 16 | 6417 kip (passe) | 2277 kip (echoue) |

Le proxy d'une face nord reduite a 11 paires ne couvre pas le cut-set, meme avec le siege exterieur le plus resistant publie. Une face intacte de 31 paires couvre la demande pour certains details, mais pas pour les quatre details a 94 kip. Cette comparaison reste une enveloppe de capacite : elle ne fournit ni la rigidite, ni la deformation ultime, ni l'affectation des details, ni la carte de survie des fermes.

## Hypotheses propres a V8J

- Le nombre 31 vient de la largeur de tour divisee par la largeur tributaire de 6,67 ft d'une paire de fermes. Le nombre 11 est un simple prorata des 21 poteaux nord non classes severes/lourdement endommages; il ne remplace pas une carte siege par siege.
- Le cut-set provient de la topologie nearest-four et des lois force-deplacement V8I. Il identifie une exigence de transfert du proxy, pas la geometrie du plancher reel.
- Aucune capacite de siege n'est transformee en ressort vertical noyau-facade. Cette conversion exigerait la raideur de la ferme, sa geometrie, ses appuis, sa ductilite, le comportement de dalle composite et la survie apres impact.
- Le hat truss est separe en chemin froid et chemin thermique. Le credit froid impose est 0 kip; la capacite calibree NIST d'environ 6957 kip reste une verification interne du modele officiel, pas une capacite independante.

## Contradictions et informations manquantes

- Le resultat observe - la tour reste debout - contredit le reseau V8I/V8J s'il est traite comme chemin autonome. Il ne contredit pas encore une structure reelle qui contenait des poutres, dalles, fermes, facades et assemblages absents du proxy.
- La nomenclature Drawing Book 5 des poutres du noyau, les connexions Drawing Book 6, l'affectation des huit details de sieges du niveau 96 et une carte des fermes survivantes ne sont pas disponibles dans le corpus de travail actuel.
- NIST fournit des modeles globaux a diaphragmes equivalents et des modeles de sous-systemes, mais pas dans les pages inspectees une loi reduite force-deplacement directement transposable au cut-set 503-504-505-604.
- La prochaine iteration doit reconstruire la vraie topologie des poutres/assemblages du niveau 96 ou obtenir les fichiers de Drawing Book 5/6. Tant que ce chemin n'est pas specifie, augmenter une resistance abstraite serait du calibrage circulaire.

## Decision du gate

**NON VALIDE.** V8J localise et quantifie le chemin manquant, mais ne demontre pas encore une loi force-deplacement survivante capable de porter les 3256 kip. Les cas thermiques et Blender restent suspendus a cette verification.

Temps d'execution : 9.93 s. Configuration, diagnostic du graphe, enveloppes de capacite et sources sont conserves dans le JSON V8J.
