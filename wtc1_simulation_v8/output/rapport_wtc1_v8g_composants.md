# WTC 1 - V8G : transferts bornes par les composants

## Resultat principal

Le transfert maximal de noyau vers les facades publie par NIST est de **6748 kip** a 80 min. Le composant qui controle le chemin publie est l'outrigger E, avec un DCR de **0.97**. Une extrapolation lineaire donne une capacite globale d'environ **6957 kip**, soit seulement **3.1 %** de marge au-dessus de la demande a 80 min.

La connexion la plus sollicitee de la Table 4-29 atteint **0.544** de sa capacite ultime. Dans les verifications publiees, ce sont donc les diagonales/outtriggers, et non les connexions listees, qui bornent le transfert.

Cette coherence ne constitue pas une validation independante de la reponse globale NIST : la demande de 6 748 kip et le DCR de 0,97 proviennent du meme modele officiel. Elle montre toutefois que la charge transferee n'est pas superieure aux capacites de composants que NIST a publiees.

## Attaches de plancher a 100 min

Fraction des combinaisons *temperature synthetique x type d'attache NIST* dont la capacite verticale devient inferieure a la charge normale de 16 kip. Ce ne sont ni des comptes d'attaches reelles rompues, ni des probabilites.

| Niveau | attaches interieures | attaches exterieures | plage thermique NIST |
|---:|---:|---:|---:|
| 94 | 0,0 % | 0,0 % | 50-411 deg C |
| 95 | 0,0 % | 3,6 % | 48-861 deg C |
| 96 | 0,0 % | 5,4 % | 82-902 deg C |
| 97 | 0,0 % | 6,4 % | 66-927 deg C |
| 98 | 0,0 % | 6,2 % | 51-926 deg C |
| 99 | 0,0 % | 0,0 % | 78-461 deg C |

Les attaches interieures restent generalement plus fortes verticalement. Aux temperatures voisines de 900 deg C, plusieurs types d'attaches exterieures tombent a 11-17 kip, donc autour ou sous la charge normale de 16 kip. Cela rend des deconnexions locales plausibles dans les zones les plus chaudes sans qu'une surcharge dynamique soit necessaire. La carte thermique exacte des attaches reste inconnue.

## Sensibilite du chemin du noyau a 100 min

Les valeurs ci-dessous reprennent le reseau V8F avec gamma=1, aucun affaiblissement invente des dommages moderate/light et aucune amplification de transfert. Seule la capacite du chapeau structurel change.

| Capacite du chapeau | demande noyau ajustee | 4 voisines | 8 voisines | redistribution globale |
|---|---:|---:|---:|---:|
| capacite calibree NIST | 28478 kip | 61,5 % | 51,5 % | 0,0 % |
| transfert demontre a 80 min | 28478 kip | 61,5 % | 51,5 % | 0,0 % |
| 75 % de la capacite calibree (hypothese) | 29211 kip | 68,0 % | 57,0 % | 1,0 % |
| 50 % (hypothese) | 30951 kip | 81,0 % | 65,0 % | 1,5 % |
| aucun transfert (borne) | 34429 kip | 94,0 % | 88,0 % | 4,5 % |

## Faits, hypotheses et incertitudes

### Faits directement transcrits

- NIST donne les capacites verticales des attaches en fonction de la temperature et une charge normale d'environ 16 kip par paire de poutrelles.
- Dans la reponse globale Case B, le noyau cede environ 6 748 kip aux facades a 80 min par le chapeau structurel; l'outrigger E atteint un DCR de 0,97.
- Les charges totales aux niveaux 98 et 105 different de seulement 35 kip a 80 min, ce qui confirme que le transfert axial principal s'effectue au sommet plutot que directement par les planchers 94-99.

### Hypotheses de V8G

- La capacite agregee de 6 957 kip suppose une mise a l'echelle lineaire de la demande de l'outrigger E.
- Les cas a 75 %, 50 % et sans chapeau ne sont pas des dommages observes; ils bornent la sensibilite.
- Faute de carte attache-par-attache, les temperatures synthetiques sont croisees avec tous les types publies.
- La redistribution entre colonnes du noyau reste celle de V8F. Les sections et connexions des poutres interieures ne sont pas encore suffisamment transcrites pour la remplacer proprement.

### Contradictions ou zones non resolues

- Aucune contradiction numerique interne n'apparait entre le transfert global publie et les capacites publiees du chapeau, mais la marge calculee sur l'outrigger E est faible et depend d'une verification NIST post-traitee.
- Le modele global NIST ne representait pas explicitement toutes les ruptures de raccords du chapeau; celles-ci ont ete verifiees separement. Cette separation limite l'independance de la sequence calculee.
- Les planchers du modele global etaient des plaques calibrees en rigidite membranaire, avec une rigidite de flexion non reproduite exactement. Les sous-modeles de plancher compensent partiellement cette limite, sans constituer un modele complet unique.
- V8G ne teste aucune hypothese d'explosif. Elle montre seulement que le chemin de charge officiel publie est mecaniquement admissible au niveau des composants transcrits, avec une faible marge locale au composant critique.
