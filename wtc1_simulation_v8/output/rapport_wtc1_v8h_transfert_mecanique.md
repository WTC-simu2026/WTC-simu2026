# WTC 1 - V8H-A : transfert mecanique borne dans le noyau

## Resultat principal

V8H-A remplace la redistribution directe de V8F par des ressorts axiaux de colonnes et des poutres bilineaires limitees en force et en deformation. Le resultat le plus net n'est pas une validation finale, mais l'identification d'une donneee indispensable : le sous-reseau NIST des seules poutres a assemblages rigides ne relie que 24 des 47 colonnes par 17 liaisons. Il ne peut donc pas, a lui seul, redistribuer les charges des colonnes endommagees des rangees 500 et 1000.

Le reseau proxy a quatre voisins relie les 47 colonnes par 118 liaisons. Il teste mecanquement une enveloppe de chemins supplementaires (poutres secondaires + dalle), mais ne constitue pas le plan d'origine.

Dans les 19 200 chemins tardifs testes (80 et 100 min), toutes les variantes finissent par creer une composante chargee sans appui apres plastification/rupture des liaisons : 18 633 s'arretent d'abord au niveau 97 et 567 au niveau 96. Ce resultat vaut uniquement pour ces reseaux locaux bornes. Chaque champ synthetique force en outre au moins une colonne a l'extremum chaud NIST du niveau; il s'agit d'un test de robustesse enveloppe, pas d'une distribution mesuree.

### Comparaison a 100 min, gamma=1

Assemblage a 100 % de la resistance plastique proxy, deux plans de poutres actifs, temperature de poutre prise comme moyenne des temperatures synthetiques aux extremites.

| Topologie | Section WF proxy | champs sans equilibre | premier niveau defaillant median |
|---|---:|---:|---:|
| NIST, poutres moment seulement | 12WF65 | 100.0 % | 97.0 |
| NIST, poutres moment seulement | 14WF136 | 100.0 % | 97.0 |
| NIST, poutres moment seulement | 14WF228 | 100.0 % | 97.0 |
| Proxy connecte a 4 voisins | 12WF65 | 100.0 % | 97.0 |
| Proxy connecte a 4 voisins | 14WF136 | 100.0 % | 97.0 |
| Proxy connecte a 4 voisins | 14WF228 | 100.0 % | 97.0 |

Reference V8F non bornee correspondante (4 voisins) : 61.5 % de champs sans equilibre. La difference avec V8H-A mesure l'effet combine de la rigidite, de la capacite et de la rupture des chemins; elle n'est pas une probabilite physique.

## Faits directement documentes

- NIST n'a modele individuellement dans le modele global que les poutres de noyau a assemblages rigides; la rigidite axiale des autres poutres etait integree a celle de la dalle.
- NIST attribue aux profiles WF de noyau de nuance 36 ksi un comportement de materiau avec Fy=37,0 ksi a temperature ambiante.
- Le modele detaille du plancher 96 comporte les poutres du noyau et la dalle; NIST traite ce plancher comme typique des niveaux superieurs.
- NCSTAR 1-2A nomme les fichiers originaux de nomenclature des poutres et assemblages, mais ces fichiers ne figurent pas dans l'archive locale inspectee.

## Hypotheses du modele

- Les profils 12WF65, 14WF136 et 14WF228 sont des bornes de sensibilite issues de la table historique AISC deja tracee; aucune de ces sections n'est attribuee a une poutre reelle des niveaux 94-99.
- La resistance d'assemblage vaut 50 % ou 100 % de la force de plastification de la poutre proxy; aucune valeur Book 6 n'est disponible pour la remplacer.
- Un ou deux plans de plancher peuvent participer au transfert. La rotation relative ultime de 0,02 rad et le tangent post-plastique de 1 % sont des hypotheses explicites.
- La temperature de poutre est soit maintenue a 20 C (borne optimiste de transfert), soit prise comme moyenne des temperatures synthetiques des deux colonnes terminales (proxy, pas une mesure).

## Resultats derives et limites

- Une perte d'equilibre indique qu'aucune solution statique n'est trouvee avec les liaisons et limites imposees. Elle ne calcule ni la chute du bloc superieur ni la propagation dynamique globale.
- Le motif final des 19 200 calculs est `disconnected_loaded_component` : apres ruptures successives, un groupe de noeuds conserve une charge verticale mais n'est plus relie a aucune colonne porteuse dans le reseau impose.
- Le reseau moment-only est structurellement incomplet par conception; son echec ne contredit pas NIST, puisque NIST attribue aussi un role local a la dalle composite.
- Le proxy connecte peut tester l'ordre de grandeur des sections, mais il ne peut pas valider l'as-built tant que les Books 5 et 6, la ferraille de dalle et les modifications locales ne sont pas recuperes.
- Les fractions portent sur 100 champs synthetiques bornes par les extrema NIST. Elles ne sont jamais interpretees comme probabilite de l'evenement reel.

## Contradictions ou informations manquantes

Aucune contradiction numerique nouvelle avec les sorties NIST n'est etablie a ce stade. En revanche, il existe une lacune documentaire bloquante pour une verification independante : les fichiers WTCAB-Bk5-BeamSched.xls / WTCAB_DBk5.mdb et les donnees Book 6 d'assemblages ne sont pas publies dans le corpus local utilise. Une simulation qui leur substituerait une section unique sans intervalle donnerait une precision artificielle.

Temps d'execution : 234.7 s. Configuration, graines et resultats complets sont conserves dans le JSON V8H-A.
