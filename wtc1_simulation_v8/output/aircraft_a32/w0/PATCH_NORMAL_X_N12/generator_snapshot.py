"""Mass-preserving efficient solid-shell probes, anchored to actual curved-root mapping.

The installed binary lacks the demonstrated implicit route. Test the stated full
3D tensor, native balances and physical inertia before any whole insertion.
"""
from run_aircraft_a31 import ROOT,RUNTIME,read,dump,rel,now,harness,execute,env,streamsha,ff,ii,parent,group,histories,constitutive
from run_aircraft_a23 import brick_grid,inertia
import test_aircraft_a29_law12 as source_skin
import argparse,json,re,shutil,traceback,urllib.request
from pathlib import Path
import numpy as np
OUT=ROOT/'wtc1_simulation_v8/output/aircraft_a32'
CFG=ROOT/'wtc1_simulation_v8/data/aircraft_a32_predeclaration.json'
PREV=ROOT/'wtc1_simulation_v8/output/aircraft_a31'
URLS={'type21':'https://help.altair.com/hwsolvers/rad/topics/solvers/rad/prop_type21_tsh_orth_starter_r.htm','type6':'https://help.altair.com/hwsolvers/rad/topics/solvers/rad/prop_type6_sol_orth_starter_r.htm','solid_shell':'https://help.altair.com/hwsolvers/rad/topics/solvers/rad/theory_element_library_solid_shell_elements_r.htm'}
PATCH=[f'PATCH_NORMAL_{a}_N12' for a in 'XYZ']+[f'PATCH_SHEAR_{a}_N12' for a in ['XY','YZ','XZ']]
OTHER=['FREE_ROTATION_X_N12','FREE_ROTATION_Y_N12','FREE_ROTATION_Z_N12','FREE_TRANSLATION_N12','FREE_ROTATION_Y_N12_HALF','MEMBRANE_N6','MEMBRANE_N12','CONSTRAINED_BENDING_N6','CONSTRAINED_BENDING_N12']

def declare():
    assert not OUT.exists() and not CFG.exists();h=harness();assert h['Status']=='PASS' and h['CurrentIteration']=='AIRCRAFT-A31';assert read(PREV/'publication_verification.json')['pass'];assert read(PREV/'curved_root_surface_mapping.json')['pass']
    cy=read(ROOT/'harness/publication_cycle.json');assert cy['pending_count']==0 and cy['last_published_iteration']=='AIRCRAFT-A31';assert read(ROOT/'outputs/github_publication/updates_2026-10-11_aircraft_a30_a31/final_remote_verification.json')['pass']
    OUT.mkdir();dump(OUT/'harness_before.json',h)
    for n in ['state.json','publication_cycle.json','experiments/registry.jsonl']:shutil.copy2(ROOT/'harness'/n,OUT/('before_'+Path(n).name))
    c={'iteration':'AIRCRAFT-A32','declared_utc':now(),'seed':1102057,'random_draws':0,'purpose':'Make the10physical-second route feasible without mass or inertia scaling. Compare documented efficient translation-only formulations against the explicit full3D LAW12 tensor and A31 curved-root surface preparation, before any whole insertion. The branch can fail; no target-damage fitting.',
       'parent_configuration':rel(source_skin.CFG),'parent_configuration_sha256':streamsha(source_skin.CFG),'material':'exact unchanged A29LAW12/4 scalar card, including explicitly hypothetical nu23/nu31 and giant elastic-witness strengths','geometry':{'bounds_mm':[[-5,-5,-.25],[5,5,.25]],'XY_meshes':[6,12],'geometric_Z_elements':1,'volume_mm3':50,'density_g_mm3':.00183,'mass_g':.0915},
       'branches':{'w0':{'property':'TYPE21 HSEPH Isolid15 Ismstr4,9through-thickness quadrature points,dn1e-20,physical thickness. Source material skew rowsY,-X,Z projected to plane. Scalar LAW12 fields and full3D constitutive reference retained; no presumption of plane-law equivalence.','cases':PATCH+OTHER},
                   'w1':{'property':'TYPE6 HEPH Isolid24 Ismstr4 Icpre3 Iframe2,dn1e-20,one physical thickness element; exact same LAW12 card and skew. Full3D physical-stabilization candidate, not fitted quadrature.','cases':PATCH+OTHER}},
       'stop_rule':'Within each branch stop after first failed affine constitutive/full-balance gate or native fatal. Preserve all attempted outputs. Subsequent branches may still test an independent documented candidate. Full qualification requires all declared cases, finite fields, mass/tensor, independent elasticity, and refinements; native completion alone is insufficient.',
       'loading':{'patch_strain':.001,'patch_ms':.1,'free_duration_ms':.05,'free_omega_rad_ms':10,'translation_m_s':[-200,5,2],'ramp':'3u2-2u3','membrane':'ux=.001x;uy=-.00025y;uz=-.00025z, source full3D uniaxial stress compliance','constrained_bending':'ux=-.001*x*z-.001²*x³/6;uy=0;uz=.001*x²/2; epsilonYY=epsilonZZ=0tofirstorder; full3DCxx bending stiffness. Single-layer interpolation/assumed strains are tested rather than accepted.'},
       'reference':{'full_C_MPa':constitutive().tolist(),'Voigt':['XX','YY','ZZ','gammaXY','gammaYZ','gammaXZ'],'patch':'0.5epsilon*C*epsilon*50mm3','membrane_J':.5*22000*.001**2*50*.001,'constrained_bending_J':.5*constitutive()[0,0]*.001**2*(100*.5**3/12)*.001,'native_elastic_comparison':'IE+HE for physical-stabilization candidates; IE andHE retained separately in full energy balance. No added reconstructed energy.','continuous_inertia_g_mm2':(.0915*(100+.25)/12,.0915*(100+.25)/12,.0915*200/12)},
       'acceptance':{'mass_relative':1e-6,'ADMAS_relative':1e-9,'full_balance_fraction':.02,'energy_absolute_J':1e-7,'elastic_fraction':.02,'free_energy_fraction':.002,'free_L_fraction':.002,'continuous_initial_KE_fraction':.02,'no_RKE_J':1e-7,'spatial_fraction':.05,'time_fraction':.002,'actual_half_dt_ratio_max':.6,'no_erosion_and_finite_fields':True},
       'execution':{'CPU_threads':1,'GPU':False,'mass_scaling':False,'native_DT_factor':.4,'native_half_DT_factor':.2,'no_DTIX_cap':'Use actual native critical step to assess efficiency; reduction of factor still tests time refinement. No relaxation of stability condition.','per_process_cap_s':600,'estimated_minutes':[5,25],'history_dt_ms':.001,'animation_dt_ms':.025},
       'curved_roots':{'source':rel(PREV/'curved_root_surface_mapping.json'),'sha256':streamsha(PREV/'curved_root_surface_mapping.json'),'roots':24,'anchors':144,'physical_surface_gaps_mm':read(PREV/'curved_root_surface_mapping.json')['gap_range_mm'],'finite_attachment_footprint_volume_mass_capacity':None,'no_flat_budget_substitution':True,'coupled_native_curved_fixture_pending':True},
       'implicit_route':{'source':rel(PREV/'implicit_binary_capability_assessment.json'),'available_in_installed_binary':False,'no_software_modification':True},'whole_aircraft_inputs_changed':False,'whole_insertion_ready':False,'old_native_solver_reruns':0,'objective1_complete':False,'sources':URLS}
    dump(CFG,c);dump(OUT/'declaration_guard.json',{'created_utc':now(),'sha256':streamsha(CFG),'before_new_native':True});sd=OUT/'sources';sd.mkdir();sources=[]
    for key,url in URLS.items():
        q=sd/(key+'.html');q.write_bytes(urllib.request.urlopen(url,timeout=45).read());sources.append({'path':rel(q),'sha256':streamsha(q),'bytes':q.stat().st_size,'url':url,'redistribution':'exclude_third_party'})
    for q in [source_skin.CFG,Path(source_skin.__file__),PREV/'publication_verification.json',PREV/'sandwich_qualification_review.json',PREV/'curved_root_surface_mapping.json',PREV/'whole_volume_geometry_preparation.json',PREV/'candidate_volume_skin_hexahedra.npz',PREV/'implicit_binary_capability_assessment.json',ROOT/'wtc1_simulation_v8/output/aircraft_a29/composite_qualification_review.json']:
        sources.append({'path':rel(q),'sha256':streamsha(q),'bytes':q.stat().st_size})
    dump(OUT/'source_manifest.json',{'created_utc':now(),'files':sources,'archive_rescanned':False,'known_damage_not_used':True});print({'A32_declared':True,'maximum_new_controls':30,'CPU_minutes':[5,25],'mass_scaling':False},flush=True)

def guard():assert streamsha(CFG)==read(OUT/'declaration_guard.json')['sha256']

def property_card(branch):
    skew=source_skin.property_card()[:5]
    if branch=='w0':return skew+['/PROP/TYPE21/1','HSEPH_FULL_TENSOR_COMPATIBILITY_PROBE',ii(15,4)+' '*20+ii(0,9)+' '*20+ff(1e-20),ff(0,0),ff(0,0,0)+ii(1,0),ff(0),ff(0,0,0,0,0),' '*20+ii(2)]
    return skew+['/PROP/TYPE6/1','HEPH_FULL_VOLUME_COMPATIBILITY_PROBE',ii(24,4)+' '*10+ii(3,0,0,0,2)+ff(1e-20),ff(0,0,0),ff(0,0,0)+ii(1,0,0),ff(0,0,0,0),ff(0,0,0,0,0),ii(0,0,2)]

def imposed(L,X,cid):
    T=np.linspace(0,.1,1001);s=3*(T/.1)**2-2*(T/.1)**3;counter=10000;cache={}
    for ni,(x,y,z) in enumerate(X,1):
        D=np.zeros(3)
        if cid.startswith('PATCH_NORMAL_'):a='XYZ'.index(cid.split('_')[2]);D[a]=.001*[x,y,z][a]
        elif cid.startswith('PATCH_SHEAR_'):
            a,b=['XYZ'.index(v) for v in cid.split('_')[2]];D[a]=.0005*[x,y,z][b];D[b]=.0005*[x,y,z][a]
        elif cid.startswith('MEMBRANE'):D=np.array([.001*x,-.00025*y,-.00025*z])
        else:D=np.array([-.001*x*z-.001**2*x**3/6,0,.001*x*x/2])
        L+=group(ni,'PRESCRIBED_NODE',[ni])
        for ax,direction in enumerate('XYZ'):
            val=D[ax]*s;key=val.tobytes()
            if key not in cache:counter+=1;cache[key]=counter;L+=[f'/FUNCT/{counter}','DECLARED_MANUFACTURED_FIELD']+[ff(t,u) for t,u in zip(T,val)]
            counter+=1;L+=[f'/IMPDISP/{counter}','TRANSLATIONS_ONLY',ii(cache[key])+f'{direction:>10}'+ii(0,0,ni)+' '*10+ii(0),ff(1,1,0,1e30)]
    return L

def native_frame(d,n,branch):
    txt=(d/(n+'_0000.out')).read_text();p=re.search(r'SKEW SYSTEM SETS.*?\n\s*1\s+0\s+0\s+0\s+([^\n]+)\n\s+([^\n]+)\n\s+([^\n]+)',txt,re.S);assert p;axes=np.array([[float(v) for v in line.split()][:3] for line in p.groups()]);header='Isolid  Ismstr   Icpre  Iframe    IHKT Itetra4 Itetra10 IMATVIS ICONTROL';p=re.search(re.escape(header)+r'\s+'+r'\s+'.join([r'(\d+)']*9),txt);assert p;flags=list(map(int,p.groups()));checks={'skew_rows':bool(np.allclose(axes,[[0,1,0],[-1,0,0],[0,0,1]],atol=1e-6,rtol=0)),'native_formulation':flags[0]==(15 if branch=='w0' else 24),'geometric_nonlinear':flags[1]==4,'corotational':flags[3]==2}
    if branch=='w1':checks['compressible_pressure_flag']=flags[2]==3
    dump(d/'native_frame_gate.json',{'created_utc':now(),'flags':flags,'axes_rows':axes.tolist(),'checks':checks,'pass':all(checks.values()),'before_Engine':True});assert all(checks.values()),checks

def review(d,n):
    g=read(d/'generation.json');H=histories(d/(n+'T01.csv'));T=H['time'];c=read(CFG);terms=['KINETIC ENERGY','ROTATION ENERGY','INTERNAL ENERGY','HOURGLASS ENERGY','SPRING ENERGY','ELASTIC CONTACT ENERGY','FRICTIONAL CONTACT ENERGY','DAMPING CONTACT ENERGY '];total=sum(H[k] for k in terms)*.001;EW=H['EXTERNAL WORK']*.001;R=total-total[0]-EW;IE=H['INTERNAL ENERGY']*.001;HE=H['HOURGLASS ENERGY']*.001;KE=H['KINETIC ENERGY']*.001;X0=np.array(g['nodes_mm']);m=np.array(g['nodal_masses_g']);nk=[k for k in H if k.startswith('NATIVE_SCOPE_NODES')];assert len(nk)==len(X0)*6;node=np.column_stack([H[k] for k in nk]).reshape(len(T),len(X0),6);X=X0+node[:,:,:3];V=node[:,:,3:];L=np.sum(m[None,:,None]*np.cross(X,V),axis=1)*1e-6;P=np.sum(m[None,:,None]*V,axis=1)*.001;ref=None
    checks={'native_termination':True,'strict_zero_warnings':read(d/'starter_gate.json')['pass'],'native_frame':read(d/'native_frame_gate.json')['pass'],'physical_mass':bool(abs(H['MASS']-.0915).max()<1e-6*.0915),'no_ADMAS':bool(abs(H['ADDED MASS']).max()<1e-9*.0915),'native_full_balance':bool(abs(R).max()<.02*max(float(abs(total).max()),float(abs(EW).max()))+1e-7),'no_native_RKE':bool(abs(H['ROTATION ENERGY']).max()*.001<1e-7),'finite_histories':bool(np.isfinite(node).all() and np.isfinite(total).all())}
    cid=g['case'];elastic=IE+HE
    if g['free']:
        expected=.5*float(np.sum(m[:,None]*np.array(g['initial_velocity_m_s'])**2))*.001;checks['known_lumped_initial_KE']=bool(abs(KE[0]-expected)<.002*expected+1e-7);checks['free_energy']=bool(abs(total-total[0]).max()<.002*abs(total[0])+1e-7);checks['free_physical_L']=bool(np.linalg.norm(L-L[0],axis=1).max()<.002*np.linalg.norm(L[0])+1e-12);checks['free_momentum']=bool(np.linalg.norm(P-P[0],axis=1).max()<.002*np.linalg.norm(P[0])+1e-9)
        if 'ROTATION' in cid:
            omega=np.array(g['initial_omega_rad_ms']);icont=np.diag(c['reference']['continuous_inertia_g_mm2']);continuous=.5*omega@icont@omega*.001;checks['continuous_initial_KE']=bool(abs(KE[0]-continuous)<.02*continuous+1e-7)
    else:
        if cid.startswith('PATCH_'):e=source_skin.patch_strain(cid);ref=float(.5*e@constitutive()@e*50*.001)
        elif cid.startswith('MEMBRANE'):ref=c['reference']['membrane_J']
        else:ref=c['reference']['constrained_bending_J']
        u=T[-1]/.1;s=3*u*u-2*u*u*u;ref*=s*s;checks['independent_elastic_energy']=bool(abs(elastic[-1]-ref)<.02*ref+1e-7)
    np.savez_compressed(d/'histories_SI.npz',time_ms=T,IE_J=IE,HE_J=HE,KE_J=KE,total_J=total,EW_J=EW,residual_J=R,physical_L_kg_m2_s=L,momentum_Ns=P,positions_mm=X,velocities_m_s=V,time_step_ms=H['TIME STEP'])
    r={'created_utc':now(),'branch':g['branch'],'case':cid,'checks':checks,'pass':all(checks.values()),'last_ms':float(T[-1]),'actual_median_dt_ms':float(np.median(H['TIME STEP'][1:])),'native_IE_J':float(IE[-1]),'native_HE_J':float(HE[-1]),'independent_reference_J':ref,'maximum_residual_J':float(abs(R).max()),'whole_insertion_ready':False};dump(d/'review.json',r);print({'A32':g['branch'],'case':cid,'pass':r['pass'],'failed':[k for k,v in checks.items() if not v],'median_dt_ms':r['actual_median_dt_ms']},flush=True)

def run_one(branch,cid):
    guard();d=OUT/branch/cid;assert not d.exists();d.mkdir(parents=True);n='A32_'+branch.upper()+'_'+cid;ncell=int(re.search(r'_N(6|12)',cid).group(1));X,B,m,left,right=brick_grid([ncell,ncell,1],[-5,-5,-.25],[5,5,.25]);m*=.00183/.00278;free=cid.startswith('FREE');duration=.05 if free else .1
    L=['#RADIOSS STARTER','/BEGIN',n,ii(2026,0),ff('g','mm','ms'),ff('g','mm','ms'),'/TITLE',n,'/ANALY',ii(0)+ff(0)+ii(0),'/SPMD',ii(0,0)+ff(0,1),'/NODE']+[ii(j+1)+ff(*p) for j,p in enumerate(X)]+source_skin.law12_card()+property_card(branch)+['/PART/1','DECLARED_PHYSICAL_SKIN',ii(1,4,0),'/BRICK/1']+[ii(j+1,*b) for j,b in enumerate(B)];omega=np.zeros(3);V=np.zeros_like(X)
    if free:
        if 'ROTATION' in cid:omega=np.eye(3)['XYZ'.index(re.search('ROTATION_([XYZ])',cid).group(1))]*10;V=np.cross(omega,X)
        else:V=np.tile([-200,5,2],(len(X),1))
        for ni,v in enumerate(V,1):L+=group(ni,'PHYSICAL_INITIAL_NODE',[ni])+[f'/INIVEL/TRA/{ni}','INITIAL_TRANSLATIONS',ff(*v)+ii(ni,0),ff(0)+ii(0)]
    else:L=imposed(L,X,cid)
    L+=['/TH/PART/1','SKIN_SCOPE',''.join(f'{v:>10}' for v in ['IE','KE','HE','PW']),ii(1),'/TH/NODE/1','NATIVE_SCOPE_NODES',''.join(f'{v:>10}' for v in ['DX','DY','DZ','VX','VY','VZ'])]+[ii(j,0) for j in range(1,len(X)+1)]+['/END'];(d/(n+'_0000.rad')).write_text('\n'.join(L)+'\n',encoding='utf-8')
    E=['/ANIM/DT',ff(0,.025),'/ANIM/MASS','/ANIM/VECT/DISP','/ANIM/VECT/VEL','/ANIM/ELEM/ENER','/ANIM/BRICK/TENS/STRESS','/DT',ff(.2 if cid.endswith('HALF') else .4,0),'/PRINT/-100/100',f'/RUN/{n}/1',ff(duration),'/TFILE/4',ff(.001),'/VERS/2026'];(d/(n+'_0001.rad')).write_text('\n'.join(E)+'\n',encoding='utf-8');shutil.copy2(__file__,d/'generator_snapshot.py');dump(d/'generation.json',{'created_utc':now(),'name':n,'branch':branch,'case':cid,'free':free,'mesh_n':ncell,'geometric_Z_elements':1,'nodes_mm':X.tolist(),'bricks':B,'nodal_masses_g':m.tolist(),'known_mass_g':float(m.sum()),'initial_velocity_m_s':V.tolist(),'initial_omega_rad_ms':omega.tolist(),'known_lumped_inertia_g_mm2':inertia(X,m).tolist(),'configuration_sha256':streamsha(CFG),'generator_sha256':streamsha(Path(__file__))});en=env();en.update(OMP_NUM_THREADS='1',RAD_HMPP_DOMAINS='1')
    try:
        ok=execute(RUNTIME/'starter_win64.exe',['-i',n+'_0000.rad','-np','1'],d,'starter.log',600,en);t=(d/'starter.log').read_text(errors='replace');nw=int(re.findall(r'(\d+) WARNING\(S\)',t)[-1]);ne=int(re.findall(r'(\d+) ERROR\(S\)',t)[-1]);dump(d/'starter_gate.json',{'created_utc':now(),'warnings':nw,'errors':ne,'pass':bool(ok and nw==0 and ne==0)});assert ok and nw==0 and ne==0;native_frame(d,n,branch);assert execute(RUNTIME/'engine_win64.exe',['-i',n+'_0001.rad'],d,'engine.log',600,en);assert 'NORMAL TERMINATION' in (d/'engine.log').read_text(errors='replace');assert execute(RUNTIME/'th_to_csv_win64.exe',[n+'T01'],d,'converter.log',600,en);review(d,n)
    except Exception:dump(d/'retained_failure.json',{'created_utc':now(),'traceback':traceback.format_exc(),'no_implicit_rerun':True});raise

def run():
    guard();branches=[]
    for branch,settings in read(CFG)['branches'].items():
        rows=[];stopped=None
        for cid in settings['cases']:
            d=OUT/branch/cid
            try:
                if d.exists():assert (d/'review.json').exists(),'No rerun of incomplete native attempt'
                else:run_one(branch,cid)
            except Exception:stopped={'case':cid,'reason':'native/preparation fatal; retained failure','traceback':traceback.format_exc()};break
            r=read(d/'review.json');rows.append(r)
            if cid.startswith('PATCH') and not r['pass']:stopped={'case':cid,'reason':'original independent affine/full-balance gate failed'};break
        dest=OUT/(branch+'_case_summary.json');assert not dest.exists();dump(dest,{'created_utc':now(),'branch':branch,'cases':rows,'stopped':stopped,'declared_controls':len(settings['cases']),'completed_controls':len(rows),'whole_insertion_ready':False});branches.append(read(dest))
    dump(OUT/'native_case_summary.json',{'created_utc':now(),'branches':branches,'whole_insertion_ready':False,'old_native_solver_reruns':0,'objective1_complete':False});print({'A32_campaign_bounded_finished':True,'completed_controls':sum(len(x['cases']) for x in branches),'stopped_branches':[x['branch'] for x in branches if x['stopped']]},flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['declare','run']);globals()[p.parse_args().action]()
