# V10U — tentative 01 rejetée et conservée

Cette arborescence conserve intégralement la première exécution V10U, sa configuration, son lanceur, ses neuf jeux d'entrée CalculiX et toutes ses sorties.

Décision : `FAIL_INDEPENDENT_LINEAR_B32R_BENCHMARK`.

La fermeture charge-réaction et la linéarité charge-déplacement ont réussi. Le protocole a toutefois appliqué à tort la tolérance analytique finale de 1 % aux maillages grossiers utilisés pour observer la convergence, puis s'est arrêté à 32 éléments alors que la variation 16→32 valait encore 0,3431246331 %. Aucun seuil numérique n'est relâché dans la tentative 02 : la séquence de maillage est prolongée jusqu'à 128 éléments et la tolérance analytique inchangée s'applique au maillage final et à son balayage de charge non nul.

Cette tentative n'est pas enregistrée comme itération validée du harnais et n'accorde aucun crédit physique au WTC 1.
