# Instantané AIRCRAFT-A86+AIRCRAFT-A87 —15octobre2026

Instantané du **15 octobre 2026** : **AIRCRAFT-A87 terminée**, prochaine **AIRCRAFT-A88**, registre **206 entrées**. **Les dix secondes physiques et la vidéo3D restent à produire.**

**A86 prépare une garde pour les deux critères relatifs exactement nuls.** Le cas A85 mesuraitDE0=1e−20,EIMP=0,U2=DU2=0, force libre et correctionDD exactement nulles. La proposition définit les ratios à0 dans ce seul sous-espace dégénéré, sous restrictions explicites : Newmark non quasi-statique, Newton modifié, critères123, mouvement imposé, aucune interface générale/rotation, un domaine/un thread, itération>=2. Le chemin non nul et CRIT_ITE restent textuellement conservés ; les tolérances ne changent pas. L’itération1 garde sonInfinity possible. Les86cas mathématiques et16contrôles finaux de portée passent statiquement, sans constituer une validation Fortran native.

**A87 applique le diff exact après accord distinct et publication A84+A85 vérifiée.** Dixième moteur isolé, sourceNL_SOLV seule nouvellement modifiée, recette et correctifs A73 conservés. Compilation309,388s sur sixCPU, dans le plafond1h, sans GPU, installation ou Starter compilé. Nouveau binaireSHA2569e72f04411158c9b48f67968eff3fe01f741aca5cb5bd3201985cdbaf75e27cd ; neuf anciens moteurs conservés.

**Les deux régressions du nouveau binaire passent sans relâcher leurs seuils.** FREE_Ismstr4 etAREA_EVOLUTION_FREE_Y atteignent1ms. Pour chaque cas,8001lignes/99colonnes décodées sont identiques valeur par valeur aux binaires A67 sauvegardés. L’analyse mécanique A67 est reprise sur les nouvelles sorties, avec ses seuils et portées d’origine. La portéeY à aire variable reste distincte d’une qualification globale du mouvementX imposé. Aucun ancien solveur n’est rejoué ; aucun convertisseur natif lancé.

**La boucle A81 franchit son premier pas, puis s’arrête au suivant.** Le marqueur de garde apparaît une fois à l’itération2 du premier essai. Un cycle1 à0,000125ms et deux états TH réels, dont un à temps positif, existent. Dernier temps binaire0,0001250000059371814ms : c’est une durée locale du coupon, aucun crédit sur l’impact entier. Au second essai,Infinity/NaN persistent et l’Engine s’arrête à nouveau au maximum30 puis79/ISTOP−2. La condition précise qui exclut ce second cas n’a pas été lue nativement et ne sera pas déduite sans preuve.

**La qualification locale reste échouée.** Ni plateau de compression, rupture, refermeture ou force après rupture n’est atteint. Les premiers champs natifs non nuls sont conservés, sans qualifier leur sémantique de dommage. Le résidu énergétique sur les deux états vaut au maximum1,39045e−12J pour le seuil1e−7J conservé ; cette fenêtre initiale ne valide pas la boucle0,65ms ni le travail indépendant des réactions. DifférenceKE reconstruite/native1,82489e−12J sur cette seule fenêtre. Aucun RKE ajouté ou seuil augmenté après coup.

**Trois Engine sont consommés sur quatre maximum, zéro Starter.** UnCPU/plafond180s chacun, zéro GPU/installation/extension entière. La quatrième place de CHECK était conditionnelle aux critères locaux ; elle reste inutilisée et n’est pas réaffectée. Les cinqTYPE25 ignorés et107391avertissements restent bloquants. Anciennes sorties, sources, budgets et critères échoués sont conservés. Aucune archive historique ou vidéo source réanalysée.

**A88 doit exploiter les nouveaux états en lecture seule et préciser le refus du second essai.** La garde du premier pas, les deux régressions et une trajectoire complète sont trois niveaux de preuve distincts. Aucun nouveau calcul automatique ou modification du moteur n’est couvert par la place conditionnelle restante.

Les [rapports A86](wtc1_simulation_v8/output/aircraft_a86/rapport_aircraft_a86.md) et [A87](wtc1_simulation_v8/output/aircraft_a87/rapport_aircraft_a87.md) séparent les six catégories de preuve. **Meilleur impact entier0,0200001220703125s.** Publication/CI attestent l’intégrité, pas la validation physique de l’impact réel.


1 archives complémentaires ; 147 archives précédentes conservées. Sources externes exclues, scripts et résultats propres sous MIT. Vérification de publication sans relancer les solveurs.
