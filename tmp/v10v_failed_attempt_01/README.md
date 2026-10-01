# V10V — tentative 01 rejetée et conservée

Les sept calculs CalculiX ont terminé, et les trois cas non linéaires contiennent chacun 104 incréments convergés. La tentative est néanmoins rejetée avant publication parce que le parseur attendait l'ancien titre `EIGENVALUE OUTPUT`, tandis que CalculiX 2.22 écrit `BUCKLING FACTOR OUTPUT`. La génération du rapport n'était en outre pas tolérante aux valeurs nulles produites par cet échec de parsing.

La tentative 02 ne change aucun paramètre physique, maillage, pas de temps ou seuil d'acceptation. Elle ajoute uniquement la compatibilité avec le titre réellement observé et un formatage sûr des échecs éventuels.

Cette tentative n'est pas enregistrée comme itération validée et ne confère aucun crédit physique au WTC 1.
