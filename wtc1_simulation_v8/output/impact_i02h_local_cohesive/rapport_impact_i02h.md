# IMPACT-I02H — raffinement local et sensibilité matériau d'un coupon M(T)

Clôture bornée du 29 septembre 2026. Prochaine itération : **IMPACT-I02I**.

## Décision

Le seuil de première séparation passe le contrôle moyen/fin (écart **2,734 %**, limite 10 %) et le contrôle au demi-pas de temps (**0,000305 %**, limite 5 %). Trois avances fines au-delà de 2,3 mm restent dans la zone raffinée. C'est un progrès par rapport à I02G, pas une validation de la propagation : grossier/moyen échoue encore (**12,920 %**), la déchirure tardive dépend du maillage et les angles d'ouverture varient au demi-pas de temps. La convention de la courbe matériau source reste à établir.

Sept cas terminés ont été réaudités depuis leurs historiques sauvegardés : 49/49 contrôles de cas passent. L'audit de campagne donne **9/10**, avec l'échec conservé ; ce décompte mêle des contrôles numériques et deux diagnostics ajoutés à la clôture, il ne représente pas dix validations physiques. La publication et la validation scientifique sont deux opérations distinctes.

**Aucun transfert physique vers une aile, une façade complète ou une conclusion historique n'est autorisé par I02H.** Le témoin froid V11F, la branche thermique V11R et les anciens résultats restent inchangés. La procédure de reprise du harnais a guidé la réutilisation des sorties et la vérification des empreintes ; l'inspection visuelle du PDF a empêché de présenter la table NASA comme une carte matériau déjà identifiée sans ambiguïté.

## 1. Faits observés ou transcrits

### Sources primaires

Les dimensions nominales M(T), 76,2 × 300 × 2,3 mm, fissure centrale totale 25,4 mm et orientation L-T, proviennent de NASA CR-191523, déjà archivé et identifié dans I02F/I02G. Ses comparateurs ne sont pas utilisés pour ajuster Gf ici. Cette géométrie n'est pas celle d'une aile.

Le [manuel STAGS NASA/CR-2006-214281](https://ntrs.nasa.gov/citations/20060008654), PDF p.181/196 (pages imprimées 177/192), a été téléchargé séparément, haché et contrôlé visuellement. La table 15 imprime les déformations **0,15 et 0,4** ; le jeu d'entrée imprime **0,015 et 0,04**. Ce désaccord est réel dans le document, pas seulement dans son extraction. Les points de contrainte du tableau sont 345/390/430/470/491 MPa. Le jeu d'entrée contient aussi de petits écarts en psi : 62 400 contre 62 300 et 71 100 contre 71 200. E=71 400 MPa et ν=0,30 sont indiqués. Les pages examinées n'établissent pas explicitement la convention nominale/vraie.

La variante déjà calculée retient les décimales du jeu d'entrée et les contraintes MPa du tableau. Elle doit être nommée **sensibilité tabulée sous hypothèse de conversion**, et non mesure de matériau Boeing vérifiée. Le lien NASA 19990021015 de la configuration antérieure n'est pas utilisé comme corroboration de cette clôture : sa récupération n'a pas abouti.

La [documentation Altair LAW36](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/mat_law36_plas_tab_starter_r.htm) décrit l'écrouissage tabulé en déformation plastique. La [documentation de propriété de coque](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/prop_type1_shell_starter_r.htm) identifie Ishell=24 comme **QEPH avec stabilisation physique**, pas une coque entièrement intégrée. Le libellé ancien `FULLY_INTEGRATED_2024_T3_SHEET` est donc incorrect ; le nombre écrit dans le jeu solveur fait foi. La convention de contrainte dépend également du mode de déformation de coque : elle doit être vérifiée avec la carte et un essai élémentaire dans I02I.

### Exécution directement constatée

Cinq cas antérieurs complets ont été relus, sans relance solveur. Deux nouveaux témoins ont terminé normalement, en 163,875 et 147,484 s. Durée cumulée enregistrée des sept cas : 1 677,073 s (27,95 min), dont seulement 311,360 s de solveurs ajoutés à cette clôture. OpenRadioss Windows double précision, distribution locale `v20260728-win64` ; exécutables et commandes exacts hachés dans chaque `execution.json`. Calculs déterministes, une tâche OpenMP par cas, aucune graine aléatoire applicable.

## 2. Résultats d'un modèle officiel

**Aucun résultat NIST d'impact n'a été importé dans cette itération.** STAGS fournit ici un exemple et des entrées de matériau ; reproduire sa table dans un autre solveur n'est pas une validation croisée de sa solution. Les anciens comparateurs NASA ne constituent ni une loi de rupture Boeing ni une prédiction de pénétration dans le WTC1. Aucun résultat officiel n'a servi de cible à un ajustement de Gf.

## 3. Affirmations provenant des archives locales

Aucune nouvelle affirmation d'archive n'a été analysée ou adoptée. Aucun nouveau visionnage vidéo, aucun scan de l'archive, aucune modification de source. L'aspect d'une aile dans une vidéo et l'hypothèse d'une projection holographique ne sont pas testés par ce coupon. Une discordance de ce sous-modèle avec une observation ne démontrerait pas à elle seule un mécanisme alternatif.

## 4. Hypothèses propres au modèle

### Géométrie, matériaux et liaison

- Deux demi-tôles à nœuds doubles sur le trajet horizontal prescrit ; mouvement hors plan empêché. Pas de tunnellisation, de branchement spontané, de fragmentation volumique, de rivets, de longerons, de carburant ni de contact avec une façade.
- Masse volumique : 0,00278 g/mm³ ; masse nominale : 146,16684 g. Section brute initiale : 175,26 mm². Unités solveur g/mm/ms, force N, contrainte MPa, énergie brute N·mm=mJ ; énergies publiées multipliées par 0,001 pour obtenir des J.
- Témoin EPP : E=73 100 MPa, ν=0,33, limite plastique 360 MPa, sans écrouissage. Variante TAB : E=71 400 MPa, ν=0,30 et loi tabulée isotrope. **E, ν, limite et écrouissage changent ensemble**, ainsi que la raideur des liaisons : ce n'est pas une expérience isolant le seul écrouissage.
- Conversion supposée : εv=ln(1+εn), σv=σn(1+εn), εp=max(0,εv−σv/E). Le premier point plastique est ramené à zéro ; cette opération et le plateau numérique à 569,56 MPa jusqu'à εp=1 ne sont pas des données de rupture mesurées. Aucun état déjà endommagé n'a reçu une nouvelle loi : tous les cas partent d'un état neuf.
- Ressorts TYPE8 sans masse sur les ligaments, aires tributaires de Voronoï tronquées à l'entaille, largeur totale intacte 50,8 mm. Traction maximale 495 MPa et **Gf=30 N/mm hypothétique**, non ajusté aux comparateurs NASA. δf=2Gf/495=0,121212 mm. Énergie triangulaire nominale pour tous les ligaments : 3,5052 J, qui ne doit pas être confondue avec toute l'énergie interne de la tôle.
- Raideur normale par aire Kn=E/h (N/mm³), tangentielle Kt=G/h ; force de ressort obtenue avec l'aire B×largeur tributaire. δ0=495h/E. Ainsi **changer h change aussi la souplesse numérique de la liaison**. La comparaison n'est pas un raffinement à loi cohésive strictement fixe.
- Échelle indicative E Gf/495² : 8,9501 mm pour EPP, 8,7420 mm pour TAB. Ce n'est ni une longueur interne identifiée expérimentalement ni une preuve de résolution de zone plastique.

### Maillage, chargement et mesure

| Pas local h (mm) | Nœuds | Coques | Ressorts |
|---:|---:|---:|---:|
| 2,54 | 1 650 | 1 536 | 16 |
| 1,27 | 3 268 | 3 108 | 24 |
| 0,635 | 7 584 | 7 332 | 40 |

La zone fine s'étend à x=±22,86 mm, y=±12,7 mm. Avec a0=12,7 mm, une avance de **10,16 mm par pointe** atteint sa limite en x. Les avances finales de 12,7 mm ne relèvent donc plus de cette résolution locale.

Déplacement du mors supérieur : 6(3s²−2s³) mm, s=t/36 ms, échantillonné sur 401 points ; mors inférieur fixe en y, ancrage unique en x. Les cas TAB s'arrêtent à 12 ms : déplacement cible à cet instant ≈1,55556 mm, **pas 6 mm**. Les derniers historiques sont vers 11,990 ms, donc ≈1,55335 mm. Le témoin faible déplacement va à 0,02 mm en 12 ms. Le témoin sans propagation utilise le même historique que les cas TAB mais une liaison linéaire sans séparation.

Le facteur de pas explicite est 0,9, puis 0,45 dans le contrôle temporel ; intervalle de sortie 0,01 ms. La petite différence de seuil au demi-pas reste limitée par cet échantillonnage : elle ne prouve pas une précision physique à six chiffres. La fenêtre 12 ms a été choisie après l'essai long difficile ; c'est une borne exploratoire a posteriori, pas une durée physique préenregistrée.

Force publiée : somme des FY de la section cohésive. Contrainte nominale : force / section brute initiale. La somme brute des REACY du mors n'est pas interprétable comme la force utilisée ici et ne ferme pas le travail ; elle est conservée comme diagnostic. Le travail ∫Fsection du est comparé au travail externe, sans identifier la somme de section à une réaction de support exacte pendant les transitoires inertiels.

CTOA : angle géométrique calculé par 2 atan(ouverture/(2d)), aux distances d=B et 2B derrière la pointe discrète, moyenne des deux côtés. La pointe est construite par sommation des largeurs des ressorts contigus séparés. Coordonnées de référence et interpolation, pas une mesure expérimentale de pointe déformée ; aucune équivalence instrumentale n'est démontrée.

## 5. Résultats dérivés

### Seuils et avances

| Cas | Première séparation (MPa) | Pic nominal (MPa) | Avance finale par pointe (mm) | Avances distinctes |
|---|---:|---:|---:|---:|
| EPP, h=1,27, 36 ms | 205,295 | 238,327 | 0,635 | 1 |
| TAB, h=2,54, 12 ms | 182,454 | 246,422 | 6,350 | 3 |
| TAB, h=1,27, 12 ms | 209,525 | 240,690 | 12,700 | 5 |
| TAB, h=0,635, 12 ms | 215,415 | 226,425 | 12,700 | 8 |
| TAB, h=1,27, demi-pas | 209,525 | 240,762 | 12,700 | 5 |
| Témoin faible déplacement | aucune | 4,515 | 0 | 0 |
| Témoin sans propagation | aucune | 277,141 | 0 | 0 |

Différences relatives = |a−b|/max(|a|,|b|). Grossier/moyen : 12,920 %, **échec** du seuil 10 %. Moyen/fin : 2,734 %, **pass**. Demi-pas pour la première séparation : 0,000305 %, **pass**. L'écart moyen/fin des pics est néanmoins 5,927 % ; le seuil et le pic ne sont pas la même observable. L'EPP s'arrête après une unique avance : son cas fin n'a pas été lancé inutilement.

### Angle d'ouverture et propagation

| Avance fine (mm), dans la zone raffinée | CTOA(B) | CTOA(2B) |
|---:|---:|---:|
| 2,8575 | 5,569° | 3,590° |
| 4,7625 | 6,778° | 4,712° |
| 6,6675 | 4,863° | 4,309° |

La porte d'accessibilité « au moins deux avances fines après 2,3 mm » est franchie. Ce n'est pas la porte de calibration CTOA : les angles dépendent de la distance de mesure et du stade. Deux valeurs B proches de 5–7° ne suffisent pas. Au demi-pas, l'écart CTOA(B) à même avance vaut 2,53 % à 3,175 mm, 10,22 % à 5,715 mm et **21,00 % à 9,525 mm**. Il atteint 37,78 % à 12,7 mm, mais cette dernière comparaison sort de la zone fine. La propagation complète reste **non convergée/non qualifiée**.

### Bilans et témoins

Les sept cas passent les contrôles hérités : terminaison normale, absence d'erreur solveur, masse, résidu simplifié Wext−IE−KE, fermeture ∫Fsection du/Wext, KE/IE au pic, absence de propagation pour les témoins. Limites respectives : masse 0,01 %, énergie 1 %, travail 1 %, KE/IE au pic 5 %. Résultats maximaux : masse **0,00002737 %**, résidu d'énergie **0,04929 %**, erreur travail **0,06510 %**, KE/IE au pic **0,00821 %**.

Le bilan simplifié est examiné après que |Wext| dépasse 1 % de son maximum pour éviter les rapports artificiels près de zéro ; ce n'est pas une décomposition exhaustive de dissipation plastique, rupture et stabilisation. À la dernière sortie du TAB fin : Wext=34,49146 J, IE=34,41359 J, KE=0,0625431 J, reste=0,0153269 J. Le témoin à faible déplacement donne IE=0,007912133 J ; l'écart avec ½Fu est **0,00120 %**, cohérent avec l'élasticité attendue, sans remplacer un benchmark indépendant de compliance fissurée ou une sortie explicite de déformation plastique.

Un diagnostic nouveau balaie toute la fenêtre significative : KE/IE atteint **6,956 %** dans le cas fin à 10,33 ms, contre 3,993 % dans le moyen. Le critère initial porte seulement sur le pic de force ; son succès ne démontre pas une propagation entièrement quasi statique. Les oscillations restent visibles dans la figure, sans lissage destiné à améliorer la comparaison.

Avertissements : 445, inertie nulle des ressorts, conservés avec le plancher d'inertie imprimé 1e−20. L'EPP comporte aussi 506, réajustement de pente de ressort ; les différences imprimées sont inférieures à 1e−9 en relatif et contrôlées séparément dans `warning_audit.json`. Les répétitions de résumé ne sont pas comptées comme nouveaux avertissements. Aucune suppression silencieuse de ces diagnostics.

## 6. Contradictions, lacunes et suite

1. **Matériau :** établir la convention STAGS ; vérifier la traduction LAW36 par traction d'un élément neuf, y compris la transition élastique/plastique. Les identifiants historiques `nasa_law36` sont préservés mais ne signifient pas « carte validée ». Garder séparées convention, écrouissage, vitesse, anisotropie, triaxialité et rupture.
2. **Régularisation :** I02I devra comparer des h différents avec Kn/Kt fixes, puis une sensibilité de pénalité distincte. Ne pas attribuer le résultat actuel au seul raffinement ; ne pas supprimer le témoin sans propagation.
3. **Propagation :** comparer forces, avances et CTOA à déplacements/avances communs, affiner les sorties autour des sauts et examiner la vitesse de chargement. Agrandir la zone locale ou borner explicitement les mesures avant Δa=10,16 mm. Pas de validation sur la seule première séparation.
4. **Rupture :** Gf=30 N/mm reste hypothétique ; une sensibilité 15/30/60 N/mm à entrée matériau fixée reste à faire. Ne pas ajuster à 6° ou 200/230 MPa. Les effets 3D et de vitesse nécessaires à l'impact restent absents.
5. **Provenance :** le témoin EPP porte des empreintes anciennes de générateur/configuration, dont les versions originales n'ont pas été sauvegardées séparément. Ses jeux solveur et résultats existent et sont préservés. Les quatre cas TAB retenus correspondent aux empreintes courantes ; les deux nouveaux témoins ont leur configuration effective propre et vérifiée. Ne pas prétendre reconstruire exactement l'ancien générateur EPP.
6. **Essais non retenus :** premier Starter TAB avec champ VP décalé, puis correction dans un dossier distinct. Essai TAB 36 ms interrompu : 2 808 sorties jusqu'à 28,07 ms, aucune terminaison normale ; son `execution.json` ne mesure que le Starter, pas le temps total. Il reste diagnostic, jamais cas accepté. Tous ces fichiers sont conservés.

Un échec de modèle peut révéler une discrétisation, une loi ou des conditions aux limites inadéquates. Il ne réfute pas automatiquement l'événement réel. Inversement, les contrôles réussis ici ne valident pas l'impact, une aile intacte ou l'effondrement. La localisation en flexion après fracture complète reste non validée. Une température imposée n'est pas un incendie calculé. Blender reste une visualisation sans nouveau transfert mécanique validé dans I02H.

## Reproductibilité et reprise compacte

- Entrée d'origine inchangée : `wtc1_simulation_v8/data/impact_i02h_local_cohesive.json`.
- Complément de clôture : `wtc1_simulation_v8/data/impact_i02h_completion_r1.json` ; exécution par `scripts/complete_impact_i02h.py`. Ne pas relancer un dossier existant.
- Réaudit et figure : `scripts/summarize_impact_i02h.py` ; les audits recalculés sont séparés sous `verification_r1/`, les originaux inchangés. La création de synthèse refuse une deuxième écriture.
- Résultats : `summary_i02h.json`, `comparisons.json`, `campaign_audit.json`, `additional_diagnostics.json`, `warning_audit.json`, `synthese_impact_i02h.png`.
- Sources et intégrité : `source_manifest.json`, `preservation_before_finalization.json` (282 fichiers), `artifact_manifest.json`, `release_audit.json`. Vérification après enregistrement : `publication_verification.json`.
- Passation : `harness/handoffs/WTC1_IMPACT_I02H_HANDOFF.md`.

À la reprise, lire l'état et cette passation ; ne pas refaire les sept calculs. Commencer I02I par la convention matériau et une séparation contrôlée de la raideur de liaison et du maillage. Tout calcul susceptible de durer plusieurs heures doit être annoncé avant lancement.
