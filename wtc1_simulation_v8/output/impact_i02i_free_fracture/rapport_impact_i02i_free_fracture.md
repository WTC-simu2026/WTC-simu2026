# WTC1 — IMPACT-I02I-H : précision libre et séparation normale libre

## 1. Faits directement observés ou transcrits

Quatre états neufs, 12 exécutables sauvegardés, 4.643206 s cumulées ; limites 90 s/cas et 600 s/campagne respectées. Aucune alerte starter, terminaison normale, pas réel sauvegardé plafonné et une ligne TH par cycle, aucun ajout de masse. Les deux contrôles élastiques sont exécutés et audités avant déclaration des cas de rupture. Le garde dans fracture_declaration_guard.json prouve que leur audit strict et la référence vérifiée existaient avant les deux nouveaux calculs de rupture. Aucun déplacement imposé sur le degré de liberté mobile ; uniquement une vitesse initiale, contraintes transversales et nœud fixe.

Tous les 122 critères de cas et 14 comparaisons déclarés passent, ainsi que les 9 contrôles de référence. Les anciennes sorties de G à 100/50 ns sont réutilisées, sans les recalculer ni changer leurs huit diagnostics stricts échoués.

La définition primaire de /INIVEL, /TH/NODE, /DTIX et TYPE8 est réutilisée depuis les manifestes sources sauvegardés G/F/D ; aucune donnée matérielle précise ajoutée. La documentation appelle REACX/REACY une force alors que cette sortie de la version installée est compatible avec une impulsion cumulative. Les deux lectures et le contrôle indépendant par intégrale de force sont conservés. Le phasage exact du code TH n'est toujours pas établi, aucune série n'est décalée pour réussir un critère.

## 2. Résultats d'un modèle officiel

Aucun nouveau modèle NIST/WTC ajouté. La documentation Radioss définit des options de logiciel et non une explication historique. Les deux conventions NASA précédentes restent non identifiées et aucune branche n'est choisie à partir de H.

## 3. Affirmations des archives locales

Aucune nouvelle affirmation d'archive, aucune vidéo inspectée. 1765 fichiers précédents contrôlés à partir des inventaires sauvegardés, sans archive rescannée ni ancien solveur relancé. V11F froid, V11R et V11S différée conservés. F+G publiée et vérifiée reste la base publique ; le dépôt n'est pas modifié pour H seule.

## 4. Hypothèses propres au modèle, propriétés, unités et références

Deux nœuds coïncidents reliés par une seule liaison TYPE8, aire de référence 1 mm², masse totale 0,2 g répartie 0,1 g/nœud, inertie de rotation 0,001 g mm² et rotations bloquées. Les cartes sont neuves à chaque cas, sans restart, viscosité, ajout de masse ou substitution de propriété endommagée.

Élastique X : Kt=21500 N/mm, v0=1 mm/ms, u0=0, X libre et Y/Z bloqués. Même référence que G : ω=√(k/m), T≈0,0135506659245 ms, durée huit périodes, E0=0,00005 J, P0=0,1 N ms. Tous les champs bruts amplitude/impulsion sont désormais limités à 1 %, énergie/période à 0,5 %. Ratios d'erreur par rapport à G 50 ns attendus en h² pour déplacement/momentum global/énergie, h pour vitesse/impulsion, tolérance relative 10 %. Seuils fixés avant moteur, sans phase ajustée.

Rupture normale Y : Kn=56000 N/mm, pic hypothétique 495 N, Gf=30 N/mm pour aire 1 mm² ; δ0=0.00883928571429 mm, δf=0.121212121212 mm. F=kδ jusqu'à δ0 puis F=ks(δf−δ), ks=4404.97917319 N/mm, jusqu'à désactivation complète. X/Z bloqués, Y libre, v0=30 mm/ms=30 m/s ; cette vitesse appartient au témoin, pas au Boeing. E0=45 N mm=0,045 J > travail normal 30 N mm=0,03 J, garantissant une ouverture monotone dans la référence. Il n'y a aucun réservoir de cisaillement dans cet essai.

Unités : g, mm, ms, N ; N=g mm/ms², N ms=g mm/ms, N mm=mJ, J=0,001 N mm. Dans v(δ)=√(v0²−2W/m), W est en N mm, jamais en J sans conversion. Énergies IE/KE/WE du solveur sont converties par ×0,001. Bilans bruts : J1+J2+P0−P, avec P0=mv0 ; E0+WE−IE−KE, avec U récupérable=F²/(2Kn) en phase active, IE−U rapporté comme travail numérique non récupéré. Aucune dissipation physique mesurée n'est identifiée par IE.

Référence propre : mδ̈=−F(δ). Branche élastique δ=v0 sin(ωt)/ω. Au pic t0=0.000297084046428 ms, vpic=29.2616734948 mm/ms. Pour τ=t−t0, x=δf−δ=x0 cosh(λτ)−vpic sinh(λτ)/λ, λ=√(ks/m). La séparation survient à tf=t0+atanh(λx0/vpic)/λ=0.00561201925604 ms. Après séparation : F=0, v=√(v0²−2Gf A/m)=17.3205080757 mm/ms et déplacement linéaire. Référence indépendante par quadrature t(δ)=∫dδ/√(v0²−2W(δ)/m), 512/1024/2048/4096 subdivisions par branche. Équation du mouvement, dérivée dW/dδ=F, continuités et énergie contrôlées ; erreur maximale d'identité énergétique 2.77556e-17 J.

Critères de rupture déclarés après ces gardes et avant moteur : champs bruts 1 % de leurs amplitudes, bilan et travail 0,5 %, OFF à moins de deux pas du temps analytique, forces nulles après deux lignes, vitesse post-rupture à 1 % et momentum constant, aucun travail externe. Fin demandée 0,012 ms ; dernières lignes 0,012 ms et 0,011975 ms conservées sans extrapolation.

## 5. Résultats dérivés

### Contrôles libres élastiques

| Cas | Pas (ns) | Déplacement (%) | Vitesse nodale (%) | Impulsion brute (%) | Bilan énergie (%) |
|---|---:|---:|---:|---:|---:|
| ELASTIC_025NS | 25 | 0.02813873 | 0.5787248 | 0.5796554 | 0.003370722 |
| ELASTIC_012P5NS | 12.5 | 0.007034525 | 0.289582 | 0.289821 | 0.000852572 |

Les champs bruts passent maintenant tous le seuil 1 % dans ces deux cas neufs. Le résidu d'impulsion décroît encore comme h et les erreurs déplacement/momentum global/énergie approximativement comme h² aux tolérances déclarées. Ce résultat ne réécrit pas les diagnostics de G, ne prouve pas l'algorithme exact de centrage et ne ferme pas les essais mixtes OFF/FX de F.

### Séparation normale libre

| Cas | OFF (ms) | IE finale (J) | KE finale (J) | Vitesse finale (mm/ms) | Impulsion brute (%) | Bilan énergie (%) |
|---|---:|---:|---:|---:|---:|---:|
| NORMAL_050NS | 0.00565 | 0.02999665 | 0.01500335 | 17.32244 | 0.412173 | 0.001697778 |
| NORMAL_025NS | 0.005625 | 0.02999843 | 0.01500157 | 17.32142 | 0.2061057 | 0.0004288889 |

À 50 ns : P0+Jappui=3−1,267756=1,732244 N ms, égal au momentum final sauvegardé. À 25 ns : P0+Jappui=3−1,267858=1,732142 N ms, égal au momentum final sauvegardé. WE=0, masse conservée. Après OFF, forces nulles et vitesse/momentum constants : le mouvement post-séparation est calculé, sans trajectoire prescrite. IE tend vers 0,03 J et KE vers 0,015 J, comme la référence de la loi hypothétique ; vitesse finale à environ 0,011154/0,005265 % de la référence. Les événements OFF suivent tf à moins d'un pas dans les sorties observées, sans forcer leur temps.

L'écart entre IE et le travail de F intégré sur le déplacement est inférieur à 0,000026 % du travail normal. Le bilan énergétique global maximal vaut 0,001698 % puis 0,000429 % de E0. Le résidu brut d'impulsion reste non nul (0,412/0,206 %), mais passe les seuils. Les tableaux près d'OFF sont conservés, sans interpréter leur partition comme une dissipation physique.

Il s'agit d'une vérification numérique locale de séparation normale libre et de mouvement ensuite sans force, pour une unique liaison et ces paramètres. Aucun rivet réel, déchirure de plaque ou effondrement ne peut être déduit de cet accord.

## 6. Contradictions et informations manquantes

Restent ouverts : les cinq critères mixtes OFF/FX de F, le réservoir élastique tangentiel supprimé avec l'élément, la définition exacte de REACX/REACY et du centrage TH, toutes les limitations d'inertie/angle/couverture de E, l'identification nominal/vrai NASA et la calibration physique de Gf30. Gf15/60 restent différés. Aucun contact post-fracture, état de plaque ou mode mixte n'est qualifié par H.

I testera d'abord l'arrêt et la restitution lors d'une ouverture qui n'atteint pas la séparation, avec historique de décharge H2. Le plan proposé contient un cas énergie 0,02 J (v0=20 mm/ms) dans l'adoucissement et un retour sous pic à 0,001 J. Avant tout moteur I, dériver/vérifier les références et vérifier que la fenêtre reste en ouverture positive sans compression. Rien n'est exécuté en I ici.

La localisation en flexion après fracture complète n'est pas validée ; température imposée ≠ incendie calculé. Blender reste une visualisation. Impact complet Boeing/façade, incendie et effondrement réel restent non validés.

## Reproduction et reprise

Deux pré-déclarations JSON immuables, scripts, référence analytique, graines sans tirage, decks, journaux/versions/empreintes d'exécutables, CSV et rapports sauvegardés. Les étapes exécutées sont declare_elastic, run_elastic, audit elastic, référence verify, declare_fracture, run_fracture, audit fracture ; la seconde déclaration vérifie les SHA-256 des deux gardes. Le harnais est contrôlé avant/après et l'état n'est actualisé qu'après présence et contrôle de ces artefacts.

Contrôle sans solveur : `C:/Python314/python.exe -X utf8 wtc1_simulation_v8/scripts/complete_impact_i02i_free_fracture.py verify`. Publication : H seule pending 1/2, H+I après une I vérifiée, avec contrôle distant des archives et CI. Aucun envoi X.
