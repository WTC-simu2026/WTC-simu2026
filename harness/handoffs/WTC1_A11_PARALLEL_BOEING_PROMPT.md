# Travail parallèle : construction mécanique du Boeing 767

Tu travailles dans le dossier existant :
C:\Users\jeuxpc\Documents\Codex\2026-08-13\referenced-chatgpt-conversation-this-is-an

Commence par lire AGENTS.md, harness/state.json, harness/handoffs/WTC1_AIRCRAFT_A10_HANDOFF.md et harness/publication_cycle.json. Suis l’état local actuel ; les anciens points V8H/V11H/I02I ne décrivent plus la reprise. Un autre agent pilote AIRCRAFT-A11, la scène d’impact, les contacts et les essais dynamiques. Ton travail parallèle porte sur la construction mécanique du Boeing 767 et doit rester indépendant de ses écritures.

Objectif : améliorer le modèle mécanique existant pour préparer une collision progressive, sans ajuster les paramètres aux dégâts observés ni aux résultats NIST. Commence par inventorier les composants déjà présents, leurs masses, inerties, géométries, matériaux, assemblages et leurs sources. Réutilise les sorties A01 à A10 sauvegardées ; aucune relance ancienne et aucun scan général de l’archive.

À lire en priorité :
- wtc1_simulation_v8/data/aircraft_a09_predeclaration.json ;
- wtc1_simulation_v8/output/aircraft_a09/r0/BASE_FINE/generation.json et mesh.json ;
- wtc1_simulation_v8/output/aircraft_a09/source_manifest.json ;
- wtc1_simulation_v8/output/aircraft_a10/authoritative_review.json et rapport_aircraft_a10.md ;
- les sources primaires déjà référencées par ces manifestes, uniquement quand nécessaires.

Livrable concret : un module de construction indépendant, paramétré en JSON, pour une amélioration prioritaire réalisable de l’avion. Choisis cette amélioration après l’inventaire : par exemple structure et assemblages aile–pylône–moteur, ou structure interne du fuselage. Justifie le choix par son rôle dans les premiers contacts. N’invente pas des détails internes prétendument historiques ; les paramètres sans données restent des hypothèses avec plages de sensibilité. Ne change pas implicitement les budgets de masse ou les matériaux.

Produis :
1. Un inventaire machine-readable des éléments établis, hypothétiques et manquants, avec unités et provenance.
2. Une configuration et un générateur réutilisable de la sous-structure choisie, dans tes propres fichiers. Vérifie connectivité, unités, masses, centre de gravité, inerties et absence de doublons. Conserve chaque première erreur ou essai rejeté.
3. Un audit avant/après et une proposition d’intégration précise : fichiers à lire, interface du module, changements attendus, risques et critères de contrôle. Un module numérique hypothétique peut être livré, clairement étiqueté ; il ne reçoit pas de validation physique automatique.
4. Un rapport compact et un fichier integration_ready.json indiquant ce qui est réellement prêt ou encore bloqué.

Écris exclusivement dans tes nouveaux dossiers :
- wtc1_simulation_v8/input/aircraft_a11_boeing_parallel/
- wtc1_simulation_v8/data/aircraft_a11_boeing_parallel/
- wtc1_simulation_v8/scripts/aircraft_a11_boeing_parallel/
- wtc1_simulation_v8/output/aircraft_a11_boeing_parallel/

N’édite pas AGENTS.md, harness/state.json, registry.jsonl, publication_cycle.json, les passations globales, les scripts existants ni output/aircraft_a11/. L’agent principal fera l’intégration et l’enregistrement. Archives, sources et anciennes itérations restent en lecture seule. Exécute le contrôle du harnais avant/après tes modifications et arrête pour diagnostiquer s’il échoue. Des évolutions de l’état par l’autre agent sont possibles : ne les annule pas et ne modifie pas ses fichiers.

Cherche des sources primaires ciblées si une donnée précise l’exige. Pas de logiciel installé/modifié, publication GitHub, X ou action Yoremi. Aucun long solveur ni GPU : privilégie les vérifications statiques ; un petit témoin neuf peut être exécuté après déclaration des critères, limité à 120 secondes et un thread CPU pour ne pas concurrencer l’autre agent. Préserve V11F/V11R ; V11S/I02I-M restent différées.

Sépare observations, modèles officiels, affirmations d’archives, hypothèses, résultats dérivés et inconnues. Impact historique, écrasement et effondrement restent non qualifiés ; Blender est une visualisation. Termine par le chemin de integration_ready.json et une passation concise destinée à l’agent principal.
