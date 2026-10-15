# Instantané AIRCRAFT-A88+AIRCRAFT-A89 —15octobre2026

Instantané du **15 octobre 2026** : **AIRCRAFT-A89 terminée**, prochaine **AIRCRAFT-A90**, registre **208 entrées**. **Les dix secondes physiques et la vidéo3D restent à produire.**

**A88 prépare une observation ciblée du second essai avec le moteur A87 inchangé.** Les deux régressions A87 sont conservées à l’identique, mais le coupon n’a qu’un pas accepté. Les positions typées des modes,NCYCLE/TT sont calculées depuis cinq déclarations source épinglées et bornées par les symboles du binaire exact. Treize contrôles source/observateur, cinq du lanceur et dix contrôles finaux passent statiquement ; aucun Engine pendant la préparation. L’ancienne place de CHECK conditionnelle n’est pas réaffectée.

**A89 consomme son unique Engine distinctement autorisé après publication A86+A87 vérifiée.** UnCPU/plafond180s, mêmes cartes/restart initial, zéro Starter/correctif/compilation/GPU/installation/extension entière. Dix-neuf arrêts matériels, lecture seule des données et configuration des registres matériels de débogage seulement. Les points sont désactivés après le critère2 du second essai, puis le moteur termine lui-même. Lecteur code0, Engine code2 sans signal : observation réussie, trajectoire physique échouée. Les anciens libellés consoleA85 sont cosmétiques ; configuration et répertoire A89 sont explicites et conservés.

**Le second essai est maintenant observé avec son cycle/temps natifs.** NCYCLE2,TT0,00025ms ; IDYNA2,IQSTAT0,INSOLV1,NITOL123,ISPRB0,IDTC1,ILAST0,NFXVEL4,NINTER0,IRODDL0,NSPMD1,NTHREAD1,IMCONV0,ICONT0,NDDL8. F libre contient huit zéros exacts,DE0=1e−20,EIMP0,R02=1. U2=DU2=0 aux retours natifs. Au critère2 :URNaN,RR0,ERInfinity ; arrêt79/ISTOP−2.

**La condition sur toute la correction brute exclut les quatre mouvements imposés.** Les seules composantesDD non nulles sont les quatreZ supérieurs imposés,−1,90288107842e−9mm chacune ; D vaut−1,328447181728e−8mm sur cesZ. ALL(DD brut==0) est donc faux malgré une norme libre nulle. R2=0 est reconstruit depuisF nul etIRIKS0 depuisIDTC1 selon le code ; ces deux variables locales n’ont pas été directement lues. Les autres paramètres sont observés. Les dix contrôles de transcription/portée A89 passent.

**A90 doit préparer un contrôle exact de la correction projetée/condensée.** Il ne suffit pas de supprimer la conditionDD ou de tester seulement son carré : un petit non-zéro libre dont le carré sous-déborde doit rester bloquant. Aucun nouveau correctif moteur n’est appliqué ou compilé par A89, aucune tolérance changée. Un nouvel accord distinct sera nécessaire pour une nouvelle modification ou un autre lot.

**Deux états sauvegardés seulement, dernier0,000125ms.** Le temps tenté0,00025ms n’est pas un état accepté. Rupture, plateaux et refermeture non atteints ; aucun crédit nouveau sur l’impact entier. L’unique Engine A89 est consommé, sans réessai. Anciennes sorties, budgets, critères échoués, cinqTYPE25 ignorés et107391avertissements restent conservés ; aucune archive historique ou vidéo réanalysée, aucun RKE inventé ou ajustement aux dégâts connus.

Les [rapports A88](wtc1_simulation_v8/output/aircraft_a88/rapport_aircraft_a88.md) et [A89](wtc1_simulation_v8/output/aircraft_a89/rapport_aircraft_a89.md) séparent les six catégories de preuve. **Meilleur impact entier0,0200001220703125s.** Publication/CI attestent l’intégrité, pas la validation physique de l’impact réel.


1 archives complémentaires ; 148 archives précédentes conservées. Sources externes exclues, scripts et résultats propres sous MIT. Vérification de publication sans relancer les solveurs.
