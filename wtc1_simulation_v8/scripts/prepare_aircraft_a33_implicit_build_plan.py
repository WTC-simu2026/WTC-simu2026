"""Read-only software preflight and concrete proposal; never install or build."""
from run_aircraft_a33 import *
import subprocess

def main():
    guard();dest=OUT/'native_build_preflight';q=dest/'build_proposal.json';assert not q.exists()
    sh=OUT/'read_only_build_preflight.sh';r=subprocess.run(['wsl.exe','-d','Ubuntu','--','sh','/mnt/c/Users/jeuxpc/Documents/Codex/2026-08-13/referenced-chatgpt-conversation-this-is-an/wtc1_simulation_v8/output/aircraft_a33/read_only_build_preflight.sh'],capture_output=True,text=True,encoding='utf8',timeout=60)
    dump(dest/'environment_inventory.json',{'created_utc':now(),'stdout':r.stdout,'stderr':r.stderr,'exit_code':r.returncode,'exit1_from_absent_package_query_not_build_failure':True,'read_only':True,'software_modifications_performed':False})
    source=read(dest/'source_manifest.json');assert source['source_commit']=='bad6688602d770e019b75773d2d5a48b4f9bd918'
    c={'created_utc':now(),'stage':'proposal_only_awaiting_explicit_human_authorization','purpose':'Test a genuinely available implicit route rather than assume documentation or repeat unsupported Windows probes. Availability does not qualify the whole10second impact.',
       'permission_source':{'file':'AGENTS.md','quote':'Les écritures externes, publications, envois ou modifications de logiciels exigent une demande explicite de Jeremy.'},
       'current_binary_preserved':{'path':rel(RUNTIME/'engine_win64.exe'),'sha256':streamsha(RUNTIME/'engine_win64.exe'),'MUMPS_capability':'FourA31attempts retained; compactrecords pass reader then both solvers terminate MUMPSrequired'},
       'candidate_source':{'repository':'https://github.com/gabrielrussell/OpenRadioss','commit':source['source_commit'],'documentation_git_blobs_verified':True,'license':'AGPL-3.0 per pinned LICENSE.md','equivalence_to_installed_Windows_binary_proven':False,'new_restart_required':True},
       'proposed_software_changes':{'environment':'ExistingUbuntu24.04.4WSL','minimal_packages_if_absent':['gfortran','libopenmpi-dev','libmumps-dev','libscalapack-openmpi-dev','liblapack-dev'],'dependencies':'Only required package-manager dependencies after recording proposed changes; no general upgrade','source_and_build_destination':'wtc1_simulation_v8/openradioss_runtime/a34_mumps_candidate','installed_Windows_solver_replacement':False,'physics_source_patch_authorized_by_this_plan':False},
       'build_configuration':{'architecture':'linux64_gf','precision':'dp','MPI':'ompi','MUMPS':'explicitmumps_root after checking installed library/header layout','ScaLAPACK_LAPACK':'explicitroots after checking actualstaticlibs','basis':'PinnedHOWTOandengine/build_script exposeMUMPSonlydpwithMPI; flags and linkedlibs must be recorded','maximum_CPU_threads':6,'GPU':False,'wall_cap_minutes':60,'estimated_minutes':[15,60],'estimated_workspace_GB':[2,8]},
       'deliverables':['separateStarter/Engineifbuildsucceeds, executableSHA256andversion','compiler/package/buildconfigurationandlogs includingfailure','freshdeclared1mmcubeimplicitPCG/MUMPSprobe, nativeenergy/work/mass/fieldgates','explicitvsimplicitsame-versioncontrols before anymultiphasewholeclaim'],
       'not_approved_or_performed':['installation','compilation','nativebinarymodification','wholeimpactextension','binarypublication'],'sources':source['files'],'whole_insertion_ready':False,'objective1_complete':False}
    dump(q,c)
    (dest/'proposition_compilation.md').write_text('''# Proposition : solveur séparé avec MUMPS

Le binaire Windows actuel s’arrête avec **MUMPSrequired** sur les sondes implicites A31. Ubuntu 24.04.4 WSL dispose de CMake, GCC et Make, mais pas de GFortran ou MPI sur PATH; aucun paquet MUMPS n’apparaît dans l’inventaire. Aucune installation ou compilation n’a été effectuée.

Action proposée après accord explicite : installer dans cet Ubuntu les seuls outils manquants GFortran, OpenMPI, MUMPS, ScaLAPACK et LAPACK ainsi que leurs dépendances indispensables; compiler une version séparée dans `wtc1_simulation_v8/openradioss_runtime/a34_mumps_candidate`. Aucun remplacement du solveur Windows ni modification de son code. Pas de mise à niveau générale. Compilation limitée à six threads processeur et une heure; estimation 15–60 minutes, espace 2–8 Go.

Source candidate figée : miroir gabrielrussell/OpenRadioss, commit **bad6688602d770e019b75773d2d5a48b4f9bd918**. Documentation et scripts de construction contrôlés par empreintes de blobs Git; licence AGPL-3.0 conservée. Ce n’est pas une preuve d’identité avec le binaire installé. Les instructions de compilation indiquent MUMPS en double précision avec MPI; les chemins de bibliothèques effectivement présents seront vérifiés avant construction. Toute erreur, option et dépendance sera journalisée. Aucun patch de physique proposé.

Livrables : binaires séparés si la construction réussit, empreintes, versions et journaux; nouvelles sondes implicites déclarées sur un cube physique à intérieur libre, bilans, travail, masse et champs. Les échecs restent conservés. Aucun fichier de reprise Windows n’est supposé compatible. Des témoins explicite/implicite de cette même nouvelle version seront nécessaires avant transfert à un modèle entier.

La construction peut échouer et ne garantit ni une accélération ni dix secondes d’impact. Elle permettrait de tester une voie actuellement indisponible. Les propriétés matérielles, prises, contacts et défauts A32/A33 restent à résoudre.

Accord requis par `AGENTS.md` : « Les écritures externes, publications, envois ou modifications de logiciels exigent une demande explicite de Jeremy. » La publication GitHub est déjà autorisée; cette installation et compilation constituent une action supplémentaire.
''',encoding='utf8')
    print({'build_proposal_prepared':True,'installation_performed':False,'compilation_performed':False},flush=True)

if __name__=='__main__':main()
