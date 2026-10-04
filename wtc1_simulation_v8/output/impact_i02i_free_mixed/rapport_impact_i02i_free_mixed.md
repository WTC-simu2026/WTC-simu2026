# WTC1 — IMPACT-I02I-K : ouverture et cisaillement libres sans séparation

## 1. Faits directement observés ou transcrits

Quatre états neufs, douze jobs (starter, moteur et export de chaque cas), sans warning de précontrôle, avec terminaison normale. Durée cumulée des jobs : 3.566064 s, budget 90 s/cas et 600 s/campagne. Les 1922 lignes ont chacune 41 valeurs : 78802 valeurs binaires reproduisent exactement les jetons CSV .6e. Deux lecteurs indépendants concordent ; IE globale, SPRING ENERGY et IE de liaison sont identiques bit pour bit. TH une ligne par cycle, pas maximal mesuré 25/12,5 ns, aucune masse ajoutée et WE=0.

Les critères pré-déclarés passent : **254/254 de cas, 28/28 comparaisons et 26/26 références**. Les 20 références mécaniques incluent une intégration RK4 directe indépendante (4096/8192 pas), les équations de mouvement et l’identité énergétique. Les six références de lecture vérifient les rejets de fichiers invalides et des états élastiques exacts avec deux forces. OFF=1 dans tous les cas, Y reste positif et inférieur à la séparation complète.

## 2. Résultats d’un modèle officiel

Aucun nouveau résultat NIST ni modèle historique. Le solveur est utilisé pour quatre témoins TYPE8 bornés, pas comme validation du WTC. Les propriétés et mots-clés hérités sont documentés dans les manifestes I/J/H ; aucune nouvelle donnée physique ou source primaire nécessaire pour cette combinaison des mêmes lois. Le lecteur J n’est accepté que sur les signatures déclarées, version 3040, blocs et codes vérifiés. Le schéma binaire officiel et le code original du convertisseur restent non obtenus. La définition documentaire REACX/REACY comme force et leur comportement observé d’impulsion cumulative restent une limite ; le centrage interne TH demeure non établi.

## 3. Affirmations des archives locales

Aucune nouvelle assertion d’archive et aucune vidéo inspectée. 2011 fichiers antérieurs épinglés depuis les inventaires sauvegardés, vérifiés inchangés. Aucun ancien moteur relancé ni archive rescannée. Les échecs I/J et E/F/G ainsi que le contrôle froid V11F et la branche V11R → V11S sont conservés.

## 4. Hypothèses propres au modèle, propriétés, unités et historique

Deux nœuds, chacun de masse 0,1 g ; nœud 1 fixe, nœud 2 libre sur X et Y, Z et rotations bloqués. Une liaison TYPE8, sans contact ni couplage matériel entre axes. Kn=56000 N/mm, Kt=21500 N/mm, pic normal hypothétique 495 N, aire 1 mm², Gf=30 N/mm hypothétique. Séparation normale δf=0,1212121212 mm, début d’adoucissement δ0=0,0088392857 mm ; aucun OFF attendu dans les fenêtres. Loi tangentielle purement élastique, rupture tangentielle désactivée. Tous les états sont neufs, sans restart ou modification d’une propriété endommagée.

Unités : g, mm, ms et N, car 1 g·mm/ms²=1 N ; 1 N·mm=0,001 J. Vitesses mm/ms (=m/s), impulsions N·ms. Cas arrêt : vx0=10, vy0=20, E0x=0,005 J et E0y=0,020 J, total0,025 J, fin0,012 ms. Cas sous-pic : vx0=1, vy0=√20, E0x=0,00005 J, E0y=0,001 J, total0,00105 J, fin0,004 ms. Seed1102019, zéro tirage. Caps25 et12,5 ns ; aucun déplacement X/Y imposé.

Référence séparable : ωx=√(Kt/m), x=vx0/ωx·sin(ωx t), vx=vx0 cos(ωx t), Fx=Kt x. Y reprend la référence H2 vérifiée en I avec maximum historique δmax conservé. À la décharge, Fy=max[0,Fenveloppe(δmax)+Kn(y−δmax)] ; Dy=Wchargement(δmax)−Fenveloppe(δmax)²/(2Kn), sans réinitialisation de l’histoire. Réserve récupérable Ux=Fx²/(2Kt), Uy=Fy²/(2Kn), puis conversion en J ; IE=Ux+Uy+Dy ; KE=m(vx²+vy²)/2 ; E0+WE=IE+KE. Dy est du travail numérique non récupéré, sans identification à une chaleur ou fissuration réelle.

P0x=m vx0, P0y=m vy0 ; Jappui,axe=Paxe−P0axe. Les intégrales −∫Faxe dt sont comparées séparément aux sorties REAC, et ∫(Fx dx+Fy dy) au travail interne. Force élastique, force H2, énergie issue du maximum historique et références en temps sont contrôlées séparément. Seuils déclarés avant moteur : amplitudes par axe/impulsions ≤1 %, énergie/travail et comparaisons ≤0,5 %, avec échelles fixes prévues.

Précision pré-déclarée : cellules binaires32 au plus proche, milieux exacts entre voisin et valeur stockée (fractions dyadiques), calcul exact de l’intervalle IE−Fx²/(2Kt)−Fy²/(2Kn). Borne supérieure ≥0 à chaque ligne ; dans la phase historiquement élastique, intervalle contenant0. Temps final : cellule intersectant [fin−2pas,fin]. Il s’agit d’hypothèses de représentation, sans accès à la valeur interne. Aucun clipping, tolérance de signe ajustée, déphasage ou promotion d’un ancien échec. Les valeurs brutes et les fractions exactes sont sauvegardées.

## 5. Résultats dérivés

| Cas | Lignes | Erreur vx (% amplitude) | Erreur vy (% amplitude) | Résidu énergie (% E0) | Ux finale (J) | IE−Ux−Uy final brut (J) |
|---|---:|---:|---:|---:|---:|---:|
| FREE_MIXED_ARREST_025NS | 480 | 0.578729 | 0.308936 | 0.00102806 | 0.002226508744 | 0.01921334874 |
| FREE_MIXED_ARREST_012P5NS | 960 | 0.289585 | 0.154498 | 0.000259399 | 0.002197781114 | 0.01921341846 |
| FREE_MIXED_ELASTIC_RETURN_025NS | 161 | 0.578729 | 0.933158 | 0.00844247 | 4.607768954e-05 | -8.232206986e-12 |
| FREE_MIXED_ELASTIC_RETURN_012P5NS | 321 | 0.289585 | 0.467134 | 0.0021155 | 4.607673392e-05 | 5.481430343e-12 |

Le plus grand écart brut de vitesse/impulsion est 0,93546 % dans le cas sous-pic 25 ns, puis ≈0,46772 % à12,5 ns. Aucun ajustement temporel. Les forces/déplacements ont des écarts nettement plus faibles. Le résidu énergétique maximal est 0,008443 % de E0 ; le critère0,5 % passe. Les comparaisons sont faites aux temps déclarés couverts, sans extrapolation.

Dans l’arrêt normal, Uy et Fy deviennent nuls, vy≈−3,966 mm/ms ; Dy≈0,0192134 J persiste, tandis que X continue à osciller et Ux finale≈0,0022 J. La réserve X n’est donc pas supprimée lorsque Y se décharge **tant que l’élément reste actif**. Ce résultat ne traite pas la désactivation totale OFF. Dans le sous-pic, l’intervalle de D contient0 sur toutes les lignes : retour numériquement compatible avec la référence élastique séparable.

| Cas | Minimum D brut (J) | Lignes D brut<0 | Temps final binaire (ms) | Condition brute fin sans intervalle (diagnostic) |
|---|---:|---:|---:|---|
| FREE_MIXED_ARREST_025NS | -2.159982046e-10 | 11 | 0.01197499968111515 | passe |
| FREE_MIXED_ARREST_012P5NS | -1.221326794e-10 | 20 | 0.011987499892711639 | passe |
| FREE_MIXED_ELASTIC_RETURN_025NS | -1.282944594e-10 | 78 | 0.0040000001899898052 | échoue |
| FREE_MIXED_ELASTIC_RETURN_012P5NS | -1.257381645e-10 | 159 | 0.0040000001899898052 | échoue |

Les quatre minima bruts restent sous −1e−10 J, seuil historique I mentionné à titre descriptif seulement. Les deux fins sous-pic dépassent la fin demandée de ≈1,90e−10 ms. **Aucun signe brut ni temps n’est corrigé** ; les critères K portent dès leur déclaration sur les intervalles de représentation. Toutes les bornes supérieures de D sont non négatives et les cellules élastiques contiennent0. Les cellules de fin passent. Ces compatibilités ne résolvent pas le signe interne et ne modifient pas les quatre échecs I ou les trois critères bruts J.

## 6. Contradictions et informations manquantes

K vérifie deux modes indépendants simultanés sans séparation ; aucun vrai couplage de contact, de matériau, de dalle ou de rupture mixte. Le devenir de Ux lorsque la rupture normale désactive tout l’élément reste ouvert. F avait conservé IE≈0,0343 J sous cisaillement fixé, avec réserve tangentielle≈0,0043 J avant suppression ; cela ne qualifie pas sa restitution dans un corps libre. L’étape L préparera le registre énergétique sur les sorties F sauvegardées avant une nouvelle séparation mixte libre. Toute politique de suppression/rétention/restitution d’énergie devra être explicite et comparée à une référence avant moteur, sans changer un état endommagé ancien.

Conserver cinq échecs OFF/FX F, huit diagnostics stricts G, sensibilités d’inertie/angle et couverture E, quatre signes I et trois fins J, limites de précision/centrage/REAC. Les conventions NASA restent non identifiées, Gf30 hypothétique et Gf15/60 différés. Aucune calibration physique de fracture, impact complet Boeing/façade, incendie ou effondrement réel. Flexion localisée après fracture complète non validée ; température imposée ≠ incendie calculé ; Blender reste une visualisation.

## Reproduction et reprise

Configuration JSON, référence, scripts, sources héritées, cartes, exécutables hachés, versions, journaux, T01/CSV, comparaisons et intervalles exacts conservés. Vérifier sans moteur : complete_impact_i02i_free_mixed.py verify. Rapport et passation existent avant registre/état. J+K publication due après vérification d’intégrité, avec anciens échecs conservés ; ensuite L+M. Cadence locale fait foi, aucune publication X.
