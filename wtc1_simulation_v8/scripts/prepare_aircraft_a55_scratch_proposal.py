"""Prepare, never apply or compile, a separately authorized TYPE43 scratch fix."""
from build_aircraft_a54_graph import ROOT,read,dump,sha,now,rel,harness
import tarfile,hashlib,difflib,json

OUT=ROOT/'wtc1_simulation_v8/output/aircraft_a55'
DEST=ROOT/'tmp/aircraft_a55_smstr_patch_proposal_r1'
TARGET='engine/source/elements/elbuf/alloc_elbuf_imp.F'
ARCHIVE=ROOT/'wtc1_simulation_v8/openradioss_runtime/a44_legacy_mumps_candidate/source.tar.gz'

def main():
    assert read(ROOT/'harness/state.json')['current_iteration']=='AIRCRAFT-A54'
    h=harness(); assert not DEST.exists()
    with tarfile.open(ARCHIVE) as archive:
        member=next(m for m in archive.getmembers() if m.name.endswith(TARGET))
        original=archive.extractfile(member).read()
    original_sha=hashlib.sha256(original).hexdigest()
    assert original_sha=='9fdd36d3e265755cce16484a3259fea248180cbcbde193113a038d91225ebf54'
    source=original.decode('utf8')
    line=next(v for v in source.splitlines(keepends=True) if 'ALLOCATE (ELBUF_IMP(NG)%GBUF%SMSTR(NEL*GBUF%G_SMSTR)' in v)
    replacement='''C     TYPE43 implicit geometry accesses a 21-column scratch view.
C     Keep source/restart dimensions; pad the temporary copy only.
        IF (IGTYP==43.AND.GBUF%G_SMSTR<21) THEN
          ALLOCATE (ELBUF_IMP(NG)%GBUF%SMSTR(21*NEL),STAT=ERR)
          IF (ERR==0) ELBUF_IMP(NG)%GBUF%SMSTR = 0.0D0
        ELSE
          ALLOCATE (ELBUF_IMP(NG)%GBUF%SMSTR(
     .              NEL*GBUF%G_SMSTR),STAT=ERR)
        ENDIF
'''
    assert source.count(line)==1
    assert max(map(len,replacement.splitlines()))<=72
    assert 'IGTYP = ELBUF_TAB(NG)%IGTYP' in source
    proposed=source.replace(line,replacement).encode('utf8')
    diff=''.join(difflib.unified_diff(source.splitlines(keepends=True),proposed.decode().splitlines(keepends=True),fromfile='a/'+TARGET,tofile='b/'+TARGET))
    tests=[]
    for kind in [14,21,43]:
        for nel in [0,1,128,624]:
            for width in [0,6,21,24]:
                size=nel*(21 if kind==43 and width<21 else width)
                addresses=[i+nel*j for j in range(21) for i in range(nel)] if kind==43 else []
                expected=nel*max(width,21) if kind==43 else nel*width
                tests.append({'IGTYP':kind,'NEL':nel,'G_SMSTR':width,'allocation':size,'pass':size==expected and (not addresses or max(addresses)<size)})
    assert len(tests)==48 and all(t['pass'] for t in tests)
    DEST.mkdir()
    (DEST/'alloc_elbuf_imp.F.proposed').write_bytes(proposed)
    (DEST/'type43_smstr_scratch.patch').write_bytes(diff.encode('utf8'))
    initial=ROOT/'tmp/aircraft_a55_smstr_patch_proposal'
    old=[{'path':rel(p),'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(initial.iterdir()) if p.is_file()]
    dump(OUT/'initial_scratch_proposal_failure.json',{'created_utc':now(),'files_preserved':old,'reason':'Initial static assertion failed: ZERO constant absent in allocator scope. No patch applied, no native compile. R1 uses literal 0.0D0 and checks STAT before initialization.'})
    review={'created_utc':now(),'target':TARGET,'source_pin':'3d75ff13d1946f6d28a43920eac4fa2aae41b27a','source_sha256':original_sha,
      'patch_path':rel(DEST/'type43_smstr_scratch.patch'),'patch_sha256':sha(DEST/'type43_smstr_scratch.patch'),
      'proposed_source_path':rel(DEST/'alloc_elbuf_imp.F.proposed'),'proposed_sha256':sha(DEST/'alloc_elbuf_imp.F.proposed'),
      'arithmetic_checks':tests,'arithmetic_gate_pass':True,'fixed_form_added_line_limit_pass':True,'line_endings':'LF',
      'software_patch_applied':False,'compiled_or_native_qualified':False,'human_authorization_received':False,
      'native_heap_corruption_directly_observed':True,'insufficient_capacity_is_source_contract_inference':True,'native_G_SMSTR_capacity_not_read':True,
      'scope':'Temporary implicit TYPE43 SMSTR storage only, at least NEL*21 values; other types unchanged, source/restart widths and physical cards unchanged.',
      'build_proposal':{'iteration':'AIRCRAFT-A56','isolated_directory':'wtc1_simulation_v8/openradioss_runtime/a56_type43_scratch_candidate','prior_A53_graph_patch_retained':True,'maximum_build_s':3600,'CPU_threads':6,'GPU':False,'new_installation':False,'dependencies':'same cached and installed A54 environment'},
      'native_proposal':{'per_process_cap_s':180,'CPU_threads':1,'GPU':False,'checks':['native temporary capacity and bounds','heap corruption regression','loaded implicit cohesion and energy','whole graph and CHECK','explicit cohesive and TYPE7 contact regression'],'acceptance_thresholds_unchanged':True},
      'remaining_failed_gates':['whole CHECK 15 errors','TYPE25 implicit ignored','loaded implicit cohesion','whole contact and energy coverage'],
      'new_whole_duration_credit_s':0,'objective1_complete':False,'harness':h}
    dump(OUT/'smstr_patch_proposal_review.json',review)
    report=OUT/'proposition_correctif_tampon_cohesif.md'
    report.write_text('''# Proposition A55 pour A56 — tampon temporaire cohésif

Cette proposition est préparée, non appliquée et non compilée. Elle exige un nouvel accord explicite ; l'accord donné pour le correctif A53 ne couvre pas cette modification.

## Faits directement observés

Sur le moteur A54 intact, l'en-tête de l'allocation NODREAC passe de0x31 à0 à l'écriture SRCOORK+0x4488, puis free déclenche SIGABRT. La capture R2 observe NEL=1, IGTYP=43, ISMSTR=1, JHBE=0, JCVT=1 et SAV voisin de l'allocation corrompue. Le processus s'arrête à NC=0/T=0. Les sorties et tentatives d'observation sont conservées.

## Source du logiciel

SRCOORK déclare SAV(NEL,21). S8ZKE3 lui transmet GBUF%SMSTR ; l'allocation temporaire implicite actuelle utilise NEL*G_SMSTR. L'insuffisance de capacité est une inférence de ce contrat et de la corruption observée. La valeur native du descripteur G_SMSTR n'a pas été lue. Aucune validation historique n'en découle.

## Archives locales

Aucune nouvelle archive historique consultée ou modifiée.

## Hypothèse et modification proposée

Dans alloc_elbuf_imp.F uniquement, réserver au moins21*NEL valeurs pour le tampon SMSTR temporaire des TYPE43 et initialiser le complément à0.0D0 si l'allocation réussit. Les autres types gardent leur dimension. Le dimensionnement source/restart, masses, matériaux, inerties, contacts et chargements restent inchangés. La dynamique et les critères physiques restent à qualifier ; aucune erreur de volume n'est supprimée.

## Contrôles préparatoires

48 cas arithmétiques de capacité et bornes passent ; lignes ajoutées limitées à72 colonnes et empreintes enregistrées. Cela ne remplace pas une compilation Fortran. La première proposition utilisait ZERO, absent de ce fichier : cette préparation échouée est préservée, R1 utilise un littéral et protège l'initialisation par STAT.

## Limites et exécution après accord

Créer un quatrième moteur isolé avec la même source figée, le correctif de graphe A53 déjà autorisé et cette seule nouvelle différence. Compilation plafonnée à une heure, six CPU, sans GPU ni installation ; contrôle de capacité natif, régression mémoire, cohésion chargée, graphe/CHECK et témoins physiques plafonnés à180 secondes chacun. Les moteurs antérieurs et les échecs sont conservés. Ce travail ne suffit pas à valider les TYPE25 ni les dix secondes d'impact. La meilleure fenêtre entière reste0,0200001220703125s.
''',encoding='utf8')
    print(json.dumps({'proposal_ready':True,'applied':False,'compiled':False,'arithmetic_checks':48,'patch_sha256':review['patch_sha256']}),flush=True)

if __name__=='__main__':main()
