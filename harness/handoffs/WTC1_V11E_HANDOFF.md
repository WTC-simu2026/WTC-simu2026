# Reprise WTC 1 après V11E

Lire intégralement AGENTS.md et harness/state.json puis exécuter Test-WtcHarness.ps1 depuis le dossier actif. V11E est terminée, prochaine V11F. L'ancien point V8H et l'ancien verrou documentaire V10J ne remplacent pas l'état courant : prototypes exploratoires avec hypothèses visibles autorisés par Jeremy. Ne pas rescanner les archives ni relancer de calcul ancien sans question précise.

## Acquisition de cette itération

Section de dalle à fibres, isotherme à 20 °C : traction du béton élastique puis adoucissante, endommagement irréversible, déchargement sécant et fermeture en compression ; armatures élastiques-parfaitement plastiques. Interface `Section.trial(old, [eps0, kappa])` sans modification de l'état ancien ; engagement seulement après convergence. Vérification de section AVANT transfert au panneau. Aucun calcul de panneau V11D, de propagation V11B ou Blender modifié.

14 parcours, 6 768 états, 86/86 contrôles de calcul (62 analytiques et intégrations séparées +24 d'ensemble). Audit supplémentaire des fichiers sauvegardés :10/10 contrôles. Pas de relecture multi-agent ni de comparaison à un autre solveur pour cette itération ; ne pas les revendiquer. Aucun logiciel installé, GPU, impact ou incendie calculé.

Dossier final : `wtc1_simulation_v8/output/v11e_cracked_section`. Rapport : `rapport_v11e_section_fissuree.md`. Résultats : `results_v11e.json`. Figure : `synthese_v11e_section_fissuree.png`. Inventaire : `section_inventory.json`. Historiques et bilans : `section_summaries.csv`, `section_history.csv`, `section_fibers.csv`, `cycle_vertices.csv`, `material_coupons.csv`, `convergence_comparison.csv`. Audits : `numerical_audit.json`, `source_manifest.json`, `offline_manifest.json`, `release_audit.json`.

Code neuf : `scripts/v11e_section_model.py`, `test_v11e_section.py`, `run_v11e_cracked_section.py`, `audit_v11e_release.py` sous wtc1_simulation_v8. Configuration : `data/v11e_cracked_section_predeclaration.json`.

L'essai final est `tmp/v11e_cracked_section/attempt02`, vérifié puis copié à l'identique dans un dossier final initialement absent. Les répétitions refusent tout dossier existant. `attempt01` est conservé comme diagnostic remplacé (compression au milieu de la fibre extérieure) ; voir son SUPERSEDED.md. Les scripts actuels et la configuration reproduisent attempt02, pas attempt01.

## Hypothèses et sources

Largeur80in =2,032m ; épaisseur équivalente4,35in =0,11049m, héritées de l'exemple V11A/V11D. Pas de géométrie exacte de dalle-bac. Ec2500ksi, fc3ksi et ft1MPa hérités des HYPOTHÈSES antérieures, pas d'une caractérisation WTC. Aucun inventaire réel d'armatures acquis.

Armatures HYPOTHÉTIQUES : E200GPa, fy400MPa ; ratios d'aire totale0/0,001/0,002/0,004 de la section brute. Nappes supérieure seule, inférieure seule ou deux symétriques partageant le total. Centres à25mm des faces. Adhérence parfaite, pas de glissement interne acier-béton, bac, cisaillement, confinement, plasticité en compression du béton, flambement/fatigue/rupture d'armature ou vitesse. L'écran1% de déformation d'acier est une limite de domaine CHOISIE, pas la rupture mesurée.

Ac+As=Abrute : l'aire de béton est réduite uniformément du taux d'acier. C'est une approximation diffuse de remplacement, pas les trous réels des barres. 160fibres béton au milieu de bandes égales +0/1/2points acier ; raffinements80/320. Le défaut d'inertie élastique de la quadrature milieu est le facteur1−1/n² ; la comparaison analytique en tient compte.

Gf50/100/150J/m² et longueur LONGITUDINALE Lch0,05/0,10/0,20m selon variantes ; référence100 et0,10. Hypothèses non calibrées, jamais l'épaisseur de dalle ni la hauteur de fibre. Ne pas transformer le nombre de fibres en nombre de fissures. Gf/Lch règle ici la loi contrainte-déformation ; deux couples de même quotient produisent la même courbe de section. Pas de validation de localisation longitudinale ou d'indépendance du maillage d'un futur panneau.

Trois pages de documentation primaire consultées sur le web le6septembre2026, liens et périmètres dans configuration/manifeste/rapport : DIANA Total Strain Crack Models (traction linéaire avec Gf et largeur de bande), DIANA Theory74.2 (ouverture/déchargement sécant/fermeture), OpenSees ElasticPP. Références de MÉTHODE uniquement, pas données WTC ni exécution de ces logiciels. Aucune nouvelle analyse de PDF, vidéo ou archive. Anciennes sources et sorties conservées, contrôles d'intégrité seulement.

## Équations et contrôles à préserver

eps(y)=eps0−y*kappa, y positif vers le haut, traction positive. N=ΣAσ ; M=−ΣAyσ. K=ΣAEt[1,−y]ᵀ[1,−y]. Le travail N*d(eps0)+M*d(kappa) et les énergies de section sont en J/m de longueur, PAS en J d'un étage. Les contraintes sont en Pa=J/m³. Crédit d'énergie, résistance ou masse transféré à un calcul global : zéro.

Béton : e0=ft/E ; ef=2Gf/(ftLch)>e0 obligatoire ; tension σ=Eeps puis ft(ef−eps)/(ef−e0) puis0. r=max historique positif ; pente sécante σenv(r)/r pour décharge/recharge. En compression σ=Eeps après fermeture à0 ; r n'est jamais effacé. Pas de guérison ni contrainte résiduelle de traction. Stockage ψ=σε/2 ; D=ft*ef/[2(ef−e0)]*bornage(r−e0,0,ef−e0). À ouverture complète D=Gf/Lch, triangle pré-pic inclus. Travail calculé séparément par primitive exacte des segments de contrainte, puis W=ψ+D vérifié. Fermeture compressive ici réversible, sans frottement ni déformation plastique de béton.

Acier : essai E(eps−eps_p), retour à±fy, eps_p mis à jour si plastification. D incrémentale=fy|delta eps_p|, ψ=σ²/(2E). Travail calculé par intégration des branches élastique/plastique, non défini par la somme des énergies. Pas d'écrouissage.

La courbure est imposée et N=0, sauf une précompression de5%fcAc montée en20pas. Ce n'est pas une charge historique. L'équation N(eps0) est linéaire par morceaux : toutes les ruptures de pente sont énumérées, et une seule racine à tangente axiale positive est requise. Racine multiple/absente : arrêt non résolu, pas stabilisation ou verdict d'effondrement. Les intervalles neutres sont comptés à part ; la courbure contrôlée peut suivre une branche à moment décroissant sans démontrer sa stabilité dynamique.

Essais d'équilibre et de bissection sans engagement de dommage/plasticité. Première fissure et premier acier plastifié enregistrés mais n'arrêtent pas le parcours. Les courbures de ces deux événements sont les premiers ÉCHANTILLONS, pas des seuils continus précis. Arrêt au domaine fc à la FACE extérieure exacte, récupérée par E*(eps0−|kappa|h/2), ou au domaine de déformation acier1% ; le dernier incrément est subdivisé. Le milieu d'une fibre sous-estimait la compression de face dans attempt01, d'où attempt02 et quatre tests ajoutés.

La somme des travaux matériaux est exacte pour les incréments de déformation linéaires engagés. Le travail des N/M aux extrémités calculé par trapèzes est contrôlé SÉPARÉMENT : erreur finie qui diminue à demi-pas. Ne pas confondre ce bilan isotherme local avec un bilan thermique, dynamique ou de gravité du bâtiment.

## Résultats utiles

13parcours atteignent leur borne dans le domaine choisi ; le cas avec précompression atteint fc en face à kappa0,06740085992261993m⁻¹ et M19,6482696789kN·m. Aucun de ces statuts ne signifie survie ou chute d'un plancher. Tous les parcours représentent des chargements imposés de section.

À kappa0,08m⁻¹, moments de la bande : sans armature0,289531kN·m ; symétrique0,1%4,731342 ;0,2%8,834925 ;0,4%16,527552. Avec0,2% en nappe supérieure seule2,753930, inférieure seule15,051657. Le cas supérieur avec flexion inversée est son miroir. Ce ne sont pas des charges admissibles de plancher.

Cycle référence : sommets0,+0,012,0,−0,012,0,+0,03,0,−0,03,0,+0,05,0,−0,05,0. À kappa finale0, moment266,090870N·m toujours fourni par le contrôle de courbure ; PAS un déchargement à moment nul ni une flèche résiduelle. Dissipations béton224,066649J/m, acier321,242577J/m. Le modèle peut perdre toute traction de béton sans supprimer les armatures ni le contact compressif de la loi.

Résidus max : équilibre axial4,131981201e−11 ; bilan matériaux7,443852833e−16 ; travail extérieur par trapèzes0,00225864554 (0,225864554%). À demi-pas, ce dernier descend à0,000542769640 (0,054276964%). Raffinement160→320 : écart maximal des moments0,000213140096 du pic (0,0213140096%) ; courbure terminale relative2,725694527e−12. Demi-pas : moment relatif1,629464749e−12 et courbure terminale1,078912171e−13. Comparaisons par segment de cycle, sur domaine commun, sans extrapolation après arrêt.

Empreinte numérique : `dcbc9838edf537a696431d5b6a7c61f216f164435901b3e3145bc798763d5dfa`. Calcul54,849803s avec référence/répétition/raffinements/audit, hors génération graphique/rapport. Python3.14.3, NumPy2.4.6, Pillow12.2.0. Les12sorties du manifeste,13entrées/protégés,14anciennes sorties V11D et13anciennes entrées V11D ont été vérifiées ; audit supplémentaire sauvegardé et script d'audit haché.

## Prochaine V11F

Intégrer la section au panneau V11D à froid, avec une interface d'essai/engagement conservant les états aux points d'intégration longitudinaux. D'abord reproduire le domaine élastique et ses réactions/charges, puis franchir la fissuration et vérifier la redistribution, les contacts et les attaches. Ne pas remplacer simplement EI par un facteur de dommage ni réutiliser sans justification la bulle UDL élastique de V11D pour une section non linéaire.

La longueur de fissuration longitudinale Lch doit être explicite et liée à une stratégie vérifiée de discrétisation/localisation ; changer le nombre de fibres dans l'épaisseur n'est pas ce contrôle. Préserver toute charge80psf une fois seulement. Vérifier équilibres par unités, énergie, demi-pas et maillage, retour d'état après échec, branches adoucissantes/instabilité ; un solveur sans convergence n'est pas un effondrement. Les températures autres que20°C sont volontairement rejetées par cette bibliothèque.

Après ce couplage seulement : températures/gradients et matériaux appropriés, géométrie non linéaire, postflambement, liaisons avec colonnes/allèges, impact calculé d'un767 et feux résolus spatialement. Aucun scénario d'effondrement ou de non-effondrement n'est pré-écrit. Blender demeure une visualisation séparée ; ne pas annoncer que l'animation a changé.
