# WTC 1 — maquette 3D V4.2

Ce jalon crée une maquette Blender paramétrique de référence. Il ne simule encore ni l’impact, ni l’incendie, ni l’effondrement.

## Contenu vérifiable

- enveloppe de **207 ft 2 in × 207 ft 2 in** (63,1444 m) ;
- hauteur architecturale cible de **1 368 ft** (416,9664 m) et antenne à 1 728 ft ;
- **110 niveaux** construits à partir du calendrier de hauteurs associé aux dessins A-AB-201/A-AB-301 ;
- noyau d’environ **135 ft × 87 ft**, axe long est–ouest ;
- **236 poteaux périphériques**, 59 par face, à l’entraxe nominal de 3 ft 4 in ;
- topologie officielle des **47 poteaux du noyau**, identifiants 501–1008 ;
- coordonnées du noyau reconstruites depuis les figures 2-2 et 2-7 de NCSTAR 1-3A, avec une tolérance de plan annoncée de ±0,30 m ;
- **141 tronçons du noyau** issus du Drawing Book 3 : 47 colonnes × 3 bandes de raccordement autour des niveaux 92–101 ;
- nuances d’acier 36, 42, 45 et 50 ksi affectées tronçon par tronçon ;
- zone **89–103** isolée et repère d’impact nord, niveaux 93–99 ;
- trois scènes Blender : `WTC1_MASTER`, `IMPACT_SEGMENT` et `COLLAPSE_SEGMENT`.

## Convention de représentation des sections

Dans la zone 92–101, chaque tronçon du noyau est représenté par un carré possédant la **même aire brute** que la section indiquée au Drawing Book 3. L’épaisseur visible est donc proportionnelle à l’aire réelle, et la couleur représente `Fy` :

- bleu : 36 ksi ;
- vert : 42 ksi ;
- jaune : 45 ksi ;
- rouge : 50 ksi.

Ce carré équivalent n’est pas la forme exacte du profilé WF ou du caisson. Pour les WF, l’aire est reconstituée à partir du poids nominal et de la masse volumique de l’acier. Pour les caissons 377–379, elle provient des quatre plaques décrites par la feuille 3-AB2-9.

## Limites à ne pas confondre avec des faits

- Le relevé des 47 nomenclatures est une transcription manuelle des scans 240 dpi ; une seconde lecture indépendante reste requise.
- Hors de la zone 92–101, les poteaux du noyau conservent une section visuelle générique.
- Les lignes bleues de la zone 89–103 représentent les directions de portée et l’entraxe des fermes, pas leurs diagonales, sièges, boulons ou lois de rupture.
- Les poteaux périphériques respectent nombre et entraxe, mais pas encore chaque variation de plaque et de nuance avec l’altitude.
- Le volume et la trajectoire rouges sont des repères : aucune masse, vitesse, température ou rupture n’est appliquée.
- La géométrie Blender est adaptée à l’audit visuel et à l’animation. Un solveur structurel explicite reste nécessaire pour une simulation de rupture prédictive.

## Construire ou reconstruire le fichier

Double-cliquer sur `build_wtc1_v4.cmd`, ou lancer :

```text
"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" --background --python "scripts\build_wtc1_v4.py"
```

Le script produit :

- `output/WTC1_V4_2_MASTER.blend` ;
- `output/model_manifest.json` avec les contrôles numériques ;
- cinq images de validation dans `renders/`, dont l’implantation du noyau et les 141 tronçons de section.

## Étapes suivantes

1. Relire indépendamment les 47 feuilles de nomenclature.
2. Affecter aux colonnes les charges, températures, dommages et défauts géométriques documentés par NIST.
3. Ajouter les sections de façade, les connexions de plancher et le hat truss nécessaires aux transferts de charge.
4. Exporter une géométrie structurale simplifiée vers un solveur explicite ; Blender restera l’outil de visualisation et de montage.
5. Alimenter `IMPACT_SEGMENT`, figer un état de transfert documenté, puis seulement alimenter `COLLAPSE_SEGMENT`.
