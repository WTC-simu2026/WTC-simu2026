# Proposition A55 pour A56 — tampon temporaire cohésif

Cette proposition est préparée, non appliquée et non compilée. Elle exige un nouvel accord explicite ; l'accord donné pour le correctif A53 ne couvre pas cette modification.

## Faits directement observés

Sur le moteur A54 intact, l'en-tête de l'allocation NODREAC passe de0x31 à0 à l'écriture SRCOORK+0x4488, puis free déclenche SIGABRT. La capture R2 observe NEL=1, IGTYP=43, ISMSTR=1, JHBE=0, JCVT=1 et SAV voisin de l'allocation corrompue. Le processus s'arrête à NC=0/T=0. Les sorties et tentatives d'observation sont conservées.

## Source du logiciel

SRCOORK déclare SAV(NEL,21). S8ZKE3 lui transmet GBUF%SMSTR ; l'allocation temporaire implicite actuelle utilise NEL*G_SMSTR. L'insuffisance de capacité est une inférence de ce contrat et de la corruption observée. La valeur native du descripteur G_SMSTR n'a pas été lue. Aucune validation historique n'en découle.

## Archives locales

Aucune nouvelle archive historique consultée ou modifiée.

## Hypothèse et modification proposée

Dans alloc_elbuf_imp.F uniquement, réserver au moins21*NEL valeurs pour le tampon SMSTR temporaire des TYPE43 et initialiser le complément à0.0D0 si l'allocation réussit. Les autres types gardent leur dimension. Le dimensionnement source/restart, masses, matériaux, inerties, contacts et chargements restent inchangés. La dynamique et les critères physiques restent à qualifier ; aucune erreur de volume n'est supprimée.

## Contrôles préparatoires

48 cas arithmétiques de capacité et bornes passent ; lignes ajoutées limitées à72 colonnes et empreintes enregistrées. Cela ne remplace pas une compilation Fortran. La première proposition utilisait ZERO, absent de ce fichier : cette préparation échouée est préservée, R1 utilise un littéral et protège l'initialisation par STAT.

## Limites et exécution après accord

Créer un quatrième moteur isolé avec la même source figée, le correctif de graphe A53 déjà autorisé et cette seule nouvelle différence. Compilation plafonnée à une heure, six CPU, sans GPU ni installation ; contrôle de capacité natif, régression mémoire, cohésion chargée, graphe/CHECK et témoins physiques plafonnés à180 secondes chacun. Les moteurs antérieurs et les échecs sont conservés. Ce travail ne suffit pas à valider les TYPE25 ni les dix secondes d'impact. La meilleure fenêtre entière reste0,0200001220703125s.
