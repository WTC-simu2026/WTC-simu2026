# Proposition de classement futur — aucune opération effectuée

Ce fichier prépare une future session de rangement lorsque le nouveau disque sera disponible. Les archives actuelles n'ont pas été déplacées, renommées ou copiées.

## Arborescence suggérée

```text
WTC/
  00_MANIFESTES_ET_INDEX/
  01_SOURCES_OFFICIELLES/
    NIST/
    FEMA/
    USGS/
    EPA/
    FOIA_JUDICIAIRE/
  02_ARTICLES_SCIENTIFIQUES/
    STRUCTURES_INCENDIES/
    POUSSIERES_MATERIAUX/
    ENVIRONNEMENT_SANTE/
  03_TECHNOLOGIES_DE_REFERENCE/
    NANOENERGETIQUES/
    EXPLOSIFS_DETONATEURS/
  04_HYPOTHESES_ET_CRITIQUES/
    THERMITE/
    DEMOLITION/
    AUTRES_HYPOTHESES/
    CONTRE_ANALYSES/
  05_MEDIAS_PRIMAIRES/
    PHOTOS/
    VIDEOS/
    AUDIO/
  06_MEDIAS_DERIVES_ET_SCHEMAS/
  07_LIVRES_ET_TEMOIGNAGES/
  08_TRAVAUX_CODEX_DERIVES/
```

## Règle de nommage suggérée

`AAAA_AuteurOuInstitution_TitreCourt_Type_Statut.ext`

Exemples :

- `2001_USGS_WTC_Environmental_Assessment_OFFICIEL.pdf`
- `2005_Clapsaddle_Novel_Energetic_Nanocomposites_TECHNOLOGIE.pdf`
- `2009_Harrit_Active_Thermitic_Material_ARTICLE_CONTROVERSE.pdf`
- `2012_Millette_Red_Gray_Chips_RAPPORT_PRELIMINAIRE.pdf`
- `2023_Cole_North_Tower_Collapse_Schematic_SCHEMA_SECONDAIRE.jpg`

## Destination proposée pour les pièces de cet audit

| Pièce | Catégorie future |
|---|---|
| trois PDF USGS | `01_SOURCES_OFFICIELLES/USGS/` |
| Harrit 2009, Environmental anomalies, Extremely high temperatures | `02_ARTICLES_SCIENTIFIQUES/POUSSIERES_MATERIAUX/`, avec métadonnées de controverse |
| Clapsaddle 2005 | `03_TECHNOLOGIES_DE_REFERENCE/NANOENERGETIQUES/` |
| retour I-Kon et brevet WO | `03_TECHNOLOGIES_DE_REFERENCE/EXPLOSIFS_DETONATEURS/` |
| Hightower et 911facts.dk | `04_HYPOTHESES_ET_CRITIQUES/CONTRE_ANALYSES/` |
| schéma de Cole | `06_MEDIAS_DERIVES_ET_SCHEMAS/` |

## Précautions pour la future migration

1. faire d'abord un inventaire CSV/JSON avec chemin, taille, date et SHA-256;
2. détecter les doublons par taille puis empreinte, sans supprimer automatiquement;
3. conserver un manifeste ancien chemin → nouveau chemin;
4. copier et vérifier avant toute suppression de l'ancien disque;
5. conserver séparément source primaire, copie web, traduction, capture et travail dérivé;
6. enregistrer pour chaque document le statut probatoire, la provenance et les éventuels problèmes de chaîne de garde;
7. n'entreprendre aucun renommage destructif tant que deux copies vérifiées n'existent pas.
