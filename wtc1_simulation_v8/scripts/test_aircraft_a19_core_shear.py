"""Finite transverse shear reference: native removal, mass and work accounting witness."""
import numpy as np
from run_aircraft_a19 import *
from run_aircraft_a18 import blocks
from test_aircraft_a19_triangles import histories
from diagnose_aircraft_a19_cached import fast

SCFG=ROOT/'wtc1_simulation_v8/data/aircraft_a19_core_shear_declaration.json'
def declare():
    guard();assert not SCFG.exists();p=ROOT/'wtc1_simulation_v8/input/aircraft_a05_sources/hrh10_eu.pdf';c={'iteration':'AIRCRAFT-A19','declared_utc':now(),'seed':1102044,'random_draws':0,
      'scope':'Native pure transverse shear of an8mm reference core-only triangle. Diagnose finite shear failure and account for removed-element energy and persistent nodal mass. Not actual radome calibration.',
      'source':{'path':rel(p),'sha256':streamsha(p),'page':4,'grade':'HRH10-3.2-48','test_thickness_mm':12.7,'rho_kg_m3':48,'G_L_MPa':41,'G_W_MPa':24,'tau_L_MPa':1.21,'tau_W_MPa':.69,'test':'typical room-temperature plate shear values; no high-rate fracture-energy curve'},
      'onset_gamma':min(1.21/41,.69/24),'onset_rule':'Conservative circular envelope gamma=sqrt(gamma13^2+gamma23^2), weakest reported tau/G; not an identified anisotropic surface.',
      'softening_ratios':[.2,.02],'softening_ratio_is_hypothesis':True,'core_G_measured':False,'material':'A18 LAW25/5 unchanged except native gamma_ini/gamma_max/d3max for finite cases',
      'cases':['UNBOUNDED','FINITE_R20','FINITE_R02'],'d3max':.999,'model_thickness_mm':8,'triangle_mm':[[0,0,0],[300,0,0],[0,300,0]],'Ish3n':2,'angle_path_rad':[0,.015,0,.06,.06],
      'time_path_ms':[0,.25,.5,.75,1],'rotations':'Uniform YY director rotation, all midsurface translations and XX/ZZ fixed; no bending/membrane strain intended. No contact/instrument masses.',
      'dt_cap_ms':.000025,'history_dt_ms':.001,'animation_dt_ms':.025,'engine_cap_s':120,
      'acceptance':{'mass_relative':1e-6,'nodal_mass_preservation_relative':1e-6,'negative_IE_allowance_J':.001,'global_energy_balance_fraction':.02,'absolute_energy_balance_J':.001,'finite_element_removal_expected':True,'unbounded_element_remains_expected':True},
      'sources':['https://help.altair.com/hwsolvers/rad/topics/solvers/rad/tsai_wu_formulation_starter_r.htm'],'whole_core_transfer_qualified':False,'old_solver_reruns':0}
    dump(SCFG,c);dump(OUT/'core_shear_guard.json',{'sha256':streamsha(SCFG),'declared_before_all_core_witnesses':True});print({'core_controls_declared':3,'gamma_onset':c['onset_gamma']},flush=True)

def witness(cid):
    c=read(SCFG);assert streamsha(SCFG)==read(OUT/'core_shear_guard.json')['sha256'];d=OUT/'s0'/cid;assert not d.exists();d.mkdir(parents=True);n='A19_CORE_'+cid;pb={b[0]:b for b in blocks((SOURCE/(read(SOURCE/'generation.json')['name']+'_0000.rad')).read_text().splitlines())}
    L=['#RADIOSS STARTER','/BEGIN',n,ii(2026,0),ff('g','mm','ms'),ff('g','mm','ms'),'/TITLE',n,'/ANALY',ii(0)+ff(0)+ii(0),'/SPMD',ii(0,0)+ff(0,1),'/NODE']+[ii(i+1)+ff(*q) for i,q in enumerate(c['triangle_mm'])]
    mat=pb['/MAT/LAW25/5'].copy()
    if cid!='UNBOUNDED':r=.2 if cid=='FINITE_R20' else .02;mat[-2]=ff(c['onset_gamma'],c['onset_gamma']*(1+r),c['d3max'])
    prop=pb['/PROP/TYPE51/21'][:6]+pb['/PROP/TYPE51/21'][8:10];L+=mat+pb['/PROP/TYPE19/42']+prop
    assert prop[-2].startswith(ii(42));L+=['/PART/21','CORE_ONLY_REFERENCE',ii(21,5,0),'/SHELL/21',ii(1,1,2,3,3),'/GRNOD/NODE/1','ALL_NODES',ii(1,2,3),'/BCS/1','MIDSURFACE_FIXED_AND_XX_ZZ_FIXED','   111 101'+ii(0,1)]
    ts=np.linspace(0,1,10001);angle=np.zeros_like(ts)
    for ta,tb,a,b in zip(c['time_path_ms'][:-1],c['time_path_ms'][1:],c['angle_path_rad'][:-1],c['angle_path_rad'][1:]):
        sel=(ts>=ta)&(ts<=tb);u=(ts[sel]-ta)/(tb-ta);angle[sel]=a+(b-a)*(3*u*u-2*u*u*u)
    L+=['/FUNCT/90','DIRECTOR_ANGLE']+[ff(t,a) for t,a in zip(ts,angle)]+['/IMPDISP/90','UNIFORM_CORE_TRANSVERSE_SHEAR',ii(90)+f'{"YY":>10}'+ii(0,0,1)+' '*10+ii(0),ff(1,1,0,1e30),'/TH/PART/21','CORE_ONLY_PART',''.join(f'{q:>10}' for q in ['IE','KE','HE','PW']),ii(21),'/END'];(d/(n+'_0000.rad')).write_text('\n'.join(L)+'\n',encoding='utf-8')
    E=['/ANIM/DT',ff(0,.025),'/ANIM/MASS','/ANIM/ELEM/ENER','/ANIM/SHELL/DAMA/ALL','/ANIM/VECT/DISP','/ANIM/VECT/VEL','/DT',ff(.4,0),'/DTIX',ff(.000025,.000025),'/PRINT/-100/100',f'/RUN/{n}/1',ff(1),'/TFILE/4',ff(.001),'/VERS/2026'];(d/(n+'_0001.rad')).write_text('\n'.join(E)+'\n',encoding='utf-8');dump(d/'generation.json',{'created_utc':now(),'name':n,'case':cid,'configuration_sha256':streamsha(SCFG),'core_only_volume_mm3':45000*8,'expected_mass_g':45000*8*4.8e-5})
    assert execute(RUNTIME/'starter_win64.exe',['-i',n+'_0000.rad','-np','1'],d,'starter.log',120,env());s=(d/'starter.log').read_text(errors='replace');assert int(re.findall(r'(\d+) WARNING\(S\)',s)[-1])==0 and int(re.findall(r'(\d+) ERROR\(S\)',s)[-1])==0
    assert execute(RUNTIME/'engine_win64.exe',['-i',n+'_0001.rad'],d,'engine.log',120,env());assert 'NORMAL TERMINATION' in (d/'engine.log').read_text(errors='replace');assert execute(RUNTIME/'th_to_csv_win64.exe',[n+'T01'],d,'converter.log',120,env());review(d,n,c,cid)

def review(d,n,c,cid):
    H=histories(d/(n+'T01.csv'));IE=H['INTERNAL ENERGY']*.001;terms=['KINETIC ENERGY','ROTATION ENERGY','INTERNAL ENERGY','HOURGLASS ENERGY','SPRING ENERGY'];total=sum(H[k] for k in terms)*.001;ew=H['EXTERNAL WORK']*.001;res=total-total[0]-ew;files=sorted(p for p in d.glob(n+'A*') if re.fullmatch(re.escape(n)+r'A\d{3}',p.name));q0=fast(files[0]);q1=fast(files[-1]);mass=H['MASS']*.001;nmerr=float(np.max(abs(q1['node_mass_g']-q0['node_mass_g'])));m0=float(q0['node_mass_g'].sum());alive=bool(q1['alive'][0]);scale=max(float(abs(total).max()),float(abs(ew).max()));expected_early=.5*(5/6)*41*(.015**2)*(45000*8)*.001;ipeak=int(np.argmin(abs(H['time']-.25)))
    checks={'normal_termination':True,'nonnegative_IE':bool(IE.min()>-.001),'native_global_energy_balance':bool(abs(res).max()<.02*scale+.001),'native_mass_constant':bool(abs(mass-mass[0]).max()<1e-6*mass[0]),'nodal_mass_constant':nmerr<1e-6*m0,'native_mass_expected':abs(mass[0]-.01728)<1e-8,'expected_removal':(not alive) if cid!='UNBOUNDED' else alive,'precritical_elastic_energy':bool(abs(IE[ipeak]-expected_early)<.02*expected_early+.001)}
    r={'created_utc':now(),'case':cid,'last_native_ms':q1['time_ms'],'last_IE_J':float(IE[-1]),'minimum_IE_J':float(IE.min()),'maximum_IE_J':float(IE.max()),'maximum_global_energy_residual_J':float(abs(res).max()),'mass_kg':float(mass[0]),'native_nodal_mass_g':m0,'nodal_mass_change_g':nmerr,'final_shell_alive':alive,'early_IE_J':float(IE[ipeak]),'early_analytic_shear_IE_J':expected_early,'checks':{k:bool(v) for k,v in checks.items()},'pass':all(checks.values()),'core_fracture_G_measured':False,'whole_core_transfer_qualified':False,'bulk_erosion_no_discrete_fragment_mesh':True};dump(d/'review.json',r);print(r,flush=True)

def run():
    for cid in read(SCFG)['cases']:witness(cid)
    r=[read(OUT/'s0'/cid/'review.json') for cid in read(SCFG)['cases']];dump(OUT/'core_shear_review.json',{'created_utc':now(),'cases':r,'pass':all(q['pass'] for q in r),'whole_transfer_qualified':False,'mass_retained_after_native_removal':all(q['checks']['nodal_mass_constant'] for q in r),'cannot_render_deleted_shell_as_intact_fragment':True})

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['declare','run']);globals()[p.parse_args().action]()
