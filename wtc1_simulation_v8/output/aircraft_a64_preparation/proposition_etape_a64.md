# Étape A64 proposée — raffinement et CHECK, moteur existant

Préparée, aucun calcul lancé. Le lot A61 de12contrôles est consommé ; cette nouvelle étape demande un accord distinct sur son budget.

Deux essais libres sur le moteur A62 inchangé, avec pas0,000125 et0,0000625ms. Matériau, surface, masse instrumentale8g, vitesse initiale1mm/ms, supports, durée1ms et seuils de conservation/comparaison sont identiques à A63. Seul le pas change selon la borne analytique du schéma, sans ajustement aux dégâts ni aux paramètres physiques. L’échec des pas0,001/0,0005ms reste conservé.

Si les bilans et la comparaison demi-pas passent tous, deux CHECK du modèle entier sont lancés sur le même moteur : scène originale et paireA53, avec exactement les anciens états initiaux/cartes, vérifiés par SHA256. Leur but est de mesurer l’effet du traitement surfacique sur le blocage géométrique ; aucune dynamique entière prolongée et aucun passage inféré de NORMAL/code0. TYPE25, bilans locaux, domaines matériaux et autres critères échoués restent bloquants.

Au maximum4 nouveaux Engine, un CPU, plafond180s chacun, sansGPU, installation ou compilation. Estimation1–5minutes ; aucun calcul de plusieurs heures. Les deux dernières vérifications sont conditionnelles au passage local. Les paramètres et le lanceur sont sauvegardés, l’application logicielle du moteur reste inchangée.

L’objectif reste dix secondes physiques d’impact puis vidéo3D. Meilleure fenêtre entière actuelle0,0200001220703125s ; aucune seconde manquante interpolée ou créditée par ces témoins.
