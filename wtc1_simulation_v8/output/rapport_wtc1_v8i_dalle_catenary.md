# WTC 1 - V8I-A : dalle armee bornee et transition 20-60 min

## Resultat principal

V8I-A ajoute au reseau mecanique V8H une action de catenaire de dalle fissuree, portee uniquement par les armatures et bornee par leur limite elastique et leur allongement ultime. Il ne s'agit ni de la dalle NIST lineaire-elastique sans rupture, ni d'une transcription as-built : la topologie, la ferraille locale, les ouvertures et les degats de dalle restent incomplets.

Le proxy geometrique relie 47 colonnes par 118 aretes. L'enveloppe convexe des axes de colonnes mesure 1091.2 m2; cette surface n'est pas la surface as-built nette de dalle.

Resultat de validation decisif : les 3 600 champs spatiaux perdent l'equilibre, mais les controles uniformes minimaux et meme le cas post-impact entierement froid a 20 C echouent aussi. Or WTC 1 est reste debout 102 min apres l'impact. V8I-A est donc invalide comme representation autonome du chemin de charge reel; ses 100 % d'echec ne peuvent pas etre interpretes comme une probabilite ni comme une preuve en faveur d'un mecanisme de demolition.

### Champs synthetiques, gamma=1

| Cas de dalle | 20 min | 40 min | 60 min |
|---|---:|---:|---:|
| no_slab_v8h_reference | 100.0 % | 100.0 % | 100.0 % |
| weak_cracked_partial | 100.0 % | 100.0 % | 100.0 % |
| low_ratio_full_area | 100.0 % | 100.0 % | 100.0 % |
| high_ratio_quarter_area | 100.0 % | 100.0 % | 100.0 % |
| high_ratio_full_area | 100.0 % | 100.0 % | 100.0 % |
| cold_upper_envelope | 100.0 % | 100.0 % | 100.0 % |

Chaque champ synthetique impose au moins un point a l'extremum chaud NIST du niveau. Les pourcentages ci-dessus mesurent donc la robustesse aux champs construits, jamais une probabilite de l'effondrement reel.

### Cas uniformes de controle

| Cas de dalle | Temps | minimum NIST | milieu de plage | maximum NIST |
|---|---:|---:|---:|---:|
| no_slab_v8h_reference | 20 | echec F96 | echec F96 | echec F97 |
| no_slab_v8h_reference | 40 | echec F96 | echec F96 | echec F97 |
| no_slab_v8h_reference | 60 | echec F96 | echec F96 | echec F97 |
| high_ratio_full_area | 20 | echec F96 | echec F96 | echec F97 |
| high_ratio_full_area | 40 | echec F96 | echec F96 | echec F97 |
| high_ratio_full_area | 60 | echec F96 | echec F96 | echec F97 |
| cold_upper_envelope | 20 | echec F96 | echec F96 | echec F97 |
| cold_upper_envelope | 40 | echec F96 | echec F96 | echec F97 |
| cold_upper_envelope | 60 | echec F96 | echec F96 | echec F97 |

### Validation statique post-impact, structure froide a 20 C

| Cas de dalle | Demande noyau | Resultat |
|---|---:|---:|
| no_slab_v8h_reference | 34429 kip | echec F96 |
| high_ratio_full_area | 34429 kip | echec F96 |
| cold_upper_envelope | 34429 kip | echec F96 |

## Faits et sorties officielles transferees

- NCSTAR 1-6C decrit au plancher 96 une dalle de noyau de 4,5 pouces sur poutres et poutres maitresses WF boulonnees aux colonnes.
- NCSTAR 1-6C fournit 0,21 % et 0,74 % comme taux d'armatures de la dalle-type selon les deux directions, mais ne publie pas ici la ferraille as-built du noyau 94-99.
- NCSTAR 1-6D indique que le module de la dalle de noyau du modele global a ete ajuste pour reproduire la rigidite composite acier-dalle; la valeur ajustee n'est pas fournie dans le passage inspecte.
- NIST attribue aux planchers globaux une action de diaphragme et de membrane, tout en precisant que leur representation ne capture pas leurs modes de rupture thermiques.
- La chronologie d'observation NIST place l'impact a 8:46:26 et le debut de l'effondrement a 10:28:20, soit 102 min plus tard; le batiment devait donc conserver un equilibre global apres impact et avant l'initiation.

## Hypotheses propres a V8I

- La dalle fissuree ne conserve aucune traction du beton : seule l'armature agit en catenaire. Cette option borne le mecanisme plus strictement que la coque lineaire-elastique globale de NIST.
- Les taux 0,21 % et 0,74 % sont appliques isotropiquement, separement, comme bornes basse et haute; ils ne sont pas affectes a des directions reelles du noyau.
- La largeur efficace est normalisee sur l'aire convexe des axes des colonnes, puis reduite par une fraction active. Les ouvertures, bords reels et degats localises ne sont pas mailles.
- La limite d'elasticite de 70 ksi provient d'une representation NIST de treillis soude; le cas faible utilise 50 ksi et une ductilite inferieure pour tester la sensibilite.
- Les poutres restent le proxy moyen 14WF136 de V8H avec deux plans actifs et assemblages a 100 % de la plastification proxy. Ce choix est favorable au transfert mais n'est pas une nomenclature as-built.

## Resultats derives et limites

- Une perte d'equilibre signifie qu'aucune solution statique n'est trouvee apres les ruptures imposees dans ce reseau reduit. Elle ne calcule ni l'initiation complete, ni la chute du bloc, ni la propagation dynamique.
- Un maintien d'equilibre dans une borne favorable ne valide pas la chaine officielle complete; il montre seulement que ce sous-mecanisme peut porter la demande imposee avec ces hypotheses.
- Un echec de toutes les bornes ne prouverait pas un explosif : il pourrait aussi signaler une topologie proxy incorrecte, des chemins manquants vers le perimetre ou le hat truss, ou une mauvaise reconstruction des champs thermiques.
- Ici, l'echec du cas post-impact froid contredit directement la survie observee de la tour. La conclusion valide porte donc sur le sous-modele : il manque au moins un chemin stabilisant majeur avant toute etude d'initiation.

## Contradictions et informations manquantes

- Contradiction documentaire officielle : NCSTAR 1-6C qualifie la dalle de noyau de legere, tandis que NCSTAR 1-6 la qualifie de beton normal. V8I n'utilise pas la traction du beton, ce qui neutralise cette contradiction dans la loi de catenaire mais pas dans un futur modele de masse/compression.
- Les fichiers WTCAB-Bk5-BeamSched.xls, WTCAB_DBk5.mdb et les donnees Drawing Book 6 ne figurent toujours pas dans le corpus local indexe.
- Le module equivalent ajuste de la dalle globale NIST, la ferraille locale, les ouvertures et la carte de degats de dalle restent inconnus ou non transcrits.
- La prochaine iteration doit d'abord reproduire l'equilibre post-impact froid en ajoutant explicitement les chemins noyau-planchers-perimetre et le hat truss; aucune animation d'effondrement ne doit etre couplee avant ce test.

Temps d'execution : 282.2 s. Configuration, graines, cas deterministes et lignes d'ensemble sont conserves dans le JSON V8I-A.
