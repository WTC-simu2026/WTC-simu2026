"""Static scientific figure drawn solely from saved mechanical states/histories."""
from PIL import Image,ImageDraw,ImageFont
import numpy as np
from run_aircraft_a05 import ROOT,OUT,read,sha,dump,rel,now

def main():
    review=read(OUT/'cached_review/review.json');paths={k:OUT/v for k,v in read(OUT/'case_selection.json')['case_directories'].items()};im=Image.new('RGB',(1600,1100),'#f7f9fc');dr=ImageDraw.Draw(im)
    def font(n,bold=False):return ImageFont.truetype('C:/Windows/Fonts/'+('arialbd.ttf' if bold else 'arial.ttf'),n)
    def txt(x,y,s,n=22,c='#172a40',b=False):dr.text((x,y),s,font=font(n,b),fill=c)
    def plot(box,xlim,ylim,xlabel,ylabel):
        x0,y0,x1,y1=box;dr.rectangle(box,fill='white',outline='#b9c6d2');
        def mapxy(p):return (x0+(p[0]-xlim[0])/(xlim[1]-xlim[0])*(x1-x0),y1-(p[1]-ylim[0])/(ylim[1]-ylim[0])*(y1-y0))
        for x in np.linspace(*xlim,5):
            u,v=mapxy((x,ylim[0]));dr.line((u,y0,u,y1),fill='#e6ecf2');txt(u-16,y1+8,f'{x:g}',17)
        for y in np.linspace(*ylim,5):
            u,v=mapxy((xlim[0],y));dr.line((x0,v,x1,v),fill='#e6ecf2');txt(x0-55,v-10,f'{y:g}',17)
        txt((x0+x1)/2-45,y1+35,xlabel,18);txt(x0,y0-28,ylabel,18);return mapxy
    def lines(x,tri,mapxy,axes,color,width=1):
        for el in tri:
            p=[mapxy(x[n-1,axes]) for n in el];dr.line(p+[p[0]],fill=color,width=width)
    txt(55,28,'AIRCRAFT-A05 — avion entier, nez arrondi et sandwich de référence',30,b=True)
    txt(55,72,'États OpenRadioss sauvegardés • déplacements ×1 • conditions de test propres au modèle',21)
    d=paths['COMP_SELF'];m=read(d/'mesh.json');z=np.load(d/'verified_states_SI.npz');x=z['initial_positions_m'];xf=x+z['displacement_m'][-1];t=z['time_s'][-1]*1000
    mp=plot((100,150,1490,460),(-1,50),(-25,25),'X (m)','Y (m)');lines(xf,m['original_triangle_node_ids'],mp,[0,1],'#3b718d')
    xx=mp((-.05,-25))[0];dr.line((xx,150,xx,460),fill='#ad4343',width=3);txt(150,160,f'Vue XY — état nominal à {t:.6f} ms ; plan initial de façade en rouge',20)
    txt(100,520,'Le contact reste limité au nez ; ailes et moteurs n’ont pas encore atteint la façade.',22,b=True)
    mn=plot((100,625,770,960),(-.6,2.2),(-2.2,2.2),'X (m)','Z (m)');rad=set(m['radome_element_ids']);tri=[el for eid,el in zip(m['aircraft_triangle_ids'],m['original_triangle_node_ids']) if eid in rad];lines(x,tri,mn,[0,2],'#a4aeb8');lines(xf,tri,mn,[0,2],'#197fa1',2)
    f=paths['COMP_FINE'];mf=read(f/'mesh.json');zf=np.load(f/'verified_states_SI.npz');rf=set(mf['radome_element_ids']);tf=[el for eid,el in zip(mf['aircraft_triangle_ids'],mf['original_triangle_node_ids']) if eid in rf];lines(zf['initial_positions_m']+zf['displacement_m'][-1],tf,mn,[0,2],'#d87e22')
    txt(100,580,'Nez XZ : initial gris, nominal bleu, maillage affiné orange',20,b=True)
    me=plot((920,625,1490,960),(0,2),(-160,360),'temps (ms)','énergie (kJ)')
    for cid,color in [('COMP_SELF','#197fa1'),('COMP_FINE','#d87e22')]:
        h=np.load(paths[cid]/'balance_history_SI.npz')
        for field,w in [('generated_energy_J',3),('energy_residual_J',2)]:dr.line([me(p) for p in zip(h['time_s']*1000,h[field]/1000)],fill=color,width=w)
    txt(920,580,'Énergie générée (+) et résidu du bilan (−)',20,b=True)
    txt(55,1040,'Convergence spatiale en échec : écart d’impulsion 14,35 % ; énergie générée 43,25 %.',22,b=True)
    txt(55,1073,'Référence élastique dépassée ; rupture, écrasement de l’âme, incendie et effondrement non calculés.',20)
    dst=OUT/'cached_review/summary_aircraft_a05.png';assert not dst.exists();im.save(dst)
    dump(OUT/'cached_review/figure_provenance.json',{'created_utc':now(),'figure':rel(dst),'sha256':sha(dst),'displacement_scale':1,'final_states_native_separate_times_ms':[float(t),float(zf['time_s'][-1]*1000)],'facade_line_initial_midplane_X_m':-.05,'facade_deformation_not_shown':True,'not_Blender_or_historical_reconstruction':True,'inputs':[{'path':rel(paths[c]/f),'sha256':sha(paths[c]/f)} for c in ['COMP_SELF','COMP_FINE'] for f in ['verified_states_SI.npz','balance_history_SI.npz','mesh.json']]})
    print({'figure':rel(dst)})

if __name__=='__main__':main()
