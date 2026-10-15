# Proposition A81 — observer la compression et la refermeture du joint

## Décision A80
L'attente d'un contact jusqu'à sa première sortie complète du gap nominal n'est pas retenue comme correctif. Avec la carte cohésive actuelle, la formule de mode I linéaire donne un début de dommage à 450/4400 ≈ 0,10227 mm et une rupture à 2×50/450 ≈ 0,22222 mm. Une ouverture de 0,3 mm peut ainsi rompre le joint sans sortir d'un gap de 0,5 mm. Sa refermeture pourrait alors manquer de réaction. Il faut mesurer ce point avant un développement logiciel transversal.

Ces nombres sont des résultats dérivés sous une branche constitutive donnée, non une observation du binaire ni une propriété mesurée d'un assemblage d'avion. Les défauts de la carte courte doivent être confrontés aux sorties natives. A67 qualifiait un domaine élastique limité; dommage, suppression et retour après rupture restent ouverts.

## Un seul témoin proposé
Le témoin reprend la géométrie native connue A67 FREE_Ismstr4 : deux faces carrées superposées de 10×10 mm, huit nœuds distincts et un élément TYPE43. Les lignes numériques LAW117/TYPE43 sont identiques à A79 : EN4400, ET800, TN450, TT100, GI/GII50; Imass1, Idel4, Irupt1, Ismstr4 et épaisseur vraie0. Aucun lien avec la géométrie nœud–facette A79 n'est introduit dans ce coupon.

La face inférieure est fixée. Le déplacement normal Z de la face supérieure suit une compression−0,05 mm, un retour0, une ouverture+0,3 mm, puis une refermeture−0,05 mm. Des paliers et des transitions quintiques échantillonnées sont tabulés dans les entrées. Le trajet finit à0,65 ms. X/Y restent libres afin de conserver des inconnues dynamiques comme dans la trame implicite déjà vérifiée; la validité du mode I exige donc déplacements transverses et cisaillements négligeables, quatre sauts normaux uniformes et aire constante.

La vitesse initialeY de la trame A67 est supprimée. Aucun contact général n'est défini afin d'isoler la cohésion. Les huit masses instrumentales de1g sont conservées dans ce coupon indépendant; aucune masse de la scène entière n'est compensée. Les unités restent g/mm/ms, forceN et énergieN·mm convertie enJ par0,001. Graine1102092, zéro tirage.

## Enregistrement et critères
Moteur A73 et Starter Windows inchangés, vérifiés par empreinte. Newmark et les tolérances sont conservés. Le pas plafond est0,000125 ms, comme A67; le minimum est fixé à la même valeur : toute réduction nécessaire arrête le témoin et sera un échec conservé. Les historiques et champs sont demandés tous les demi-pas, environ5200 pas jusqu'à la cible, et le RUN va jusqu'à0,6500625 ms pour sauvegarder la frontière réelle.

Sont demandés : mouvements et réactions des huit nœuds, accélérationZ, énergies de la pièce et globales, étatOFF, contraintes et variables de matériau (saut, maximum historique, dommage, traction, seuils). La disponibilité et le peuplement réels des sortiesUSR restent à vérifier; leurs zéros ou absences ne seront jamais assimilés à un dommage nul. Les sorties de champ doublent les historiques. Une sortie manquante, une référence non qualifiée, une erreur ou un avertissement non classé empêche de déclarer l'observation complète.

Les critères de mesure sont séparés des critères physiques. REAC est une impulsion de support cumulée (N·ms), et non une force instantanée; la conversion enN·s vaut0,001. La force de la base fixe se déduit de la pente ΔREAC/Δt avec les temps réels. Comparer les plateaux−0,05mm avant rupture (0,08–0,10ms) et après refermeture (0,62–0,65ms); le module intact attendu est22000N. Le signe sera contrôlé par le bilan indépendant d'impulsion. L'inertie du déplacement imposé est identifiée avec les accélérations; action/réaction/impulsion et travail extérieur/énergie sont contrôlés séparément. Les formules de seuils A67 restent inchangées dans la configuration. L'aire et les quatre sauts seront contrôlés avant d'utiliser la formule puremodeI. La réaction en compression après rupture sera mesurée, non supposée. Une fin normale ne qualifie pas le comportement physique. L'absence de contact dans le coupon ne valide aucun contact futur.

## Autorisation distincte demandée, aucun lancement effectué
Maximum deux processus natifs : un Starter, puis un seul Engine si la préparation passe. Un CPU, plafond180s chacun, estimation totale1–5minutes. Sans correctif, compilation, GPU, installation ni prolongement d'impact entier. Tout lancement, même échoué ou expiré, consomme sa place; aucun remplacement automatique. Si le Starter échoue, l'Engine conditionnel reste inutilisé. Les budgets et échecs A75/A77/A79 sont conservés.

Les cartes exactes, la configuration finale et les vérifications statiques sont présentes. Aucun calcul A81 n'est autorisé par cette préparation. Les dix secondes physiques et la vidéo3D de l'impact entier restent incomplètes.

Références primaires : [LAW117](https://help.altair.com/2024/hwsolvers/rad/topics/solvers/rad/mat_law117_starter_r.htm), [TYPE43](https://2025.help.altair.com/2025/hwsolvers/rad/topics/solvers/rad/prop_type43_connect_starter_r.htm), [sorties BRICK](https://2024.help.altair.com/2024/hwsolvers/rad/topics/solvers/rad/anim_brick_restype_engine_r.htm). Les sources épinglées éclairent les branches logicielles sans établir l'identité du Starter Windows.
