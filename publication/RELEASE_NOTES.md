# Instantané AIRCRAFT-A56+AIRCRAFT-A57 — 13 octobre 2026

Instantané du **13 octobre 2026** : **AIRCRAFT-A57 terminée**, prochaine étape **AIRCRAFT-A58**. Le registre compte **176 entrées**. Les deux itérations conservent les anciens moteurs, budgets et critères échoués ; la vidéo des dix secondes physiques demeure incomplète.

A56 compile le correctif du tampon temporaire dans un quatrième moteur isolé. Il ne résout pas la corruption : sept arrêts cohésifs implicites avant le premier pas, parmi17Engine nouveaux, aucun Starter. Les contrôles natifs de graphe/attaches, quatre témoins explicites et deuxTYPE7 passent dans leur domaine. Une mesure de740appels lit le tampon **d'origine** ELBUF_STR%GBUF%SMSTR : demande0, double8octets, bornes1..0, capacité0. Son pointeur est exactement SAV transmis à SRCOORK. La proposition initiale ciblait une copie temporaire ; son échec est conservé.

A57 applique le nouveau correctif original explicitement autorisé dans **un cinquième moteur séparé**, avec les correctifs antérieurs conservés. Source figée3d75ff13d1946f6d28a43920eac4fa2aae41b27a, compilation plafonnée1h/sixCPU, sans GPU ni installation. Seule nouvelle différence : allocbuf_auto.F réserve au moins21*NEL valeurs au TYPE43 sans changer largeurs de redémarrage, offsets ni nombre de valeurs restaurées. Les sources dérivées/patch/binaire AGPL restent hors du manifeste MIT ; scripts propres, sorties et empreintes sont conservés.

Les mesures et critères A57 sont enregistrés séparément : **17 nouveaux Engine**, aucun ancien moteur rejoué, contrôles plafonnés180s/unCPU. **Capacité native originale21/NEL1 et pointeur SAV exact, en-tête mémoire intact ; les quatre témoins implicites restent àT=0 avecSTOP volume nul etUSER BREAK. Graphe/attaches, quatre témoins explicites et deuxTYPE7 passent dans leur domaine, physique entière toujours non qualifiée.**


Les [rapports A56](wtc1_simulation_v8/output/aircraft_a56/rapport_aircraft_a56.md) et [A57](wtc1_simulation_v8/output/aircraft_a57/rapport_aircraft_a57.md) séparent les six catégories de preuve. Le CHECK entier échoué et les cinqTYPE25 ignorés ne sont pas annulés par la correction d'un tampon. A52 n'est pas intégré, les travaux/inerties et la couverture énergétique entière restent manquants. Aucune masse compensatoire, RKE inventée ou cible de dégâtsNIST. Sources historiques et anciennes archives restent intactes.

Meilleur impact entierA20 : **0,0200001220703125seconde**. Aucun temps des témoins isolés n'est crédité à l'impact entier. Aucune vidéo de dix secondes fabriquée par extrapolation ou ralenti ; publication/intégrité ne signifie ni validation physique ni validation historique.


2 archives complémentaires ; 131 archives précédentes conservées. Sources externes exclues, scripts et résultats propres sous MIT. Vérification de publication sans relancer les solveurs.
