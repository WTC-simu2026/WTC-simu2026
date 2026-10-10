"""Native A16 damage/geometry and comparison with cached undamaged A15."""
import base64,gzip,hashlib,json,re
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from reportlab.graphics.shapes import Drawing,String
from reportlab.graphics.charts.lineplots import LinePlot
from reportlab.graphics import renderSVG,renderPDF
from reportlab.lib import colors
import pypdfium2 as pdfium
from run_aircraft_a16 import ROOT,OUT,PREV,read,dump,now

def main():
    dst=OUT/'visualisation';assert not dst.exists();s=read(OUT/'campaign_review.json');assert s['cases'];dst.mkdir();rows=s['cases'];nom=read(PREV/'r0/IMPACT_10_DT50/review.json')
    arrays=[np.load(PREV/'r0/IMPACT_10_DT50/balance_history_SI.npz')]+[np.load(OUT/'r0'/r['case']['id']/'balance_history_SI.npz') for r in rows]
    palette=[colors.HexColor('#7b8792'),colors.HexColor('#288679'),colors.HexColor('#ab6337')];labels=['A15 : sans dommage des peaux']+[r['case']['id'] for r in rows]
    fig=Drawing(1120,810);fig.add(String(40,771,'AIRCRAFT-A16 : dommage des peaux, impact couple',fontSize=20));fig.add(String(40,741,'Avion et facade conserves. Etats natifs. Comparaison de parametres, pas convergence.',fontSize=12));fig.add(String(40,716,'Pas de G physique identifie, pas de fragments libres ni de delamination.',fontSize=12))
    for i,label in enumerate(labels):fig.add(String(40+365*i,683,label,fontSize=11,fillColor=palette[i]))
    for key,title,factor,x,y in [('contact_impulse_Ns','Impulsion X facade (kN.s)',.001,80,395),('generated_energy_J','Energie hors translation (MJ)',1e-6,635,395),('energy_residual_J','Residuel energetique (kJ)',.001,80,82)]:
        c=LinePlot();c.x=x;c.y=y;c.width=410;c.height=215;c.joinedLines=1;c.xValueAxis.valueMin=0;c.xValueAxis.valueMax=10;c.data=[]
        for i,z in enumerate(arrays):
            ix=np.unique(np.r_[np.arange(0,len(z['time_s']),max(1,len(z['time_s'])//430)),len(z['time_s'])-1]);v=z[key][:,0] if key=='contact_impulse_Ns' else z[key];c.data.append(list(zip((z['time_s'][ix]*1000).tolist(),(v[ix]*factor).tolist())));c.lines[i].strokeColor=palette[i];c.lines[i].strokeWidth=1.3
        fig.add(c);fig.add(String(x,y+240,title,fontSize=14));fig.add(String(x+130,y-31,'Temps physique (ms)',fontSize=11))
    txt=['Avion complet : 121963 kg environ.','Trois etages de facade deformable.','Quatre controles de dommage/cycles passent.','Aucune recharge au meme pic ne cree du dommage.','Loi de deformation maximale, peaux uniquement.','Coeur et metaux sans nouvelle rupture.','Contraintes imprimees : effectives, a interpreter.','Fermeture numerique et realisme restent distincts.']
    for i,t in enumerate(txt):fig.add(String(635,311-27*i,t,fontSize=12))
    renderSVG.drawToFile(fig,str(dst/'comparaison_impact.svg'));pdf=pdfium.PdfDocument(renderPDF.drawToString(fig));pg=pdf[0];bm=pg.render(scale=1.4);bm.to_pil().save(dst/'comparaison_impact.png');bm.close();pg.close();pdf.close()
    r=rows[0];case=r['case']['id'];d=OUT/'r0'/case;z=np.load(d/'verified_states_SI.npz');dm=np.load(d/'native_radome_damage.npz');m=read(d/'mesh.json');L=arrays[1];X=np.asarray(z['initial_positions_m'],dtype='<f8');U=np.asarray(z['displacement_m'],dtype='<f4');tri=[[n-1 for n in t] for t in m['original_triangle_node_ids']];wall=[[n-1 for n in t] for t in m['facade_quads_node_ids']];beams=[[n-1 for n in t] for t in m['original_beam_node_ids']]
    di={int(e):i for i,e in enumerate(dm['element_ids'])};mapping=[di.get(int(e),-1) for e in m['aircraft_triangle_ids']];indices=[int(np.argmin(abs(dm['time_s']-t))) for t in z['time_s']];assert all(abs(dm['time_s'][i]-t)<1e-7 for i,t in zip(indices,z['time_s']));D=np.max(dm['skin_core_skin_damage'][indices][:,[0,2],:],axis=1)
    raw=X.tobytes()+U.tobytes();packed=gzip.compress(raw,mtime=0);assert gzip.decompress(packed)==raw
    payload={'case':case,'nn':len(X),'nt':len(U),'time_ms':(z['time_s']*1000).tolist(),'triangles':tri,'wall':wall,'beams':beams,'triangle_damage_index':mapping,'skin_damage':D.tolist(),'impulse_Ns':np.interp(z['time_s'],L['time_s'],L['contact_impulse_Ns'][:,0]).tolist(),'energy_J':np.interp(z['time_s'],L['time_s'],L['generated_energy_J']).tolist(),'residual_J':np.interp(z['time_s'],L['time_s'],L['energy_residual_J']).tolist(),'facade_displacement_mm':[q['maximum_facade_displacement_mm'] for q in r['state_diagnostics']]}
    template=(PREV/'visualisation/impact_avion_facade.html').read_text(encoding='utf-8')
    template=re.sub(r"const D=.*?,PACK='[^']*';",lambda _:"const D="+json.dumps(payload,separators=(',',':'))+",PACK='"+base64.b64encode(packed).decode()+"';",template,count=1)
    template=template.replace('A15','A16').replace('premier contact A16','dommage des peaux A16').replace('bilans_impact.svg','comparaison_impact.svg').replace('rapport_aircraft_a15.md','rapport_aircraft_a16.md')
    old='Les résultats restent exploratoires : rupture, écrasement et délamination ne sont pas représentés, et les critères numériques échoués figurent dans le rapport.'
    new='Les peaux du radôme perdent leur résistance selon une loi de déformation maximale. Rouge : au moins un point de peau totalement endommagé ; orange : dommage partiel ; vert : faible dommage. Le cœur reste intact, sans fragments détachés. Énergie de fracture physique, écrasement et délamination non qualifiés ; les échecs figurent au rapport.'
    assert old in template;template=template.replace(old,new)
    template=template.replace("for(let r of rows){","for(let ri=0;ri<rows.length;ri++){let r=rows[ri];if(rows===D.triangles&&!init){let di=D.triangle_damage_index[ri],v=di<0?0:D.skin_damage[k][di];ctx.strokeStyle=v>=.999999?'#f66a69':v>.01?'#ffc56b':col;}")
    template=template.replace('Vert : avion ; orange : façade ; gris : position initiale si activée.','Vert : avion ; brun : façade ; rouge/jaune : dommage des peaux ; gris : position initiale.').replace('elle ne décrit pas une rupture historique','elle ne décrit pas une rupture historique')
    (dst/'impact_avion_facade_dommage.html').write_text(template,encoding='utf-8');(dst/'viewer_script_for_validation.js').write_text(template.split('<script>')[1].split('</script>')[0],encoding='utf-8')
    im=Image.new('RGB',(1680,1240),'#111e2b');draw=ImageDraw.Draw(im);font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',25);small=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',21)
    draw.text((35,25),'AIRCRAFT-A16 — impact avec dommage des peaux du radôme',fill='#edf4fa',font=font);draw.text((35,68),f"{case} · état natif {z['time_s'][-1]*1000:.6f} ms · déplacements ×1",fill='#b9ccdd',font=small)
    for close,cy in [(False,370),(True,900)]:
        sc=83 if close else 19;center=np.array([0.,0.,0.]) if close else np.array([15.,0.,0.]);xyz=X+U[-1]-center;initial=X-center
        def project(v):return np.column_stack([840+sc*(.819*v[:,0]+.574*v[:,1]),cy-sc*(.94*v[:,2]-.342*(-.574*v[:,0]+.819*v[:,1]))])
        pp=project(xyz);p0=project(initial)
        for faces,color,points,isair in [(tri,'#455a6a',p0,False),(wall,'#c88964',pp,False),(tri,'#53d1b2',pp,True)]:
            for fi,face in enumerate(faces):
                ij=np.asarray(face);xy=points[ij]
                if close and (np.all(abs(xyz[ij,0])>6) or np.all(abs(xyz[ij,1])>6) or np.all(abs(xyz[ij,2])>4)):continue
                if np.any((xy[:,0]<0)|(xy[:,0]>1680)|(xy[:,1]<(640 if close else 115))|(xy[:,1]>(1160 if close else 610))):continue
                col=color
                if isair and mapping[fi]>=0:
                    dv=D[-1,mapping[fi]];col='#f66a69' if dv>=.999999 else '#ffc56b' if dv>.01 else color
                draw.line([tuple(v) for v in xy]+[tuple(xy[0])],fill=col,width=1)
        draw.text((35,cy-220),'Dommage des peaux, coque encore présente' if close else 'Avion complet et façade',fill='#edf4fa',font=small)
    draw.text((35,1185),'Rouge : point de peau totalement endommagé. Cœur intact ; fragments et énergie de fracture non qualifiés.',fill='#b9ccdd',font=small);im.save(dst/'impact_dommage_natif.png')
    dump(dst/'provenance.json',{'created_utc':now(),'case_selected':case,'selection_reason':'first declaredR20, not selected by outcome','native_geometry_states':len(U),'all_native_damage_frames_in_source':len(dm['time_s']),'displacement_scale':1,'no_geometry_interpolation':True,'native_damage_binary_reader_verified':True,'gzip_roundtrip_exact':True,'uncompressed_payload_sha256':hashlib.sha256(raw).hexdigest(),'data_schema_pass':True,'interactive_GUI_render_verified':False,'physical_impact_qualified':False,'topological_fragmentation':False})
    print({'visualisation_created':True,'case':case},flush=True)

if __name__=='__main__':main()
