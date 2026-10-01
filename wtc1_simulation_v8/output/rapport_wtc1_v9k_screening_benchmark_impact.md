# WTC 1 - V9K, criblage d'un benchmark ouvert d'impact rapide

## Conclusion courte

V9K est valide comme criblage, mais **aucun des quatre candidats ne franchit les sept portes pre-declarees**. Aucun benchmark n'est selectionne et aucun solveur n'est lance. La recherche confirme qu'il existe des comparateurs utiles pour le contact, la perforation et la fragmentation, mais pas encore un cas ouvert qui combine deck reconstructible, mesure physique, rupture objective et convergence exploitable pour qualifier le projectile deformable de la facade.

## 1. Faits directement observes ou transcrits

- Les deux fiches NASA sont des sources gouvernementales publiques. Le cas de 1996 publie un regime d'essai jusqu'a 350 m/s et un graphe de vitesse de perforation, mais pas de deck ni de definition complete du projectile.
- L'article NASA de 1997 decrit un impact de racine de pale sur panneau metallique, DYNA3D, Cowper-Symonds et une rupture par deformation plastique effective. Les auteurs ont ajuste la deformation maximale pour obtenir un accord qualitatif et disent que les parametres predictifs restent a etablir.
- Le rapport FAA DOT/FAA/TC-14/43 documente des sensibilites de maillage et de rupture. La fragmentation change avec le maillage; le rapport indique aussi que les valeurs de rupture doivent etre ajustees selon l'evenement et le maillage. Les temps de calcul complets publies vont de 10 a 208 heures sur 8 a 24 processeurs.
- L'exemple officiel Altair RD-E 2602 fournit un petit fichier d'entree annonce et plusieurs lois de rupture, mais utilise une sphere rigide, omet les effets de vitesse et ne compare pas ses sorties a un essai mesure.

## 2. Resultats de modeles officiels

- NASA rapporte un accord qualitatif pour la vitesse de perforation et la fleche, sans serie mesuree ni incertitude publiee dans l'article.
- La FAA rapporte une sequence de fragmentation compatible avec des essais industriels decrits, mais sans paire ouverte complete mesure/calcul pour le modele de soufflante.
- Altair compare entre elles plusieurs formulations numeriques de rupture. Ce cas illustre le solveur; il ne valide pas physiquement la rupture.

## 3. Affirmations provenant des archives locales

- Aucune. L'archive WTC en lecture seule n'a pas ete rescanee.

## 4. Hypotheses propres a V9K

- Les sept portes sont toutes obligatoires : provenance, licence, deck ou reconstruction complete, rupture regularisee, mesures, convergence et execution locale bornee.
- Une etude de sensibilite dont l'issue qualitative change avec le maillage n'est pas une preuve de convergence.
- Le seuil futur de 10 pour cent sur l'observable d'impulsion ou equivalent n'est pas applique ici, car aucune simulation V9K n'est autorisee.

## 5. Resultats derives

| Candidat | Portes franchies | Decision | Motif controlant |
| --- | ---: | --- | --- |
| NASA_METAL_FAN_CONTAINMENT_IMPACT | 1/7 | REJETE | The report is public-use government work, but no model file or reusable model-file license exists in the record. |
| NASA_TRANSIENT_FE_FAN_CONTAINMENT | 1/7 | REJETE | The article is public-use government work, but no solver model file or model-file reuse terms are supplied. |
| FAA_DOT_TC_14_43_GENERIC_FAN_BLADE_OUT | 1/7 | REJETE | The report is publicly readable, but the repository supplies no model file with explicit reuse terms. |
| OPENRADIOSS_OFFICIAL_HIGH_RATE_IMPACT_EXAMPLE | 3/7 | REJETE | The files are publicly downloadable, but the inspected page states All Rights Reserved and no explicit reusable deck license was identified. |

- Candidats evalues : **4**.
- Candidats selectionnes : **0**.
- Le meilleur cas executable est RD-E 2602, mais il ne franchit que 3 portes sur 7 et echoue sur la licence explicite du deck, la regularisation, la mesure et la convergence.
- Le cas FAA est le plus instructif pour la fragmentation : il montre directement que la rupture depend du maillage et du choix de loi. Cette information justifie de ne pas passer a la facade globale.

## 6. Contradictions et informations manquantes

- Les pages Altair annoncent un ZIP public, mais la page inspectee est protegee par une mention All Rights Reserved et ne fournit pas de licence de reutilisation explicite pour le deck.
- La FAA explore trois configurations de maillage, mais elles ne forment pas une sequence de convergence avec un observable commun; le maillage fin change le verdict de fragmentation.
- Les sources NASA donnent des essais physiquement pertinents, mais pas les definitions et sorties quantitatives necessaires a une reproduction independante.
- Le telechargement local du PDF FAA a ete refuse par le serveur ROSA P (HTTP 403). Son texte primaire indexe, son DOI, sa taille et son empreinte SHA-512 de depot ont ete controles; l'absence de deck et les echecs de convergence/execution suffisent au rejet.

## Decision

Le resultat negatif est conserve sans assouplir les criteres. V9K ne qualifie ni la rupture du projectile, ni le contact deformable-deformable, ni l'impulsion de facade. Il n'autorise aucune substitution de ces analogues aux aciers WTC M26/C80 ou aux materiaux d'un CF6-80A2 de production. Blender reste uniquement un outil de visualisation.
