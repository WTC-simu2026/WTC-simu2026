# WTC 1 - V8F : chemin de charge vertical couple, niveaux 94-99

## Resultat principal

V8F conserve les redistributions de charge d'un niveau au suivant. La fraction de champs sans equilibre reste une metrique de robustesse sur 200 champs thermiques synthetiques bornes par NIST; ce n'est pas une probabilite de l'effondrement reel.

### Cas de base a 100 min

Redistribution vers quatre colonnes voisines, aucun affaiblissement invente des dommages moderate/light, amplification de transfert 1,00.

| Champ thermique | V8E, niveaux independants | V8F, chemin vertical | premier niveau defaillant median |
|---|---:|---:|---:|
| gamma=0,5 | 92.5 % | 89.0 % | 97.0 |
| gamma=1,0 | 71.0 % | 61.5 % | 97 |
| gamma=2,0 | 45.0 % | 23.5 % | 96 |
| gamma=4,0 | 21.5 % | 7.5 % | 95 |

### Sensibilite du transfert a 100 min, gamma=1

| Portee de redistribution | Capacite moderate/light | champs sans equilibre |
|---|---|---:|
| 4 voisines | 100 % / 100 % (regle NIST de retrait seule) | 61.5 % |
| 4 voisines | 95 % / 99 % (hypothese) | 63.0 % |
| 4 voisines | 80 % / 95 % (hypothese conservative) | 62.5 % |
| 8 voisines | 100 % / 100 % (regle NIST de retrait seule) | 51.5 % |
| 8 voisines | 95 % / 99 % (hypothese) | 51.0 % |
| 8 voisines | 80 % / 95 % (hypothese conservative) | 50.0 % |
| globale proportionnelle a la capacite | 100 % / 100 % (regle NIST de retrait seule) | 0.0 % |
| globale proportionnelle a la capacite | 95 % / 99 % (hypothese) | 0.0 % |
| globale proportionnelle a la capacite | 80 % / 95 % (hypothese conservative) | 0.0 % |

## Interpretation

- Une perte d'equilibre signifie que ce reseau statique ne trouve plus de chemin de compression avec la regle imposee; elle ne simule pas encore le mouvement global ni la propagation dynamique.
- Le couplage vertical diminue ici la fraction sans equilibre par rapport a V8E : a gamma=1, elle passe de 71,0 % a 61,5 %. La distribution heritee des niveaux superieurs peut donc decharger certaines colonnes localement vulnerables au lieu de recommencer une repartition independante a chaque etage.
- La comparaison V8E/V8F isole l'effet du couplage vertical. Les variations entre 4 voisines, 8 voisines et redistribution globale mesurent l'incertitude sur le role des poutres, dalles et connexions.
- Une amplification hypothetique de 1,15 de chaque charge transferee porte, a 100 min et gamma=1, la fraction sans equilibre a 99,0 % pour 4 voisines, 92,0 % pour 8 voisines et 1,5 % pour la redistribution globale. Ce fort ecart montre pourquoi l'etape dynamique ne peut pas etre deduite du seul calcul statique.
- Les facteurs moderate/light sont volontairement separes des faits NIST. Aucun de ces facteurs n'est presente comme une mesure publiee.
- Leur effet n'est pas strictement monotone dans les variantes locales (ecarts de quelques points), car l'algorithme sequentiel change l'ordre des ruptures et donc le chemin impose. C'est une sensibilite de la regle de cascade, pas un effet physique a interpreter.
- Le modele ne verifie pas la resistance du diaphragme qui effectue le transfert. Cette limite peut rendre certaines redistributions trop optimistes.
- La facade, les planchers exterieurs, le hat truss, le fluage, les connexions et la dynamique de chute restent absents.
