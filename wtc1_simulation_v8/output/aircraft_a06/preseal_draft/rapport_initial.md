# AIRCRAFT-A06 — énergie du radôme et contrôles de l’avion entier

A06 est terminée comme investigation limitée, avec des critères physiques échoués conservés. Quatre départs intacts nouveaux de l’avion entier atteignent2ms. Huit témoins natifs nouveaux examinent la loi de rupture et son historique ; ils font partie de cette seule itération. Aucun ancien Engine relancé. Le calcul de rupture n’est pas transféré au radôme de l’avion : son énergie totale dépend de la longueur des éléments et sa recharge au même pic accumule du dommage. Supprimer la viscosité métallique par défaut explique peu la perte d’énergie d’A05. Ce résultat ne qualifie ni impact réel, ni incendie, ni effondrement.

## 1. Faits directement transcrits et vérifications natives

Configuration immutable : aircraft_a06_predeclaration.json, graine1102031, zéro tirage. Déclaration monotone supplémentaire avant ses Engines : aircraft_a06_monotone_predeclaration.json. Douze Starter sans erreur ni avertissement, douze Engines normaux, quatre observateurs isolés. Main/observateur gardent la même loi et le même historique. Aucun état endommagé ne reçoit de nouvelles propriétés. Leurs pas de continuation sont exclus des résultats. Tous les binaires, decks, listings, CSV et tableaux NPZ sont conservés, y compris les critères échoués. 3431 fichiers antérieurs hashés intacts ; archive non rescannée ; huit hashes source du harnais vérifiés. Intégrité des sorties ne signifie pas validation physique.

Les listings A06 confirment dm=dn=10⁻²⁰ sur toutes les propriétés métalliques TYPE1. Les zéros d’entrée A05 produisaient dm=0,015 et, pour les quadrilatères de façade, dn=0,015. Toutes les autres cartes mécaniques des parents sont identiques : contrôle de différence de cartes conservé dans generation.json. Masse avion121962,860670kg et masse totale191273,837943kg ; masses égales pour les quatre cas. Sans ajout de masse numérique, trajectoire prescrite, modification du nez ou compensation de masse. Les contraintes de façade restent fixes.

Le sandwich de référence reste faces0,5mm/âme8mm/faces0,5mm, trois couches TYPE19 de trois points Gauss dans TYPE51, axe X projeté dans chaque facette. Faces : ρ1830kg/m³, E11=E22=22GPa, ν12=0,25, G12=G23=G31=4GPa. Seuls densité et E11 proviennent directement de la fiche ; les autres rigidités planes sont hypothétiques. Âme : ρ48kg/m³, E11=E22=1MPa, ν=0,1, G12=0,5MPa hypothétiques ; G31=41/G23=24MPa de référence. E33=138MPa ne représente pas l’écrasement dans cette coque plane. LAW25 est maintenue élastique par ses caps numériques élevés ; ceux-ci ne sont pas des résistances physiques. Les métaux et poutres restent A04 : aluminium E73,1/71,7GPa et seuils324/503MPa, façade acier E200GPa, seuil427,656MPa, ν0,33/0,33/0,3. Aucun changement de la loi plastique métallique ou de l’amortissement des poutres.

## 2. Résultats d’un modèle officiel et sources primaires

Aucun résultat officiel de dégâts ou d’effondrement n’est employé comme cible. La façade nominale représentative demeure issue des entrées NIST héritées : cette dépendance d’entrée est explicite et ne rend pas le modèle indépendant de toute donnée NIST.

[La documentation ORTHENERG](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/fail_orthenerg_starter_r.htm) définit des modes directionnels, un seuil de contrainte, un paramètre énergétique et une extinction des points d’intégration. Pour LAW25, TYPE51 est la propriété compatible documentée. La copie primaire [du code shell](https://github.com/OpenCourant/OpenCourant/blob/0168ab344bd743051e996d90c7c8d80728bb04a8/engine/source/materials/fail/orthenerg/fail_orthenerg_c.F) utilise pour le mode normal linéaire ΔD=Le·Δε·σcrit/(2G), avec maximum conservé et saturation à1 ; l’équation linéaire de la page omet le facteur σcrit/2. Le commit copié n’est pas prouvé identique à celui de l’exécutable installé : les témoins natifs vérifient le comportement observé de cet exécutable. Aucun solveur installé ou remplacé. Copies tierces sous input/aircraft_a06_sources exclues de publication ; liens et hashes sauvegardés. L’ancien dépôt source répond404 lors de cette recherche ; les exécutables locaux hashés restent utilisables.

[HexPly913](https://www.hexcel.com/wp-content/uploads/2026/01/HexPly_913_us_DataSheet.pdf) donne450MPa en traction et460MPa en compression pour le tissu de référence7781GL/R913. Il ne s’agit pas d’une identification du radôme construit du767. G=50N/mm=50kJ/m² est un paramètre d’essai numérique annoncé, pas une mesure de ce tissu ni du767. La résistance de cisaillement plane ±100MPa est une hypothèse ; le cisaillement interlaminaire65MPa de la fiche n’est pas recyclé en résistance plane.

## 3. Affirmations des archives locales

Aucune nouvelle affirmation ni vidéo d’archive examinée dans A06. Sources et anciennes itérations préservées. Les observations historiques ne servent pas à choisir résistances, énergie, maillage ou érosion.

## 4. Hypothèses et protocole propres au modèle

Les huit témoins emploient un carré de deux triangles du même sandwich, déplacements affines X/Y, Z et rotations bloqués. L10,20,500mm désignent le côté du carré. Les cinq premiers parcourent des déformations logarithmiques0→0,04→0→0,04→0,12 à0/0,25/0,5/0,75/1ms. Un témoin élastique L10 sert de contrôle et un L10 à demi-pas vérifie la discrétisation temporelle. Limites50/25ns, historiques1µs. Ces témoins testent un mécanisme bloquant précis du nez ; ils ne sont pas des itérations indépendantes d’avancement.

Trois témoins supplémentaires monotones intacts, déclarés après le constat du problème cyclique, suivent ε=0,12(3u²−2u³), u=t/1ms ; εY=−0,25ε. Déplacements lisses exp(ε)−1, limites25ns et historiques50ns. L’arrêt lisse réduit le problème de travail des changements de vitesse abrupts du premier L500. Aucune propriété ni G n’est corrigé pour faire passer ces essais.

ORTHENERG est appliquée seulement aux faces, NMOD1, P_thick_fail1, forme1. Une défaillance complète dans un mode peut désactiver les autres composantes du point : en traction quasi uniaxiale, ce risque est limité ; en multiaxial il reste non qualifié. L’âme reste élastique, les faces peuvent être désactivées mais les coques conservent masse/topologie : aucun fragment libre complet, aucune érosion globale démontrée. Crush, délaminage et liaison réelle au fuselage ne sont pas modélisés.

L’avion entier reprend les conditions A05 :35020nœuds nominaux,35332affinés,216/840triangles de radôme,4408poutres, façade59colonnes×3étages. Vitesse initiale(−200,5,2)m/s, aucune attitude historique identifiée. Contact extérieur TYPE7 à gap constant5mm, variante gap d’épaisseur avec minimum1mm ; radôme seul en autocontact. Friction et viscosité de contact négligeables, pas de précharge ni gravité. Moteurs encore masses/RBE3, sans surface de contact ni liaison mécaniquement identifiée ; noyau et planchers absents. Les quatre nouveaux cas modifient seulement dm/dn par rapport à leurs parents. Le radôme reste élastique dans l’avion, conformément au refus de transfert de la rupture.

## 5. Résultats dérivés et bilans

### Loi de rupture : énergie et historique

Unités natives g/mm/ms, contraintes MPa=N/mm², énergie Nmm ; ×0,001 vers J. Une énergie surfacique1N/mm vaut1000J/m²=1kJ/m². IE inclut travail irréversible et énergie stockée ; PW est un sous-ensemble d’IE et n’est jamais ajouté deux fois. Dans ces témoins PW=0 malgré le dommage : PW seul ne mesure donc pas l’énergie dissipée par cette loi.

Pour un trajet monotone uniaxial, une référence avec volume initial donne ε0=σ/E, a=Leσ/(2G), D=a(ε−ε0), σrésistante=(1−D)Eε jusqu’à D=1. Ce sont des hypothèses de référence vérifiées séparément par quadrature Gauss8, sans calage sur les forces. L’intégration donne :

G_total = Leσ²/(2E) + G + 2EG²/(3Leσ²).

Le premier terme est l’énergie élastique stockée à l’initiation ; le travail après initiation n’est pas simplement G si la contrainte effective continue à augmenter. Dans nos carrés, Le candidat=L/√2 ; la pente native d’endommagement retrouve7,0688mm et14,1394mm pour les10/20mm. L500 se rompt trop vite pour identifier cette pente dans les animations espacées10µs. Le reste un candidat géométrique dans ce cas et n’a pas été exporté de UVAR13. Les énergies du tableau retirent une petite approximation élastique de l’âme et sont normalisées par volume initial total des faces/Le ; elles ne sont pas une mesure de ténacité du matériau.

|Côté carré mm|Le candidat mm|Travail total des faces par surface N/mm|Référence volume initial N/mm|Écart référence|Écart travail des réactions|
|---:|---:|---:|---:|---:|---:|
|10|7.0711|110.4845|108.1501|2.158%|0.00286%|
|20|14.1421|130.0049|127.8895|1.654%|0.00378%|
|500|353.5534|1699.8207|1677.6613|1.321%|0.01902%|

Avec G entré50, aucun cas ne passe l’égalité5% entre G et ce travail total. La référence analytique passe2% pour20/500mm, échoue légèrement pour10mm (2,158%) ; le seuil n’est pas augmenté. Finite déformation, épaisseur et temps discret de désactivation ne sont pas absorbés par un ajustement. Les trois bilans globaux natifs et les travaux de réactions lisses passent1% ; l’écart de travail maximum est0,0191%. Les quatre cas endommagés cycliques montrent du dommage conservé à la décharge. Le L10 augmente encore D de~0,622 à1 lors de la recharge à la même déformation0,04 ; cette accumulation ne constitue pas une fatigue physique identifiée. Demi-pas cyclique : écart IE finale0,17704%, inférieur au1% déclaré.

Dans le premier L500 cyclique, le bilan IE+K−travail externe passe, mais le travail reconstruit des réactions aux changements abrupts de vitesse échoue1% avec15,856% : échec conservé, distinct du résultat des témoins lisses. Le L10 élastique conserve dommage0 et décharge quasiment sans travail irréversible ; les mouvements affines sont vérifiés depuis les déplacements natifs.

Les canaux REACX/REACY des témoins se comportent comme impulsions cumulées N·ms : le travail Σv·ΔR ferme le bilan, contrairement à ΣR·Δx. Leur dérivée donne la réaction-force ; l’inertie nodale est soustraite pour obtenir un effort résistif équivalent. À0,310025ms en L10, la sortie de contrainte effective vaut603,899MPa, tandis que l’effort réduit donne environ469,578MPa ; à0,290025ms en L20 :537,379 et401,648MPa. La normalisation en contrainte par largeur courante et épaisseur initiale n’est qu’un diagnostic. [Les tenseurs d’animation](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/anim_shell_dama_engine_r.htm) sont conservés comme champs natifs ; ils ne doivent pas être utilisés comme contraintes résistantes après dommage sans vérifier leur rôle. A05 reste correctement interprétée dans son régime sans endommagement.

Un modèle classique de fissure avec énergie totale G, picσ et loi contrainte-ouverture linéaire exige Le≤2EG/σ², ici10,8642mm. Les altitudes géométriques minimales des facettes du radôme sont165,67mm nominales et82,84mm affinées ; elles ne sont pas les champs natifs Le. Le maillage courant ne peut être déclaré résolu pour une rupture fragile physique de cette énergie. Augmenter G uniquement pour compenser ce maillage serait un changement de matériau injustifié. Des G physiques, l’identification du radôme et une représentation énergétique adaptée restent nécessaires.

### Avion entier : contact, énergie et sensibilité

|Cas|Fin native ms|Impulsion X N·s|Énergie générée kJ|Résidu final kJ|PW global kJ inclus IE|Max diagnostic face|
|---|---:|---:|---:|---:|---:|---:|
|ZERO_DM|2.00057268|-2622.918|283.768|-77.522|4.339|3.5421|
|ZERO_DM_FINE|2.00016546|-2248.117|160.836|-44.214|0.217|4.5242|
|ZERO_DM_HALF|2.00034690|-2603.303|283.940|-77.090|4.343|3.5390|
|ZERO_DM_TRUE_GAP|2.00016546|-2537.758|302.824|-56.366|4.220|4.0138|

Énergie comptée : Ktranslation+Krotation+IE+hourglass+spring+contact élastique+contact friction+contact amortissement ; CONTACTENERGY n’est pas rajouté à ses composantes. Résidu=ΔE−travail externe, ce dernier nul pour l’avion. Énergie générée=Krotation+IE+hourglass+spring+contact élastique. Critère global0,5%K0 passé ; critère local5%énergie générée+1000J au-delà1kJ échoué dans les quatre cas. Les quantités de mouvement et appuis passent leurs contrôles hérités. Les supports froids ne bougent pas.

À temps commun2,00042772ms avec A05 nominale, le déficit passe de−78,6424 à−77,5186kJ, soit environ1,1237kJ d’écart ; impulsion0,2814% et énergie générée0,1896% d’écart. La viscosité par défaut ne résout pas la perte dominante. Les courbes sauvegardées montrent une chute rapide du bilan vers1,65ms, à examiner sans lui attribuer une cause non démontrée. Les historiques natifs ne signalent pas de rupture d’élément ; absence de message ne qualifie pas le mécanisme de perte.

Demi-pas à2,0003469ms : impulsion0.8167%, énergie0.0957% : critères5/10% passés. Maillage à2,00016546ms : impulsion14.4204%, énergie43.2858% : critères10/10% échoués. Gap d’épaisseur au même temps : impulsion3,4964%, énergie6,7823%, sensibilité mesurée sans la confondre avec convergence ou contact exact. Géométrie plane par morceaux et masse restent égales nominal/affiné. Les paramètres ne sont pas choisis d’après leur ressemblance aux dégâts réels.

Les sorties de contrainte des faces dépassent les références dès le premier état sauvegardé vers0,6ms : maxima3,539 à4,524fois la référence selon cas. Ce n’est pas un temps de fracture calculée dans l’avion. Aucun état final2ms ne peut donc être transféré comme état d’impact physique qualifié. La figure est tirée de vrais états enregistrés, déplacements×1 ; le plan de façade rouge est initial seulement.

## 6. Contradictions, manques et suite

Le nom du paramètre énergétique ne vaut pas une validation de la dissipation. La loi ORTHENERG avec cette LAW25 élastique ne fournit pas une fracture indépendante du maillage de50kJ/m² ; même la référence mécanique limitée échoue un seuil2% en L10. Les cycles accumulent du dommage sans nouveau pic. Les tenseurs de contrainte effective doivent être distingués des efforts endommagés. L’avion garde donc sa limite matérielle A05 ; l’investigation A06 ne prétend pas l’avoir levée. Une sensibilité physique G n’a pas été lancée dans l’avion après ce refus de transfert : la dépendance analytique est explicitée avant toute nouvelle plage d’essais.

Le contrôle dm/dn enlève une incertitude numérique sans fermer le bilan local ni la sensibilité spatiale. Les moteurs doivent encore recevoir géométrie de contact, masse distribuée et liaisons justifiées. AIRCRAFT-A07 : compléter la géométrie mécanique/contact des nacelles et moteurs et leurs liaisons avec des sources primaires et hypothèses explicites, dans l’avion entier. En parallèle ciblé, identifier la perte d’énergie du contact observée vers1,65ms depuis les champs sauvegardés et définir une rupture du radôme dont énergie totale, longueur caractéristique et historique sont maîtrisés. Ne pas transférer ORTHENERG A06 tel quel : G entré ne vaut pas le travail total, recharge au même pic accumule du dommage. Aucun prolongement comme impact physique qualifié tant que bilan local et sensibilité spatiale restent en échec. Aucun ajustement aux dégâts NIST, aucune inflation de G pour tolérer le maillage grossier. Préserver V11F, V11S et IMPACT-I02I-M différées. Publier A06+A07 après vérification des deux itérations.

Limites antérieures conservées : localisation en flexion après fracture complète non validée ; température imposée distincte d’un incendie calculé ; sous-modèles et tests numériques distincts de la validation de l’effondrement réel ; Blender reste une visualisation. V11F froid et V11R préservés ; V11S et IMPACT-I02I-M différées. Aucun résultat attendu imposé.

Reprise : lire AGENTS.md, état local, WTC1_AIRCRAFT_A06_HANDOFF.md. Utiliser summary.json, witness_review.json et monotone_review.json, tableaux NPZ et figure sauvegardés ; aucun calcul ancien à refaire. complete_aircraft_a06.py verify contrôle hashes/registre/état/harnais sans Engine. Publication après paire A06+A07 : A06 seule restera pending1, aucune écriture GitHub dans cette session. A04+A05 déjà vérifiées distantes avant A06 ; aucune opération Yoremi ou X.
