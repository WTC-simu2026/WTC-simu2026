# Instantané AIRCRAFT-A48+AIRCRAFT-A49 — 12 octobre 2026

Instantané du **12 octobre 2026** : **AIRCRAFT-A49 terminée**, prochaine étape **AIRCRAFT-A50**. Le registre compte **168 entrées**. La panne d’assemblage est reliée aux peaux inférieures du radôme ; une représentation équivalente des chaînes rigides permet au modèle entier de terminer son diagnostic.

A48 teste quatre petits assemblages puis une copie entière sans les368RBE3. Leur retrait conserve masse totale, centre et ADMAS prescrites, mais ne supprime pas SIGSEGV. Une observation du processus fils inchangé capture26paires/156lignes sans colonne attendue dans ASSEMC_KIJ. Les labels originaux restent alors inconnus.

A49 observe aussi les tableaux de coques et coordonnées : **128éléments et302nœuds internes correspondent exactement à l’entrée**, erreur0mm. Les26paires manquantes ont un nœud de peau secondaire d’une racine entièrement rigide et principal d’une liaison cohésive déportée. **Cinq petits reproducer ne reproduisent pas la panne**. L’option numérique Idrill1, vérifiée réellement reçue par le moteur, ne la corrige pas non plus ; le défaut persiste avec des DOF6/6.

Une copie distincte compose **144chaînes déjà entièrement rigides**, sans supprimer leurs déports ou bras de levier. Les3072contrôles indépendants de pose, vitesse et moments passent les seuils pré-déclarés. Coordonnées, matériaux, propriétés, masses, groupes, contacts et RBE3 sont conservés. **Le modèle entier termine maintenant CHECK sans planter**, code0/NORMAL, en7,39s natives. Masse191273837,9425g, centre et ADMAS100368522,1367g restent identiques à la référence.

**Le contrôle mécanique entier reste échoué** :15directions de raideur suspectes,5avertissements récapitulatifs et **49370messages de connectivité** dans le listing, dont48996TYPE2 et374RBE2. Les valeurs négatives extrêmes ne sont pas interprétées comme un mécanisme physique. Deux avertissements Starter originaux et cinq TYPE25 ignorés en implicite restent explicites. L’histoire initiale CHECK n’est pas convertible ; l’inertie redistribuée et le travail natifs ne sont pas supposés qualifiés. Un addendum distingue mat_ID4 et Npt_ply3 dans TYPE19, sans modifier l’entrée.

A49 comprend sept préparations Starter et neuf Engine nouveaux, un thread CPU chacun, caps180s, sans GPU. Aucun patch logiciel ou de données mécaniques, installation, compilation ou ancien calcul réussi relancé. Les [rapports A48](wtc1_simulation_v8/output/aircraft_a48/rapport_aircraft_a48.md) et [A49](wtc1_simulation_v8/output/aircraft_a49/rapport_aircraft_a49.md) séparent les six catégories de preuve. Les bilans natifs de la copie composée et les connexions TYPE2/RBE2 sont la suite, avec contacts originaux conservés. A40 chargé/croissance, A34 peaux et A36 raffinement restent échoués.

La vidéo3D des **dix premières secondes physiques** reste incomplète : meilleur impact entier A20 = **0,0200001220703125seconde**. Aucun temps de diagnostic ou de panneau n’est crédité à l’impact entier. L’intégrité de publication ne valide pas la physique ni l’événement historique.

Archives antérieures et critères échoués conservés.


2 archives complémentaires ; 125 archives précédentes conservées. Sources externes exclues, scripts et résultats propres sous MIT. Vérification de publication sans relancer les solveurs.
