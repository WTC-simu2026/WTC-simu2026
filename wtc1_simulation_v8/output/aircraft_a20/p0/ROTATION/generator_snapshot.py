"""Conformal skin/core geometry controls before whole-aircraft integration."""
from run_aircraft_a20 import *
from run_aircraft_a18 import blocks
PCFG=ROOT/'wtc1_simulation_v8/data/aircraft_a20_sandwich_declaration.json'

def parent_cards():
    g=read(SOURCE/'generation.json');return {b[0]:b for b in blocks((SOURCE/(g['name']+'_0000.rad')).read_text().splitlines())}

def face_property(pid,ply,bottom):
    b=parent_cards()['/PROP/TYPE51/21'];L=b[:6];L[0]=f'/PROP/TYPE51/{pid}';L[1]='HALF_MM_SKIN_AT_CORE_BOUNDARY'
    # Lower skin: top at reference nodes. Upper skin: bottom at reference nodes. Total thickness8+.5+.5mm.
    L[5]=ff(1,0,0)+ii(0,0,3 if bottom else 4,0)
    return L+[ii(ply)+ff(0,0,1,1),'']

def declare():
    guard();assert read(OUT/'core_verified_review.json')['pass'];assert not PCFG.exists()
    c={'iteration':'AIRCRAFT-A20','declared_utc':now(),'seed':1102045,'random_draws':0,
      'scope':'Shared solid/skin translational nodes; shell rotations free; explicit outer ply positioning. Verify true thickness, no tying of top to bottom, mass, rigid rotation and small membrane/bending response.',
      'geometry':'10x10mm core, z-4..4; lower face ply-.5..0 at lower nodes, upper0..+.5 at upper nodes;9mm total. TYPE51 Ipos3/4, TYPE6 Ip11 projection of globalX onto local(r,s).',
      'skin':'Inherited LAW25/4, TYPE19/41/43 each0.5mm, ORTHSTRAIN4 unchanged. No surrogate core ply42.',
      'core_configuration':rel(CFG),'core_configuration_sha256':streamsha(CFG),
      'cases':['ROTATION','MEMBRANE','SHEAR','BENDING'],'duration_ms':1,'dt_cap_ms':.000025,
      'strain':.001,'curvature_per_mm':.0001,'maximum_shear':.15,'history_ms':.001,'animation_ms':.025,'engine_cap_s':120,
      'reference_mass_g':.2214,'acceptance':{'mass_relative':1e-6,'energy_balance_relative':.02,'absolute_energy_J':.0001,'rigid_IE_J':.0001,'elastic_IE_fraction':.02,'core_deletion_expected_shear':True,'skin_survival_expected':True},
      'references':['https://help.altair.com/hwsolvers/rad/topics/solvers/rad/prop_type51_starter_r.htm','https://help.altair.com/hwsolvers/rad/topics/solvers/rad/prop_type6_sol_orth_starter_r.htm'],
      'core_skin_debonding':False,'physical_sandwich_qualification':False,'fracture_energy_measured':False,'no_mass_scaling':True}
    dump(PCFG,c);dump(OUT/'sandwich_guard.json',{'sha256':streamsha(PCFG),'declared_before_panels':True});print({'sandwich_cases_declared':4},flush=True)

def panel(cid):
    guard();assert streamsha(PCFG)==read(OUT/'sandwich_guard.json')['sha256'];c=read(PCFG);d=OUT/'p0'/cid;n='A20_PANEL_'+cid;assert not d.exists();d.mkdir(parents=True)
    xyz=np.array([[0,0,-4],[10,0,-4],[10,10,-4],[0,10,-4],[0,0,4],[10,0,4],[10,10,4],[0,10,4]],float);ts=np.linspace(0,1,10001);u=3*ts**2-2*ts**3;disp=np.zeros((len(ts),8,3));ang=np.zeros((len(ts),8,3))
    if cid=='ROTATION':
        a=np.pi/2*u;disp[:,:,0]=xyz[None,:,0]*np.cos(a[:,None])+xyz[None,:,2]*np.sin(a[:,None])-xyz[None,:,0];disp[:,:,2]=-xyz[None,:,0]*np.sin(a[:,None])+xyz[None,:,2]*np.cos(a[:,None])-xyz[None,:,2];ang[:,:,1]=a[:,None]
    elif cid=='MEMBRANE':disp[:,:,:2]=c['strain']*u[:,None,None]*xyz[None,:,:2]
    elif cid=='SHEAR':disp[:,:,0]=smooth_path(ts,read(CFG)['witness']['paths']['L'])[:,None]*(xyz[None,:,2]+4)
    else:
        k=c['curvature_per_mm']*u;k[0]=1e-30;theta=k[:,None]*xyz[None,:,0];disp[:,:,0]=(1/k[:,None]+xyz[None,:,2])*np.sin(theta)-xyz[None,:,0];disp[:,:,2]=(1/k[:,None]+xyz[None,:,2])*np.cos(theta)-1/k[:,None]-xyz[None,:,2];disp[0]=0;ang[:,:,1]=theta
    P=parent_cards();L=['#RADIOSS STARTER','/BEGIN',n,ii(2026,0),ff('g','mm','ms'),ff('g','mm','ms'),'/TITLE',n,'/ANALY',ii(0)+ff(0)+ii(0),'/SPMD',ii(0,0)+ff(0,1),'/NODE']+[ii(i+1)+ff(*q) for i,q in enumerate(xyz)]
    L+=material()+solid_property(skew=0,ip=11)
    for key in ['/MAT/LAW25/4','/PROP/TYPE19/41','/PROP/TYPE19/43','/FAIL/ORTHSTRAIN/4']:L+=P[key]
    L+=face_property(122,41,True)+face_property(123,43,False)+['/PART/28','PANEL_3D_CORE',ii(28,28,0),'/BRICK/28',ii(1,1,2,3,4,5,6,7,8),'/PART/122','PANEL_LOWER_SKIN',ii(122,4,0),'/SHELL/122',ii(2,1,2,3,4),'/PART/123','PANEL_UPPER_SKIN',ii(123,4,0),'/SHELL/123',ii(3,5,6,7,8)]
    fid=1000
    for ni in range(1,9):
        L += [f'/GRNOD/NODE/{ni}',f'NODE_{ni}',ii(ni)]
        for ax,direction in enumerate(['X','Y','Z','XX','YY','ZZ']):
            vals=disp[:,ni-1,ax] if ax<3 else ang[:,ni-1,ax-3];fid+=1
            L += [f'/FUNCT/{fid}',f'MOTION_{ni}_{direction}']+[ff(t,v) for t,v in zip(ts,vals)]+[f'/IMPDISP/{fid}',f'MOTION_{ni}_{direction}',ii(fid)+f'{direction:>10}'+ii(0,0,ni)+' '*10+ii(0),ff(1,1,0,1e30)]
    L+=['/TH/PART/28','CONFORMAL_SANDWICH',''.join(f'{v:>10}' for v in ['IE','KE','HE','PW']),ii(28,122,123),'/END'];(d/(n+'_0000.rad')).write_text('\n'.join(L)+'\n',encoding='utf-8')
    E=['/ANIM/DT',ff(0,.025),'/ANIM/MASS','/ANIM/VECT/DISP','/ANIM/VECT/VEL','/ANIM/BRICK/TENS/STRESS','/ANIM/SHELL/DAMA/ALL','/ANIM/ELEM/ENER','/DT',ff(.4,0),'/DTIX',ff(.000025,.000025),'/PRINT/-100/100',f'/RUN/{n}/1',ff(1),'/TFILE/4',ff(.001),'/VERS/2026'];(d/(n+'_0001.rad')).write_text('\n'.join(E)+'\n',encoding='utf-8');shutil.copy2(__file__,d/'generator_snapshot.py');dump(d/'generation.json',{'created_utc':now(),'name':n,'case':cid,'configuration_sha256':streamsha(PCFG),'nodes_mm':xyz.tolist()})
    ok=execute(RUNTIME/'starter_win64.exe',['-i',n+'_0000.rad','-np','1'],d,'starter.log',120,env());s=(d/'starter.log').read_text(errors='replace');warnings=int(re.findall(r'(\d+) WARNING\(S\)',s)[-1]);errors=int(re.findall(r'(\d+) ERROR\(S\)',s)[-1]);dump(d/'starter_gate.json',{'exit_ok':ok,'warnings':warnings,'errors':errors,'pass':ok and warnings==0 and errors==0});assert ok and warnings==0 and errors==0,s[-4000:]
    assert execute(RUNTIME/'engine_win64.exe',['-i',n+'_0001.rad'],d,'engine.log',120,env());assert 'NORMAL TERMINATION' in (d/'engine.log').read_text(errors='replace');assert execute(RUNTIME/'th_to_csv_win64.exe',[n+'T01'],d,'converter.log',120,env());review(d,n,cid)

def review(d,n,cid):
    c=read(PCFG);H=histories(d/(n+'T01.csv'));IE=H['INTERNAL ENERGY']*.001;total=sum(H[k] for k in ['KINETIC ENERGY','ROTATION ENERGY','INTERNAL ENERGY','HOURGLASS ENERGY','SPRING ENERGY'])*.001;res=total-total[0]-H['EXTERNAL WORK']*.001;scale=max(float(abs(total).max()),float(abs(H['EXTERNAL WORK']*.001).max()));mass=H['MASS']*.001
    p=sorted(q for q in d.glob(n+'A*') if re.fullmatch(re.escape(n)+r'A\d{3}',q.name))[-1];q=vtk(subprocess.run([str(RUNTIME/'anim_to_vtk_win64.exe'),str(p)],capture_output=True,text=True,check=True,timeout=120).stdout);(d/(p.name+'.vtk')).write_text(subprocess.run([str(RUNTIME/'anim_to_vtk_win64.exe'),str(p)],capture_output=True,text=True,check=True,timeout=120).stdout,encoding='utf-8');alive={int(e):bool(a) for e,a in zip(q['ELEMENT_ID'],q['EROSION_STATUS'])};core_alive=alive[1];skin_alive=alive[2] and alive[3]
    ref=None
    if cid=='MEMBRANE':ref=100*(22000/(1-.25)*1+1*8)*c['strain']**2*.001
    if cid=='BENDING':ref=.5*100*(22000/(1-.25**2)*(2*(.5*4.25**2+.5**3/12))+1*8**3/12)*c['curvature_per_mm']**2*.001
    checks={'normal_termination':True,'zero_errors_warnings':True,'mass_expected':bool(abs(mass[0]-.0002214)<1e-10),'mass_constant':bool(abs(mass-mass[0]).max()<1e-6*mass[0]),'nonnegative_IE':bool(IE.min()>-.0001),'energy_balance':bool(abs(res).max()<.02*scale+.0001),'skin_alive':bool(skin_alive),'core_expected_status':not core_alive if cid=='SHEAR' else core_alive}
    if cid=='ROTATION':checks['rigid_rotation_IE']=bool(abs(IE).max()<.0001)
    if ref is not None:checks['analytic_small_response']=bool(abs(IE[-1]-ref)<.02*ref+.000001)
    r={'created_utc':now(),'case':cid,'end_ms':q['time'],'mass_g':float(mass[0]*1000),'last_IE_J':float(IE[-1]),'analytic_IE_J':ref,'maximum_energy_residual_J':float(abs(res).max()),'core_final_alive':core_alive,'skins_final_alive':skin_alive,'checks':{k:bool(v) for k,v in checks.items()},'pass':all(checks.values()),'physical_sandwich_qualified':False};dump(d/'review.json',r);print(r,flush=True)

def run():
    for cid in read(PCFG)['cases']:panel(cid)
    rows=[read(OUT/'p0'/cid/'review.json') for cid in read(PCFG)['cases']];dump(OUT/'sandwich_review.json',{'created_utc':now(),'cases':rows,'pass':all(r['pass'] for r in rows),'physical_skin_core_debonding_qualified':False,'no_implicit_mass_change':True})

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['declare','run']);globals()[p.parse_args().action]()
