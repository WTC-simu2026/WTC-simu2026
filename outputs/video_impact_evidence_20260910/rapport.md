# Evidence1 / Evidence2 : impact, visibilité de l'aile et état réel du modèle

Date : 10 septembre 2026. Identifiant : VIDEO_IMPACT_EVIDENCE_20260910. Analyse locale des cinq fichiers fournis, originaux conservés. Cette étude latérale ne remplace pas V11R et ne valide pas V11S.

## Conclusion opérationnelle

**La maquette 3D existe, mais nous n'avons pas un modèle complet de résistance dynamique de chaque élément et assemblage, à chaque étage. Aucune nouvelle collision physique avion–façade n'a donc été exécutée ici.** La réponse à « reproduit-on Evidence1 ? » reste indéterminée, et non oui ou non. L'inspection a en revanche transformé les vidéos en pièces comparables et identifié deux limites décisives : montage temporel dans Evidence1 ; seconde tour dans la prise de vue attribuée à Courchesne. Il ne faut pas calibrer un impact WTC1 sur ces images de WTC2.

**Dans Evidence2, une partie sombre de la silhouette est très peu lisible avant l'impact ; cela ne démontre pas une disparition physique de l'aile.** La copie ne permet pas de déterminer séparément la contribution de la perspective, de l'éclairage, du flou et des traitements vidéo. Aucune explication unique n'est déclarée prouvée.

Voir `aile_comparaison_finale.png` : trois recadrages mobiles, tous agrandis exactement deux fois par répétition des pixels, sans accentuation, débruitage, interpolation temporelle ni génération d'image. Coordonnées dans `moving_crop_manifest.json`. Les images natives demeurent disponibles pour contrôler le cadrage. Le premier `aile_comparaison.png` est conservé mais NON retenu : le cadrage fixe coupait l'avion dans la troisième vue. Même réserve pour la fin de la planche à six recadrages fixes, utile seulement sur son domaine cadré.

## 1. Faits directement observés / transcrits

### Evidence1

- Conteneur MP4, vidéo H.264, YUV 4:2:0, 720 × 480 pixels ; 360 échantillons vidéo ; environ 12,013 s ; cadence nominale 29,970 images/s. Aucun flux audio déclaré par le lecteur de métadonnées.
- Le fichier contient le champ `handler_name: Twitter-vork muxer` et une date de création de conteneur de 2026. Ces champs ne prouvent ni sa plateforme d'origine, ni une date de tournage, ni son authenticité.
- La séquence commence par une vue rapprochée, revient à des positions d'approche antérieures, puis passe en écran partagé (visible à 3,003 s). Les vues d'approche se répètent ensuite. La seconde tour déjà fumante apparaît dans la composition : la lecture visuelle est celle du second impact, sans attribution vérifiée des deux opérateurs de caméra.
- Dans les 360 images décodées : 312 empreintes de pixels distinctes et 48 paires successives strictement identiques. Des correspondances approchées séparées d'environ 46 images apparaissent dans la partie en écran partagé ; leur diagnostic est sauvegardé, ce n'est pas une synchronisation physique des deux caméras.
- La durée de ce montage n'est pas une durée de pénétration. On ne peut en tirer directement ni décélération, ni effort d'impact, ni énergie absorbée. La silhouette qui semble entrer dans le bâtiment est observable ; les ruptures intérieures ne le sont pas.

### Evidence2

- MP4, H.264, YUV 4:2:0 BT.709, 976 × 720 pixels ; 5 363 échantillons vidéo à 30 images/s ; durée vidéo 178,7667 s, durée du conteneur annoncée 178,86 s avec audio AAC. La résolution de la copie n'est pas la résolution optique originale.
- Vue d'ensemble extraite, puis **151 images consécutives de 93,000 à 98,000 s**. Les 151 images décodées ont des empreintes différentes : aucun gel par répétition exacte détecté dans cette fenêtre. Cela n'exclut ni images interpolées/recompressées en amont, ni ralentissement hérité, ni stabilisation ; aucune authenticité n'en est déduite.
- L'approche est visible notamment à 95,400–95,967 s. À 95,600 et 95,733 s, le fuselage est oblique presque vertical dans l'image ; les contours brillants sur la droite de l'image se lisent nettement mieux que la zone sombre proche de son côté gauche. À 95,967 s, cette asymétrie persiste sur le fond de façade. Les flous et liserés de contours sont déjà présents dans la vidéo décodée, pas ajoutés aux recadrages.
- Des changements locaux clairs près de la zone de rencontre avec la façade sont visibles vers 96,033–96,200 s, puis un nuage se développe ; les couleurs orangées deviennent nettes vers 96,600 s. Ce sont des repères dans le fichier, **pas** un chronométrage certifié du premier contact ou de l'allumage. Pas de force ou de température déduite des couleurs.
- Aucun fragment d'aile détaché n'est identifié de manière fiable dans la fenêtre pré-impact examinée. Cette non-identification n'est pas la preuve de son absence.

### Identification documentaire

La notice de l'[ONF, STK-ID 59348](https://archives.nfb.ca/stockshot/59348/) attribue à Luc Courchesne une prise de vue du Boeing frappant la seconde tour. Elle décrit une collection Radio-Canada et un format Digital Betacam 4/3, 720 × 486 disponible. Cela appuie l'identification **WTC2, second impact**, cohérente avec la tour déjà en feu dans les images. La notice n'authentifie pas le MP4 local ni ses transformations ; ne pas transformer ses champs en identification certaine du modèle de caméra ou de la chaîne de compression locale.

## 2. Résultats de modèles officiels — statut distinct

Le rapport final [NIST NCSTAR 1-2, chapitre 5, notamment §5.4.4](https://nvlpubs.nist.gov/nistpubs/Legacy/NCSTAR/ncstar1-2v1.pdf) décrit des essais numériques de composants, dont une section d'aile avec carburant rencontrant des panneaux de façade, et l'interaction fluide–structure. C'est une référence méthodologique de modèle officiel, pas un résultat indépendant de notre simulation ni une explication de l'aile dans ce MP4. Aucun calcul NIST n'est crédité comme résultat nouveau du projet.

## 3. Affirmations provenant des fichiers et de leur présentation

- Nom du fichier : attribution « Luc Courchesne », à distinguer de l'authentification de cette copie.
- Question de l'utilisateur : « l'aile gauche disparaît avant de toucher la tour ». L'effacement apparent est une observation à examiner ; la disparition de matière et l'instant du contact sont des interprétations supplémentaires, non établies.
- On emploie ici « gauche de l'image » pour éviter de confondre un côté de l'image avec bâbord/tribord sans reconstruction d'attitude et de caméra.

## 4. Hypothèses explicatives, non prouvées individuellement

Une aile n'est détectable que si sa projection occupe assez de pixels et contraste avec le fond. Une surface vue presque par la tranche peut avoir une faible largeur projetée ; ses contours peuvent aussi se rapprocher de ceux du fuselage selon le point de vue. Une aile moins éclairée sur un fond sombre peut perdre sa silhouette tandis qu'une autre reste brillante. Le flou et une compression avec pertes peuvent ensuite atténuer le contraste restant. **Il n'est donc pas nécessaire qu'une pièce cesse d'exister pour qu'elle cesse d'être distinguable dans une vidéo.**

Ce raisonnement explique la possibilité physique et optique d'un effacement apparent ; il n'identifie pas le mélange exact de causes de cette copie. Nous n'avons ni position/optique de caméra calibrées, ni temps d'exposition, ni trames originales, ni historique vérifié d'encodage. La présence de H.264 ne prouve pas que H.264 est la cause principale. L'obstruction complète par la tour ou par le fuselage ne doit pas être affirmée sans géométrie correspondante.

L'alignement avion/toit/façade dans une image est une superposition 2D : franchir le bord apparent du toit n'est pas atteindre le plan de façade. L'ordre de contact nez/aile ne peut pas être lu à partir de ce seul bord projeté.

## 5. Résultats dérivés et capacité actuelle du projet

| Élément | Ce qui existe dans les fichiers actuels | Ce qui ne s'ensuit pas |
|---|---|---|
| Maquette V4.2 | 110 niveaux, 236 poteaux périphériques, 47 poteaux de noyau, 141 tronçons documentés autour de 92–101 | Pas toutes les sections exactes et connexions étage par étage ; hors zone, sections génériques ; les carrés de même aire ne restituent pas l'inertie réelle |
| Panneau V11R | Dalle, ferme, contacts, attaches, appuis, gravité et chauffage ; 261 degrés de liberté, 63 barres | Un panneau équivalent à petits déplacements, pas une tour ni un impact à haute vitesse |
| Ancienne branche impact V9M | Contrôles de cinématique, vol libre et contact conservatif limités sauvegardés | Rupture du projectile/façade, indépendance au maillage de l'énergie de fracture et convergence de l'impulsion non qualifiées |
| Animations V9P / V10Z | Livrables visuels déjà disponibles | V9P s'arrête au contact ; V10Z n'intègre pas le panneau V11R et n'est pas une collision prédictive |

Sources locales consultées sans recalcul : `harness/state.json` (V11R, prochaine V11S), `harness/handoffs/WTC1_V11R_HANDOFF.md`, `wtc1_3d_v4/README.md`, résultats synthétiques V8S/V9J/V9M/V9P dans l'état. Le contrôle froid V11F et les anciennes itérations n'ont pas été modifiés.

Une capacité statique exprimée en newtons n'est pas une énergie de rupture en joules. L'énergie absorbée dépend notamment de l'intégrale force–déplacement, de la plasticité, des ruptures et des assemblages ; un impact ajoute inertie, contact, déformation de l'avion et carburant. Les seules résistances statiques par type de poutre ne ferment donc pas le problème. Le modèle doit permettre l'arrêt, le rebond ou la pénétration selon les lois et données retenues, sans animation imposant la réponse.

### Prochain lot utile pour l'impact

Ne pas relancer les anciens coupons ni simuler une perforation par suppression arbitraire d'éléments. Le prochain lot d'impact doit d'abord satisfaire le déclencheur documentaire et numérique gelé en V9M : secteur de façade et joints explicitement définis, composant déformable qualifié et bilan de rupture/impulsion convergé. Ensuite seulement, réunir un secteur multiétage, avion déformable, contact, carburant et sensibilités, avec limites déclarées. Les vidéos fournies servent à définir **un cas de comparaison WTC2 distinct** ; elles ne fournissent pas les lois de matériau manquantes. La poursuite structurelle WTC1 reste V11S (fissuration contrôlée du panneau), non déclarée accomplie ici.

## 6. Contradictions, manques et contrôle de livraison

- Demande WTC1 face avant / documents vidéo du second impact : événements à séparer. La face de comparaison doit être identifiée dans un repère, pas seulement nommée « avant ».
- Pas d'original caméra ni de chaîne de conservation reliant ces MP4 à la notice ONF. L'estimation de la visibilité complète de l'aile reste limitée.
- Le montage Evidence1 n'est pas un étalon temporel brut ; ni ses deux cadrages ni Evidence2 ne sont synchronisés par une méthode validée.
- Pas de verdict sur l'effondrement, la présence d'explosifs, un trucage ou l'absence d'avion à partir de ces seuls fichiers.
- Pas de logiciel installé, pas d'archive rescannée. Un FFmpeg installé mais limité fournit les métadonnées ; faute de ffprobe utilisable, les tables MP4 `stts/ctts/mdhd/elst` sont conservées et analysées par le script. Le séquenceur de Blender 5.2 sert **uniquement au décodage vidéo**, sans scène mécanique ni animation calculée. Repli explicite par rapport à la procédure ffprobe.
- Evidence2 : horodatages relatifs de présentation conformes à 30 images/s ; Evidence1 : écart maximal de 0,000867 s entre PTS et cadence nominale. Les noms des images Evidence1 portent donc un temps nominal, non la date caméra.
- L'appel initial du harnais depuis Windows PowerShell a échoué car `Get-FileHash` n'était pas disponible dans cet environnement enfant. Le contrôle direct dans PowerShell 7 et la relecture sauvegardée passent : 96 entrées avant enregistrement de ce dossier, 98 fichiers requis, 8 empreintes source vérifiées. Le journal d'échec est conservé ; ce n'était pas une altération du projet.
- Empreintes SHA-256 avant dans `intake.json`, contrôle après dans `integrity_after.json`. Métadonnées, 547 PNG natifs extraits (36 d'aperçu + 511 de détail, avec recouvrement), planches, diagnostics de pixels, horodatages et scripts conservés. Ces contrôles valident la livraison et l'intégrité, pas l'authenticité de la prise de vue.

## Reprise compacte

Lire ce rapport et `harness/handoffs/WTC1_VIDEO_EVIDENCE_20260910_HANDOFF.md`. Ne pas réextraire les vidéos : images et PTS sauvegardés. Si la priorité reste l'anomalie visuelle, prochaine information décisive : version de génération antérieure à celle-ci, avec provenance et cadence/trames connues, puis confrontation image par image et géométrie caméra. Si la priorité revient au modèle WTC1, reprendre V11S depuis V11R, sans réutiliser ces vidéos de WTC2 comme calibration WTC1.
