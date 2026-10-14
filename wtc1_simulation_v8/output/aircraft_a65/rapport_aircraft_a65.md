# AIRCRAFT-A65 — dynamique libre raffinée qualifiée, CHECK entier échoué

Les deux témoins passent22contrôles chacun et la comparaison demi-pas au seuil conservé. Les deux scènes entières terminent leur CHECK avec quinze erreurs affichées,624messages STOPvolume et cinq contactsTYPE25 ignorés chacune. Aucun crédit d’impact entier ni nouvelle compilation.

## 1. Faits directement observés ou transcrits

Accord humain explicite «Oui, exécuter ce lot A65» enregistré avec empreintes du plan/proposition/lanceur. Deux Starter propres et quatre Engine CPU1/cap180s, sansGPU/installation/compilation. Les sorties locales enregistrent8001 et16001lignes, chaque pas réellement calculé, et rejoignent1ms ; le second champ terminal provient des huit nœuds TH, car sa dernière animation reste0,995062ms. Aucune extrapolation.

| Cas libre | Lignes natives | Champ terminal ms | Résidu énergie J | Résidu impulsion/support Ns |
|---|---:|---:|---:|---:|
| FREE_REFINED | 8001 | 1.0 | 2.378543902e-08 | 2.715480001e-08 |
| FREE_REFINED_HALF | 16001 | 1.0 | 4.479485528e-08 | 4.808432003e-08 |

Les44contrôles locaux passent : formats binaires/CSV, cycles/horloges et pas, identité de déplacement/sécante, vitesse physique Newmark, KE/P natifs et bilans/supports, masse8g, masse ajoutée0, travail extérieur0, réponse discrète exacte, tractions, domaine élastique et supports. Comparaison KEmax=5.470142415e-06J ; IEmax=5.4914e-06J ; seuil préexistant1,01e-5J.

Les deux CHECK utilisent exactement les anciennes initialisations/cartes originales et appariées, empreintes vérifiées. Les messagesSTOPvolume visent les624ID60001–60624 et concordent dans journal et listing. Chaque résumé affiche15ERRORS/5WARNINGS ; ce décompte n’est pas supposé égal aux624messages détaillés. TYPE25 ignoré cinq fois. Le code0/NORMAL n’est pas un passage. Le premier lecteur étroit cherchaitERROR(S) et STOPsans deux-points : ses champs null/false sont conservés, une nouvelle analyse reconnaît les messages réels.

## 2. Résultats d’un modèle officiel

Aucun nouveau modèle historique officiel. Le moteurA62 inchangé est figé SHA256d36015d6238b5216ae7c5c4cbd909abb5c3cd7b25f724e6ef2faebc4814a4235. Le protocole Newmarkgamma0,5/beta0,25 et ses sources précédemment vérifiées servent au lecteur ; la référence analytique exacte n’est pas ajustée aux sorties. Un passage de ce domaine élastique libre ne valide pas toute la physique de l’impact.

## 3. Affirmations provenant des archives locales

Aucune archive historique, vidéo, photographie ou PDF inspecté/modifié ; aucun dégât connu ciblé. Les sources logicielles et entrées propres au projet sont distinctes des archives historiques.

## 4. Hypothèses propres au modèle

Graine1102090, zéro tirage, unitésg/mm/ms. Les surfaces10×10mm, masse instrumentale8g, quatre nœuds supérieurs libres, vitesse initialeY1mm/ms, supports et propriétés A64 sont conservés. Pas0,000125/0,0000625ms, seuils inchangés. SeulsTFILEdt/2 et arrêt1+dt/2 changent pour enregistrer chaque cycle et sauvegarder la frontière cible, dans la borne d’un pas d’overshoot déjà déclarée. Les masses instrumentales ne fixent pas le futur pas d’avion ; propriétés de cohésion non identifiées comme mesures physiques réelles.

## 5. Résultats dérivés

Le défaut de sortieA64 est résolu dans ces nouveaux essais : les bilans physiques, la solution discrète exacte et la convergence temporelle au seuil déclaré passent simultanément. Le critère grossierA63 et l’analyse initialeA64 restent échoués/conservés. Les CHECK entiers montrent que le correctif d’assemblage surfacique ne suffit pas à rendre la scène entière admissible. Il faut localiser leurs contrôles géométriques et contacts incompatibles avant toute extension dynamique. Scripts, paramètres, horloges et messages sauvegardés ; anciens fichiers vérifiés par métadonnées, anciens étatsCHECK rehashés.

## 6. Contradictions et informations manquantes

Les erreursCHECK et contacts ignorés sont bloquants malgréNORMAL. A52nonintégré ; domaines matériaux, inerties, bilans locaux entiers, état/retour arrière, dommage général et grandes rotations restent non qualifiés. Échecs au repos et sous mouvements imposésA62 préservés. LotA65 de quatre Engine entièrement consommé ; aucun nouveau correctif moteur appliqué. Meilleur impact entier0,0200001220703125s, dix secondes physiques et vidéo3D incomplètes. Aucun RKE compensateur ni temps manquant fabriqué.

AIRCRAFT-A66 : audit borné en lecture seule des nouveaux messages CHECK A65, des624éléments60001–60624 et des cinq contacts TYPE25, puis de leurs branches sources natives. Réutiliser les sorties A65 sans nouveau Starter/Engine, sans patch/compilation ni modification des budgets. Distinguer un contrôle volumique appliqué à une surface valide d’une géométrie réellement invalide ; ne pas supprimer les messages ou substituer silencieusement les contacts. Préparer ensuite la proposition concrète nécessaire. A65 quatre contrôles autorisés exécutés : local libre raffiné PASS, scènes entières quinze erreurs affichées/624STOPvolume/cinqTYPE25 ignorés chacune. Les échecs au repos/imposés A62, temporels grossiers A63 et lecteur incomplet A64 restent préservés. Meilleur impact entier0,0200001220703125s ; dix secondes et vidéo3D incomplètes. Toute nouvelle modification/compilation du moteur exige un accord explicite distinct.
