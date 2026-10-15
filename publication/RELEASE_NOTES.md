# Instantané AIRCRAFT-A84+AIRCRAFT-A85 —15octobre2026

Instantané du **15 octobre 2026** : **AIRCRAFT-A85 terminée**, prochaine **AIRCRAFT-A86**, registre **204 entrées**. **Les dix secondes physiques et la vidéo3D restent à produire.**

**A84 localise les normalisations en lecture seule.** La source épinglée définitRE=DE0/EIMP etRU=LS3*sqrt(DU2/U2), avec plancherDE0=1e−20 pour les très petits incréments. PRODUT_UHP forme une norme après projection/condensation sur les inconnues libres. Des dénominateurs nuls étaient une hypothèse compatible à vérifier. Les16contrôles source/observateur et8contrôles du lanceur passent statiquement ; aucun moteur n’est exécuté pendant cette préparation.

**Un addendum corrige l’interprétation de la ligne0 A83.** Le même en-tête visuel recouvre à0 les grandeurs initiales sqrt(U2),sqrt(R02),EIMP ; les lignes positives impriment les ratiosRU,RR,RE. Les chaînes transcrites A83 sont exactes ; leur appellation générale de ratios était trop large pour0. Le rapport d’origine reste conservé et la correction est explicitement ajoutée dans A84. Infinity/NaN aux itérations positives restent observés.

**A85 exécute son unique Engine distinctement autorisé après vérification A82+A83.** UnCPU, plafond180s, zéro Starter, correctif, compilation, GPU, installation ou prolongement entier. Carte A83, restart initial propre A81 et tous critères/paramètres inchangés. Durée5,004s avec lancement,0,641s dans l’observateur. Celui-ci retourne0 et l’Engine2 sans signal terminal : la réussite de mesure ne vaut pas convergence. Onze arrêts matériels bornés, lectures seules des données, aucune instruction ou donnée numérique modifiée ; désactivation après le critère2, puis arrêt propre du moteur.

**Les valeurs natives confirment les deux divisions dégénérées.** Aux critères1et2 : DE0=1e−20,EIMP=0,R02=1 et les huit composantesF libres exactement0 ; ER=+Infinity. À2 : U2=DU2=0 au retour natif,LS3=1 etUR=NaN. Les24composantes de correctionDD sont nulles, tandis que D contient−1,90288107842e−9mm sur les quatreZ supérieurs imposés. La norme libre peut donc être nulle malgré le mouvement imposé. Les opérandes consommés établissent1e−20/0 et0/0 dans ce cas précis ; leDE brut antérieur au plancher n’est pas capturé.

**Les16contrôles de transcription et portée A85 passent ; la physique reste échouée.** Le carré du résidu recalculé depuisF est étiqueté dérivé, jamais assimilé à une lecture de la variable localeR2. Le temps/cycle global n’a pas été observé ni promis. EIMP est une variable d’algorithme, pas l’énergie physique totale. Un seul état TH réel et une animation initiale à0ms ; maximum30 puis MESSAGE79/ISTOP−2, avertissementsPARITH/ON etISOLID0 conservés. Compression, rupture, refermeture, plateaux, travail de fracture et peuplementUSR restent non mesurés.

**A86 doit préparer un traitement borné des cas exactement nuls.** Définir gardes et témoins adverses pour conserver les critères non nuls, les déséquilibres et l’énergie indépendante. Aucun correctif moteur appliqué ou compilé. Le seul EngineA85 est consommé sans remplacement ; anciennes sorties, budgets, critères échoués et107391avertissements A73 restent conservés. Aucun RKE inventé, temps interpolé, ajustement aux dégâts connus ou archive historique réanalysée.

Les [rapports A84](wtc1_simulation_v8/output/aircraft_a84/rapport_aircraft_a84.md) et [A85](wtc1_simulation_v8/output/aircraft_a85/rapport_aircraft_a85.md) séparent les six catégories de preuve. **Meilleur impact entier0,0200001220703125s.** Publication/CI attestent l’intégrité, pas la validation physique de l’impact réel.


1 archives complémentaires ; 146 archives précédentes conservées. Sources externes exclues, scripts et résultats propres sous MIT. Vérification de publication sans relancer les solveurs.
