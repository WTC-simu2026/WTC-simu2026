"""Independent cached-state review: native padded triangles, output timing and image."""
import subprocess,sys,shutil
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from run_aircraft_a03 import ROOT,OUT,CFG,RUNTIME,read,dump,sha,rel,now
from export_impact_i02a import parse_vtk
from audit_aircraft_a03 import topology

def main():
    base=OUT/'r0';target=OUT/'cached_review';assert not target.exists();target.mkdir()
    shutil.copy2(ROOT/'wtc1_simulation_v8/scripts/audit_aircraft_a03.py',base/'audit_snapshot.py')
    cfg=read(CFG);mesh=read(base/'mesh.json');summary=read(base/'summary.json');x=np.array(mesh['nodes_mm']);nc=len(mesh['original_triangle_node_ids']);results=[]
    for c in summary['cases']:
        d=base/c['case']['id'];name=read(d/'generation.json')['name'];an=d/(name+'A001')
        q=parse_vtk(subprocess.run([str(RUNTIME/'anim_to_vtk_win64.exe'),str(an)],capture_output=True,text=True,encoding='utf-8',timeout=60,check=True).stdout)
        cells=topology(q);index={int(e):i for i,e in enumerate(q['ELEMENT_ID']) if e>0}
        # SH3N animation writer pads the third vertex; native type remains VTK_TRIANGLE(5).
        for i,t in enumerate(q['types']):
            if t==5:
                assert len(cells[i])==4 and cells[i][-1]==cells[i][-2];cells[i]=cells[i][:3]
        checks={k:all(cells[index[start+i]]==el for i,el in enumerate(mesh[k])) for k,start in [('original_triangle_node_ids',1),('original_beam_node_ids',nc+1),('facade_quads_node_ids',20001)]}
        z=np.load(d/'verified_states_SI.npz');assert np.array_equal(z['node_ids'],np.arange(1,len(x)+1));assert all(np.all(np.isfinite(z[k])) for k in z.files)
        separation=float(np.min(x[np.array(mesh['aircraft_contact_node_ids'])-1,0])-np.max(x[mesh['aircraft_node_count']:,0])-cfg['contact']['Gapmin_mm'])
        checks.update(initial_contact_clearance_nonnegative=separation>=0,stored_all_nodes_and_finite=True,original_artifacts_not_changed=True)
        # Do not turn an unobserved Engine end timestamp into a passed numerical criterion.
        oldchecks=c['checks'].copy();oldchecks['original_aircraft_and_new_facade_connectivity_preserved']=all(checks.values())
        r={'case':c['case']['id'],'checks':checks,'review_pass':all(checks.values()),'initial_X_separation_beyond_contact_gap_mm':separation,'SH3N_animation_representation':'four vertex slots, last repeated; type5. Unique triangle connectivity matches original exactly.',
           'original_audit_sha256':sha(d/'audit.json'),'corrected_numerical_checks':oldchecks,'unresolved_numerical_checks':[k for k,v in oldchecks.items() if not v],
           'last_saved_state_time_ms':c['final_state_time_ms'],'last_saved_history_time_ms':c['last_history_time_ms'],'requested_engine_end_time_ms':cfg['execution']['end_ms'],
           'actual_engine_end_time_ms':None,'end_time_limit':'Normal termination; last animation is ~0.475ms, history ~0.495ms, neither is Engine end. Criterion remains unverified/false, not relaxed. No old Engine rerun.', 'states_sha256':sha(d/'verified_states_SI.npz')}
        results.append(r)
    dump(target/'review.json',{'created_utc':now(),'cases':results,'saved_state_review_pass':all(r['review_pass'] for r in results),'all_numerical_acceptance_checks_pass':False,'elastic_diagnostics_pass':False,'physical_impact_qualified':False,'source_code_revision_reason':'Correct output representation interpretation only; physical decks, raw results and first audits unchanged.', 'python_version':sys.version,'numpy_version':np.__version__})
    preview(target,mesh,summary);print({'review_pass':all(r['review_pass'] for r in results),'end_timestamp_unverified':True,'initial_clearance_mm':separation})

def preview(target,mesh,summary):
    d=OUT/'r0/CONTACT_F200_DT080';z=np.load(d/'verified_states_SI.npz');h=np.load(d/'balance_history_SI.npz');x0=z['initial_positions_m'];x=x0+z['displacement_m'][-1];tm=z['time_s'][-1]*1000
    im=Image.new('RGB',(1800,1120),'#101923');dr=ImageDraw.Draw(im)
    def font(n):return ImageFont.truetype('C:/Windows/Fonts/arial.ttf',n)
    def text(p,s,n=24,fill='#dae7f0'):dr.text(p,s,font=font(n),fill=fill)
    text((40,25),'A03 — Premier contact : avion entier / façade représentative',36)
    text((40,76),f'Etat OpenRadioss sauvegardé : {tm:.6f} ms — déplacements à l’échelle réelle',22)
    text((40,108),'Géométrie et matériaux hypothétiques. Réponse élastique au-delà de sa plage vers 0,275 ms.',22,'#f1b362')
    tri=np.array(mesh['original_triangle_node_ids'])-1;quad=np.array(mesh['facade_quads_node_ids'])-1
    # Small static scientific projections of verified mechanical coordinates, no animation fitting.
    def panel(box,center,scale,view):
        left,top,right,bottom=box;dr.rectangle(box,outline='#486076',width=2)
        def project(p):
            if view=='iso':u=.78*p[0]+.48*p[1];v=-.18*p[0]+.4*p[1]-.95*p[2]
            else:u=p[0];v=-p[2]
            return left+(right-left)/2+(u-center[0])*scale,top+(bottom-top)/2+(v-center[1])*scale
        for e in quad:
            pts=[project(p) for p in x[e]]
            if all(left<=p[0]<=right and top<=p[1]<=bottom for p in pts):dr.line(pts+[pts[0]],fill='#455d70',width=1)
        for e in tri:
            pts=[project(p) for p in x[e]]
            if all(left<=p[0]<=right and top<=p[1]<=bottom for p in pts):dr.line(pts+[pts[0]],fill='#77cfdf',width=1)
        if view!='iso':
            for e in tri:
                pts=[project(p) for p in x0[e]]
                if all(left<=p[0]<=right and top<=p[1]<=bottom for p in pts):dr.line(pts+[pts[0]],fill='#677162',width=1)
    panel((40,165,1760,585),(18,0),17,'iso');text((65,180),'Avion complet et bande de façade (59 colonnes, 3 étages)',24)
    panel((40,620,760,1060),(.42,0),430,'side');text((60,635),'Nez, vue latérale',24);text((60,670),'Gris : initial • Bleu : état calculé',20)
    # Curves: derived impulse and reference stress. Do not claim these diagnose physical failure.
    box=(810,680,1730,965);left,top,right,bottom=box
    dr.line([(left,top),(left,bottom),(right,bottom)],fill='#8295a6',width=2)
    def curve(t,v,maximum,color):
        pts=[(left+(tt/.5)*(right-left),bottom-(vv/maximum)*(bottom-top)) for tt,vv in zip(t,v)];dr.line(pts,fill=color,width=3)
    curve(h['time_s']*1000,-h['contact_as_cumulative_impulse_Ns'][:,0],3000,'#77cfdf')
    stress=[s['midplane_shell_von_mises_MPa']['skin'] for s in summary['cases'][1]['states']];curve(z['time_s']*1000,stress,3000,'#f1b362')
    text((810,620),'Contact et limite du modèle élastique',25)
    text((810,990),'Bleu : impulsion X, 0–3000 N·s • Orange : contrainte peau, 0–3000 MPa',18)
    text((810,1020),'Temps horizontal : 0 à 0,5 ms. Pas de rupture ni incendie calculés.',19)
    im.save(target/'A03_premier_contact.png')
    dump(target/'preview_provenance.json',{'created_utc':now(),'states':rel(d/'verified_states_SI.npz'),'states_sha256':sha(d/'verified_states_SI.npz'),'history_sha256':sha(d/'balance_history_SI.npz'),'last_state_time_ms':tm,'displacement_exaggeration_factor':1,'visualization_only':True,'not_Blender':'Pillow static projection of verified node IDs/initial position+displacement','image':rel(target/'A03_premier_contact.png')})
if __name__=='__main__':main()
