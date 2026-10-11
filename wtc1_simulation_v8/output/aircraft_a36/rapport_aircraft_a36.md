# AIRCRAFT-A36 — budgets de réactions expliqués, raffinement incomplet

Onze nouveaux calculs natifs de 50 µs sont terminés : neuf témoins initiaux et deux translations plus observables. La compilation A35 n’est pas prolongée. Le témoin Windows confirme le même écart initial que Linux; le raffinement améliore la comparaison mécanique. Une prédiction tirée des sources et des témoins distincts de translation expliquent les réactions implicites dans leur périmètre sans facteur ajusté. Les échecs de convergence et l’écart d’historique initial restent conservés; aucun nouvel impact entier ou vidéo de dix secondes créé.

## 1. Faits directement observés ou transcrits

Les onze préparations Windows et onze moteurs terminent. Versions Windows conservée et Linux MUMPS compilée A35. Source figée, CPU un thread, aucun GPU ni ajout de masse. Bilans et champs natifs sont contrôlés, avec identifiants de nœuds lus dans les colonnes. Les états antérieurs ne sont pas recalculés. A34+A35 ont été publiées avec deux archives, leurs empreintes et deux contrôles GitHub réussis; la publication n’est pas une validation physique.

## 2. Résultats d’un modèle officiel

Les sources épinglées OpenRadioss, commit bad6688602d770e019b75773d2d5a48b4f9bd918, indiquent que BCS1TH_IMP accumule une intégrale trapézoïdale du résidu nodal; FV_FINT0 inclut séparément MS×DY_A pour le travail imposé. Chemins, liens primaires et empreintes sont enregistrés dans primary_source_review.json. Ces lignes motivent la prédiction testée; aucune modification du moteur. Aucun résultat NIST n’est utilisé comme cible. Le préparateur Linux A35 reste incomplet et H3D non qualifié.

## 3. Affirmations provenant des archives locales

Aucune nouvelle lecture de photographie, vidéo ou archive. Aucune observation historique AA11 nouvelle. Les premiers défauts A35, les seuils et sorties A34 ainsi que les budgets de l’avion restent conservés.

## 4. Hypothèses propres au modèle

Graine1102061, zéro tirage. Même cube1mm, LAW2source E73100MPa/ν0,33/densité0,00278g/mm³, masse0,00278g, TYPE14/HA8 Isolid14/Ismstr4/Icpre2/Gauss222/Iframe2. Charges aux faces ou translation identique de tous les nœuds; déplacements0,001mm avec rampe3u²−2u³ en0,05ms. Références conventionnelles2³Gauss N2/N4/N8/N16 calculées avant les nouveaux moteurs, avec tenseur inchangé et équilibre/travail virtuel contrôlés. Pas explicite10⁻⁵ms, Newmarkγ0,5/β0,25 et pas implicite0,001/0,0005ms. Deux nouvelles translations rigides, déclarées séparément avant calcul, ont une amplitude0,1mm et des pas0,0001/0,00005ms : même masse et déformation nulle, énergie cinétique observable environ10000fois plus grande. Compatibilité et réactions ne sont testées que dans ce périmètre sans contact/plasticité/rupture.

Prédiction avant les nouveaux résultats : en implicite, l’impulsion TH plus la variation de quantité de mouvement des nœuds imposés donne la variation totale; le travail issu de TH plus la variation de leur énergie cinétique donne le travail externe. Il s’agit des mêmes masses physiques déjà présentes, sans ajout dans l’entrée. En explicite, TH inclut déjà leur contribution. Le témoin de translation de tous les nœuds prédit une réaction TH implicite nulle et une inertie totale non nulle, ce qui distingue un budget additif d’un facteur2. Tolérances originales2%+10⁻⁹Ns et2%+10⁻⁷J conservées. Aucun nouveau RKE.

## 5. Résultats dérivés

| Cas | IE(J) | Référence(J) | Écart U(mm) | Critères individuels |
|---|---:|---:|---:|---|
| WINDOWS_EXPLICIT_N2 | 4.140536e-05 | 4.27679785e-05 | 2.48815385e-05 | échoués |
| WINDOWS_EXPLICIT_N4 | 4.01907e-05 | 4.06579247e-05 | 1.13928503e-05 | réussis |
| LINUX_EXPLICIT_N4 | 4.01907e-05 | 4.06579247e-05 | 1.13928503e-05 | réussis |
| MUMPS_N4 | 4.018911e-05 | 4.06579247e-05 | 1.13928503e-05 | réussis |
| MUMPS_N4_HALF | 4.018992e-05 | 4.06579247e-05 | 1.13928503e-05 | réussis |
| MUMPS_N8 | 3.967828e-05 | 3.98686109e-05 | 7.98062148e-06 | réussis |
| WINDOWS_TRANSLATION | 5.799168e-40 | 0 | 0 | réussis |
| LINUX_TRANSLATION | 5.799168e-40 | 0 | 0 | réussis |
| MUMPS_TRANSLATION | 1.036393e-39 | 0 | 0 | réussis |
| MUMPS_TRANSLATION_DT100 | 2.146615e-35 | 0 | 0 | réussis |
| MUMPS_TRANSLATION_DT050 | 4.512266e-35 | 0 | 0 | réussis |

10/11 ensembles individuels, 11/11 bilans et 33 champs natifs réussis. 10/11 ensembles de budgets de réactions/travail et comparaison au momentum global réussis. Les comparaisons Windows/Linux, explicite/implicite et demi-pas sont conservées dans comparison_review.json.

| Raffinement indépendant | Écart énergie | Écart U commun(mm) | Critère |
|---|---:|---:|---|
| N2→N4 | 5.18977% | 4.05507242e-05 | échoué |
| N4→N8 | 1.97979% | 1.21573402e-05 | échoué |
| N8→N16 | 0.768023% | 1.07089193e-05 | échoué |

Le résultat N2 Windows reproduit l’écart A35 Linux; la compatibilité du fichier préparé n’explique donc pas à elle seule l’écart de la référence. Les critères individuels améliorés à N4/N8 ne remplacent pas la convergence : le seuil indépendant N8→N16 (0,5% et2×10⁻⁶mm) et le seuil natif N4→N8 (1%+10⁻⁷J) sont conservés même lorsqu’ils échouent. Le test de translation et le budget additif ne réécrivent aucun ancien critère A35.

La translation initiale passe les prédictions additives de réaction et travail, mais échoue au rapprochement du momentum global et des nœuds. Sa très faible énergie ne permet pas de qualifier un bilan observable. Les deux nouveaux témoins0,1mm ont une énergie cinétique physique supérieure à10⁻⁶J, un TH implicite nul et des prédictions additives d’impulsion/travail, momentum et KE globale réussies. Les pas plus fins et leur comparaison temporelle réussissent; la cause précise de la différence d’historique initial n’est pas identifiée par ces seules mesures. Aucun échec initial n’est remplacé. Les masses nodales physiques indépendantes déterminent KE et P, sans facteur numérique ajusté.

## 6. Contradictions et informations manquantes

Les réactions ont une interprétation testée dans ce seul cube; contraintes générales, inerties rotatoires, changement de masse et transferts de contact restent hors du périmètre. Une réussite énergétique et de déplacement face à une référence au même maillage ne suffit pas à montrer la convergence continue. La transition explicite→implicite, contact, plasticité, rupture et impact entier restent à mesurer. Les peaux composites et leurs prises courbes A34 ne sont pas qualifiées par ce métal isotrope. Dix secondes physiques d’impact ne sont pas produites; meilleur entierA20=20ms. Aucun prolongement balistique ou horloge de rendu ne remplace la dynamique.

AIRCRAFT-A37 : reprendre A36 et les sorties en cache. Le nouveau moteur MUMPS, les budgets physiques de réactions dans ce témoin élastique et la compatibilité de fichiers fraîchement préparés fonctionnent dans leur périmètre; ce n’est pas une validation entière. Les raffinements de la référence indépendante et du natif restent hors des seuils et doivent être conservés. Passer à un témoin explicite→implicite frais avec mouvement libre et contact borné, mêmes masses, état transféré complet, impulsions/travail/énergie avant-après, sans ancien solveur relancé. Mesurer le coût réel sur un impact entier court uniquement après ces critères de transition; ne pas projeter le rapport de pas du cube sur dix secondes. Pour la mécanique des peaux A34, reprendre séparément la formulation et ses champs sans multiplier les contrôles identiques ni ajuster la référence. Aucun changement de densité/matériau/masse/inertie, RKE inventé ou dommage connu comme cible. Préparateur Linux toujours incomplet, compilation A35 terminée; aucune nouvelle installation/compilation engagée. Objectif dix secondes physiques 3D puis vidéo/GIF incomplet, meilleur entier A20=20ms. A34+A35 publiées et vérifiées; A36 locale, prochaine paire A36+A37 après vérification.
