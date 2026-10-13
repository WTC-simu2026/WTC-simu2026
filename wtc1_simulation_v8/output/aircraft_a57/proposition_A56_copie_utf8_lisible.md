# Proposition A56 pour A57 — allocation du tampon d'origine réellement utilisé

Préparée, non appliquée et non compilée. Nouveau correctif distinct, nécessitant un accord explicite.

## 1. Faits directement observés

A56 applique et compile le correctif A55 du tampon temporaire ; les témoins implicites échouent encore. La surveillance observe de nouveau NODREAC0x31→0 pendant SRCOORK et l'arrêt avant tout pas chargé. Une autre mesure native,740appels d'allocateur bornés, capture le descripteur SMSTR : label ELBUF_STR%GBUF%SMSTR, demande0, double8octets, bornes1..0, capacité0. Son pointeur correspond exactement à SAV reçu par SRCOORK, TYPE43/NEL1. Ce buffer vient du chargeur ALLOCBUF_AUTO, retour0x468d01 dans le binaire A56. L'hypothèse « seule copie temporaire » est rejetée et conservée.

## 2. Source du logiciel

ALLOCBUF_AUTO alloue le tampon original d'après NEL*G_SMSTR issu du redémarrage. SRCOORK utilise21colonnes. Le défaut de capacité sur le pointeur effectivement utilisé est maintenant une observation native, pas seulement une inférence du contrat source.

## 3. Archives

Aucune archive historique consultée ou modifiée.

## 4. Modification proposée

Dans allocbuf_auto.F seulement, porter l'allocation TYPE43 à au moins21*NEL valeurs et initialiser le stockage ajouté. Garder exactement la largeur sérialisée G_SMSTR, SDP_RBUF, les offsets et le nombre de valeurs lues ; restaurer ces valeurs dans leur plage d'origine. Les autres types restent inchangés. Le chargeur est partagé explicite/implicite ; l'allocation mémoire est donc concernée dans les deux modes, sans changer les cartes physiques. Conserver les correctifs A53 du graphe et A55 du tampon temporaire dans un cinquième moteur séparé.

## 5. Contrôles préparatoires

48cas de bornes et restauration des données sérialisées passent ; nouvelles lignes72colonnes maximum, empreintes enregistrées. Aucun contrôle compilé ou physique du nouveau correctif revendiqué. A56, ses sorties et son critère mémoire échoué restent intacts.

## 6. Limites et suite après accord

Compilation plafonnée1h, sixCPU, sans GPU ni installation, mêmes sources/dépendances. Contrôles natifs de capacité/pointeur/mémoire, cohésion implicite chargée et demi-pas, graphe/CHECK et témoins explicites/TYPE7,180s par processus, seuils inchangés. La réponse implicite et les15erreurs entières/cinqTYPE25 ignorés restent bloquants. Aucun résultat d'impact entier supplémentaire : meilleure fenêtre0,0200001220703125s, objectif vidéo3D des dix secondes physiques toujours incomplet.
