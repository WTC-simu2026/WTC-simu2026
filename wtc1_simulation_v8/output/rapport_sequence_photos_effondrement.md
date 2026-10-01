# Audit de la sequence photographique d'effondrement ajoutee le 20 aout 2026

## Inventaire utile

Les quatre fichiers suivants forment une sequence visuellement continue :

| Fichier | Dimensions | SHA-256 |
|---|---:|---|
| `wtc_2_021_18.JPG` | 1536 x 1024 | `754DED2B25149593B27D3D96EBA2DDDEE14ADFA74BC7921384F190AC52791E45` |
| `wtc_2_022_19.JPG` | 1536 x 1024 | `A2723C60CAC25C473169DC7DBA59B159954BBE06D146CAE4D536EF9996AE2037` |
| `wtc_2_023_20.JPG` | 1536 x 1024 | `BC8CD76981208E8D9FEFBC20FA37349E17A101135870A4AAEE8A383945DCF453` |
| `wtc_2_024_21.JPG` | 1536 x 1024 | `71A16F8D3FFDD52F76A3CF4BA40FA38684CE2EFA0CD9734CDA752D38F783F9BB` |

Les sources locales ont ete lues sans modification.

## Metadonnees observees

- Fabricant inscrit : Eastman Kodak Company.
- Materiel inscrit : Kodak CLAS Digital Film Scanner / HR200.
- Logiciel inscrit : Kodak Digital Central Lab System.
- Date EXIF commune : 2001-09-16 02:27:42.
- Cette date est celle de la numerisation, pas celle de chaque prise de vue.
- Les fichiers ne fournissent ni heure de prise de vue, ni cadence, ni focale exploitable.

## Portee pour la simulation

Le prefixe `wtc_2` et l'aspect de la sequence indiquent qu'il s'agit tres vraisemblablement de l'effondrement de WTC 2. La serie ne doit donc pas etre utilisee pour ajuster quantitativement le modele WTC 1. Elle peut servir a definir des controles qualitatifs independants :

1. attitude et rotation apparente de la partie superieure ;
2. position du toit et du front opaque par rapport aux etages encore visibles ;
3. croissance laterale de l'enveloppe de debris et de poussiere ;
4. persistance temporaire de fragments verticaux ;
5. asymetrie de la chute et des expulsions visibles.

Sans intervalle temporel entre les vues, cette serie ne permet pas de mesurer une acceleration, une vitesse ou un temps de chute. Sans catalogue source reliant les noms de fichiers a un photographe et a une planche-contact, sa provenance precise reste a confirmer.

## Regle de validation

Une ressemblance visuelle ne suffira pas a valider le modele. L'animation devra etre confrontee, sans retoucher les parametres apres coup, a une sequence WTC 1 independante donnant au minimum la cadence, le point de vue, l'echelle apparente, la trajectoire du toit, la rotation et plusieurs instants de reference. Les photographies WTC 2 resteront un controle secondaire de morphologie.
