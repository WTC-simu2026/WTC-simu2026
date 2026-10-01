# WTC 1 - V8M : couplage froid noyau-planchers-facades

## Resultat principal

Le chemin froid plancher-facade ne ferme pas le cut-set V8L dans les limites publiees. Meme l'enveloppe intacte sur quatre faces et six niveaux exige une descente relative bien superieure a 25 in; avec le proxy de dommages nord, le seuil est encore plus eleve. Le plafond provient de la geometrie membranaire et de la traction horizontale des sieges, pas de la resistance axiale des facades.

Le meilleur cas physiquement plafonne transfere 1517 kip a 25 in et exige 79.5 in pour reprendre les 4 772 kip de la composante V8L. Le cas qui conserve le proxy de dommages nord exige 110.1 in. Ces deplacements depassent le seuil de 25 in que NIST classait deja comme deplacement vertical significatif du plancher.

En supprimant les limites de connexion, la coque equivalente la plus raide atteint la cible a 11.4 in. Ce resultat montre la sensibilite a la loi de connexion; il ne constitue pas une capacite physique mesuree.

## Faits et resultats officiels

- Une connexion interieure de paire de fermes porte environ 16 kip en service et sa capacite horizontale publiee a 20 C est 44 kip.
- Le modele de ferme composite de reference avait une portee longue de 713 in, une dalle tributaire de 80 in par paire et une epaisseur moyenne de 4,3 in.
- Les coques de plancher du modele global avaient une raideur membranaire calibree sur le modele de ferme, mais la valeur numerique equivalente n'est pas publiee dans les pages sourcees.
- NIST utilise ces coques pour l'action de diaphragme et le transfert lorsque le noyau descend sensiblement par rapport aux facades.
- Apres impact, le changement de charge du noyau est +400 kip aux niveaux 98 et 105; V8M ne credite donc aucun transfert froid additionnel par le hat truss.

## Hypotheses propres a V8M

- La membrane suit une geometrie de cable: seul le composant vertical de la traction axiale transfere la charge.
- Les sections de corniere de la Figure 4-23 sont converties en aire brute en negligeant les conges; trois fractions de beton efficace (0, 0,25 et 1,0) encadrent la raideur inconnue.
- Toutes les paires actives d'un cas subissent le meme deplacement relatif. C'est une enveloppe superieure de compatibilite, pas une carte as-built.
- Le proxy nord endommage conserve 11 paires par niveau; les enveloppes intactes en utilisent 31 par face.
- Le prototype de poteau exterieur 151 sert seulement a verifier que la facade n'est pas le premier plafond arithmetique; il ne remplace pas le calendrier complet des plaques.

## Resultats selectionnes

| Topologie | Limite de connexion | Beton efficace | Transfert a 25 in | Deplacement requis pour 4 772 kip | Gate physique |
|---|---|---:|---:|---:|---|
| north_damage_scaled_5floors | published_seat_capped | 1.00 | 85 kip | impossible | non |
| north_full_5floors | published_seat_capped | 1.00 | 239 kip | 698.3 in | non |
| all_faces_north_damage_scaled_5floors | published_seat_capped | 1.00 | 1110 kip | 110.1 in | non |
| all_faces_full_5floors | published_seat_capped | 1.00 | 1264 kip | 96.0 in | non |
| all_faces_full_6floors | published_seat_capped | 1.00 | 1517 kip | 79.5 in | non |
| all_faces_full_6floors | uncapped_global_shell | 1.00 | 50408 kip | 11.4 in | non |

## Comparaison au modele officiel

La difference de changement de charge du noyau entre les niveaux 98 et 93 est de 956 kip dans les tableaux NIST. Le cas physiquement plafonne et endommage atteint cette valeur a 21.5 in. Ce rapprochement ne calibre pas le modele, car la difference officielle inclut aussi les charges des elements severes et n'isole pas la contribution des planchers.

## Contradictions et informations manquantes

- V8M ne trouve pas de chemin plancher-facade physiquement plafonne capable de reprendre 4 772 kip avant grande deformation.
- Le cas de coque non plafonnee peut mathematiquement fermer le chemin, mais depend d'une raideur equivalente non publiee et ignore la rupture horizontale de 44 kip.
- L'echec ne contredit pas a lui seul le modele global NIST: V8L peut encore sous-representer la redistribution interne dans les dalles et poutres du noyau, et la topologie as-built manque.
- Les affectations exactes des sieges, la carte de survie des fermes et les fichiers SAP2000/ANSYS restent manquants.

## Decision du gate

**NON VALIDE.** Aucun cas respectant la limite horizontale publiee de 44 kip ne reprend la composante V8L a 25 in ou moins. La prochaine iteration doit auditer la raideur equivalente et la redistribution interne du noyau a partir des fichiers globaux ou de substituts calibres; la thermique et Blender dynamique restent suspendus.

Temps d'execution : 0.02 s. Les 45 enveloppes sont conservees dans le JSON V8M.
