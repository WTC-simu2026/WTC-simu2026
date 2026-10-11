"""Read-only whole-nose conversion budget, retaining source geometry and failures."""
from run_aircraft_a31 import *
CFGGEOM=ROOT/'wtc1_simulation_v8/data/aircraft_a31_volume_geometry_preparation.json'
SOURCE=ROOT/'wtc1_simulation_v8/output/aircraft_a20/r0/CORE3D_TIED_20/mesh.json'
SIGNS=np.array([[-1,-1,-1],[1,-1,-1],[1,1,-1],[-1,1,-1],[-1,-1,1],[1,-1,1],[1,1,1],[-1,1,1]],float)

def integral(X):
    vol=0.;first=np.zeros(3);tensor=np.zeros((3,3));minimum=1e99
    for a in [-1/np.sqrt(3),1/np.sqrt(3)]:
        for b in [-1/np.sqrt(3),1/np.sqrt(3)]:
            for c in [-1/np.sqrt(3),1/np.sqrt(3)]:
                p=np.array([a,b,c]);N=np.prod(1+SIGNS*p,axis=1)/8;D=np.column_stack([SIGNS[:,k]*np.prod(1+SIGNS[:,[j for j in range(3) if j!=k]]*p[[j for j in range(3) if j!=k]],axis=1)/8 for k in range(3)]);det=float(np.linalg.det(X.T@D));minimum=min(minimum,det);point=N@X;vol+=det;first+=point*det;tensor+=(point@point*np.eye(3)-np.outer(point,point))*det
    return vol,first,tensor,minimum

def main():
    guard();dest=OUT/'whole_volume_geometry_preparation.json';assert not dest.exists() and not CFGGEOM.exists();pin=streamsha(SOURCE);m=read(SOURCE);X=np.array(m['nodes_mm']);rho=.00183
    c={'iteration':'AIRCRAFT-A31','declared_utc':now(),'seed':1102056,'random_draws':0,'source':rel(SOURCE),'source_sha256':pin,'purpose':'Before any insertion, map each existing skin quad to its real unchanged core face. Construct0.5mm physical volume toward its outer side; calculate source-volume, centroid, tensor and positive-Jacobian gates. Preserve source inputs, do not compensate density or thickness.',
       'mesh_scope':'1296skin quads,216actualfacets,one physical thickness cell for efficiency candidates; reference four thickness subdivisions remains separately qualified A29/A31. No native whole execution.',
       'material_frames':'source facet L,W,normal and90deg skin orientation -> rowsW,-L,normal; source constants unchanged. No global flat frame used on curved facets.',
       'acceptance':{'source_unchanged':True,'native_input_volume_relative':1e-8,'source_midplane_identity_mm':1e-8,'positive_all_Gauss_Jacobians':True,'orthonormal_frame_tolerance':1e-10},'new_connector_mass':None,'whole_insertion_ready':False}
    dump(CFGGEOM,c);dump(OUT/'volume_geometry_declaration_guard.json',{'created_utc':now(),'sha256':streamsha(CFGGEOM),'before_conversion':True});rows=[];hexa=[];totalV=0.;F=np.zeros(3);I=np.zeros((3,3));worst_mid=0.;minJ=1e99
    for quad in m['radome_skin_quads']:
        f=m['radome_facets'][quad['facet']-1];n=np.array(f['normal']);layers=f['layers'];low=quad['side']=='lo';mid_ids=layers[0 if low else 1];core_ids=layers[2 if low else 3];idx=[mid_ids.index(ni) for ni in quad['nodes']];inner_ids=[core_ids[j] for j in idx];inner=X[np.array(inner_ids)-1];outer=inner+(-.5 if low else .5)*n;H=np.vstack([outer,inner] if low else [inner,outer]);v,first,tensor,j=integral(H)
        reordered=False
        if j<=0:
            order=[0,3,2,1,4,7,6,5];H=H[order];inner_ids=[inner_ids[j] for j in [0,3,2,1]];v,first,tensor,j=integral(H);reordered=True
        frame=np.array([f['W'],(-np.array(f['L'])).tolist(),f['normal']]);mid=(inner+outer)*.5;err=float(abs(mid-X[np.array(quad['nodes'])-1]).max());worst_mid=max(worst_mid,err);minJ=min(minJ,j);totalV+=v;F+=rho*first;I+=rho*tensor;hexa.append(H)
        rows.append({'source_skin_element':quad['id'],'source_skin_part':quad['part'],'facet':quad['facet'],'side':quad['side'],'source_midplane_nodes':quad['nodes'],'unchanged_shared_core_face_nodes':inner_ids,'source_midplane_error_mm':err,'volume_mm3':v,'mass_g':rho*v,'minimum_Gauss_Jacobian_mm3':j,'positive_order_reversed':reordered,'material_frame_rows_global':frame.tolist(),'frame_pass':bool(np.allclose(frame@frame.T,np.eye(3),atol=1e-10,rtol=0) and abs(np.linalg.det(frame)-1)<1e-10)})
    targetV=sum(f['skin_volume_mm3'] for f in m['radome_facets']);mass=rho*totalV;center=F/mass;Icg=I-mass*(center@center*np.eye(3)-np.outer(center,center));np.savez_compressed(OUT/'candidate_volume_skin_hexahedra.npz',physical_hex_points_mm=np.array(hexa),part_ids=np.array([r['source_skin_part'] for r in rows]),source_element_ids=np.array([r['source_skin_element'] for r in rows]))
    checks={'source_unchanged':streamsha(SOURCE)==pin,'source_count':len(rows)==1296,'positive_Jacobians':minJ>0,'physical_source_volume':abs(totalV-targetV)<1e-8*targetV,'source_midplane_identity':worst_mid<1e-8,'curved_material_frames':all(r['frame_pass'] for r in rows)}
    dump(dest,{'created_utc':now(),'configuration_sha256':streamsha(CFGGEOM),'skin_rows':rows,'checks':checks,'geometry_budget_scope_pass':all(checks.values()),'physical_skin_volume_mm3':totalV,'source_input_skin_volume_mm3':targetV,'physical_skin_mass_g':mass,'source_input_skin_mass_g':rho*targetV,'physical_skin_CG_mm':center.tolist(),'continuous_physical_skin_I_origin_g_mm2':I.tolist(),'continuous_physical_skin_I_CG_g_mm2':Icg.tolist(),'worst_source_midplane_identity_mm':worst_mid,'minimum_Gauss_Jacobian_mm3':minJ,'core_and_other_aircraft_unchanged':True,'actual_whole_mass_not_remeasured':True,'whole_native_execution':False,'new_connector_mass_g':None,'whole_insertion_ready':False,'efficiency_candidate_not_yet_qualified':True,'objective1_complete':False});print({'volume_budget_scope_pass':all(checks.values()),'checks':checks,'skin_mass_g':mass,'source_mass_g':rho*targetV,'midplane_error_mm':worst_mid},flush=True)

if __name__=='__main__':main()
