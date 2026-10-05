"""Scientific projections and histories directly from saved mechanical states."""
from PIL import Image,ImageDraw,ImageFont
import numpy as np
from run_aircraft_a04 import OUT,read,dump,rel,sha,now

def main():
    r=read(OUT/'cached_review/review.json');dest=OUT/'cached_review/A04_contact_plastique_v2.png';assert not dest.exists()
    W,H=2000,1550;im=Image.new('RGB',(W,H),'#f6f8fb');draw=ImageDraw.Draw(im)
    def font(n):return ImageFont.truetype('C:/Windows/Fonts/arial.ttf',n)
    def text(x,y,s,n=22,c='#172b46'):draw.text((x,y),s,font=font(n),fill=c)
    text(60,35,'AIRCRAFT-A04 | Premier contact plastique du Boeing entier',37)
    text(60,87,'Modèle exploratoire : conditions hypothétiques, aucun résultat historique imposé.',23)
    z=np.load(OUT/'r1/PLASTIC_NOMINAL/verified_states_SI.npz');mesh=read(OUT/'r1/mesh.json');na=mesh['aircraft_node_count'];x0=z['initial_positions_m'];xf=x0+z['displacement_m'][-1];elements=np.array(mesh['original_triangle_node_ids'])-1
    ep=z['shell_max_layer_plastic_strain'][-1];lookup={int(e):i for i,e in enumerate(z['element_ids']) if e>0};plastic=np.array([ep[lookup[i+1]] for i in range(len(elements))])
    def view(box,xb,yb,caption,zoom=False):
        l,t,rr,b=box;draw.rounded_rectangle(box,16,fill='white',outline='#cad3df',width=2);text(l+20,t+14,caption,24)
        plot=(l+30,t+65,rr-30,b-65);a,bb,c,d=plot;scale=min((c-a)/(xb[1]-xb[0]),(d-bb)/(yb[1]-yb[0]));cx=(a+c)/2;cy=(bb+d)/2
        panel=Image.new('RGB',(int(c-a),int(d-bb)),'white');pd=ImageDraw.Draw(panel)
        def xy(p):return (cx-a+(p[0]-sum(xb)/2)*scale,cy-bb-(p[1]-sum(yb)/2)*scale)
        # Scale is isotropic; deformation displayed at actual displacement x1.
        facex=-.05;pd.line([xy((facex,yb[0])),xy((facex,yb[1]))],fill='#535e70',width=3)
        for j,e in enumerate(elements):
            if zoom and not (np.any(x0[e,0]<1.35) and np.all(x0[e,0]<2.5)):continue
            if zoom:pd.line([xy(x0[e[0]]),xy(x0[e[1]]),xy(x0[e[2]]),xy(x0[e[0]])],fill='#c5cbd3',width=1)
            color='#d54c4c' if plastic[j]>.1 else '#1578a6' if plastic[j]>1e-8 else '#8092a7'
            pd.line([xy(xf[e[0]]),xy(xf[e[1]]),xy(xf[e[2]]),xy(xf[e[0]])],fill=color,width=1)
        im.paste(panel,(int(a),int(bb)))
        text(l+20,b-49,'Vue en plan, déplacement ×1 | rouge : déformation plastique > 0,1',18)
    tms=float(z['time_s'][-1]*1000)
    view((50,145,1000,655),(-1,49),(-26,26),f'Avion complet : état sauvegardé à {tms:.5f} ms')
    view((1030,145,1950,655),(-.4,1.3),(-.55,.55),'Zoom du nez : initial gris / déformé coloré',True)
    colors={'PLASTIC_NOMINAL':'#155d96','PLASTIC_HALF_DT':'#4d9fbe','PLASTIC_Y080':'#d38821','PLASTIC_Y120':'#2a8b63','PLASTIC_H002':'#8b4cba'}
    labels={'PLASTIC_NOMINAL':'Parfaitement plastique','PLASTIC_HALF_DT':'Même loi, pas réduit de moitié','PLASTIC_Y080':'Résistances ×0,8','PLASTIC_Y120':'Résistances ×1,2','PLASTIC_H002':'Écrouissage H = 0,02 E'}
    histories={cid:np.load(OUT/'r1'/cid/'balance_history_SI.npz') for cid in colors}
    def chart(box,title,ylabel,series,ymin,ymax):
        l,t,rr,b=box;draw.rounded_rectangle(box,16,fill='white',outline='#cad3df',width=2);text(l+20,t+13,title,24);a,bb,c,d=l+95,t+66,rr-30,b-64
        def xy(tt,y):return a+tt/2*(c-a),d-(y-ymin)/(ymax-ymin)*(d-bb)
        for ti in [0,.5,1,1.5,2]:
            xx,_=xy(ti,ymin);draw.line([(xx,bb),(xx,d)],fill='#e4e9ef');text(xx-18,d+10,f'{ti:g}',18)
        for y in np.linspace(ymin,ymax,5):
            _,yy=xy(0,y);draw.line([(a,yy),(c,yy)],fill='#e4e9ef');text(l+12,yy-10,f'{y:.0f}',17)
        for cid,data in series.items():
            x,y=data;draw.line([xy(float(tt),float(v)) for tt,v in zip(x,y)],fill=colors[cid],width=3)
        text(a,bb-30,ylabel,17);text(c-75,d+33,'temps (ms)',17)
    chart((50,690,1000,1120),'Impulsion normale transmise à la façade','|Jx| (kN·s)',{cid:(h['time_s']*1000,abs(h['contact_impulse_Ns'][:,0])/1000) for cid,h in histories.items()},0,12)
    chart((1030,690,1950,1120),'Travail plastique cumulé','PW (kJ), déjà compris dans l’énergie interne',{cid:(h['time_s']*1000,h['global_plastic_work_J']/1000) for cid,h in histories.items()},0,1300)
    for i,cid in enumerate(colors):
        x=70+(i%3)*625;y=1160+(i//3)*42;draw.line([(x,y+12),(x+42,y+12)],fill=colors[cid],width=4);text(x+55,y,labels[cid],20)
    text(60,1270,'4 cas plafonnés à 5 minutes de calcul : horizon 2 ms non atteint, derniers états vers 1,6 ms.',23)
    text(60,1310,'Le cas avec écrouissage atteint 2 ms ; les grandes déformations et le bilan énergétique local restent non qualifiés.',23)
    text(60,1360,'Le nez métallique est une approximation : radôme composite, rupture, autocontact et moteurs déformables manquent.',22)
    text(60,1400,'Les ailes n’ont pas encore atteint la façade. Aucun incendie ni effondrement n’est calculé dans cette fenêtre.',22)
    text(60,1450,'Trait vertical gris : position initiale de façade. La façade déformée n’est pas dessinée dans ces projections.',20)
    text(60,1487,'Données : états mécaniques OpenRadioss sauvegardés ; projection sans animation imposée.',20)
    im.save(dest);dump(OUT/'cached_review/figure_provenance_v2.json',{'created_utc':now(),'path':rel(dest),'sha256':sha(dest),'state':rel(OUT/'r1/PLASTIC_NOMINAL/verified_states_SI.npz'),'state_sha256':sha(OUT/'r1/PLASTIC_NOMINAL/verified_states_SI.npz'),'projection':'XY, isotropic scale, original plus solver displacement x1; clipping inside drawing panels; line denotes initial facade plane, not deformed facade','previous_plot_preserved':rel(OUT/'cached_review/A04_contact_plastique.png'),'previous_plot_issue':'unclipped zoom lines and impulse ymax slightly too low','physical_validation':False,'times_read_from_saved_states':True})
    print({'figure':rel(dest)})
if __name__=='__main__':main()
