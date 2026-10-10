"""Read retained A18 shell fields directly, independently validate three converters."""
import struct,subprocess,time
from collections import defaultdict
import numpy as np
from run_aircraft_a19 import *
from audit_aircraft_a05 import vtk,histories

def fast(p):
    b=p.read_bytes();magic,tm=struct.unpack_from('>if',b,0);assert magic==0x542c;nn,nf,np_,nu,ne,nv,nt,nsk=struct.unpack_from('>8i',b,291);off=323+nsk*12
    def take(n,dt):
        nonlocal off
        q=np.frombuffer(b,dtype=dt,count=n,offset=off).copy();off+=n*np.dtype(dt).itemsize;return q
    X=take(nn*3,'>f4').astype(float).reshape(nn,3);conn=take(nf*4,'>i4').reshape(nf,4);alive=take(nf,'u1');off+=np_*54+nn*6
    names=[b[off+i*81:off+(i+1)*81].decode('ascii').rstrip('\x00 ') for i in range(nu+ne)];off+=(nu+ne)*81+nu*nn*4;scalar=take(ne*nf,'>f4').astype(float).reshape(ne,nf)
    vn=[b[off+i*81:off+(i+1)*81].decode('ascii').rstrip('\x00 ') for i in range(nv)];off+=nv*81;vec=take(nv*nn*3,'>f4').astype(float).reshape(nv,nn,3)
    tn=[b[off+i*81:off+(i+1)*81].decode('ascii').rstrip('\x00 ') for i in range(nt)];off+=nt*81;tens=take(nt*nf*3,'>f4').astype(float).reshape(nt,nf,3)
    em=take(nf,'>f4').astype(float);nm=take(nn,'>f4').astype(float);nid=take(nn,'>i4');eid=take(nf,'>i4');assert len(set(eid))==nf
    return {'time_ms':float(tm),'x':X,'conn':conn,'alive':alive,'scalar':dict(zip(names[nu:],scalar)),'vector':dict(zip(vn,vec)),'tensor':dict(zip(tn,tens)),'element_mass_g':em,'node_mass_g':nm,'nid':nid,'eid':eid}

def omega(offsets,velocity):
    A=np.array([[[0,r[2],-r[1]],[-r[2],0,r[0]],[r[1],-r[0],0]] for r in offsets]).reshape(-1,3)
    w,_,rank,_=np.linalg.lstsq(A,velocity.ravel(),rcond=1e-8);return w,rank,float(np.max(abs((A@w-velocity.ravel()))))

def main():
    guard();assert not (OUT/'cached_fragment_diagnostic.json').exists();start=time.perf_counter();g=read(SOURCE/'generation.json');m=read(SOURCE/'mesh.json');n=g['name'];files=sorted(p for p in SOURCE.glob(n+'A*') if re.fullmatch(re.escape(n)+r'A\d{3}',p.name))+sorted(p for p in (SOURCE/'observer').glob(n+'A*') if re.fullmatch(re.escape(n)+r'A\d{3}',p.name));eids=np.array(m['radome_element_ids']);nt=len(eids);ix0=None
    tri=np.array([t for eid,t in zip(m['aircraft_triangle_ids'],m['original_triangle_node_ids']) if eid in set(eids)])-1;trdict={eid:t for eid,t in zip(m['aircraft_triangle_ids'],m['original_triangle_node_ids'])};tri=np.array([trdict[int(e)] for e in eids])-1
    hosts={r['host']:r['dependent_nodes'] for r in g['new_RBE2']};x0=np.array(m['nodes_mm']);ref=x0[tri];a=ref[:,1]-ref[:,0];b=ref[:,2]-ref[:,0];cross0=np.cross(a,b);area0=np.linalg.norm(cross0,axis=1)*.5;norm0=cross0/(2*area0[:,None]);e1=a/np.linalg.norm(a,axis=1)[:,None];e2=np.cross(norm0,e1);B=np.zeros((nt,2,2));B[:,0,0]=np.linalg.norm(a,axis=1);B[:,0,1]=np.sum(b*e1,axis=1);B[:,1,1]=np.sum(b*e2,axis=1);Binv=np.linalg.inv(B)
    T=[];ener=[];AR=[];ST=[];ROT=[];OM=[];DM=[];CORE=[];proofs=[];rows=[];em0=None
    for k,p in enumerate(files):
        q=fast(p);tm=q['time_ms']
        if T and abs(tm-T[-1])<1e-6:continue
        order=np.argsort(q['nid']);assert np.array_equal(q['nid'][order],np.arange(1,len(x0)+1));X=q['x'][order];VV=q['vector']['Velocity'][order]
        ix={int(e):i for i,e in enumerate(q['eid'])};sel=np.array([ix[int(e)] for e in eids]);em=q['element_mass_g'][sel]
        if em0 is None:em0=em
        else:assert np.array_equal(em,em0)
        IE=q['scalar']['Specific Energy'][sel]*em*.001;D=np.stack([q['scalar'][s][sel] for s in q['scalar'] if s.startswith('DAMAGE')])[:3]
        if k in [0,65,len(files)-1]:
            z=vtk(subprocess.run([str(RUNTIME/'anim_to_vtk_win64.exe'),str(p)],capture_output=True,text=True,check=True,timeout=120).stdout);zi={int(e):i for i,e in enumerate(z['ELEMENT_ID']) if e>0};js=np.array([zi[int(e)] for e in eids]);zo=np.argsort(z['NODE_ID'])
            assert np.allclose(X,z['points'].reshape(-1,3)[zo],rtol=5e-6,atol=1e-6);assert np.allclose(VV,z['Velocity'].reshape(-1,3)[zo],rtol=5e-6,atol=1e-6);assert np.allclose(q['scalar']['Specific Energy'][sel],z['2DELEM_Specific_Energy'][js],rtol=5e-6,atol=1e-6)
            for s,zk in [('Stress (upper)','2DELEM_Stress_(upper)'),('Strain (upper)','2DELEM_Strain_(upper)'),('Stress (layer  2)','2DELEM_Stress_(layer__2)_'),('Strain (layer  2)','2DELEM_Strain_(layer__2)_')]:
                V=z[zk].reshape(-1,3,3)[js];target=np.column_stack([V[:,0,0],V[:,1,1],V[:,0,1]]);assert np.allclose(q['tensor'][s][sel],target,rtol=5e-6,atol=1e-6)
            proofs.append({'path':rel(p),'time_ms':tm,'all_requested_native_fields_vs_converter':True})
        xp=X[tri];edgeA=xp[:,1]-xp[:,0];edgeB=xp[:,2]-xp[:,0];cross=np.cross(edgeA,edgeB);area=np.linalg.norm(cross,axis=1)*.5;normal=cross/np.maximum(2*area[:,None],1e-30);F=np.stack([edgeA,edgeB],axis=2)@Binv;stretch=np.linalg.svd(F,compute_uv=False);angle=np.full((nt,3),np.nan);ws={};director={};rankbad=0;max_vel_fit=0.
        for host,deps in hosts.items():
            rr=X[np.array(deps)-1]-X[host-1];dr=VV[np.array(deps)-1]-VV[host-1];w,rank,err=omega(rr,dr);ws[host]=np.linalg.norm(w) if rank==3 else np.nan;rankbad+=rank<3;max_vel_fit=max(max_vel_fit,err)
            r0=x0[np.array(deps)-1]-x0[host-1];C=rr.T@r0;U,S,VT=np.linalg.svd(C)
            if S[1]>S[0]*1e-8:Q=U@np.diag([1,1,np.linalg.det(U@VT)])@VT;director[host]=Q
        for ie,tr in enumerate(tri+1):
            for j,host in enumerate(tr):
                if host in director:angle[ie,j]=np.degrees(np.arccos(np.clip(np.dot(director[host]@norm0[ie],normal[ie]),-1,1)))
        W=np.array([[ws.get(int(ni),np.nan) for ni in tr] for tr in tri+1]);worst=int(np.argmin(IE));rows.append({'time_ms':tm,'radome_sum_element_IE_J':float(IE.sum()),'negative_energy_elements':int(np.sum(IE<-.001)),'minimum_element_IE_J':float(IE[worst]),'worst_element_id':int(eids[worst]),'minimum_area_ratio':float(np.min(area/area0)),'maximum_principal_stretch':float(stretch.max()),'maximum_director_plane_angle_deg':float(np.nanmax(angle)),'maximum_reconstructed_angular_velocity_rad_ms':float(np.nanmax(W)),'rank_deficient_angular_hosts':int(rankbad),'maximum_offset_velocity_fit_error_m_s':max_vel_fit})
        T.append(tm);ener.append(IE);AR.append(area/area0);ST.append(stretch);ROT.append(angle);OM.append(W);DM.append(D);CORE.append(q['tensor']['Strain (layer  2)'][sel]);
        if len(T)%20==0:print({'cached_states_read':len(T),'time_ms':tm,'radome_IE_J':float(IE.sum())},flush=True)
    T=np.array(T);ener=np.array(ener);assert len(proofs)>=2;H=histories(SOURCE/(n+'T01.csv'));Ho=histories(SOURCE/'observer'/(n+'T02_recovered.csv'));key=next(k for k in H if k.startswith('REFERENCE_RADOME ') and k.strip().endswith(' IE'));TH=np.r_[H['time'],Ho['time'][0]];IEpart=np.r_[H[key],Ho[key][0]]*.001;sample=np.interp(T,TH,IEpart);err=ener.sum(axis=1)-sample
    worst=np.argsort(ener[-1])[:12];selected=[{'element_id':int(eids[j]),'final_IE_J':float(ener[-1,j]),'first_saved_negative_ms':float(T[np.flatnonzero(ener[:,j]<-.001)[0]]) if np.any(ener[:,j]<-.001) else None,'final_area_ratio':float(AR[-1][j]),'final_principal_stretches':ST[-1][j].tolist(),'final_director_angles_deg':[None if not np.isfinite(v) else float(v) for v in ROT[-1][j]],'final_angular_velocity_rad_ms':[None if not np.isfinite(v) else float(v) for v in OM[-1][j]],'final_damage_skin_core_skin':DM[-1][:,j].tolist(),'final_core_inplane_strain':CORE[-1][j].tolist(),'original_triangle_nodes':tri[j].tolist(),'initial_positions_mm':ref[j].tolist()} for j in worst]
    np.savez_compressed(OUT/'cached_radome_fields.npz',time_ms=T,element_ids=eids,element_mass_g=em0,element_IE_J=ener,part_IE_J=sample,area_ratio=np.array(AR),principal_stretches=np.array(ST),director_angles_deg=np.array(ROT),angular_velocity_rad_ms=np.array(OM),damage_skin_core_skin=np.array(DM),core_inplane_strain=np.array(CORE))
    v={'created_utc':now(),'read_seconds':time.perf_counter()-start,'old_solver_reruns':0,'native_frames_read':len(T),'native_element_reader_validation':proofs,'minimum_final_radome_element_IE_J':float(ener[-1].min()),'sum_final_native_element_IE_J':float(ener[-1].sum()),'final_native_part_IE_J':float(sample[-1]),'maximum_element_part_sum_error_J':float(np.max(abs(err))),'last_element_part_sum_error_J':float(err[-1]),'top12_negative_energy_fraction_of_total_negative':float(-ener[-1,worst].sum()/-ener[-1][ener[-1]<0].sum()),'largest_negative_elements':selected,'history':rows,'physical_defect_cause_identified':False,'no_negative_energy_accepted_as_physical':True,'note':'Geometry metrics and director rotation are diagnostics, not a calibrated core failure law. Rank-deficient angular velocities are missing, not filled.'};dump(OUT/'cached_fragment_diagnostic.json',v);print({k:v[k] for k in ['native_frames_read','sum_final_native_element_IE_J','final_native_part_IE_J','last_element_part_sum_error_J','top12_negative_energy_fraction_of_total_negative']},flush=True);print({'most_negative_elements':selected[:3]},flush=True)
if __name__=='__main__':main()
