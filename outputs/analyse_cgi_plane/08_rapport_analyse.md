# Analyse forensique de `CGI Plane.mp4`

Date de l'analyse : 22 août 2026  
Fichier source : `C:\Users\jeuxpc\Desktop\CGI Plane.mp4`  
SHA-256 : `48E7D82F7D695E9EBA8E7B193B7485C8B538761F8660A15865115CB64FDE8FCB`

## Conclusion

L'anomalie alléguée ne constitue pas un indice positif de CGI. Dans les 180 images de la séquence d'occultation (82,000 à 88,000 s du fichier fourni), l'aile atteint la ligne de toit du petit immeuble puis est masquée progressivement par sa silhouette. La partie située à droite de l'immeuble reste visible un peu plus longtemps. Cet ordre d'occultation est cohérent avec un avion lointain et un immeuble placé entre la caméra et l'avion.

Le fichier fourni ne peut toutefois pas être certifié « original et non modifié ». C'est un montage de provenance X/Twitter, ralenti, agrandi, titré, découpé et recompressé. L'absence d'une anomalie de calques dans ce montage ne prouve pas à elle seule l'authenticité de toutes les générations antérieures ; inversement, les halos et les dédoublements de ce fichier ne prouvent pas un compositing, car ils sont attendus après ralenti, rééchantillonnage, désentrelacement éventuel et compression.

## 1. Faits observés dans le fichier fourni

- Conteneur MP4, vidéo H.264 High, 1280 × 720, 29,970 images/s, YUV 4:2:0, 3 883 images.
- Durée : 129,591 s ; débit moyen global : environ 574 kbit/s.
- Le champ `handler_name` des deux pistes vaut `Twitter-vork muxer` et la date de création inscrite est le 22 août 2026.
- Le fichier contient des textes ajoutés, des ralentis, des agrandissements, plusieurs répétitions et au moins cinq transitions nettes vers 48,949 s, 64,498 s, 64,965 s, 88,355 s et 89,056 s.
- La séquence de 0 à environ 31 s étire très fortement l'approche et l'impact. Les silhouettes fantômes visibles dans certaines images appartiennent donc à un traitement temporel déjà appliqué au fichier.
- Le tableau 6-1 du NIST décrit V4 comme une source NTSC ; le rapport précise que les numérisations NTSC analysées faisaient 720 × 480 à 29,97 images/s. Le 1280 × 720 progressif fourni ici est donc nécessairement une transformation ultérieure, pas cette numérisation de travail à l'identique.
- Dans les 180 images décodées de 82 à 88 s, aucune paire d'images adjacentes n'est strictement identique après décodage. Cela ne garantit pas 180 instants source distincts : une nouvelle compression rend généralement différentes des images répétées ou interpolées.

## 2. Lecture image par image de l'occultation

| Image | Temps du fichier | Observation |
|---:|---:|---|
| 91 | 85,018 s | L'aile est entièrement visible au-dessus du toit. |
| 106 | 85,519 s | Elle descend vers la ligne de toit ; aucun contact visuel encore. |
| 121 | 86,019 s | La pointe gauche atteint la silhouette supérieure de l'immeuble. |
| 136 | 86,520 s | La partie qui se trouverait derrière la façade n'est plus visible ; la partie à droite reste visible. |
| 151 | 87,020 s | L'occultation progresse avec le déplacement ; seul un tronçon à droite demeure. |
| 166 | 87,521 s | L'avion a presque entièrement quitté cette zone du cadre. |

Sur les 179 transitions entre images adjacentes, la différence absolue RGB moyenne est de 1,539 niveau sur 255 (médiane 1,334 ; minimum 0,016 ; maximum 13,501). Ces faibles différences sont compatibles avec un ralenti fortement interpolé ou rééchantillonné et recompressé ; elles ne permettent pas de reconstituer les champs ou images de la bande originale.

## 3. Pourquoi l'aile passe derrière l'immeuble

Une caméra ne classe pas les objets selon leur hauteur ou leur taille apparente, mais selon leur position sur la ligne de visée. La prise de vues attribuée à Michael Hezarkhani est répertoriée par le NIST comme la vidéo V4 de l'impact de WTC 2. Le tableau 6-1 (page 153 du rapport, page 267 du PDF) situe la prise de vues au niveau du sol près de Castle Clinton, au sud-est des tours. Les bâtiments visibles entre ce point et WTC 2 sont donc au premier plan par rapport à l'avion lorsqu'il arrive au voisinage de la tour.

Dans le fichier examiné, le comportement des pixels confirme cet ordre géométrique :

1. l'aile se rapproche continûment du bord du toit ;
2. elle disparaît exactement à ce bord, sans apparaître devant la façade ;
3. le tronçon qui ne se projette pas sur la façade reste visible à droite ;
4. la fumée masque également certaines parties de l'avion, avec des contours mous attendus dans une vidéo analogique ancienne plusieurs fois transformée.

Ce n'est donc pas une « superposition impossible », mais une occultation de premier plan. Un compositing volontaire pourrait évidemment reproduire une occultation correcte ; cette seule observation ne peut donc ni certifier toute la vidéo ni démontrer un faux.

## 4. Provenance documentaire

- Le plan sous-jacent est identifiable comme la prise de vues de Michael Hezarkhani. Le rapport NIST NCSTAR 1-2 / 1-2B reproduit une image créditée « © 2001 Michael Hezarkhani » et la désigne comme `Video V4 (WTC 2 impact)`.
- Le dépôt NIST distingue les « Original Video from Tapes » des clips organisés et des autres copies. Cette distinction est essentielle : le MP4 X reçu ici ne fait pas partie des masters et ne conserve pas la qualité d'une bande source.
- Une analyse secondaire publiée en réponse à cette affirmation virale arrive à la même conclusion géométrique : les bâtiments incriminés sont devant WTC 2 dans l'axe de cette caméra. Ce point secondaire est cohérent avec notre observation, mais la conclusion présente repose d'abord sur le déroulé des pixels du fichier fourni et sur la localisation documentaire du plan.

Sources :

- NIST, [Disaster and Failure Studies Repository](https://www.nist.gov/world-trade-center-investigation/photos-videos-and-simulations)
- NIST NCSTAR 1-2, [rapport principal, notamment le tableau 6-1](https://nvlpubs.nist.gov/nistpubs/Legacy/NCSTAR/ncstar1-2v1.pdf)
- NIST NCSTAR 1-2B, [Figure A-4 — Video V4, WTC 2 impact](https://www.govinfo.gov/content/pkg/GOVPUB-C13-6279f222e377ad1d41bc741934d2384c/pdf/GOVPUB-C13-6279f222e377ad1d41bc741934d2384c.pdf)
- NIST NCSTAR 1-2, [Figure E-4 — Video V4, WTC 2 impact](https://www.govinfo.gov/content/pkg/GOVPUB-C13-3cdfad1b1d757b19faa93482f06cd58b/pdf/GOVPUB-C13-3cdfad1b1d757b19faa93482f06cd58b.pdf)
- Analyse secondaire de l'affirmation virale : [Disinformation in Flight 175 Rare Video](https://www.checktheevidence.com/wordpress/2013/09/14/disinformation-in-flight-175-rare-video-posted-sep-11-2013/)

## 5. Limites et niveau de conclusion

**Établi pour ce fichier :** le MP4 est un dérivé X édité et recompressé ; la prétendue inversion de profondeur n'apparaît pas dans le déroulé image par image.

**Conclusion la mieux soutenue :** aucune signature positive de CGI n'est mise en évidence par l'aile qui disparaît derrière l'immeuble. L'occultation observée est géométriquement normale.

**Non établi :** l'intégrité bit à bit de la bande originale, l'absence absolue de toute retouche dans une génération antérieure et la chaîne de possession complète. Pour les tester, il faudrait la bande ou la numérisation la plus proche de l'original, et non un montage X de 574 kbit/s.

## 6. Livrables

- `01_vue_ensemble_5s.png` : vue d'ensemble du montage.
- `03_sequence_originale_0_31s.png` : première présentation ralentie.
- `04_reprise_zoom_49_88s.png` : reprises et agrandissements.
- `05_occultation_82_88s_10fps.png` : planche à 10 images/s de la zone contestée.
- `06_occultation_native_annotee.png` : six images natives annotées.
- `07_differences_interframes.csv` : mesures des 180 images décodées.

Le fichier source est resté inchangé ; tous les dérivés ont été écrits dans ce dossier de sortie.
