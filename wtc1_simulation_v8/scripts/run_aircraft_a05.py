"""Rounded nose and elastic reference sandwich in fresh whole-aircraft cases."""
import argparse,json,shutil,os,re
from pathlib import Path
import numpy as np
from run_aircraft_a02 import ROOT,RUNTIME,read,dump,sha,rel,now,ff,ii,harness,execute
from run_aircraft_a04 import blocks
CFG=ROOT/'wtc1_simulation_v8/data/aircraft_a05_predeclaration.json';OUT=ROOT/'wtc1_simulation_v8/output/aircraft_a05';PREV=ROOT/'wtc1_simulation_v8/output/aircraft_a04'

def preserved():
    pins=read(OUT/'preservation_before.json')['files'];bad=[r['path'] for r in pins if sha(ROOT/r['path'])!=r['sha256']];assert not bad,bad;return len(pins)

def initialize():
    assert not OUT.exists();v=harness();assert v['Status']=='PASS' and v['CurrentIteration']=='AIRCRAFT-A04';OUT.mkdir();dump(OUT/'harness_before.json',v)
    for name in ['state.json','publication_cycle.json','experiments/registry.jsonl']:shutil.copy2(ROOT/'harness'/name,OUT/('before_'+name.split('/')[-1]))
    pins={r['path']:r for name in ['preservation_before.json','artifact_manifest.json'] for r in read(PREV/name)['files']}
    for p in [PREV/'artifact_manifest.json',PREV/'publication_verification.json']:pins[rel(p)]={'path':rel(p),'sha256':sha(p),'bytes':p.stat().st_size}
    dump(OUT/'preservation_before.json',{'created_utc':now(),'files':list(pins.values())});dump(OUT/'declaration_guard.json',{'created_utc':now(),'sha256':sha(CFG),'before_any_generation_or_new_solver':True})
    c=read(CFG);files=[ROOT/c['input_deck'],ROOT/c['input_mesh'],ROOT/'wtc1_simulation_v8/output/aircraft_a01/verification_r2/airframe_mesh_SI.json',ROOT/'wtc1_simulation_v8/input/aircraft_a04_sources/boeing_arff767.pdf']+list((ROOT/'wtc1_simulation_v8/input/aircraft_a05_sources').glob('*'))
    dump(OUT/'source_manifest.json',{'created_utc':now(),'local_inputs':[{'path':rel(p),'sha256':sha(p),'bytes':p.stat().st_size,'publication':'external_source_exclude' if p.suffix=='.pdf' else 'own_provenance'} for p in files],'primary_links':c['sources'],'archive_rescanned':False,'NIST_damage_target':False})
    dump(OUT/'source_transcription.json',{'face':{'source':'HexPly913 PDF page4,7781GL/R91337%,300AW','density_original_g_cc':1.83,'density_kg_m3':1830,'tension_E_original_GPa':22,'E_MPa':22000,'tension_strength_original_ksi':65.3,'printed_MPa':450,'compression_strength_original_ksi':66.7,'printed_compression_MPa':460,'compression_E_original_GPa':28,'model_compression_E_not_identified':True,'short_beam_shear_MPa':65,'short_beam_not_in_plane_strength':True},'core':{'source':'HRH10-3.2-48 PDF page4','density_code_kg_m3':48,'E_transverse_MPa':138,'G_L_MPa':41,'G_W_MPa':24,'bare_strength_MPa':2.07,'shear_strength_L_MPa':1.21,'shear_strength_W_MPa':.69,'normal_crushing_not_resolved_by_shell':True},'A04_handoff_node_annotation_correction':{'element':4050,'correct_one_based_native_node_ids':[2041,18,19],'A04_handoff_list_was_zero_based':[2040,17,18],'actual_old_deck_not_changed':True},'not_identified_767_construction':True})
    print({'initialized':True,'old_files_pinned':preserved()})

def elastic_ortho(mid,m,c):
    # Very high constitutive caps keep elasticity; actual sheet strengths are diagnostics only.
    Y=c['sandwich']['numerical_yield_MPa'];F=c['sandwich']['numerical_failure_strain']
    return [f'/MAT/LAW25/{mid}',f'elastic_reference_orthotropic_{mid}',ff(m['rho_g_mm3']),ff(m['E11_MPa'],m['E22_MPa'],m['nu12'])+ii(0)+' '*10+ff(m['E33_MPa']),ff(m['G12_MPa'],m['G23_MPa'],m['G31_MPa'],F,F),ff(F,2*F,F,2*F,.999),ff(1e30,1)+ii(1)+' '*10+ff(1),ff(0,1,1),ff(Y,Y,Y,Y,0),ff(Y,Y,0,.001)+ii(1),ff(F,2*F,.999),ii(0)+ff(0)]

def laminate(c,face):
    layers=[(c['sandwich']['face'],face),(c['sandwich']['core'],c['sandwich']['core_thickness_mm']),(c['sandwich']['face'],face)];z=-sum(t for m,t in layers)/2;A=np.zeros((3,3));B=A.copy();D=A.copy();An=A.copy();Bn=A.copy();Dn=A.copy();rhoarea=0.;shear=np.zeros(2);gg,ww=np.polynomial.legendre.leggauss(c['sandwich']['ply_integration_points'])
    for m,t in layers:
        e1,e2,nu=m['E11_MPa'],m['E22_MPa'],m['nu12'];den=1-nu*nu*e2/e1;Q=np.array([[e1/den,nu*e2/den,0],[nu*e2/den,e2/den,0],[0,0,m['G12_MPa']]]);lo,hi=z,z+t
        A+=Q*t;B+=Q*(hi**2-lo**2)/2;D+=Q*(hi**3-lo**3)/3
        zn=(lo+hi)/2+gg*t/2;wt=ww*t/2;An+=Q*sum(wt);Bn+=Q*sum(wt*zn);Dn+=Q*sum(wt*zn**2);rhoarea+=m['rho_g_mm3']*t;shear+=np.array([m['G31_MPa'],m['G23_MPa']])*t*5/6;z=hi
    err=max(np.max(abs(An-A))/np.max(abs(A)),np.max(abs(Bn-B))/max(np.max(abs(A)),1),np.max(abs(Dn-D))/np.max(abs(D)))
    assert err<c['acceptance']['laminate_quadrature_relative_error'] and np.all(np.linalg.eigvalsh(A)>0) and np.all(np.linalg.eigvalsh(D)>0)
    return {'A_N_mm':A.tolist(),'B_N':B.tolist(),'D_Nmm':D.tolist(),'transverse_shear_N_mm':shear.tolist(),'areal_mass_kg_m2':rhoarea*1000,'thickness_mm':sum(t for m,t in layers),'quadrature_relative_error':float(err),'symmetric_B_is_zero_to_roundoff':bool(np.max(abs(B))<1e-10),'elastic_reference_only':True}

def build(revision):
    c=read(CFG);assert sha(CFG)==read(OUT/'declaration_guard.json')['sha256'];preserved();base=OUT/revision;assert not base.exists();base.mkdir();shutil.copy2(__file__,base/'generator_snapshot.py')
    original=blocks((ROOT/c['input_deck']).read_text().splitlines());oldmesh=read(ROOT/c['input_mesh']);xorig=np.array(oldmesh['nodes_mm']);origtri={int(line[:10]):[int(line[10+10*j:20+10*j]) for j in range(3)] for b in original if b[0].startswith('/SH3N/') for line in b[1:]};origbeam={int(line[:10]):[int(line[10:20]),int(line[20:30])] for b in original if b[0].startswith('/BEAM/') for line in b[1:]}
    tri_part={int(line[:10]):int(b[0].split('/')[-1]) for b in original if b[0].startswith('/SH3N/') for line in b[1:]};beam_part={int(line[:10]):int(b[0].split('/')[-1]) for b in original if b[0].startswith('/BEAM/') for line in b[1:]}
    root=c['nose']['root_X_mm'];nose_ids=[eid for eid,el in origtri.items() if tri_part[eid] in [1,2] and max(xorig[np.array(el)-1,0])<=root];nose_nodes=sorted({n for eid in nose_ids for n in origtri[eid]});oldair=list(range(1,oldmesh['aircraft_node_count']+1));pole=2041
    # Every affected existing node remains in a shell; no isolated massless nodes created.
    xbase=xorig.copy();rroot=np.max(abs(xorig[np.array(nose_nodes)-1,1]));zroot=np.max(abs(xorig[np.array(nose_nodes)-1,2]))
    for nid in nose_nodes:
        p=xorig[nid-1]
        if nid==pole:continue
        xx=c['nose']['first_ring_X_mm'] if p[0]==0 else p[0];theta=np.arctan2(p[2]/zroot,p[1]/rroot);scale=np.sqrt(1-(1-xx/root)**2);xbase[nid-1]=[xx,rroot*scale*np.cos(theta),zroot*scale*np.sin(theta)]
    removedbeams=[eid for eid,el in origbeam.items() if beam_part[eid] in [12,13] and np.min(xorig[np.array(el)-1,0])<root]
    for case in c['execution']['cases']:
        d=base/case['id'];d.mkdir();n='A05_'+case['id'];x=xbase.tolist();tris={eid:el[:] for eid,el in origtri.items()};bms={eid:el[:] for eid,el in origbeam.items()};tp=tri_part.copy();air=oldair[:];radome=nose_ids[:]
        if case['composite']:
            bms={eid:el for eid,el in bms.items() if eid not in removedbeams}
            for eid in radome:tp[eid]=21
        if case['fine']:
            mids={};replaced=[];newid=70000
            for eid in nose_ids:
                a,b,z=tris.pop(eid);tp.pop(eid);v=[a,b,z];mid=[]
                for p,q in zip(v,v[1:]+v[:1]):
                    edge=tuple(sorted([p,q]))
                    if x[p-1][0]==root and x[q-1][0]==root:mid.append(None);continue
                    if edge not in mids:mids[edge]=len(x)+1;x.append(((np.array(x[p-1])+x[q-1])/2).tolist());air.append(len(x))
                    mid.append(mids[edge])
                if all(q is not None for q in mid):
                    u,vv,w=mid;subs=[[a,u,w],[u,b,vv],[w,vv,z],[u,vv,w]]
                else:
                    j=mid.index(None);u0=[a,b,z][(j+2)%3];u1=[a,b,z][j];u2=[a,b,z][(j+1)%3];m1=mid[(j+2)%3];m2=mid[(j+1)%3];subs=[[u0,m1,m2],[m1,u1,u2],[m1,u2,m2]]
                for el in subs:tris[newid]=el;tp[newid]=21;replaced.append(newid);newid+=1
            radome=replaced
        x=np.array(x);nrad=sorted({q for eid in radome for q in tris[eid]});face=case['face_mm'];stack=laminate(c,face);shellmass=0.;beammass=0.;moment=np.zeros(3);radarea=0.;origstruct=read(ROOT/'wtc1_simulation_v8/output/aircraft_a01/verification_r2/airframe_mesh_SI.json');oldstructmass=origstruct['triangular_shells'];oldbeams=origstruct['equivalent_elastic_beams']
        for eid,el in tris.items():
            xyz=x[np.array(el)-1];area=np.linalg.norm(np.cross(xyz[1]-xyz[0],xyz[2]-xyz[0]))/2
            if tp[eid]==21:mass=area*.001*stack['areal_mass_kg_m2'];radarea+=area
            else:old=oldstructmass[eid-1];mass=area*old['thickness_m']*1000*(.00278 if old['material']=='skin_al2024_reference' else .00281)
            shellmass+=mass;moment+=mass*np.mean(xyz,axis=0)
        for eid,el in bms.items():
            old=oldbeams[eid-6539];length=np.linalg.norm(x[el[1]-1]-x[el[0]-1]);mass=length*old['area_m2']*1e6*.00281;beammass+=mass;moment+=mass*(x[el[0]-1]+x[el[1]-1])/2
        # Structural sums above in g; native /ADMAS is already g, facade remains exactly old.
        admasses={int(line[20:30]):float(line[:20]) for b in original if b[0].startswith('/ADMAS/') for line in b[2:]};admass=sum(admasses.values());moment+=sum((mass*x[nid-1] for nid,mass in admasses.items()),np.zeros(3));Mair=(shellmass+beammass+admass)*.001;Mfac=sum(oldmesh['facade_mass_kg_by_part'].values());Mtot=Mair+Mfac
        mesh={**oldmesh,'nodes_mm':x.tolist(),'aircraft_node_ids':sorted(air),'aircraft_node_count':len(air),'original_triangle_node_ids':[tris[eid] for eid in sorted(tris)],'aircraft_triangle_ids':sorted(tris),'aircraft_triangle_part_ids':[tp[eid] for eid in sorted(tris)],'original_beam_node_ids':[bms[eid] for eid in sorted(bms)],'aircraft_beam_ids':sorted(bms),'radome_element_ids':radome,'radome_node_ids':nrad,'expected_total_mass_kg':Mtot,'expected_aircraft_mass_kg':Mair,'expected_aircraft_CG_mm':(moment/(Mair*1000)).tolist(),'aircraft_contact_node_ids':sorted(set(oldmesh['aircraft_contact_node_ids']+air[len(oldair):]))}
        result=[];selected=[eid for eid,el in bms.items() if max(x[np.array(el)-1,0])<=8000]
        for card0 in original:
            card=card0.copy();key=card[0]
            if key=='/END':continue
            if key=='/BEGIN':card[1]=f'{n:<80}'
            if key=='/TITLE':card=[key,n]
            if key=='/NODE':card=[key]+[ii(i+1)+ff(*row) for i,row in enumerate(x)]
            if key.startswith('/SH3N/'):
                pid=int(key.split('/')[-1]);card=[key]+[ii(eid,*tris[eid]) for eid in sorted(tris) if tp[eid]==pid]
            if key.startswith('/BEAM/'):
                pid=int(key.split('/')[-1]);new=[]
                for line in card[1:]:
                    eid=int(line[:10])
                    if eid not in bms:continue
                    # Update local orientation only when geometry-only metallic control moves its endpoints.
                    p,q=bms[eid];delta=x[q-1]-x[p-1];e1=delta/np.linalg.norm(delta);oldv=np.array([float(line[40+j*20:60+j*20]) for j in range(3)]);e2=oldv-np.dot(oldv,e1)*e1
                    if np.linalg.norm(e2)<1e-8:e2=np.cross(e1,[0,0,1])
                    e2/=np.linalg.norm(e2);new.append(ii(eid,p,q,0)+ff(*e2))
                card=[key]+new
            if key=='/GRNOD/NODE/1':card=[key,card[1]]+[ii(*sorted(air)[i:i+10]) for i in range(0,len(air),10)]
            if key=='/GRNOD/NODE/1002':card=[key,card[1]]+[ii(*mesh['aircraft_contact_node_ids'][i:i+10]) for i in range(0,len(mesh['aircraft_contact_node_ids']),10)]
            if key.startswith('/INTER/') and not case['contact']:continue
            if key.startswith('/TH/INTER/') and not case['contact']:continue
            if key=='/INTER/TYPE7/1' and case['gap_mode']=='thickness':card[2]=card[2][:40]+ii(1)+card[2][50:];card[5]=card[5][:40]+ff(1)+card[5][60:]
            if key=='/TH/BEAM/41':card=card[:3]+[ii(e)+' '*10+f'B{e:<79}' for e in selected]
            result.extend(card)
        if case['composite']:
            result+=elastic_ortho(4,c['sandwich']['face'],c)+elastic_ortho(5,c['sandwich']['core'],c)
            for pid,mid,t in [(41,4,face),(42,5,c['sandwich']['core_thickness_mm']),(43,4,face)]:result += [f'/PROP/TYPE19/{pid}',f'radome_ply_{pid}',ii(mid)+ff(t,0)+ii(0,0,c['sandwich']['ply_integration_points'])+ff(90)]
            result+=['/PROP/TYPE51/21','reference_radome_sandwich',ii(12,4,2,2)+ff(1,0),ff(0,0,0,1e-20,1e-20),' '*20+ff(5/6)+' '*10+ii(2)+' '*10+ii(2)+ff(1),ff(1,0,0)+ii(0,0,0,0)]
            for pid in [41,42,43]:result+=[ii(pid)+ff(0,0,1,1),'']
            result+=['/PART/21','REFERENCE_RADOME',ii(21,4,0),'/SH3N/21']+[ii(eid,*tris[eid]) for eid in sorted(radome)]
            result+=['/TH/PART/32','RADOME_PART_DIAGNOSTIC',''.join(f'{v:>10}' for v in ['IE','KE','HE','PW']),ii(21)]
        if case['self_contact']:
            result+=['/GRNOD/NODE/1004','RADOME_SELF_SECONDARY']+[ii(*nrad[i:i+10]) for i in range(0,len(nrad),10)]+['/SURF/PART/1005','RADOME_SELF_MAIN',ii(21)]
            inter=next(b.copy() for b in original if b[0]=='/INTER/TYPE7/1');inter[0]='/INTER/TYPE7/2';inter[1]='RADOME_SELF_CONTACT';inter[2]=ii(1004,1005)+inter[2][20:];inter[5]=inter[5][:40]+ff(stack['thickness_mm'])+inter[5][60:];result+=inter+['/TH/INTER/12','SELF_CONTACT_RAW_HISTORY',''.join(f'{v:>10}' for v in ['FNX','FNY','FNZ']),ii(2)]
        result+=['/END'];(d/(n+'_0000.rad')).write_text('\n'.join(result)+'\n');dump(d/'mesh.json',mesh)
        engine=['/ANIM/DT',ff(0,c['execution']['animation_dt_ms']),'/ANIM/ELEM/ENER','/ANIM/VECT/VEL','/ANIM/VECT/DISP','/ANIM/SHELL/VONM','/ANIM/SHELL/EPSP/ALL','/ANIM/SHELL/TENS/STRESS/UPPER','/ANIM/SHELL/TENS/STRESS/LOWER','/ANIM/SHELL/TENS/STRAIN/UPPER','/ANIM/SHELL/TENS/STRAIN/LOWER']
        if case['composite']:engine+=['/ANIM/SHELL/TENS/STRESS/2','/ANIM/SHELL/TENS/STRAIN/2']
        engine+=['/DT',ff(case['dt_scale'],0),'/MON/ON','/PRINT/10/100',f'/RUN/{n}/1',ff(case['end_ms']),'/TFILE/4',ff(c['execution']['history_dt_ms']),'/VERS/2026'];(d/(n+'_0001.rad')).write_text('\n'.join(engine)+'\n')
        observe=['/ANIM/DT',ff(0,1e30),'/PRINT/-1/100',f'/RUN/{n}/2',ff(case['end_ms']+c['execution']['additional_observation_time_ms']),'/TFILE/4',ff(1e30),'/VERS/2026'];(d/(n+'_0002.rad')).write_text('\n'.join(observe)+'\n')
        unchanged=[k for k in ['/SHELL/31','/SHELL/32','/ADMAS/5/1','/BCS/1','/INIVEL/TRA/1'] if all(b for b in original if b[0]==k)]
        oldbs={b[0]:b for b in original};newbs={b[0]:b for b in blocks(result)};assert all(oldbs[k]==newbs[k] for k in unchanged)
        dump(d/'generation.json',{'created_utc':now(),'name':n,'case':case,'configuration_sha256':sha(CFG),'generator_sha256':sha(Path(__file__)),'mass_kg_aircraft':Mair,'mass_change_from_A04_kg':Mair-(oldmesh['expected_total_mass_kg']-Mfac),'radome_area_m2':radarea*1e-6,'laminate_reference':stack,'radome_elements':len(radome),'nose_nodes_changed':len(nose_nodes)-1,'removed_beams':removedbeams if case['composite'] else [],'beam_history_ids':selected,'all_sources_and_old_outputs_immutable':True,'facade_additional_masses_and_conditions_unchanged':True,'no_mass_top_up':True,'no_prescribed_trajectory':True,'fresh_intact_start':True,'source_root_bond_identified':False,'historical_radome_reconstructed':False,'orthotropy_direction':'global X projected onto each shell; unchanged by coplanar refinement'})
    dump(base/'harness_after_generation.json',harness());print({'built':revision,'cases':len(c['execution']['cases'])})

def run(revision,caseid):
    c=read(CFG);assert sha(CFG)==read(OUT/'declaration_guard.json')['sha256'];d=OUT/revision/caseid;g=read(d/'generation.json');n=g['name'];assert not (d/'starter.log').exists();e=c['execution'];env=os.environ.copy();env.update(RAD_CFG_PATH='C:/OpenRadioss/hm_cfg_files',RAD_H3D_PATH='C:/OpenRadioss/extlib/h3d/lib/win64',OPENRADIOSS_PATH='C:/OpenRadioss',OMP_NUM_THREADS='2',KMP_STACKSIZE='400m')
    if not execute(RUNTIME/'starter_win64.exe',['-i',n+'_0000.rad','-np','1'],d,'starter.log',e['starter_timeout_s'],env):print({'failed':'starter','case':caseid});return
    log=(d/'starter.log').read_text();warnings=int(re.findall(r'(\d+) WARNING\(S\)',log)[-1]);errors=int(re.findall(r'(\d+) ERROR\(S\)',log)[-1])
    if warnings or errors:print({'failed':'starter_gate','case':caseid,'warnings':warnings,'errors':errors});return
    normal=execute(RUNTIME/'engine_win64.exe',['-i',n+'_0001.rad'],d,'engine.log',e['engine_timeout_s'],env)
    if normal:
        pins={rel(p):sha(p) for p in d.iterdir() if p.is_file()};o=d/'observer';o.mkdir();shutil.copy2(d/(n+'_0002.rad'),o/(n+'_0002.rad'))
        for p in d.glob(n+'_0001_*.rst'):shutil.copy2(p,o/p.name)
        assert execute(RUNTIME/'engine_win64.exe',['-i',n+'_0002.rad'],o,'observer.log',60,env)
        changed=[p for p,h in pins.items() if sha(ROOT/p)!=h];dump(d/'observer_preservation.json',{'main_outputs_unchanged':not changed,'changed':changed});assert not changed
        assert execute(RUNTIME/'th_to_csv_win64.exe',[n+'T02'],o,'converter_T02.log',e['converter_timeout_s'],env)
    if (d/(n+'T01')).exists():assert execute(RUNTIME/'th_to_csv_win64.exe',[n+'T01'],d,'converter_T01.log',e['converter_timeout_s'],env)
    dump(d/'execution_summary.json',{'main_normal_termination':normal,'verified_end_possible':normal,'partial_data_only':not normal});print({'completed' if normal else 'partial':caseid})

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['initialize','build','run']);p.add_argument('--revision',default='r0');p.add_argument('--case',default='COMP_FREE');a=p.parse_args()
    if a.action=='initialize':initialize()
    elif a.action=='build':build(a.revision)
    else:run(a.revision,a.case)
