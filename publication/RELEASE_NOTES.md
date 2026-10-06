# AIRCRAFT-A08 + AIRCRAFT-A09 — 6 octobre 2026

Deux itérations et tous leurs résultats natifs, configurations, scripts, passations et critères échoués conservés. A08 : cinq contrôles de 0,8 ms avec contact segmenté, historiques complets des moteurs, masses nodales et subdivision coplanaire 960→3840 triangles. L’écart de centre de masse A07 est expliqué dans le reviewer par la répartition native selon les angles ; aucun ancien calcul ni matériau changé.

A09 : neuf nouveaux contrôles de 0,4 ms, matériaux inchangés, formulations TYPE7 et RBE3, vitesses de rotation observées. Stfac multiplie seulement la branche principale de raideur : 0,1 ne change pas les historiques sauvegardés ici. Les facteurs 0,01/0,001 sont déclarés séparément avant leur exécution et changent la réponse sans résoudre l’énergie. La variante pénalité des 32 RBE3 est confirmée par le Starter ; les canaux globaux sont identiques mais pas tous les canaux internes. La masse native est effectivement répartie différemment : vers les hôtes en cinématique, conservée aux points internes en pénalité ; la somme des deux domaines reste vérifiée.

Déficit énergétique, sensibilité spatiale et dépassements plastiques restent visibles. La formule de rotation indépendante des coques ne reproduit pas les RKE natifs ; le RKE brut des poutres initial incompatible avec la rotation globale n’est jamais ajouté au bilan. Premiers diagnostics des lecteurs, erreurs d’unités/métadonnées et corrections conservés, sans nouvelle exécution mécanique ni changement de tolérance.

Ces contrôles portent sur l’amorce du contact moteur dans l’avion couplé, avec façade déplacée ; pas traversée historique, écrasement réel ou fragmentation qualifiés. Prochaine étape A10 : référence élastique sans redistribution RBE3 et identification de la convention d’inertie native. Aucun résultat de dégâts NIST utilisé comme cible. Sources tierces exclues, liens et hashes conservés ; aucune ancienne release remplacée.


7 archives complémentaires ; 57 archives précédentes conservées. Sources externes exclues, scripts et résultats propres sous MIT. Vérification de publication sans relancer les solveurs.
