# Reprise WTC 1 — V11F terminée, prochaine V11G

## Reprendre sans relire toute l'histoire

Lire intégralement `AGENTS.md` et `harness/state.json`, puis ce document. L'état est l'autorité actuelle ; le paragraphe V8H d'AGENTS est historique. Exécuter `harness/tools/Test-WtcHarness.ps1` depuis la racine active. Archives et `work/official_sources/` restent en lecture seule. Ne pas recommencer une recherche documentaire globale ni analyser des vidéos sans question précise.

Racine : `C:\Users\jeuxpc\Documents\Codex\2026-08-13\referenced-chatgpt-conversation-this-is-an`.

La demande est une simulation exploratoire aussi réaliste que possible, avec hypothèses explicites, sans conclusion d'effondrement ou de non-effondrement prédéfinie. Les anciennes exigences documentaires ne doivent pas empêcher tout prototype ; inversement, une hypothèse ne devient pas un relevé du bâtiment réel.

## Ce qui vient d'être construit

V11F intègre à froid la section fissurable V11E à la dalle, au treillis et aux liaisons du panneau V11D. Les anciennes itérations restent intactes. Le nouveau panneau résout simultanément l'effort axial N et le moment M, sans imposer N = 0, avec contact en compression, attaches en traction et glissement horizontal excentré. La fissuration ne termine plus automatiquement ce panneau.

Le domaine reste isotherme à 20 °C et à petits déplacements. Aucune nouvelle géométrie complète de tour, température, rupture dynamique, force d'avion ou animation Blender n'est calculée. V11B et le pilote visuel V10Y/V10Z restent séparés et inchangés.

## Six catégories de preuve

1. **Transcriptions / constats** : portée héritée 713 in = 18,1102 m ; largeur tributaire de paire 80 in = 2,032 m ; épaisseur équivalente 4,35 in = 0,11049 m. Les fichiers sources et anciens résultats ont été vérifiés par empreinte, sans nouveau PDF ni média analysé.
2. **Modèles officiels / sources de méthode** : écrans NIST hérités des sièges et knuckles, avec les limitations des transcriptions antérieures. Les pages OpenSees/DIANA citées au rapport expliquent la formulation à déplacements et l'énergie de bande ; aucun de ces solveurs n'est exécuté. Aucune chronologie NIST de dommage n'est imposée.
3. **Archives** : aucune nouvelle affirmation ou interprétation d'archive dans cette itération.
4. **Hypothèses** : 16 panneaux Warren idéaux ; 32 knuckles équivalents à 17 stations ; géométrie/raideurs héritées. Béton Ec = 2500 ksi, fc = 3 ksi, ft = 1 MPa, Gf = 100 J/m² ; acier d'armature E = 200 GPa, fy = 400 MPa, centres à 25 mm des faces. Ratios 0 / 0,1 / 0,2 / 0,4 %, nappes symétriques ou supérieure. Tout cela n'identifie pas le ferraillage réel.
5. **Résultats dérivés** : 132/132 contrôles numériques, 14 parcours, 713 états de référence ; 14/14 comparaisons spatiales 4→8 et 14/14 contrôles de demi-pas passent les critères déclarés. L'audit de relecture apporte 17 contrôles supplémentaires, pas une certification externe.
6. **Inconnues / limites** : localisation longitudinale des fissures, adhérence réelle, bac, cisaillement de dalle, écrasement, grandes déformations, postflambement, rupture des attaches et thermomécanique ne sont pas validés. Le nombre de points fissurés n'est pas le nombre de fissures réelles. Aucun résultat local n'est une preuve concernant toute la tour.

## Formulation à préserver

- 33 nœuds acier, 63 barres ; référence de dalle : 65 nœuds, 64 éléments, 128 sections de Gauss, 160 fibres béton par section ; total 261 degrés de liberté. Deux et huit subdivisions donnent 165 et 453 degrés de liberté, sans changer l'acier ni les stations.
- Axial linéaire, flexion Hermite cubique ; deux points de Gauss par élément. Assemblage par intégrale de Bᵀ[N,M] et BᵀKsectionB. La section vectorisée appelle les lois V11E inchangées et conserve séparément les historiques des fibres.
- Lch = poids longitudinal du point de Gauss = demi-longueur d'élément : 0,282971875 / 0,1414859375 / 0,07074296875 m pour subdivisions 2/4/8. Les poids longitudinaux convertissent les J/m de section en J du panneau.
- Une bande entièrement fissurée dissipe AcGf = 22,406664864 J pour le cas 0,2 %. Cela ne fixe ni le nombre ni la position des bandes. Faire fissurer toutes les bandes double l'énergie totale quand leur nombre double : ne pas confondre le coupon d'une bande et l'objectivité d'une structure.
- La charge 80 psf, poids propre compris, est appliquée une seule fois à la dalle avec forces ET moments nodaux cohérents. Ne pas ajouter une masse de renfort fictive ou reprendre la bulle UDL élastique V11D dans les contraintes/énergies fissurées.
- Compression aux faces et extrémités d'élément ; déformation des armatures aux extrémités aussi. Les dommages restent aux points de Gauss. Les efforts de section satisfont un équilibre faible intégré, pas nécessairement l'équilibre ponctuel exact.
- Essais et Newton depuis le dernier état engagé, recherche linéaire et réduction de pas ; essais refusés non engagés. Pas de ressort stabilisateur. Arrêt au premier écran nominal, domaine de matériau, tangente contrainte non positive ou continuation non résolue ; jamais conversion d'une erreur de calcul en effondrement.
- La tangente positive est celle du modèle à petits déplacements, sans raideur géométrique ; elle n'établit pas la stabilité réelle. Les barres de treillis restent élastiques jusqu'au premier écran min(Afy, Euler) hérité ; pas de postflambement calculé.

## Résultats utiles

Les essais sans armature retrouvent la réponse nodale élastique V11D avant fissuration. Le cas sans armature atteint la borne de gravité 1,25 sans écran franchi ; avec 0,2 % d'armature, le premier écran de diagonale est atteint vers 1,699185 de la charge de référence. Ces multiplicateurs sont ceux de ce panneau et de ses hypothèses, pas des coefficients de sécurité du plancher réel.

Les essais d'actionneur commencent sous un quart de la gravité de référence. Les déplacements de dalle ±2 mm restent élastiques. Les abaissements imposés du treillis produisent une fissuration puis un premier écran de membrure supérieure. Ce dispositif applique un effort extérieur : ce n'est ni un impact calculé ni une dégradation spontanée.

Exemple `TRUSS_LOWER_R02` :

- première fissuration échantillonnée à −35 mm imposés ; premier écran à −68,125763 mm ; flèche nodale maximale de dalle 78,850305 mm ; 8 sections de Gauss fissurées ; pas de rupture d'attache ; une attache verticale tendue ; ouverture maximale 0,067716 mm ; aucune plasticité d'armature atteinte ;
- gravité 35 239,800130 N ; sièges +171 492,594366 N ; actionneur −136 252,794236 N : les trois contributions s'équilibrent ;
- dissipation béton locale 0,361900535 J contre 0,355471611 J au maillage fin, soit 1,776 % entre leurs états terminaux propres, distants d'environ 0,000458 mm de déplacement imposé ;
- le cycle du treillis 0 / −60 / 0 mm conserve un dommage et 0,217135075 J dissipé, puis referme le contact. Sa réaction finale vaut environ +0,0391 N : retour du déplacement imposé à zéro, pas déchargement libre.

L'amplitude cyclique de 60 mm a été choisie après un premier essai monotone atteignant un écran près de 68 mm pour exercer un cycle fissuré sans dépasser ce domaine. C'est un choix de test divulgué, pas une prédiction aveugle ou un ajustement historique.

Sur référence, répétition, maillages et demi-pas : résidu d'équilibre maximal 2,810189333e−11, identité exacte W = U + D à 2,201447558e−16, écart de travail extérieur par trapèzes à 1,231921085e−7 relatif. Le travail de l'actionneur et les moments nodaux sont inclus. En relecture des fichiers sans importer le noyau : 56 panneaux terminaux, bilans de forces et moments, déformations et énergies reconstruits ; erreur de moment normalisée maximale 3,350908864e−13.

Attention aux tolérances : les comparaisons communes par phase utilisent un plancher de 1 µm pour la flèche, 1 N pour la force, **1 J pour la dissipation**. Le critère béton de 10 % signifie donc 0,1 J absolu quand l'énergie est inférieure à 1 J, pas 10 % de cette petite énergie. Le rapport et `release_audit.json` donnent aussi les vrais écarts relatifs finaux, sans changer les critères après calcul. Les courbes restent très proches ici, mais cela ne valide pas à lui seul la localisation après fissuration complète.

L'audit de relecture ne reconstruit pas tout le travail extérieur vectoriel : les historiques exportés ne contiennent pas tous les déplacements nodaux à chaque pas. Cette vérification existe dans le solveur et son contrôle de demi-pas ; ne pas revendiquer une seconde reconstruction complète depuis les CSV.

## Livrables et reproductibilité

Répertoire publié : `wtc1_simulation_v8/output/v11f_panel_coupling/` ; rapport `rapport_v11f_panneau_fissure.md`, résultats `results_v11f.json`, figure `synthese_v11f_panneau_fissure.png`. Les inventaires, courbes, états de section, efforts des composants et déplacements sont conservés. `verification_runs.json` contient les historiques des maillages 2/8 et du demi-pas.

Configuration : `wtc1_simulation_v8/data/v11f_panel_coupling_predeclaration.json` ; noyau `wtc1_simulation_v8/scripts/v11f_panel_model.py` ; pilote `run_v11f_panel_coupling.py` ; tests `test_v11f_panel.py` ; relecture `audit_v11f_release.py` dans le même dossier de scripts. Graine 1101006 conservée ; aucun tirage aléatoire utilisé.

Empreinte numérique : `14c653db4392244bc377a41705597d40adbc687fbd4afc92ffb33389d1c3ccff`.

Calcul final 100,0185167 s, CPU, Python 3.14.3, NumPy 2.4.6, Pillow 12.2.0, `OPENBLAS_NUM_THREADS=1`. `tmp/v11f_panel_coupling/attempt02` publié byte-identiquement, 17 fichiers. `attempt01` reste un calcul antérieur aux clarifications du rapport/graphe et à l'ajout du script d'audit ; empreinte numérique identique, mais ses empreintes de pilote ne correspondent plus au pilote éditorial final. Ne pas le promouvoir ni le supprimer.

15 sorties du manifeste et 21 entrées/protégés vérifiés ; les 12 sorties/13 entrées V11E et 14 sorties/13 entrées V11D restent intègres. Le manifeste exclut sa propre empreinte et l'audit de relecture ajouté ensuite ; ces fichiers et le handoff sont épinglés par le registre. Pas d'installation, GPU, publication externe, revue multi-agent ou exécution Blender.

Contrôle rapide, depuis la racine :

```powershell
./harness/tools/Test-WtcHarness.ps1
$env:PYTHONDONTWRITEBYTECODE='1'
& C:/Python314/python.exe wtc1_simulation_v8/scripts/audit_v11f_release.py --directory wtc1_simulation_v8/output/v11f_panel_coupling
```

Pour refaire le calcul seulement si nécessaire : fixer `OPENBLAS_NUM_THREADS=1`, lancer le pilote avec `--output tmp/v11f_panel_coupling/<nouveau_nom>` ; le dossier doit être inexistant. Les sorties existantes sont volontairement refusées.

## Prochaine V11G : contrôle longitudinal borné, puis chauffage

Construire un essai longitudinal simple dont l'énergie de fracture complète est connue, avec une stratégie explicite de localisation et un contrôle adapté à l'adoucissement. Comparer plusieurs longueurs d'élément sur une géométrie physique inchangée ; distinguer énergie par bande et nombre de fissures. Quantifier également le défaut d'équilibre ponctuel des N/M du panneau V11F, sans demander à une formulation faible d'être exactement forte à maillage fini.

Il ne s'agit pas de chercher un échec caché des 14 critères présents : ils passent. Le contrôle additionnel doit préciser le domaine d'emploi en fissuration plus avancée avant chauffage, et rester un benchmark borné. Ensuite : thermomécanique et gradients, géométrie non linéaire/postflambement, assemblages avec colonnes/allèges, impact calculé du 767 et feux résolus spatialement. Aucun transfert d'énergie locale à la propagation ni mouvement Blender avant un couplage explicitement vérifié.
