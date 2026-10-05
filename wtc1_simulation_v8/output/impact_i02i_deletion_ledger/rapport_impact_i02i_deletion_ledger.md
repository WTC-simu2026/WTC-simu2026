# WTC1 — IMPACT-I02I-L : registre énergétique à suppression complète

## 1. Faits directement observés ou transcrits

Huit essais F sauvegardés relus : **215216 lignes, 8823856 valeurs**. Toutes les valeurs binaires reproduisent exactement les CSV .6e ; deux lecteurs indépendants concordent, IE globale/SPRING ENERGY/IE liaison identiques bit pour bit. Analyse13,181737s, budget120s ; zéro job de solveur ou convertisseur relancé. La référence conditionnelle propre ajoute20 contrôles mécaniques, sans moteur.

Nouveaux contrôles L : **186/186 de cas,12/12 comparaisons,26/26 références**. Ces comptes sont ceux du diagnostic L. Les cinq critères stricts OFF/FX de F restent échoués et all_scientific_checks_pass de F reste false. L vérifie leur préservation et reproduit le retard d’une ligne ; elle ne promeut pas la qualification des anciens essais.

## 2. Résultats d’un modèle officiel

Aucun nouveau résultat NIST ou modèle du WTC. La [documentation primaire TYPE8](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/prop_type8_spr_gene_starter_r.htm) décrit des modes indépendants et les options de rupture. La [documentation /TH/SPRING](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/th_spring_starter_r.htm) définit OFF, les composantes de force et IE ; elle ne fournit pas ici une répartition de l’énergie supprimée en chaleur, fracture et mouvement. Deux snapshots sont conservés comme preuves documentaires, avec copyright et exclusion de redistribution.

Le chemin interne de cette énergie dans l’exécutable et le centrage TH ne sont pas identifiés. Le code du convertisseur et le schéma binaire officiel demeurent indisponibles ; le lecteur propre n’est accepté que sur sa signature3040 déclarée et ses blocs/codes contrôlés. L’égalité avec les CSV et les deux lecteurs vérifie ces fichiers, pas le solveur entier.

## 3. Affirmations des archives locales

Aucune nouvelle assertion d’archive, image ou vidéo examinée ; aucune archive rescannée. 2110 fichiers antérieurs épinglés depuis les inventaires K et précédents, inchangés. Source et anciennes itérations restent en lecture seule. Les propriétés et résultats H/K servent de références sauvegardées, sans relance. La preuve locale confirme la publication J+K et pending0 avant L ; après L enregistrée,pending1/2, prochaine paire L+M.

## 4. Hypothèses propres au diagnostic, unités et histoire

F : deux nœuds avec masse totale0,2g (0,1g chacun), nœud1fixe, déplacements X/Y du nœud2 imposés. Kn56000N/mm,Kt21500N/mm,picnormal495N,aire1mm²,Gf30N/mm hypothétique. H2 sur X et Y ; la courbe X est linéaire symétrique de penteKt, donc élastique dans ces essais. Rupture tangentielle désactivée et rotations bloquées. Aucun restart ni propriété d’un état endommagé modifiée.

Unités g/mm/ms/N, énergie de sortie Nmm=mJ puis ×0,001J, impulsionNms. Garea=30Nmm=0,03J ; réserve élastique X à0,02mm : Ux=Kt x²/2=4,3Nmm=0,0043J. Ux=Fx²/(2Kt),Uy=Fy²/(2Kn) sont des réserves **inférées de la loi** sur les lignes cohérentes. D=IE−Ux−Uy est un registre de travail non récupéré ; il n’identifie pas un canal physique de dissipation.

Sélection avant analyse : première transition OFF1→0 à la lignej, ligne avantj−1 et ligne aprèsj+2 fixées. Les six lignesj−2…j+3 sont conservées sur leurs temps originaux. Aucune partition récupérable n’est affirmée àj ouj+1, où OFF/force peuvent différer ; les valeurs brutes restent affichées. Le premier zéro des deux forces est un diagnostic séparé et ne sert pas à déplacer les signaux ou à choisir un meilleur résidu. Des vues CSV clairsemées portent les indices originaux ; les histoires complètes F restent épinglées.

Cellules binaires32 au plus proche, avec milieux exacts entre voisins, arithmétique rationnelle pour les cellules IE/KE/WE/F et les carrés. Aux lignes sélectionnées, calculer les intervalles exacts de ΔIE,ΔKE,ΔWE,ΔUx,ΔUy,ΔD et du bilan. Hypothèse d’arrondi explicite, sans accès aux doubles internes ; les cellules sont prises indépendamment, sans covariance supposée. Le signe et la valeur bruts ne sont jamais corrigés. L’intervalle du résidu ΔD−(Uavant−Uaprès)−(ΔWE−ΔKE) est descriptif et en grande partie une identité de registre ; son inclusion de0 **ne démontre pas le mécanisme de transfert**.

Seuils avant analyse :0,5% des échelles fixes d’énergie/réserve,force zéro1e−5N ; contrôle masse sans ajout. La compatibilité du registre retenu est testée contre IEaprès≈Garea+Uxavant+ΔWE−ΔKE, complétée par contrôles sans réserve et retour élastique. Elle reste une compatibilité numérique conditionnelle.

## 5. Résultats dérivés

| Cas sauvegardé | Ux avant (J) | IE après (J) | IE après−0,03J (J) | ΔIE (J) | ΔKE (J) | ΔWE (J) | Retard force/lignes |
|---|---:|---:|---:|---:|---:|---:|---:|
| FIXED_CAP200NS | 0.0043 | 0.0342999992371 | 0.004299999237 | 3.814697e-09 | 0 | 0 | 1 |
| FIXED_CAP100NS | 0.0043 | 0.0342999992371 | 0.004299999237 | 0 | 0 | 0 | 1 |
| FIXED_CAP050NS | 0.0043 | 0.0342999992371 | 0.004299999237 | 0 | 0 | 0 | 1 |
| PROP_CAP100NS | 0.003899865094 | 0.0339007072449 | 0.003900707245 | 8.430481e-07 | 0 | 8.430481e-07 | 1 |
| PROP_CAP050NS | 0.003900145848 | 0.0339005661011 | 0.003900566101 | 4.196167e-07 | 0 | 4.234314e-07 | 1 |
| AFTER_CAP100NS | 0 | 0.03 | 0 | 1.907349e-09 | 0 | 0 | 0 |
| AFTER_CAP050NS | 0 | 0.03 | 0 | 0 | 0 | 0 | 0 |

FIXED : à200/100/50ns, réserve≈0,0043J avant,forces nulles après et IE≈0,0342999992371J. L’excès au-delà du travail normal≈0,0042999992371J correspond à la réserve tangente. ΔKE brute=0 et son intervalle≈±2,91e−14J contient0 ; ΔWE brute=0 aussi. Le très petit ΔIE à200ns (≈3,81e−9J) apparaît en binaire malgré les CSV arrondis ; il est conservé et sa cellule admet0. ΔD vaut≈+0,0043J : la réserve cesse d’être récupérable d’après la force mais reste dans IE. Le gain cinétique enregistré ne vaut pas cette réserve dans ce protocole contraint.

PROP : réserve avant≈0,0038999/0,0039001J et petit travail imposé supplémentaire≈8,43e−7/4,23e−7J pendant la transition. Le bilan conserve cet apport ; aucun modèle de suppression instantanée à temps ajusté n’est utilisé. Les résidus du registre retenu sont≈−8,98e−10/−3,18e−9J, bien plus petits que la réserve.

AFTER : aucune réserve X avant la rupture,IE=0,03J après, même quand X est déplacé ensuite. RETURN sans OFF : la réserve maximale≈0,0043J revient à une IE finale≈3,568e−17J. Ces deux familles distinguent réserve préalable supprimée et énergie récupérée par retour élastique.

Les sept cellules exactes de bilan à l’événement admettent0. Les trois comparaisons de quantités par paire de pas passent12/12, sans alignement temporel ni extrapolation. Cinq Fx sur la ligne OFF demeurent non nulles :430N pour FIXED,≈409,5343N pour PROP, puis zéro une ligne plus tard. Les deux AFTER ont zéro dès OFF. La diminution de durée du retard avec le pas est conservée ; le centrage interne demeure inconnu.

### Référence conditionnelle pour une future séparation libre

Réutiliser le mouvement normal H (vy0=30mm/ms,m0,1g,Garea0,03J) et X indépendant jusqu’à tf=0,00561201925604ms. Àtf, déclarer **pour la comptabilité numérique** forcesX/Ynulles,vitesses continues,IEaprès=Garea+Ux(tf). Le mouvement suivant est balistique. IE reste continue ; le registre D acquiert la réserve Ux supprimée. Quadrature indépendante du travail/impulsionX,RK4 directe jusqu’àtf,continuité et conservation totale passent20/20 contrôles. Cela ne calibre pas une fracture mixte.

| vx0 (mm/ms) | E0 (J) | Ux(tf) (J) | vx(tf) (mm/ms) | IE après retenue (J) | KE après (J) |
|---|---:|---:|---:|---:|---:|
| 5 | 0.04625 | 0.000329765540009 | -4.290068671 | 0.03032976554 | 0.01592023446 |
| 10 | 0.05 | 0.00131906216004 | -8.580137342 | 0.03131906216 | 0.01868093784 |

Contrefactuel : si IEaprès est remplacée par0,03J tout en conservant les mêmes vitesses, le bilan perd exactement Ux(tf), soit0,00032976554/0,00131906216J. Une vraie restitution exigerait un canal d’énergie et une dynamique d’impulsion explicites ; augmenter arbitrairement une vitesse ou effacer l’énergie ne fournit pas ce mécanisme. Aucune politique de restitution physique complète n’est construite ici et aucun de ces cas n’est exécuté dans OpenRadioss en L.

## 6. Contradictions et informations manquantes

L confirme la compatibilité du registre de rétention sur des **déplacements imposés** et dérive une référence conditionnelle libre ; elle ne vérifie pas encore une séparation mixte libre. Le destin interne des0,0043J n’est pas identifié et aucune température/chaleur/énergie de fissuration n’en est déduite. Au point OFF, les sorties force/flag ne donnent pas une partition synchrone ; les cinq échecs F restent ouverts.

M proposera quatre états neufs libres,vx5/10,vy30,caps25/12,5ns,avec politique de rétention explicitée avant moteur. Tout échec brut à la transition restera échoué ; un contrôle de mouvement ou de bilan sur une fenêtre pré-déclarée ne le remplacera pas. Les références peuvent être réfutées par les sorties. Aucun matériau ancien endommagé ne sera reconfiguré.

Conserver les huit diagnostics G,sensibilités/couvertureE,quatre signesI,trois fins brutesJ,REAC/centrage TH,schéma officiel et provenance exacte du moteur non identifiés. NASA non résolu,Gf30hypothétique/Gf15/60différés,V11Ffroid et V11R→V11S conservés. Impact complet Boeing/façade,incendie et effondrement réel non qualifiés. Localisation en flexion après fracture complète non validée,température imposée≠incendie calculé,Blender visualisation.

## Reproduction et reprise

Pré-déclaration JSON1102020,zéro tirage,scripts,référence,histoires F épinglées,snapshots documentaires,intervalles exacts,comparaisons,rapport et passation conservés. Une erreur de syntaxe du brouillon de préparation a arrêté Python avant initialisation ou analyse ; brouillon conservé dans development_r0, correction de syntaxe uniquement. Aucun moteur ni ancien fichier modifié. Vérifier sans solveur avec complete_impact_i02i_deletion_ledger.py verify. L seule pending1/2 ; publier L+M après M vérifiée, pas de publication X.
