# AIRCRAFT-A16 — dommage natif des peaux dans l'impact avion–façade

**Quatre contrôles mécaniques courts passent ; 2 nouveaux impacts couplés achevés avec dommage des peaux du radôme.** Le défaut d'histoire observé avec ORTHENERG dans A06 est évité : décharge et recharge au même maximum ne créent pas de dommage supplémentaire dans les nouveaux témoins. L'avion, la façade, les masses, les assemblages et les contacts A15 sont conservés. Aucun résultat historique ou NIST visé.

Cette avancée est une **perte de résistance des peaux calculée par le solveur**, pas encore une fissure de ténacité mesurée, une ouverture complète ni des fragments libres. L'âme reste intacte, les coques ne sont pas supprimées. L'énergie de fracture physique, la convergence spatiale et l'impact historique restent non qualifiés. Les nouveaux bilans et leurs échecs sont conservés ci-dessous.

## 1. Faits directement observés ou transcrits

Configuration épinglée avant génération et calcul, quatre témoins neufs et deux impacts demandés de10ms. Journaux, arguments, durées, exécutables et codes de sortie enregistrés. Historique natif/CSV intégral vérifié :10000 lignes par témoin, tous les records et canaux ; les sorties couplées et leurs records de fin sont vérifiés avec le même lecteur A15. REAC et contact sont des impulsions cumulées, non des forces à réintégrer. REAC/contacts de l'observateur exclus car leurs cumuls repartent à zéro.

Les animations portent les indices natifs de dommage par couche et les messages moteur nomment les peaux41/43 défaillantes. Le cœur42 ne reçoit pas de loi de dommage. Lecture directe des scalaires binaires FASTMAGI10 vérifiée contre le convertisseur sur premier, milieu et dernier états : indices élémentaires concordants, précision d'affichage respectée. **Toutes les images natives de dommage0,1ms** sont lues ; géométrie/vitesses/masses détaillées sur états réguliers≈0,5ms, premier et dernier inclus, comme dans A15. Tous les fichiers bruts sont conservés.

Le champ DAMA d'une couche est un maximum sur les points dans son épaisseur. D=1 signale au moins un point totalement endommagé, pas nécessairement toute la couche. Les messages de défaillance de pli donnent un indicateur distinct après les règles d'intégration. Les comptages ci-dessous sont des nombres d'éléments/couches, **pas une surface exacte ni une probabilité de l'événement**. Pas de nouvelle observation historique.

## 2. Résultats d'un modèle officiel

Les nouvelles sorties proviennent d'OpenRadioss v20260728-win64, pas d'un modèle officiel NIST de dommages. Entrées de façade représentative nominales NIST héritées ; cette dépendance d'entrée reste signalée, sans ajustement à ses résultats. Conditions historiques AA11 non établies.

La [documentation primaire ORTHSTRAIN](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/fail_orthstrain.htm) décrit un dommage fondé sur un maximum conservé, avec seuil de début et fin, puis réduction du tenseur. A16 choisit la déformation vraie et désactive les dépendances à la vitesse et à la taille. Les [règles TYPE51](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/prop_type51_starter_r.htm) distinguent défaillance de pli et suppression de coque. Les [sorties DAMA](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/anim_shell_dama_engine_r.htm) sont contrôlées ici séparément des efforts et du travail. Ces descriptions identifient le mécanisme numérique ; elles ne fournissent pas des propriétés mesurées du radôme réel.

## 3. Affirmations provenant des archives locales

Aucune nouvelle vidéo ni photographie, aucune archive/PDF source modifié. **9052 fichiers antérieurs, 41.732Go** recontrôlés intégralement par SHA-256, sans différence. Copies de documentation nouvelles sous les seules sorties A16, empreintes et exclusions de redistribution tierce enregistrées. Sources officielles locales en lecture seule. Module Boeing parallèle séparé ; ses limites restent ouvertes.

Le rapport A06 et ses sorties sont réutilisés sans relance : ORTHENERG y accumulait du dommage à recharge égale, et le travail ne correspondait pas au G entré. Cette loi n'est pas transférée. Les échecs A11-A15 et les champs anciens ne sont pas reclassés. Dernière publication distante vérifiée A12+A13 ; paire A14+A15 due, A16 s'ajoute à l'attente locale. Aucune publication externe nouvelle par ce script.

## 4. Hypothèses propres au modèle

Graine1102041, zéro tirage. Avion complet de≈121963kg,37228 nœuds couplés, façade de31986 quadrilatères sur trois étages représentatifs :944 nœuds de bord fixes et intérieur déformable. Vitesse[-200,5,2]m/s, gap5mm, quatre interfaces TYPE25 canoniques uniformes Stfac1, auto-contact TYPE7 du radôme. Pas d'auto-contact global, carburant résolu, intérieur de tour ou incendie. Aucun mouvement imposé dans l'avion. Tous les nouveaux départs sont intacts ; l'état hors domaine A15 n'est pas utilisé comme état physique validé.

**Seule nouvelle carte mécanique : /FAIL/ORTHSTRAIN/4**, appliquée au matériau des deux peaux0,5mm. Cœur8mm conservé. Géométrie/matières/propriétés/masse/RBE3/BCS/INIVEL/contact comparés à l'identique du parent A15 ; seules les sorties de dommage et les titres sont ajoutés. Matériaux métalliques et leurs lois de rupture absentes restent inchangés.

Le JSON de pré-déclaration conserve des libellés hérités d'anciennes étapes, notamment « failure_disabled », le contexte moteur seul et un ancien plafond de 600 s. Ils ne sont pas corrigés après calcul. **effective_configuration.json** les distingue des cartes réellement exécutées : nouvelle loi des peaux active, quatre contacts extérieurs actifs, parent direct A15 et plafond effectif de 1200 s vérifiés. Le mécanisme de rupture interne de LAW25 reste désactivé ; la nouvelle loi FAIL est distincte. Aucune ancienne qualification n'est transformée en réussite.

En simplification uniaxiale, εdébut,traction=450/22000=0.020454545 et εdébut,compression=460/22000=0.020909091. Les450/460MPa et22GPa proviennent de la référence HexPly913/7781 héritée ; ce n'est pas une identification du matériau Boeing. Les directions11/22 utilisent les mêmes valeurs par approximation du tissu équilibré. Le cisaillement indépendant et les modes33 ne sont pas identifiés et restent désactivés ; aucun65MPa de short-beam shear n'est substitué à une résistance de cisaillement dans le plan.

εfin=(1+r)εdébut : **r=0,20** reprend le ratio de transition par défaut documenté, **r=0,02** est une sensibilité propre d'une décennie. Ces largeurs ne sont pas des mesures de déchirure et ne sont pas choisies pour obtenir une perforation. Seuil de défaillance d'épaisseur=1 au matériau et au stack : le cœur intact empêche la suppression de toute la coque. Ni délamination, écrasement, séparation des liaisons ni fragmentation topologique.

**Aucun G de fracture n'est entré ou annoncé validé.** Dans la référence uniaxiale à petit déplacement, la contrainte résistante décroît linéairement entre εdébut et εfin, et le travail total par volume vaut½E εdébut εfin. Sa normalisation par une longueur dépend du maillage. Le travail total n'est donc pas une ténacité objective ; aucune augmentation de G pour tolérer les mailles grossières. Des données et une représentation de séparation adaptées restent nécessaires.

Témoins : deux triangles du même sandwich, carrés10/20mm, déplacements affines prescrits seulement pour ces contrôles, chemin de déformation vraie0→0,0225→0→0,0225→0,04 aux temps0/0,25/0,5/0,75/1ms, interpolation cubique lisse sur chaque branche. Contraction Y=−0,25εX. Quatre cas, dont demi-pasR20 ; limites de pas25/12,5ns, TH0,1µs, animations5µs. Seuils déclarés : erreur absolue D≤0,02 ; croissance au même pic≤0,002 ; cycle énergétique≤2% ; travail/bilan≤1%+0,001J ; positions≤0,001mm ; demi-pas IE≤1%.

Impacts :10ms par cas, facteur de pas stable0,5, deux threads CPU, zéro GPU, plafond1200s par principal d'après le coût A15. TH0,01ms, images0,1ms. Ledger hérité : KE+rotation globale+IE+hourglass+spring+contact élastique/frottement/amortissement−travail externe, une fois chacun. PW inclus dans IE, aucun RKE reconstruit ajouté. Unités g/mm/ms/MPa/N/Nmm : ×0,001 pour g→kg, mm→m, ms→s, Nmm→J et Nms→Ns ; mm/ms→m/s a un facteur1. Critères de bilan/masse/quantité de mouvement A15 inchangés. Le critère local garde sa marge absolue de 1000 J liée à la précision des sorties : il ne signifie pas que chaque rapport résidu/énergie reste sous 5% dès les premiers instants. Les contraintes imprimées après dommage sont des contraintes effectives ; elles ne mesurent pas directement l'effort résistant endommagé. Leur ancien diagnostic de référence est conservé, pas utilisé comme preuve que le dommage est absent.

## 5. Résultats dérivés

| Témoin | Max erreur D | ΔD même pic | Max résidu J | Écart travail impulsions J | IE finale J |
|---|---:|---:|---:|---:|---:|
| CYCLE_L10_R20 | 0.0005175 | 0.0000000 | 0.000000962 | 0.000001239 | 0.5592102 |
| CYCLE_L10_R20_HALF | 0.0005020 | 0.0000000 | 0.000000542 | 0.000134723 | 0.5592097 |
| CYCLE_L20_R20 | 0.0005175 | 0.0000000 | 0.000004466 | 0.000015053 | 2.2368410 |
| CYCLE_L10_R02 | 0.0036142 | 0.0000000 | 0.000000520 | 0.000024677 | 0.4749888 |

Tous les contrôles déclarés passent. Demi-pas : ΔIE **0.0000894%**. Le casR20 garde D≈0,545 aux deux pics identiques ; le casR02 a déjà atteint1 au premier pic. L'âme garde D=0 ; pas d'érosion. Ces essais valident le mécanisme d'histoire/implémentation, pas une énergie de fracture physique ni la localisation d'une fissure. Le changement de taille des témoins ne constitue pas une étude d'objectivité spatiale de l'avion.

Diagnostic séparé de taille, sans nouveau critère a posteriori : IE totale normalisée par le volume initial des faces et une longueur géométrique candidate L/√2 donne39,5421N/mm enR20/L10 et79,0843N/mm enR20/L20. Cette valeur inclut aussi IE du cœur et n'est pas une ténacité. Son doublement quand la longueur double confirme qu'on ne peut annoncer une énergie surfacique objective avec cette loi. Le calcul est reproduit et comparé exactement dans ce finaliseur ; aucun G n'est ajusté.

| Impact | Fin observée ms | Impulsion X dernier TH kN·s | Max déplacement façade échantillonné mm | Énergie hors translation finale MJ | Résidu final kJ | Critères échoués |
|---|---:|---:|---:|---:|---:|---|
| IMPACT_R20_10 | 10.000175500 | -10.620980 | 49.586 | 0.950216 | -20.034244 | radome_face_reference_domain |
| IMPACT_R02_10 | 10.000361400 | -9.949219 | 43.931 | 0.901480 | -22.110294 | radome_face_reference_domain |

Aucun calcul couplé rejeté.

| Impact | Premier dommage enregistré ms | Premier pointD=1 enregistré ms | Couche/élémentDmax=1 | Plis défaillants consignés au journal |
|---|---:|---:|---:|---:|
| IMPACT_R20_10 | 0.9003915786743164 | 1.1004267930984497 | 414 / 432 | 414 |
| IMPACT_R02_10 | 0.9003915786743164 | 1.0001760721206665 | 417 / 432 | 417 |

Les instants sont ceux des images espacées0,1ms, pas des temps exacts de début. Le dommage est monotone dans tous les états enregistrés, le cœur reste à0, les coques restent présentes, masse inchangée sans masse ajoutée. Des peaux défaillantes natives coexistent donc avec un maillage continu de radôme. Contact, quantité de mouvement, énergie et travail des matériaux restent interprétés séparément.

| Comparaison avec A15 intact mis en cache | Temps commun ms | Δimpulsion % | Δénergie hors translation % |
|---|---:|---:|---:|
| IMPACT_R20_10 | 9.990067 | 77.950899 | 87.571011 |
| IMPACT_R02_10 | 9.990103 | 79.351361 | 88.210056 |

Il s'agit de **sensibilités de loi de dommage**, pas de convergence ni d'une sélection du meilleur résultat. Le casR20 est affiché car premier déclaré, sans classement d'après la forme obtenue. Le radôme ne devient pas historiquement validé parce que ses efforts changent. Aucun ancien solveur relancé. A16 n'allonge pas encore l'horizon au-delà de0,01s : il change un mécanisme matériel dans l'impact déjà lancé.

La visualisation est issue des déplacements et du dommage natifs, ×1, lecture ralentie sans interpolation géométrique. Rouge : au moins un point de peau totalement endommagé ; jaune : dommage partiel ; coque encore présente. Image statique inspectée et diagramme comparatif inspecté, données comprimées avec retour exact, syntaxe JS vérifiée ; rendu GUI interactif non certifié.

## 6. Contradictions et informations manquantes

L'histoire au même pic est désormais contrôlée et des points/plis perdent leur résistance dans l'avion, mais cette loi reste sans ténacité physique mesurée et sans objectivité spatiale. La résistance/E uniaxiale est une approximation de début de dommage, pas une enveloppe multiaxiale identifiée. La réduction de tout le tenseur par le maximum d'un mode peut aussi affecter le cisaillement ; ce couplage n'est pas validé pour le radôme réel.

L'âme intacte laisse une coque continue et un contact géométrique de sandwich, même si les peaux portent moins d'effort. Une coque affaiblie n'est pas un fragment ni un trou. Métaux, assemblages, auto-contact, écrasement, séparation des couches, carburant, conditions historiques et convergence spatiale restent ouverts. Les critères énergétiques ou matériels échoués ci-dessus sont conservés intégralement. Les premières secondes et toute chaîne d'effondrement restent non calculées.

AIRCRAFT-A17 : repartir du contact couplé et des sorties A15/A16 sans anciens solveurs relancés. La perte de résistance des peaux est maintenant native et l'historique au même pic est contrôlé. Elle ne constitue pas une fissure énergétique objective ni des fragments libres. Priorité à une représentation de séparation avec travail stocké/dissipé, surface de fissure et énergie indépendants du maillage, puis écrasement du cœur et liaisons réelles. Réutiliser la référence de traction-ouverture déclarée et les sources A06, ne pas transférer ORTHENERG rejetée ni augmenter G pour tolérer le maillage. Documenter les données physiques absentes ; toute nouvelle plage reste déclarée avant calcul et ne vise ni NIST ni une perforation connue. Contrôler la loi une seule famille nécessaire, puis revenir au même avion/façade avec coût borné. Résidus énergétiques, limites métalliques, convergence spatiale, carburant et conditions historiques restent à qualifier. Aucun état10ms hors domaine ne devient un état historique validé. Module parallèle séparé. Publication A14+A15 due, A16 en attente ; vérifier cette tâche indépendamment.
