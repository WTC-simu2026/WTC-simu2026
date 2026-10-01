# WTC 1 - V8L : redistribution froide multi-etages 94-99

## Resultat principal

Les deux topologies multi-etages perdent l'equilibre avant la demande froide complete. Ce resultat est qualitativement coherent avec la non-convergence du noyau isole Case B de NIST et indique que le prochain chemin a introduire est le couplage vers les facades et le hat truss, pas une resistance locale arbitrairement augmentee.

Le cas reconstruit le plus resistant (aucun dommage initial de poutre, 14WF228, facteur d'assemblage 1,0) reste stable jusqu'a 78%, soit environ 26 855 kip sur les 34 429 kip demandes, puis perd un composant encore charge a 79%. A ce pas, 60 poutres et 12 segments de poteaux additionnels ont atteint leurs criteres; le composant deconnecte porte 4 772 kip. La resolution de charge est de 1 point de pourcentage; 78 % est un seuil numerique de ce modele, pas une probabilite de l'evenement reel.

La V8L corrige une faiblesse structurelle de V8J/V8K : une charge arrivant sur un poteau coupe au niveau 96 peut maintenant se redistribuer par les poutres du niveau 97 avant d'atteindre la coupure. Les six niveaux sont resolus simultanement; les segments Case B 94-96 sont absents des le debut et les nouvelles surcharges peuvent provoquer plastification des poutres ou perte de segments voisins.

## Faits et resultats officiels

- La Figure 2-17 de NIST fournit les segments du noyau severes ou lourdement endommages en Case B.
- Le noyau isole NIST comprenait poteaux, poutres et dalles des niveaux 89-106. Le cas structurel B ne convergait pas, meme avec appuis lateraux; ce sous-modele ne comprenait ni transfert par les planchers vers les facades ni hat truss.
- Dans le modele global, seules les poutres du noyau a assemblage rigide etaient explicites. La rigidite axiale des autres poutres etait integree a la dalle equivalente, dont NIST dit qu'elle redistribuait localement les charges entre poteaux voisins.
- Le modele global stable rapporte environ +1 % de charge totale du noyau apres impact, avec redistribution surtout vers les poteaux voisins; 705 flambait et 605/804 montraient un flambement mineur.

## Resultats des enveloppes

| Topologie | Dommage poutres | Profil | Facteur assemblage | Equilibre | Facteur de charge atteint | Deplacement max | DCR poteau max |
|---|---|---|---:|---|---:|---:|---:|
| nist_moment_only | no_beam_damage_upper_bound | 12WF65 | 0.5 | non | 0.0% | n/a | n/a |
| nist_moment_only | no_beam_damage_upper_bound | 12WF65 | 1.0 | non | 0.0% | n/a | n/a |
| nist_moment_only | no_beam_damage_upper_bound | 14WF136 | 0.5 | non | 0.0% | n/a | n/a |
| nist_moment_only | no_beam_damage_upper_bound | 14WF136 | 1.0 | non | 0.0% | n/a | n/a |
| nist_moment_only | no_beam_damage_upper_bound | 14WF228 | 0.5 | non | 0.0% | n/a | n/a |
| nist_moment_only | no_beam_damage_upper_bound | 14WF228 | 1.0 | non | 0.0% | n/a | n/a |
| nist_moment_only | floor96_figure_damage | 12WF65 | 0.5 | non | 0.0% | n/a | n/a |
| nist_moment_only | floor96_figure_damage | 12WF65 | 1.0 | non | 0.0% | n/a | n/a |
| nist_moment_only | floor96_figure_damage | 14WF136 | 0.5 | non | 0.0% | n/a | n/a |
| nist_moment_only | floor96_figure_damage | 14WF136 | 1.0 | non | 0.0% | n/a | n/a |
| nist_moment_only | floor96_figure_damage | 14WF228 | 0.5 | non | 0.0% | n/a | n/a |
| nist_moment_only | floor96_figure_damage | 14WF228 | 1.0 | non | 0.0% | n/a | n/a |
| nist_moment_only | repeat_floor96_damage_floors94_98 | 12WF65 | 0.5 | non | 0.0% | n/a | n/a |
| nist_moment_only | repeat_floor96_damage_floors94_98 | 12WF65 | 1.0 | non | 0.0% | n/a | n/a |
| nist_moment_only | repeat_floor96_damage_floors94_98 | 14WF136 | 0.5 | non | 0.0% | n/a | n/a |
| nist_moment_only | repeat_floor96_damage_floors94_98 | 14WF136 | 1.0 | non | 0.0% | n/a | n/a |
| nist_moment_only | repeat_floor96_damage_floors94_98 | 14WF228 | 0.5 | non | 0.0% | n/a | n/a |
| nist_moment_only | repeat_floor96_damage_floors94_98 | 14WF228 | 1.0 | non | 0.0% | n/a | n/a |
| orthogonal_floor96_reconstruction | no_beam_damage_upper_bound | 12WF65 | 0.5 | non | 10.0% | n/a | n/a |
| orthogonal_floor96_reconstruction | no_beam_damage_upper_bound | 12WF65 | 1.0 | non | 20.0% | n/a | n/a |
| orthogonal_floor96_reconstruction | no_beam_damage_upper_bound | 14WF136 | 0.5 | non | 26.0% | n/a | n/a |
| orthogonal_floor96_reconstruction | no_beam_damage_upper_bound | 14WF136 | 1.0 | non | 51.0% | n/a | n/a |
| orthogonal_floor96_reconstruction | no_beam_damage_upper_bound | 14WF228 | 0.5 | non | 46.0% | n/a | n/a |
| orthogonal_floor96_reconstruction | no_beam_damage_upper_bound | 14WF228 | 1.0 | non | 78.0% | n/a | n/a |
| orthogonal_floor96_reconstruction | floor96_figure_damage | 12WF65 | 0.5 | non | 9.0% | n/a | n/a |
| orthogonal_floor96_reconstruction | floor96_figure_damage | 12WF65 | 1.0 | non | 18.0% | n/a | n/a |
| orthogonal_floor96_reconstruction | floor96_figure_damage | 14WF136 | 0.5 | non | 24.0% | n/a | n/a |
| orthogonal_floor96_reconstruction | floor96_figure_damage | 14WF136 | 1.0 | non | 47.0% | n/a | n/a |
| orthogonal_floor96_reconstruction | floor96_figure_damage | 14WF228 | 0.5 | non | 43.0% | n/a | n/a |
| orthogonal_floor96_reconstruction | floor96_figure_damage | 14WF228 | 1.0 | non | 73.0% | n/a | n/a |
| orthogonal_floor96_reconstruction | repeat_floor96_damage_floors94_98 | 12WF65 | 0.5 | non | 7.0% | n/a | n/a |
| orthogonal_floor96_reconstruction | repeat_floor96_damage_floors94_98 | 12WF65 | 1.0 | non | 12.0% | n/a | n/a |
| orthogonal_floor96_reconstruction | repeat_floor96_damage_floors94_98 | 14WF136 | 0.5 | non | 19.0% | n/a | n/a |
| orthogonal_floor96_reconstruction | repeat_floor96_damage_floors94_98 | 14WF136 | 1.0 | non | 33.0% | n/a | n/a |
| orthogonal_floor96_reconstruction | repeat_floor96_damage_floors94_98 | 14WF228 | 0.5 | non | 33.0% | n/a | n/a |
| orthogonal_floor96_reconstruction | repeat_floor96_damage_floors94_98 | 14WF228 | 1.0 | non | 61.0% | n/a | n/a |

## Hypotheses propres a V8L

- Les charges sont appliquees au niveau 99 proportionnellement aux capacites froides V8B; NIST ne publie pas ici les 47 charges nodales exactes reutilisables.
- Le reseau `nist_moment_only` reprend les 17 liaisons a assemblage rigide deja transcrites en V8H. Son absence de liaisons dans la rangee 500 est une propriete du sous-reseau explicite, pas la preuve d'une absence de plancher.
- Le reseau orthogonal relie les voisins de rangee et les memes terminaisons entre rangees, sans diagonales nearest-four. Il represente une enveloppe poutres+dalle omise, pas un plan as-built.
- Les profils 12WF65, 14WF136 et 14WF228 et les facteurs d'assemblage 0,5/1,0 sont des bornes. Les vrais Books 5/6 restent manquants.
- Les poteaux sont des ressorts axiaux scalaires; la flexion biaxiale, les rotations de noeuds, P-delta, la fissuration de dalle et la dynamique ne sont pas resolus.

## Contradictions et incertitudes

- Un echec du reseau moment-only est coherent avec le non-convergence du noyau isole Case B de NIST; il ne contredit pas le modele global, qui contient les facades, planchers de bureau et le hat truss.
- Un passage du reseau orthogonal montrerait seulement qu'un chemin composite suffisamment rigide peut fermer le cut-set. Sans module equivalent de dalle, sections et assemblages publies, ce serait une possibilite de modele, pas une validation independante.
- Le dommage de poutres raffine Case B etage par etage n'est pas disponible. Les trois cartes testees encadrent cette lacune mais ne la resolvent pas.

## Decision du gate

**NON VALIDE.** Le noyau reduit multi-etages ne suffit pas. La prochaine iteration doit ajouter les planchers de bureau, facades et/ou le hat truss froid avant toute thermique ou Blender dynamique.

Temps d'execution : 6.44 s. Les 36 cas, les retraits de segments et les sorties critiques sont conserves dans le JSON V8L.
