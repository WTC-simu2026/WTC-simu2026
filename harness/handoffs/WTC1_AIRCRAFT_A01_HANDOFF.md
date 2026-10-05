# Passation compacte - AIRCRAFT-A01 vers A02

Lire AGENTS.md puis harness/state.json(prioritaire) et cette passation. Jeremy a recentre le5octobre2026 sur le Boeing complet et des conditions sans forcer NIST; I02I-M differee, son plan ancien intact. Registre120 apres A01; avant119 dont22 impact et12 microdiagnostics I02I-A..L.

A01 :configuration aircraft_a01_predeclaration.json; sorties aircraft_a01,rapport et B767_assemblage_A01.png. Fuselage,deux ailes/caisson central,longerons,nervures,raidisseurs,empennages,deux moteurs/pylones equivalents; 2860noeuds,6538coques,4600poutres. Intact elastique hypothetique,aucune dynamique complete ni loi d'ecrasement/fracture qualifiee. Pas encore un deck solveur. SourcesprimairesBoeingCAD+ACAPp21/23/28+GE; sourceslocaleslectureseule/excluespub.

Nominal :M=122159.185978kg,structure=19971.762285kg,vide nonresolu=53187.423693kg,moteurs9000kg,fuel30000kg,charge10000kg. Reserve vide inclut structure manquante autant qu'equipements; pas de raideur cachee. CG=[22.440660398769435, 3.294483360479087e-16, -0.3309211242273247]; massesCSV/inertieexacte pourgeometrieapprochee.9scenarios,checks66/66,export4/4,raffinementstructure0.2106%,inertie0.0238%. Ce n'est pas une pesee/CG historique. Aucun ancien solveur relance,2162anciens fichiersepingles. Verifier via complete_aircraft_a01.py verify.

A02 concret :exporter masses coherentes et inerties sans les remplacer par un unique projectile rigide; orienter poutres; vol libre intact court et bilan masse/energie/moment. Preciserd'abordles inconnuesdominantes sursourcesprimaires. Puis avionentier/facade representative avec conditionsvitesse/attitude declarees et gammeplausible, pas de cibledegatsNIST. Limitesjointsmoteurs/structures manquantes etfracnoncalibree restentvisibles. Ne pas replonger automatiquement dans M.

NISTcomparaisonsepareeapresgel,aucun ajustementpourrejoindreunresultat. GarderV11F/V11R/V11S,tous échecsI02I etplanM. Grande deformation/fracturephysique/feu/effondrement nonvalides; Blender visualisation. PublicationL+A01dueapresaudit,cadenceactuelle a lire; aucunpostX ni actionYoremi.
