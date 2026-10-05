"""Build a complete parametric aircraft, not an impact outcome fit or crash solver.

All dimensions SI; explicit shells/beams and a spatial mass quadrature are exported.
Mass still unresolved in OEW is inertial only; do not give it hidden stiffness.
"""
from __future__ import annotations
from pathlib import Path
from collections import defaultdict
from datetime import datetime, timezone
import argparse,csv,hashlib,json,math,platform,sys,time
import numpy as np
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[2]
CFG=ROOT/'wtc1_simulation_v8/data/aircraft_a01_predeclaration.json'
OUT=ROOT/'wtc1_simulation_v8/output/aircraft_a01'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v): p.write_text(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
def now(): return datetime.now(timezone.utc).isoformat()

class Airframe:
    def __init__(self,c,factor=1,skin=1):
        self.c=c;self.factor=factor;self.skin=skin;self.nodes=[];self.index={};self.shells=[];self.beams=[]
        self.particles=[];self.fuel_cells=[];self.skipped_degenerate_triangles=0
    def node(self,p):
        key=tuple(round(float(v),10) for v in p)
        if key not in self.index:self.index[key]=len(self.nodes);self.nodes.append(list(key))
        return self.index[key]
    def triangle(self,ids,part,t,material='skin_al2024_reference'):
        a=np.array([self.nodes[i] for i in ids]);area=float(np.linalg.norm(np.cross(a[1]-a[0],a[2]-a[0]))/2)
        if area<1e-10:self.skipped_degenerate_triangles+=1;return
        prop=self.c['materials'][material];m=area*t*prop['rho_kg_m3']
        self.shells.append({'nodes':ids,'part':part,'thickness_m':t,'material':material,'area_m2':area,'mass_kg':m})
        for w in [[2/3,1/6,1/6],[1/6,2/3,1/6],[1/6,1/6,2/3]]:
            self.particles.append((m/3,(np.array(w)@a).tolist(),part))
    def quad(self,ids,part,t,material='skin_al2024_reference'):
        self.triangle([ids[0],ids[1],ids[2]],part,t,material)
        self.triangle([ids[0],ids[2],ids[3]],part,t,material)
    def beam(self,a,b,part,area,I):
        if a==b:return
        p,q=np.array(self.nodes[a]),np.array(self.nodes[b]);length=float(np.linalg.norm(q-p));mat='internal_al7075_reference'
        m=length*area*self.c['materials'][mat]['rho_kg_m3']
        self.beams.append({'nodes':[a,b],'part':part,'material':mat,'area_m2':area,'Iyy_m4':I,'Izz_m4':I,'J_m4':2*I,
                           'length_m':length,'mass_kg':m,'orientation_reference':'exporter must derive local frame; no solver mapping yet'})
        for s in [0.5-0.5/math.sqrt(3),0.5+0.5/math.sqrt(3)]:self.particles.append((m/2,(p+s*(q-p)).tolist(),part))
    def nearest(self,p,ids):return min(ids,key=lambda i:sum((self.nodes[i][k]-p[k])**2 for k in range(3)))
    def attachment(self,a,b,part):
        h=self.c['structure_hypotheses'];self.beam(a,b,part,h['attachment_area_m2'],h['attachment_I_m4'])
    def stations(self,points,step):
        result=[]
        for a,b in zip(points[:-1],points[1:]):result+=np.linspace(a,b,math.ceil((b-a)/step)+1).tolist()[:-1]
        return result+[points[-1]]
    def fuselage(self):
        c=self.c;h=c['structure_hypotheses'];f=self.factor;ns=c['mesh']['fuselage_circumference_nodes']*f
        xr=h['fuselage_stations_x_radius_factor'];base=self.stations([a[0] for a in xr],h['fuselage_frame_spacing_m'])
        xs=[x for a,b in zip(base[:-1],base[1:]) for x in np.linspace(a,b,f+1).tolist()[:-1]]+[base[-1]]
        ry=c['envelope']['fuselage_width']['value_m']/2;rz=c['envelope']['fuselage_height']['value_m']/2
        rings=[]
        for x in xs:
            r=float(np.interp(x,[a[0] for a in xr],[a[1] for a in xr]));rings.append([self.node([x,ry*r*math.cos(t),rz*r*math.sin(t)]) for t in np.arange(ns)*2*math.pi/ns])
        for i in range(len(xs)-1):
            for j in range(ns):
                self.quad([rings[i][j],rings[i+1][j],rings[i+1][(j+1)%ns],rings[i][(j+1)%ns]],'fuselage_skin',h['fuselage_skin_m']*self.skin)
                # Refinement adds shell nodes, not extra physical stringers.
                if j%f==0:self.beam(rings[i][j],rings[i+1][j],'fuselage_stringers',h['stringer_area_m2'],h['stringer_I_m4'])
        for i in range(0,len(rings),f):
            for j in range(ns):self.beam(rings[i][j],rings[i][(j+1)%ns],'fuselage_frames',h['frame_area_m2'],h['frame_I_m4'])
        for i in [0,len(rings)-1]:
            center=self.node([xs[i],0,0])
            for j in range(ns):self.triangle([center,rings[i][j],rings[i][(j+1)%ns]],'fuselage_caps',h['fuselage_skin_m']*self.skin)
        self.fus_ids={k for r in rings for k in r};self.fus_ids.update([self.index[(round(xs[0],10),0.,0.)],self.index[(round(xs[-1],10),0.,0.)]])
    def wing_shape(self,y,ch):
        h=self.c['structure_hypotheses'];tab=self.c['CAD_interpretation']['wing_stations_m'];ay=abs(y)
        le,te,tc=[float(np.interp(ay,[a[0] for a in tab],[a[k] for a in tab])) for k in [1,2,3]]
        chord=te-le;z=h['wing_base_z_m']+max(ay-self.c['envelope']['fuselage_width']['value_m']/2,0)*math.tan(math.radians(h['wing_dihedral_deg']))
        return le+ch*chord,z,0.5*tc*chord*math.sin(math.pi*ch),chord
    def wings(self):
        c=self.c;h=c['structure_hypotheses'];f=self.factor;step=c['mesh']['wing_span_max_step_m']/f
        base=self.stations([a[0] for a in c['CAD_interpretation']['wing_stations_m']],c['mesh']['wing_span_max_step_m'])
        stations=[x for a,b in zip(base[:-1],base[1:]) for x in np.linspace(a,b,f+1).tolist()[:-1]]+[base[-1]]
        ys=[-y for y in stations[1:][::-1]]+stations
        fractions=self.stations(c['mesh']['chord_fractions'],0.20/f)
        grid=[];self.wing_ids=set()
        for y in ys:
            row=[]
            for ch in fractions:
                x,z,t,_=self.wing_shape(y,ch);pair=[self.node([x,y,z+t]),self.node([x,y,z-t])];row.append(pair);self.wing_ids.update(pair)
            grid.append(row)
        for i in range(len(ys)-1):
            for j in range(len(fractions)-1):
                for k in [0,1]:
                    self.quad([grid[i][j][k],grid[i+1][j][k],grid[i+1][j+1][k],grid[i][j+1][k]],'wing_skin',h['wing_skin_m']*self.skin)
            for ch in h['spar_chord_fractions']:
                j=next(j for j,v in enumerate(fractions) if abs(v-ch)<1e-10)
                self.quad([grid[i][j][0],grid[i+1][j][0],grid[i+1][j][1],grid[i][j][1]],'wing_spars',h['spar_and_rib_web_m'],'internal_al7075_reference')
            for ch in [.1,.25,.45,.65,.85]:
                j=next(j for j,v in enumerate(fractions) if abs(v-ch)<1e-10)
                for k in [0,1]:self.beam(grid[i][j][k],grid[i+1][j][k],'wing_stringers',h['wing_stringer_area_m2'],h['wing_stringer_I_m4'])
        # Actual rib count and position hypothesis remains fixed with refinement.
        base=self.stations([a[0] for a in c['CAD_interpretation']['wing_stations_m']],c['mesh']['wing_span_max_step_m'])
        for i,y in enumerate(ys):
            if not any(abs(abs(y)-b)<1e-9 for b in base):continue
            for j in range(len(fractions)-1):self.quad([grid[i][j][0],grid[i][j+1][0],grid[i][j+1][1],grid[i][j][1]],'wing_ribs',h['spar_and_rib_web_m'],'internal_al7075_reference')
        # Explicit imperfectly known carry-through attachments. They are elastic beams, no failure law.
        for sign in [-1,1]:
            y=sign*c['envelope']['fuselage_width']['value_m']/2
            for ch in h['spar_chord_fractions']:
                x,z,t,_=self.wing_shape(y,ch)
                for zz in [z+t,z-t]:
                    a=self.nearest([x,y,zz],self.wing_ids);b=self.nearest(self.nodes[a],self.fus_ids);self.attachment(a,b,'wing_fuselage_attachments')
        # Eight-point volume quadrature in each symmetric bay, with physical volume weights.
        limit=c['envelope']['span']['value_m']*.5*.75
        tankys=[y for y in ys if abs(y)<limit]+[-limit,limit];tankys=sorted(set(tankys))
        a,b=h['spar_chord_fractions']
        for y0,y1 in zip(tankys[:-1],tankys[1:]):
            for gy in [-1/math.sqrt(3),1/math.sqrt(3)]:
                y=(y0+y1)/2+(y1-y0)*gy/2
                for gc in [-1/math.sqrt(3),1/math.sqrt(3)]:
                    ch=(a+b)/2+(b-a)*gc/2;x,z,t,chord=self.wing_shape(y,ch)
                    for gz in [-1/math.sqrt(3),1/math.sqrt(3)]:
                        v=(y1-y0)*(b-a)*chord*2*t/8
                        self.fuel_cells.append((v,[x,y,z+t*gz],'fuel_center' if abs(y)<2.5146 else 'fuel_wings'))
    def tail(self):
        c=self.c;h=c['structure_hypotheses'];f=self.factor
        root=h['tail_root_LE_TE_x_m'];tip=h['tail_tip_LE_TE_x_m'];span=c['envelope']['horizontal_tail_span']['value_m']/2
        self.tail_ids=set()
        for vertical in [False,True]:
            signs=[1] if vertical else [-1,1]
            length=h['vertical_tail_height_m'] if vertical else span
            lete0=h['vertical_tail_root_LE_TE_x_m'] if vertical else root
            lete1=h['vertical_tail_tip_LE_TE_x_m'] if vertical else tip
            for sign in signs:
                rows=[]
                for s in np.linspace(0,1,math.ceil(length*f)+1):
                    le,te=[lete0[k]+s*(lete1[k]-lete0[k]) for k in [0,1]];r=[]
                    for ch in [0,.25,.65,1]:
                        x=le+ch*(te-le);t=.5*h['tail_tc']*(te-le)*math.sin(math.pi*ch)
                        if vertical:p=[self.node([x,t,2.5+s*length]),self.node([x,-t,2.5+s*length])]
                        else:p=[self.node([x,sign*s*length,h['tail_z_m']+t]),self.node([x,sign*s*length,h['tail_z_m']-t])]
                        r.append(p);self.tail_ids.update(p)
                    rows.append(r)
                part='vertical_tail' if vertical else 'horizontal_tail'
                for i in range(len(rows)-1):
                    for j in range(3):
                        for k in [0,1]:self.quad([rows[i][j][k],rows[i+1][j][k],rows[i+1][j+1][k],rows[i][j+1][k]],part,h['tail_skin_m']*self.skin)
                    for j in [1,2]:self.quad([rows[i][j][0],rows[i+1][j][0],rows[i+1][j][1],rows[i][j][1]],part+'_spars',h['spar_and_rib_web_m'],'internal_al7075_reference')
                for r in [rows[0],rows[-1]]:
                    for j in range(3):self.quad([r[j][0],r[j+1][0],r[j+1][1],r[j][1]],part+'_caps',h['tail_skin_m']*self.skin)
                for j in [1,2]:
                    for k in [0,1]:
                        a=rows[0][j][k];self.attachment(a,self.nearest(self.nodes[a],self.fus_ids),part+'_attachments')
    def engines(self):
        c=self.c;h=c['structure_hypotheses'];self.engine_centers=[]
        x=c['envelope']['GE_engine_front_x']['value_m']+c['envelope']['CF6_80A_length']['value_m']/2
        for sign in [-1,1]:
            p=[x,sign*c['envelope']['engine_y']['value_m'],h['engine_center_z_m']];a=self.node(p);self.engine_centers.append(p)
            for ch in h['spar_chord_fractions']:
                xx,z,t,_=self.wing_shape(p[1],ch);b=self.nearest([xx,p[1],z-t],self.wing_ids);self.attachment(a,b,'engine_pylons')
    def build(self):self.fuselage();self.wings();self.tail();self.engines();return self
    def export(self,p):
        dump(p,{'iteration':'AIRCRAFT-A01','units':self.c['units'],'nodes_m':self.nodes,'triangular_shells':self.shells,
            'equivalent_elastic_beams':self.beams,'engine_centers_m':self.engine_centers,'materials':self.c['materials'],
            'solver_ready':False,'mass_mapping_to_solver_validated':False,'beam_local_orientation_export_pending':True,
            'assumption':'intact bonded elastic topology; strengths/fracture/engine internal behavior missing'})
    def topology(self):
        parent=list(range(len(self.nodes)))
        def find(i):
            while i!=parent[i]:parent[i]=parent[parent[i]];i=parent[i]
            return i
        for row in self.shells+self.beams:
            for i in row['nodes'][1:]:parent[find(i)]=find(row['nodes'][0])
        return len(set(find(i) for i in range(len(parent))))

def box(m,lo,hi,part):
    lo,hi=np.array(lo),np.array(hi);points=[]
    for a in [-1,1]:
        for b in [-1,1]:
            for d in [-1,1]:points.append((m/8,((lo+hi)/2+(hi-lo)/2*np.array([a,b,d])/math.sqrt(3)).tolist(),part))
    return points
def spatial_mass(model,case):
    c=model.c;h=c['structure_hypotheses'];mh=c['mass_hypotheses'];p=list(model.particles)
    structure=sum(v[0] for v in p);eng=mh['engine_equivalent_kg_each'];oew=mh['OEW_reference']['converted_kg']
    rest=oew-structure-2*eng
    assert rest>=0,('Negative OEW residual',case['id'],rest)
    length=c['envelope']['CF6_80A_length']['value_m'];rad=h['engine_equivalent_radius_m']
    for center in model.engine_centers:
        for s in [-1,1]:
            for theta in np.arange(8)*math.pi/4:
                q=[center[0]+s*length/(2*math.sqrt(3)),center[1]+rad/math.sqrt(2)*math.cos(theta),center[2]+rad/math.sqrt(2)*math.sin(theta)]
                p.append((eng/16,q,'engine_equivalent'))
    sh=case['unresolved_x_shift_m'];p+=box(rest,[6+sh,-2,-1.5],[39+sh,2,1.5],'unresolved_OEW')
    p+=box(case['payload_kg'],[7,-2,.5],[37,2,1.7],'payload')
    volume=sum(v[0] for v in model.fuel_cells);fuel=case['fuel_kg'];assert fuel<=volume*mh['fuel_density_kg_m3'],('Tank overfill',case['id'],fuel,volume)
    for v,q,part in model.fuel_cells:p.append((fuel*v/volume,q,part))
    m=np.array([a[0] for a in p]);q=np.array([a[1] for a in p]);total=float(m.sum());cg=m@q/total;d=q-cg
    inertia=np.eye(3)*float(m@(d*d).sum(axis=1))-np.einsum('n,ni,nj->ij',m,d,d)
    ledger=defaultdict(float)
    for mass,_,part in p:ledger[part]+=mass
    return p,{'case':case['id'],'structure_mass_kg':structure,'engine_mass_kg':2*eng,'unresolved_OEW_mass_kg':rest,'unresolved_OEW_fraction':rest/oew,
        'OEW_kg':oew,'fuel_kg':fuel,'payload_kg':case['payload_kg'],'total_kg':total,'CG_m':cg.tolist(),'inertia_CG_kg_m2':inertia.tolist(),
        'inertia_eigenvalues_kg_m2':np.linalg.eigvalsh(inertia).tolist(),'mass_ledger_kg':dict(ledger),
        'geometric_tank_volume_m3':volume,'geometric_tank_capacity_kg':volume*mh['fuel_density_kg_m3'],'tank_uniform_fill_fraction':fuel/(volume*mh['fuel_density_kg_m3']),
        'quadrature_particles':len(p),'topology_components':model.topology(),'nodes':len(model.nodes),'shells':len(model.shells),'beams':len(model.beams),
        'minimum_shell_area_m2':min(a['area_m2'] for a in model.shells),'degenerate_triangles_not_exported':model.skipped_degenerate_triangles,
        'mass_relative_error':abs(total-(oew+fuel+case['payload_kg']))/(oew+fuel+case['payload_kg']),
        'energy_if_uniform_translation_200_m_s_J':.5*total*200**2,'note_speed':'round-number inertial illustration, not assigned flight11 speed'}

def preview(model,summary):
    im=Image.new('RGB',(1600,1060),'#f5f7fa');d=ImageDraw.Draw(im)
    fontpath=Path('C:/Windows/Fonts/segoeui.ttf')
    font=lambda n:ImageFont.truetype(str(fontpath),n) if fontpath.exists() else ImageFont.load_default()
    d.text((35,20),'Boeing 767-200ER - assemblage parametrique AIRCRAFT-A01',font=font(30),fill='#132945')
    d.text((35,62),'Geometrie complete et masses explicites | Structure interne hypothetique | Aucun impact calcule',font=font(20),fill='#405b70')
    cols={'wing_skin':'#6c9ed0','fuselage_skin':'#acbbc8','horizontal_tail':'#7498af','vertical_tail':'#aebfce'}
    def project(p,panel):
        x,y,z=p
        if panel==0:return 50+x*29,430-y*11
        # Simple fixed orthographic oblique projection, not an animation state.
        return 65+x*23-y*8,940+y*6-z*17-x*2.6
    for panel in [0,1]:
        for row in model.shells:
            if row['part'] not in cols:continue
            v=[project(model.nodes[k],panel) for k in row['nodes']];d.polygon(v,fill=cols[row['part']])
        for row in model.beams:
            if row['part'] in ['wing_stringers','wing_fuselage_attachments','engine_pylons']:
                d.line([project(model.nodes[k],panel) for k in row['nodes']],fill='#304866',width=1)
        for x,y,z in model.engine_centers:
            x1,y1=project([x,y,z],panel);d.ellipse((x1-42,y1-16,x1+42,y1+16),fill='#ba7454',outline='#734b38',width=2)
    d.text((40,140),'Vue en plan - dimensions Boeing',font=font(22),fill='#132945')
    d.text((35,715),'Vue oblique - discretisation / liaisons equivalentes',font=font(22),fill='#132945')
    d.rounded_rectangle((1140,750,1555,1015),12,fill='white',outline='#bacbd6')
    text=[f"Masse totale : {summary['total_kg']/1000:.2f} t",f"Structure explicite : {summary['structure_mass_kg']/1000:.2f} t",
          f"Vide non resolu : {summary['unresolved_OEW_mass_kg']/1000:.2f} t",'2 moteurs equivalents : 9.00 t','Carburant / charge : 30.00 / 10.00 t',
          f"Longueur / envergure : 48.514 / 47.574 m",f"CG longitudinal : {summary['CG_m'][0]:.3f} m"]
    for i,t in enumerate(text):d.text((1155,768+32*i),t,font=font(17),fill='#23394c')
    im.save(OUT/'B767_assemblage_A01.png')
    # Plain OBJ is a durable complete mesh artifact; original third-party CAD is not embedded.
    with (OUT/'B767_airframe_A01.obj').open('w',encoding='utf-8',newline='\n') as f:
        f.write('# AIRCRAFT-A01 own parametric mesh. SI m. Not impact-qualified.\n')
        for p in model.nodes:f.write('v '+' '.join(f'{v:.10g}' for v in p)+'\n')
        last=None
        for row in model.shells:
            if row['part']!=last:last=row['part'];f.write('g '+last+'\n')
            f.write('f '+' '.join(str(i+1) for i in row['nodes'])+'\n')
        for row in model.beams:f.write('l '+' '.join(str(i+1) for i in row['nodes'])+'\n')

def build():
    start=time.perf_counter();c=json.loads(CFG.read_text(encoding='utf-8'));guard=json.loads((OUT/'declaration_guard.json').read_text())
    assert sha(CFG)==guard['sha256'] and not (OUT/'summary.json').exists()
    cases=[];all_checks={};nominal=None;particle_count=0
    for case in c['cases']:
        model=Airframe(c,skin=case['skin_factor']).build();p,s=spatial_mass(model,case);cases.append(s)
        checks={'mass_conserved':s['mass_relative_error']<c['predeclared_acceptance']['mass_relative_error'],
                'bilateral_mass':abs(s['CG_m'][1])<c['predeclared_acceptance']['bilateral_CG_y_abs_m'],
                'connected_topology':s['topology_components']==1,'positive_inertia':min(s['inertia_eigenvalues_kg_m2'])>0,
                'nonnegative_unresolved_mass':s['unresolved_OEW_mass_kg']>=0,'no_tank_overfill':s['tank_uniform_fill_fraction']<=1,
                'nondegenerate_shells':s['minimum_shell_area_m2']>c['predeclared_acceptance']['minimum_shell_area_m2']}
        all_checks[case['id']]=checks
        if case['id']=='NOMINAL':
            nominal=s;model.export(OUT/'airframe_mesh_SI.json');preview(model,s)
            with (OUT/'mass_quadrature_SI.csv').open('w',encoding='utf-8',newline='') as f:
                w=csv.writer(f);w.writerow(['mass_kg','x_m','y_m','z_m','component']);w.writerows([[m,*q,part] for m,q,part in p])
    fine=Airframe(c,factor=c['mesh']['refinement_factor']).build();_,fs=spatial_mass(fine,c['cases'][0]);dump(OUT/'mesh_refinement.json',fs)
    dm=abs(fs['structure_mass_kg']-nominal['structure_mass_kg'])/fs['structure_mass_kg']
    di=float(np.linalg.norm(np.array(fs['inertia_CG_kg_m2'])-np.array(nominal['inertia_CG_kg_m2']))/np.linalg.norm(fs['inertia_CG_kg_m2']))
    # Refining the mesh must not multiply physical frames/stringers; declared rib stations fixed.
    all_checks['refinement']={'structure_mass_difference':dm<.02,'inertia_difference':di<.02,'fine_topology_connected':fs['topology_components']==1}
    dump(OUT/'cases.json',cases)
    result={'iteration':'AIRCRAFT-A01','created_utc':now(),'nominal':nominal,'cases_count':len(cases),'cases':cases,
        'declared_checks':all_checks,'all_declared_checks_pass':all(all(v.values()) for v in all_checks.values()),
        'checks_total':sum(len(v) for v in all_checks.values()),'checks_passed':sum(sum(v.values()) for v in all_checks.values()),
        'coarse_fine_structure_mass_relative_difference':dm,'coarse_fine_inertia_relative_norm_difference':di,
        'runtime_seconds':time.perf_counter()-start,'software':{'python':sys.version,'numpy':np.__version__,'platform':platform.platform()},
        'solver_jobs':0,'old_solver_rerun':False,'NIST_results_used_as_target':False,
        'mesh_delivery_verified':True,'whole_aircraft_mass_mapping_to_solver_validated':False,
        'whole_aircraft_deformation_qualified':False,'aircraft_impact_qualified':False,'real_collapse_qualified':False,
        'scope':'Geometric assembly, explicit intact elastic topology and conditional spatial mass/inertia bookkeeping; no full dynamics or damage prediction',
        'next_iteration':'AIRCRAFT-A02'}
    dump(OUT/'summary.json',result)
    print(json.dumps({k:result[k] for k in ['iteration','cases_count','checks_passed','checks_total','all_declared_checks_pass','coarse_fine_structure_mass_relative_difference','coarse_fine_inertia_relative_norm_difference','runtime_seconds']},indent=2));print(json.dumps(nominal,indent=2))
    if not result['all_declared_checks_pass']:raise SystemExit('Declared check failed; retain result, do not register as completed')

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['build']);args=ap.parse_args();build()
