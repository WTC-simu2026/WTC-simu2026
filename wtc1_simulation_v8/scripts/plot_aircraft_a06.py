"""Static scientific figure made only from saved native states and work histories."""
from PIL import Image,ImageDraw,ImageFont
import numpy as np
from run_aircraft_a06 import ROOT,OUT,PREV,read,dump,rel,sha,now
def main():
    assert not (OUT/'summary_aircraft_a06.png').exists();s=read(OUT/'summary.json');im=Image.new('RGB',(1600,1210),'#f7f9fc');dr=ImageDraw.Draw(im)
    def font(n,b=False):return ImageFont.truetype('C:/Windows/Fonts/'+('arialbd.ttf' if b else 'arial.ttf'),n)
    def txt(x,y,v,n=21,color='#172a40',bold=False):dr.text((x,y),v,font=font(n,bold),fill=color)
    def plot(box,xlim,ylim,xlabel,ylabel):
        x0,y0,x1,y1=box;dr.rectangle(box,fill='white',outline='#b9c6d2')
        def xy(p):return(x0+(p[0]-xlim[0])/(xlim[1]-xlim[0])*(x1-x0),y1-(p[1]-ylim[0])/(ylim[1]-ylim[0])*(y1-y0))
        for x in np.linspace(*xlim,5):u,v=xy((x,ylim[0]));dr.line((u,y0,u,y1),fill='#e6ecf2');txt(u-14,y1+6,f'{x:g}',17)
        for y in np.linspace(*ylim,5):u,v=xy((xlim[0],y));dr.line((x0,v,x1,v),fill='#e6ecf2');txt(x0-58,v-9,f'{y:g}',17)
        txt(x0,y0-27,ylabel,18);txt((x0+x1)/2-65,y1+31,xlabel,18);return xy
    def curve(mp,x,y,col,w=3):dr.line([mp(p) for p in zip(x,y)],fill=col,width=w)
    txt(55,25,'AIRCRAFT-A06 — avion entier et énergie de rupture du nez',30,bold=True)
    txt(55,70,'États mécaniques sauvegardés • 4 départs intacts de l’avion • rupture limitée aux témoins',21)
    d=OUT/'r1/ZERO_DM';m=read(d/'mesh.json');z=np.load(d/'verified_states_SI.npz');xf=z['initial_positions_m']+z['displacement_m'][-1];mp=plot((100,150,1490,410),(-1,50),(-25,25),'X (m)','Y (m)')
    for el in m['original_triangle_node_ids']:
        p=[mp(xf[n-1,[0,1]]) for n in el];dr.line(p+[p[0]],fill='#3b718d')
    u=mp((-.05,0))[0];dr.line((u,150,u,410),fill='#ad4343',width=3)
    txt(145,160,f'Avion à {z["time_s"][-1]*1000:.6f} ms — déplacements ×1 ; plan initial de façade rouge',20)
    txt(100,472,'Le radôme reste élastique dans ces contrôles ; sa résistance est dépassée.',22,bold=True)
    a=plot((100,570,760,900),(0,2),(-90,10),'temps (ms)','résidu du bilan (kJ)')
    old=PREV/read(PREV/'case_selection.json')['case_directories']['COMP_SELF'];pins=[old/'balance_history_SI.npz',d/'balance_history_SI.npz']
    for p,col in [(pins[0],'#a3a6b0'),(pins[1],'#167da6')]:b=np.load(p);curve(a,b['time_s']*1000,b['energy_residual_J']/1000,col)
    txt(100,520,'A05 gris / A06 sans viscosité par défaut bleu',20,bold=True)
    txt(100,968,'Le déficit reste proche de 78 kJ à 2 ms.',21)
    b=plot((920,570,1490,900),(0,.085),(0,1700),'déformation logarithmique','contrainte (MPa)')
    w=OUT/'m1/MONO_L10';q=np.load(w/'saved_monotone_SI.npz');t=q['force_time_s'];eps=np.interp(t,q['time_s'],q['log_axial_strain']);curve(b,eps,q['force_equivalent_axial_stress_MPa'],'#167da6',3)
    ev=np.max(np.linalg.eigvalsh(q['effective_stress_elemental_MPa'][:,:,:2,:2]),axis=(1,2));ee=np.interp(q['animation_time_s'],q['time_s'],q['log_axial_strain']);mask=ee<=.08;curve(b,ee[mask],ev[mask],'#d87e22',3)
    dr.line((b((0,450)),b((.085,450))),fill='#ad4343',width=2)
    txt(920,520,'Témoin 10 mm : effort bleu / sortie effective orange',19,bold=True)
    txt(920,968,'La sortie de contrainte conserve la valeur effective.',20)
    mo=read(OUT/'monotone_review.json');txt(55,1030,'Même G entré : 50 kJ/m² ; travail total des faces par surface estimée :',22,bold=True)
    vals=[r['total_face_work_per_candidate_area_N_mm'] for r in mo['cases']];txt(55,1070,f'10 mm → {vals[0]:.1f} ; 20 mm → {vals[1]:.1f} ; 500 mm → {vals[2]:.1f} kJ/m².',24)
    txt(55,1116,'Cette loi n’est pas transférée à l’avion : énergie de fracture et sensibilité spatiale non qualifiées.',21,bold=True)
    txt(55,1157,'Conditions propres au modèle ; moteurs sans contact géométrique ; aucun résultat historique imposé.',20)
    dst=OUT/'summary_aircraft_a06.png';im.save(dst)
    inp=pins+[d/'verified_states_SI.npz',d/'mesh.json',w/'saved_monotone_SI.npz',OUT/'monotone_review.json',OUT/'summary.json']
    dump(OUT/'figure_provenance.json',{'created_utc':now(),'figure':rel(dst),'sha256':sha(dst),'inputs':[{'path':rel(p),'sha256':sha(p)} for p in inp],'displacement_scale':1,'facade_line_initial_only':True,'effective_stress_output_not_resisting_stress':True,'face_work_area_is_candidate_characteristic_length':True,'not_Blender_or_historical_reconstruction':True})
if __name__=='__main__':main()
