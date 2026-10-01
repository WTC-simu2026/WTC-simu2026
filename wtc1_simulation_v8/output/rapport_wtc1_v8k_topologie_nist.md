# WTC 1 - V8K : topologie NIST du cut-set au niveau 96

## Resultat principal

La V8K remplace les sept aretes `nearest-four` du cut-set V8J par une transcription locale de la Figure 5-59(b) du modele NIST du niveau 96. Le resultat est plus contraignant que V8J : **une des sept aretes etait une diagonale de proxy qui n'apparait pas dans le plan orthogonal**, quatre liaisons de bord sont retirees dans le modele apres impact, et seulement les chemins 505-506 et 505-605 restent visibles.

En rejouant les niveaux 99 a 97 de V8J, les colonnes retirees 503, 504 et 604 recoivent encore ensemble **2437 kip**, soit **74.9 %** des 3 256 kip du cut V8J, sans chemin local visible vers un poteau survivant au niveau 96. La colonne 505 conserve un chemin candidat vers 506/605, mais sa section 14WF136 reste un proxy non as-built.

La conclusion n'est pas que la tour reelle aurait du tomber a froid. Elle est que **les poutres locales du niveau 96 montrees par NIST ne peuvent pas, seules, reparer le chemin manquant de V8J**. La redistribution reelle observee doit donc impliquer des mecanismes absents de ce sous-modele : action de portique sur plusieurs niveaux, flexion/cisaillement des troncons de poteaux, planchers de bureau vers les facades, hat truss, ou une combinaison de ces chemins.

## Faits et resultats du modele officiel

- La Figure 2-2 fournit l'implantation et la numerotation des poteaux du noyau au niveau 96.
- Le modele complet du plancher 96 vient d'un modele SAP2000 converti et comprend poutres du noyau, dalle, fermes, poteaux et elements de rupture; il ne s'agit pas d'une nomenclature as-built publiee dans la figure.
- NIST precise que les dommages raffines Case A/B n'ont jamais ete utilises dans le modele complet de plancher; le dommage structurel Case Ai a aussi ete reutilise pour Case Bi faute de donnees disponibles au moment du calcul.
- Les poteaux endommages mais non severes ont ete conserves comme intacts dans cette analyse.
- Point essentiel : aucune charge verticale n'a ete appliquee en tete des poteaux dans l'analyse gravitaire/thermique de ce sous-systeme. La Figure 5-59 documente donc une topologie de modele, pas une validation officielle du transfert des charges verticales du bloc superieur.

## Transcription du cut-set

| Arete V8J | Statut dans la Figure 5-59(b) | Qualification |
|---|---|---|
| 502-503 | removed_after_impact | orthogonal_beam_path_visible_before_impact |
| 503-603 | removed_after_impact | orthogonal_beam_path_visible_before_impact |
| 504-605 | not_a_direct_beam_path | nearest_four_diagonal_proxy_not_visible_in_orthogonal_plan |
| 505-506 | visible_after_impact | orthogonal_beam_path |
| 505-605 | visible_after_impact | orthogonal_beam_path |
| 603-604 | removed_after_impact | orthogonal_beam_path_visible_before_impact |
| 604-605 | removed_after_impact | orthogonal_beam_path_visible_before_impact |

| Noeud retire | Charge entrante V8J | Chemin local Figure 5-59 | Gate topologique |
|---:|---:|---|---|
| 503 | 1164.5 kip | no visible beam path to a surviving core-column support | echoue |
| 504 | 865.7 kip | no visible beam path to a surviving core-column support | echoue |
| 505 | 818.7 kip | visible paths toward surviving Columns 506 and 605 | passe provisoirement |
| 604 | 407.2 kip | no visible beam path to a surviving core-column support | echoue |

## Hypotheses propres au modele

- Les charges entrantes sont celles du reseau reduit V8J apres redistribution aux niveaux 99, 98 et 97. Elles ne sont ni mesurees ni extraites d'un fichier de resultats NIST poteau par poteau.
- La transcription porte uniquement sur les sept aretes du cut-set. Elle ne transforme pas l'image ANSYS en un modele complet de 46 280 elements.
- Le statut de 505-605 est de confiance moyenne parce que la poutre est graphiquement decalee du centroide du poteau et reliee par la zone de noeud modelisee. Cette ambiguite ne change pas le sort des noeuds 503, 504 et 604.
- Les lois 14WF136+dalle heritees ne sont conservees que pour documenter le chemin candidat du noeud 505; elles ne sont pas creditees aux trois noeuds sans topologie survivante.

## Ecran force-deplacement du seul chemin candidat

Avec les deux aretes visibles 505-506 et 505-605 imposees au meme deplacement, l'enveloppe 14WF136+dalle heritee atteint au maximum **309 kip** pour une demande de **819 kip** sur 505; le deficit du proxy vaut **510 kip**. Ce resultat echoue lui aussi, mais il ne qualifie pas la capacite as-built puisque les sections et assemblages de la Figure 5-59 ne sont pas identifies.

## Contradictions et zones d'incertitude

- La tour est restee debout apres impact, alors que le chemin local Figure 5-59 laisse une charge positive sans appui dans notre empilement unidimensionnel. C'est une contradiction avec le **sous-modele V8J/V8K autonome**, pas avec la structure reelle complete.
- Le modele complet de plancher utilise une ancienne definition Case Ai et n'a jamais integre les dommages raffines Case A/B. Il est donc impropre a une reproduction definitive du cas officiel final.
- La Figure 5-59 ne donne ni sections de poutres, ni assemblages, ni lois force-deplacement, ni affectation de sieges. Drawing Book 5/6 ou les entrees SAP/ANSYS restent necessaires pour une verification as-built.
- Puisque les charges verticales en tete de poteau etaient absentes du sous-systeme NIST, son maintien sous ses propres charges de plancher ne valide pas le transfert vertical de 3256 kip teste ici.

## Decision et suite

**GATE FROID NON VALIDE.** La V8K rejette le plancher 96 local comme solution autonome au cut-set. La V8L doit construire un chemin multi-etages explicite pour 503/504/604, avec flexion/cisaillement des poteaux et poutres sur 95-99, puis comparer sa redistribution froide aux sorties globales NIST. Aucune transition thermique ni animation Blender dynamique n'est encore autorisee.

Temps d'execution : 0.12 s. La transcription, les charges rejouees et les limites epistemiques sont conservees dans le JSON V8K.
