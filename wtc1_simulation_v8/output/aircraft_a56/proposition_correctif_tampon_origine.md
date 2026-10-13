# Proposition A56 pour A57 â€” allocation du tampon d'origine rÃ©ellement utilisÃ©

PrÃ©parÃ©e, non appliquÃ©e et non compilÃ©e. Nouveau correctif distinct, nÃ©cessitant un accord explicite.

## 1. Faits directement observÃ©s

A56 applique et compile le correctif A55 du tampon temporaire ; les tÃ©moins implicites Ã©chouent encore. La surveillance observe de nouveau NODREAC0x31â†’0 pendant SRCOORK et l'arrÃªt avant tout pas chargÃ©. Une autre mesure native,740appels d'allocateur bornÃ©s, capture le descripteur SMSTR : label ELBUF_STR%GBUF%SMSTR, demande0, double8octets, bornes1..0, capacitÃ©0. Son pointeur correspond exactement Ã  SAV reÃ§u par SRCOORK, TYPE43/NEL1. Ce buffer vient du chargeur ALLOCBUF_AUTO, retour0x468d01 dans le binaire A56. L'hypothÃ¨se Â« seule copie temporaire Â» est rejetÃ©e et conservÃ©e.

## 2. Source du logiciel

ALLOCBUF_AUTO alloue le tampon original d'aprÃ¨s NEL*G_SMSTR issu du redÃ©marrage. SRCOORK utilise21colonnes. Le dÃ©faut de capacitÃ© sur le pointeur effectivement utilisÃ© est maintenant une observation native, pas seulement une infÃ©rence du contrat source.

## 3. Archives

Aucune archive historique consultÃ©e ou modifiÃ©e.

## 4. Modification proposÃ©e

Dans allocbuf_auto.F seulement, porter l'allocation TYPE43 Ã  au moins21*NEL valeurs et initialiser le stockage ajoutÃ©. Garder exactement la largeur sÃ©rialisÃ©e G_SMSTR, SDP_RBUF, les offsets et le nombre de valeurs lues ; restaurer ces valeurs dans leur plage d'origine. Les autres types restent inchangÃ©s. Le chargeur est partagÃ© explicite/implicite ; l'allocation mÃ©moire est donc concernÃ©e dans les deux modes, sans changer les cartes physiques. Conserver les correctifs A53 du graphe et A55 du tampon temporaire dans un cinquiÃ¨me moteur sÃ©parÃ©.

## 5. ContrÃ´les prÃ©paratoires

48cas de bornes et restauration des donnÃ©es sÃ©rialisÃ©es passent ; nouvelles lignes72colonnes maximum, empreintes enregistrÃ©es. Aucun contrÃ´le compilÃ© ou physique du nouveau correctif revendiquÃ©. A56, ses sorties et son critÃ¨re mÃ©moire Ã©chouÃ© restent intacts.

## 6. Limites et suite aprÃ¨s accord

Compilation plafonnÃ©e1h, sixCPU, sans GPU ni installation, mÃªmes sources/dÃ©pendances. ContrÃ´les natifs de capacitÃ©/pointeur/mÃ©moire, cohÃ©sion implicite chargÃ©e et demi-pas, graphe/CHECK et tÃ©moins explicites/TYPE7,180s par processus, seuils inchangÃ©s. La rÃ©ponse implicite et les15erreurs entiÃ¨res/cinqTYPE25 ignorÃ©s restent bloquants. Aucun rÃ©sultat d'impact entier supplÃ©mentaire : meilleure fenÃªtre0,0200001220703125s, objectif vidÃ©o3D des dix secondes physiques toujours incomplet.
