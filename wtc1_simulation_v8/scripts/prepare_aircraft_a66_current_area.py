"""Read-only whole/source audit and current-area iteration prototype; no native or source application."""
import os
os.environ['OPENBLAS_NUM_THREADS']='1';os.environ['OMP_NUM_THREADS']='1'
from build_aircraft_a54_graph import ROOT,read,dump,sha,now,rel,harness
from surface_iteration_aircraft_a61_r1 import iteration_matrix,normal
from pathlib import Path
import numpy as np,tarfile,re,json,difflib,time,hashlib

PREP=ROOT/'wtc1_simulation_v8/output/aircraft_a66_preparation'
PLAN=ROOT/'wtc1_simulation_v8/data/aircraft_a66_proposal.json'
PRIVATE=ROOT/'wtc1_simulation_v8/openradioss_runtime/a66_current_area_proposal'

def sections(path):
    out={};key=None
    for line in path.read_text(encoding='utf8').splitlines():
        if line.startswith('/'):
            key=line.strip();assert key not in out,key;out[key]=[]
        elif key and line.strip() and not line.startswith(('#','$')):out[key].append(line)
    return out

def current_areas(nodes):
    mid=(nodes[:4]+nodes[4:])/2;n=normal(nodes);g=1/np.sqrt(3);areas=[]
    for r,s in [(-g,-g),(g,-g),(g,g),(-g,g)]:
        dr=np.array([-(1-s),1-s,1+s,-(1+s)])/4
        ds=np.array([-(1-r),-(1+r),1+r,1-r])/4
        areas.append(n@np.cross(dr@mid,ds@mid))
    a=np.asarray(areas)
    if not np.isfinite(a).all() or np.any(a<=0):raise ValueError('nonpositive current projected Gauss area')
    return a

def native_formula_reference(nodes):
    # Independent projected-polygon invariant equivalent to pinned SDET43's J0/J1/J2.
    mid=(nodes[:4]+nodes[4:])/2;n=normal(nodes);r=mid[1]+mid[2]-mid[0]-mid[3];s=mid[2]+mid[3]-mid[0]-mid[1]
    e1=r/np.linalg.norm(r);e2=np.cross(n,e1);xy=np.column_stack([(mid-mid[0])@e1,(mid-mid[0])@e2]);v=xy-xy.mean(axis=0)
    m13=(v[0]+v[2])/2;m23=(v[1]+v[2])/2;m34=(v[2]+v[3])/2;g=1/np.sqrt(3)
    j1=np.linalg.det(np.stack([m23,m13]))*g;j2=-np.linalg.det(np.stack([m13,m34]))*g;j0=np.linalg.norm(np.cross(r,s))/16
    return np.array([j0+j2-j1,j0+j2+j1,j0-j2+j1,j0-j2-j1])

def main():
    assert not PREP.exists() and not PLAN.exists() and not PRIVATE.exists();h=harness();assert h['CurrentIteration']=='AIRCRAFT-A65'
    start=time.perf_counter();PREP.mkdir();PRIVATE.mkdir();dump(PREP/'harness_before_preparation.json',h)
    archive=ROOT/'wtc1_simulation_v8/openradioss_runtime/a44_legacy_mumps_candidate/source.tar.gz'
    assert sha(archive)=='d64b773e899c174f5d59aadc4d2b73a101a083581e611d67215aaa50037cf9f8'
    paths=['engine/source/elements/solid/sconnect/suser43.F','engine/source/elements/solid/sconnect/scoor43.F',
           'engine/source/elements/solid/sconnect/sdet43.F','engine/source/implicit/imp_glob_k.F','engine/source/implicit/imp_solv.F']
    source_rows=[];raw={}
    with tarfile.open(archive) as tar:
        for path in paths:
            m=next(m for m in tar.getmembers() if m.name.endswith('/'+path));b=tar.extractfile(m).read();raw[path]=b.decode('utf8')
            dest=PRIVATE/Path(path).name;dest.write_bytes(b)
            source_rows.append({'path':path,'sha256':hashlib.sha256(b).hexdigest(),'raw_local_read_only_copy':rel(dest)})
    user=raw[paths[0]]
    assert 'IF (ISMSTR == 1 .AND. TIME == ZERO)' in user and 'AREA(1:NEL) => AREAP(1:NEL,IPG)' in user
    base=ROOT/'wtc1_simulation_v8/openradioss_runtime/a62_type43_surface_iteration_candidate/s8zke3_R2_interface.proposed.F'
    original=base.read_text(encoding='utf8');assert 'IGTYP==43.AND.MTN==117.AND.ISMSTR==1' in original
    files=[ROOT/'wtc1_simulation_v8/output/aircraft_a49/WHOLE_EQUIVALENT_RIGID_CHAINS_CHECK/A49_EQUIVALENT_RIGID_CHAINS_0000.rad',
           ROOT/'wtc1_simulation_v8/output/aircraft_a52/WHOLE_PAIRED_TYPE2_BINDING_TRACE_R1/A52_TYPE2_FACET_PAIRS_R1_0000.rad']
    message=read(ROOT/'wtc1_simulation_v8/output/aircraft_a65/whole_CHECK_message_review.json');models=[];all_nodes=[]
    for path,case in zip(files,message['cases']):
        data=sections(path);node={int(line[:10]):np.array([float(line[i:i+20]) for i in [10,30,50]]) for line in data['/NODE']}
        # Starter syntax: first TYPE43 field is Ismstr; retain all original cards.
        assert int(data['/PROP/TYPE43/117'][1][:10])==4
        assert [int(data['/PART/117'][1][i:i+10]) for i in [0,10]]==[117,117]
        elements={int(line[:10]):[int(line[i:i+10]) for i in range(10,90,10)] for line in data['/BRICK/117'][1:]}
        assert set(case['STOP_volume_element_ids'])==set(elements)==set(range(60001,60625))
        geom=[]
        for eid,ids in elements.items():
            x=np.asarray([node[i] for i in ids]);area=current_areas(x);ref=native_formula_reference(x)
            assert np.allclose(area,ref,rtol=1e-12,atol=1e-12)
            geom.append({'id':eid,'nodes':ids,'coordinates_mm':x.tolist(),'pair_height_max_mm':float(np.linalg.norm(x[:4]-x[4:],axis=1).max()),
                         'current_Gauss_area_mm2':area.tolist(),'total_projected_area_mm2':float(area.sum())})
        contacts=[{'keyword':k,'cards':v} for k,v in data.items() if k.startswith('/INTER/TYPE25/')];assert len(contacts)==5
        models.append({'path':rel(path),'sha256':sha(path),'Ismstr':4,'cohesive_part':117,'LAW117':117,'elements':geom,'TYPE25_contacts':contacts})
        all_nodes.append([np.asarray(x['coordinates_mm']) for x in geom])
    assert all(np.array_equal(a,b) for a,b in zip(*all_nodes))
    dump(PREP/'whole_domain_and_geometry_review.json',{'created_utc':now(),'pass':True,'models':models,
        'all_624_flagged_elements_are_TYPE43_LAW117_Ismstr4':True,'same_original_paired_cohesive_geometry':True,
        'zero_height_is_not_zero_surface_area':True,'all_current_projected_Gauss_areas_positive':True,
        'minimum_current_GP_area_mm2':min(min(e['current_Gauss_area_mm2']) for m in models for e in m['elements']),
        'maximum_pair_height_mm':max(e['pair_height_max_mm'] for m in models for e in m['elements']),
        'A62_branch_covers_Ismstr1_only':True,'Ismstr4_reference_VOL_not_initialized_by_SUSER43':True,
        'Ismstr4_native_force_area_is_current_AREAP':True,'source_rows':source_rows,'native_reexecution':False})
    # Current-area preconditioning prototype, using the already audited matrix function without executing its old tests.
    material=read(ROOT/'wtc1_simulation_v8/data/aircraft_a65_predeclaration.json')['cohesive'];checks=[]
    def check(name,value):checks.append({'name':name,'pass':bool(value)})
    axis=np.array([1,2,3])/np.sqrt(14);W=np.array([[0,-axis[2],axis[1]],[axis[2],0,-axis[0]],[-axis[1],axis[0],0]])
    rotation=np.eye(3)+np.sin(1.1)*W+(1-np.cos(1.1))*W@W;Q=np.kron(np.eye(8),rotation)
    samples=[('square',np.array([[0,0,0],[10,0,0],[10,10,0],[0,10,0]]*2,float)),
             ('trapezoid',np.array([[0,0,0],[10,0,0],[8,10,0],[1,10,0]]*2,float)),
             ('whole_first',all_nodes[0][0]),('whole_middle',all_nodes[0][312]),('whole_last',all_nodes[0][-1])]
    for label,x in samples:
        a=current_areas(x);K=iteration_matrix(x,a,material);scale=max(abs(K).max(),1)
        check(label+'_native_projected_area_identity',np.max(abs(a-native_formula_reference(x)))<=1e-12*max(a.sum(),1))
        check(label+'_symmetric',np.max(abs(K-K.T))<=1e-12*scale)
        check(label+'_positive_semidefinite',np.linalg.eigvalsh(K).min()>=-1e-10*scale)
        check(label+'_current_area_rotation_covariance',np.max(abs(iteration_matrix(x@rotation.T+[31,-7,15],current_areas(x@rotation.T+[31,-7,15]),material)-Q@K@Q.T))<=1e-10*scale)
        for j in range(3):check(label+'_common_translation_null_'+str(j),np.linalg.norm(K@np.tile(np.eye(3)[j],8))<=1e-9*scale)
        scaled=x*2;check(label+'_current_area_quadratic_scaling',np.max(abs(iteration_matrix(scaled,current_areas(scaled),material)-4*K))<=1e-12*scale)
        check(label+'_all_deleted_GP_zero',np.all(iteration_matrix(x,a,material,[0]*4)==0))
        n=normal(x);D=material['ET_N_mm3']*np.eye(3)+(material['EN_N_mm3']-material['ET_N_mm3'])*np.outer(n,n)
        gap=np.array([.001,-.002,.003]);u=np.r_[np.zeros(12),np.tile(gap,4)];forces=(K@u).reshape(8,3)
        check(label+'_balanced_uniform_gap_force',np.linalg.norm(forces.sum(axis=0))<=1e-9*scale and np.linalg.norm(forces[4:].sum(axis=0)-a.sum()*D@gap)<=1e-9*scale)
    for label,x in [('collapsed',np.zeros((8,3))),('bowtie',np.array([[0,0,0],[10,10,0],[10,0,0],[0,10,0]]*2,float))]:
        rejected=False
        try:current_areas(x)
        except ValueError:rejected=True
        check(label+'_rejected',rejected)
    assert all(c['pass'] for c in checks)
    dump(PREP/'current_area_iteration_prototype_review.json',{'created_utc':now(),'pass':True,'checks':checks,
        'matrix_is_exact_material_or_geometric_Jacobian':False,'same_native_residual_and_history_required':True,
        'whole_domain_read_only_surface_geometry_pass':True,'native_finite_rotation_integration_not_qualified':True,
        'future_native_checks_needed':['free elastic finite formulation and half-step','rigid rotation covariance','current area scaling','nonuniform current GP areas','area evolution with a free axis','whole original/paired CHECK'],
        'no_new_native_run_source_application_or_compilation':True})
    # Prepare an exact AGPL diff outside MIT outputs. Preserve the entire existing Ismstr1 helper and dispatch.
    helper_start=re.search(r'^      SUBROUTINE WTC_A61_S43_K',original,re.M).start();helper=original[helper_start:]
    current=helper.replace('WTC_A61_S43_K','WTC_A66_S43_CURK').replace('STOP 61','STOP 66')
    current=current.replace('      my_real PG,P1,P2,P3,W,SGN,AREA,GPON(MVSIZ,4)',
        '      my_real PG,P1,P2,P3,W,SGN,AREA,GPON(MVSIZ,4)\n      my_real GR(4),GS(4),DR(4),DS(4),TR(3),TS(3),CR(3),AW')
    current=current.replace('      IF (EN<=ZERO.OR.ET<=ZERO) STOP 66','      IF (.NOT.(EN>ZERO).OR..NOT.(ET>ZERO)) STOP 66\n      IF (EN>HUGE(EN).OR.ET>HUGE(ET)) STOP 66')
    current=current.replace('      H(:,4)=(/P1,P3,P1,P2/)','      H(:,4)=(/P1,P3,P1,P2/)\n      GR=(/-PG,PG,PG,-PG/)\n      GS=(/-PG,-PG,PG,PG/)')
    current=current.replace('        IF (.NOT.ASSOCIATED(LB%VOL)) STOP 66\n','')
    current=current.replace('        IF (SIZE(LB%VOL)<NEL.OR.SIZE(LB%OFF)<NEL) STOP 66','        IF (SIZE(LB%OFF)<NEL) STOP 66')
    current=current.replace('          IF (LB%VOL(I)<=ZERO) STOP 66\n','')
    current=current.replace('          GPON(I,P)=LB%VOL(I)*LB%OFF(I)','          GPON(I,P)=LB%OFF(I)')
    current=current.replace('        IF (LEN<=ZERO) STOP 66','        IF (.NOT.(LEN>ZERO).OR.LEN>HUGE(LEN)) STOP 66')
    insert='''        DO P=1,4
          DR=FOURTH*(/-(ONE-GS(P)),ONE-GS(P),ONE+GS(P),
     .                 -(ONE+GS(P))/)
          DS=FOURTH*(/-(ONE-GR(P)),-(ONE+GR(P)),ONE+GR(P),
     .                  ONE-GR(P)/)
          TR=MATMUL(MID,DR)
          TS=MATMUL(MID,DS)
          CR(1)=TR(2)*TS(3)-TR(3)*TS(2)
          CR(2)=TR(3)*TS(1)-TR(1)*TS(3)
          CR(3)=TR(1)*TS(2)-TR(2)*TS(1)
          AW=DOT_PRODUCT(N,CR)
          IF (.NOT.(AW>ZERO).OR.AW>HUGE(AW)) STOP 66
          GPON(I,P)=GPON(I,P)*AW
        ENDDO
'''
    current=current.replace('        N=N/LEN\n','        N=N/LEN\n'+insert)
    assert '%VOL' not in current
    interface=re.search(r'        SUBROUTINE WTC_A61_S43_K.*?        END SUBROUTINE WTC_A61_S43_K',original,re.S).group(0).replace('WTC_A61_S43_K','WTC_A66_S43_CURK')
    proposed=original.replace('      END INTERFACE',interface+'\n      END INTERFACE',1)
    dispatch='''      IF (IGTYP==43.AND.MTN==117.AND.ISMSTR==4) THEN
        CALL WTC_A66_S43_CURK(ELBUF_STR,NEL,IXS(1,NFT+1),X,IPM,
     .                      BUFMAT,IDDL,IADK,JDIK,K_DIAG,K_LT,ETAG)
        RETURN
      ENDIF
'''
    marker='      NF1 = NFT+1';assert proposed.count(marker)==1;proposed=proposed.replace(marker,dispatch+marker)
    proposed+='\nC     Current projected Gauss areas for TYPE43/LAW117/Ismstr4.\nC     Symmetric iteration only; native forces/history unchanged.\n'+current
    assert proposed[proposed.index(original[helper_start:helper_start+60]):][:len(helper)]==helper
    newfile=PRIVATE/'s8zke3_Ismstr4.proposed.F';newfile.write_text(proposed,encoding='utf8',newline='\n')
    patch=PRIVATE/'current_area_Ismstr4.patch';patch.write_text(''.join(difflib.unified_diff(original.splitlines(True),proposed.splitlines(True),fromfile='engine/source/elements/solid/solide8z/s8zke3.F',tofile='engine/source/elements/solid/solide8z/s8zke3.F')),encoding='utf8',newline='\n')
    added=[line[1:] for line in patch.read_text(encoding='utf8').splitlines() if line.startswith('+') and not line.startswith('+++')]
    assert all(len(line)<=72 for line in added if line and line[0] not in 'Cc#!*')
    dump(PLAN,{'created_utc':now(),'iteration':'AIRCRAFT-A66_PROPOSAL','seed':1102091,'random_draws':0,
        'source_pin':'3d75ff13d1946f6d28a43920eac4fa2aae41b27a','source_archive_sha256':sha(archive),
        'purpose':'Whole finite formulation/current-area audit and guarded symmetric iteration proposal.',
        'native_executions':0,'new_source_application_or_compilation':False,'CPU':1,'GPU':False,'own_prototype_cap_s':120,
        'inputs':[{'path':rel(p),'sha256':sha(p)} for p in files],
        'current_Engine_sha256':read(ROOT/'wtc1_simulation_v8/data/aircraft_a65_predeclaration.json')['binary_sha256'],
        'patch':{'target':'engine/source/elements/solid/solide8z/s8zke3.F','current_A62_source':rel(base),'current_A62_source_sha256':sha(base),
                 'proposed_source':rel(newfile),'proposed_sha256':sha(newfile),'patch':rel(patch),'patch_sha256':sha(patch),
                 'new_scope':'TYPE43+LAW117+Ismstr4 only; current projected Gauss areas, no reference VOL read',
                 'previous_Ismstr1_helper_preserved_exactly':True,'native_residual_material_history_unchanged':True,
                 'matrix_is_exact_Jacobian':False,'applied':False,'compiled':False},
        'future_A67':{'new_seventh_Engine_approval_required':True,'maximum_build_s':3600,'CPU_build':6,'GPU':False,'installation':False,
            'maximum_native':8,'CPU_native':1,'each_native_cap_s':180,
            'cases':['FREE_Ismstr4','FREE_Ismstr4_HALF','RIGID_ROTATED_FREE','AREA_x4_FREE','NONUNIFORM_AREA_FREE','AREA_EVOLUTION_FREE_Y','WHOLE_ORIGINAL_CHECK','WHOLE_PAIRED_CHECK'],
            'local_duration_target_ms':1,'current_area_evolution_scale':'1+0.1*sin(pi*t/1ms)^2; common in-plane X stretch, free seeded Y',
            'whole_dynamic_extension':False,'TYPE25_contacts_unchanged_and_still_blocking':True},
        'whole_physical_budgets_changed':False,'RKE_added':False,'old_native_diagnostics_replayed':False,
        'best_whole_physical_s':.0200001220703125,'new_whole_credit_s':0,'objective1_complete':False})
    proposal=PREP/'proposition_aire_courante_Ismstr4.md'
    proposal.write_text('''# Proposition Ismstr4 — aire courante, septième moteur isolé

A65 qualifie le témoin libre raffiné mais ses deux scènes entières échouent. Les624éléments signalés utilisentTYPE43/LAW117/Ismstr4 ; leurs quatre aires projetées sont positives. Le moteurA62 traite seulementIsmstr1. Les sources natives stockent l’aire de référenceVOL seulement pourIsmstr1 ; Ismstr4 utiliseAREAP courante. Élargir simplement le test lirait un tampon qui n’est pas initialisé comme aire de référence dans ce domaine.

Une différence exacte est préparée hors des livrablesMIT. Elle ajoute une brancheTYPE43+LAW117+Ismstr4 et un helper séparé, conserve exactement l’ancienne branche/helperIsmstr1, calcule quatre aires projetées courantes par quadrature sur la face médiane et utilise la normale courante. Même matrice symétrique d’itération élastique, pas un jacobien matériel/géométrique exact. ForcesSIGEPS117, états, matériaux, inerties et budgets restent natifs et inchangés. Une aire active non positive, un agencement invalide ou une valeur non finie arrêtent le candidat code66 ; aucune épaisseur/volume fictif ni message désactivé.

Le prototype propre contrôle les mêmes formules d’aire queSDET43, la covariance aux rotations, l’évolution quadratique d’aire, la symétrie/positivité, équilibre/tractions, translations et géométries invalides. Aucun correctif appliqué ni compilé ; aucune qualification nativeIsmstr4 déduite du prototype.

Application et compilation futures dans un septième moteur isolé : plafond1heure, CPU6, sansGPU/installation, caches déjà présents. Puis maximum8Engine CPU1/plafond180s : six témoins décrits dans le plan (libre/demi-pas, rotation, aire×4, aire non uniforme, évolution d’aire avecYlibre), puis deuxCHECK entiers strictement bornés. Seuils existants conservés. Les cinqTYPE25 restent inchangés et bloquants ; ce correctif ne suffit donc pas à autoriser l’impact entier ni dix secondes dynamiques.

L’accordA65 de quatre calculs est consommé. Ce nouveau correctif et sa compilation requièrent un accord humain explicite distinct, conformément àAGENTS.md. Les entrées/caches, anciens moteurs, sorties et critères échoués seront conservés. Prochaine question de contact : préparer une variante admissible et ses bilans, sans remplacerTYPE25 silencieusement.
''',encoding='utf8')
    dump(PREP/'preparation_review.json',{'created_utc':now(),'pass':True,'plan':rel(PLAN),'plan_sha256':sha(PLAN),'proposal':rel(proposal),'proposal_sha256':sha(proposal),
        'prototype_checks':len(checks),'prototype_pass':True,'whole_geometry_and_source_scope_pass':True,
        'patch_applied':False,'compiled_or_native_Ismstr4_qualified':False,'old_outputs_modified':False,
        'wall_s':time.perf_counter()-start,'source_raw_and_patch_AGPL_outside_MIT':True,'harness':harness()})
    print(json.dumps({'A66_preparation_pass':True,'current_area_checks':len(checks),'source_patch_applied':False,'new_native_runs':0}),flush=True)

if __name__=='__main__':main()
