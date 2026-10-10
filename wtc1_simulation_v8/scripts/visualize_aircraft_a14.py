"""Saved native A14 comparisons; static scientific chart and native state viewer."""
import json,sys,math
from pathlib import Path
import numpy as np
from reportlab.graphics.shapes import Drawing,String
from reportlab.graphics.charts.lineplots import LinePlot
from reportlab.graphics import renderSVG,renderPDF
from reportlab.lib import colors
import reportlab,pypdfium2 as pdfium

ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'wtc1_simulation_v8/output/aircraft_a14'
sys.path.insert(0,str(ROOT/'wtc1_simulation_v8/scripts'))
from audit_aircraft_a05 import histories

def main():
    dst=OUT/'visualisation';assert not dst.exists();dst.mkdir()
    summary=json.loads((OUT/'plate_review.json').read_text());by={r['case']['id']:r for r in summary['cases']}
    colors4=[colors.HexColor(x) for x in ['#b45c36','#b39939','#219b80','#2369ae']]
    fig=Drawing(1120,835);fig.add(String(38,797,'AIRCRAFT-A14 : contact plan a 200 m/s et effet du maillage',fontSize=20))
    fig.add(String(38,769,'Verification numerique : plaque synthetique de 400 mm2, masse 1,112 g, mur immobilise.',fontSize=12))
    fig.add(String(38,746,'Parametres declares avant calcul. Aucun dommage historique utilise comme cible.',fontSize=12))
    for i,n in enumerate([1,2,4,8]):fig.add(String(42+265*i,716,f'{n*n} mailles / {(n+1)**2} noeuds mobiles',fontSize=12,fillColor=colors4[i]))
    arrays={k:np.load(OUT/'r0'/k/'balance_history_SI.npz') for k in by}
    for label,x in [('RAW',70),('AREA',625)]:
        ch=LinePlot();ch.x=x;ch.y=423;ch.width=415;ch.height=218;ch.joinedLines=1;ch.xValueAxis.valueMin=0;ch.xValueAxis.valueMax=.04;ch.yValueAxis.valueMin=0;ch.yValueAxis.valueMax=23
        lines=[]
        for i,n in enumerate([1,2,4,8]):
            a=arrays[f'{label}_N{n}'];ix=np.unique(np.r_[np.arange(0,len(a['time_ms']),max(1,len(a['time_ms'])//420)),len(a['time_ms'])-1]);lines.append(list(zip(a['time_ms'][ix],a['contact_J'][ix])))
            ch.lines[i].strokeColor=colors4[i];ch.lines[i].strokeWidth=1.3
        ch.data=lines;fig.add(ch);fig.add(String(x,665,('Penalite constante par noeud' if label=='RAW' else 'Penalite proportionnelle a la surface'),fontSize=14));fig.add(String(x,646,'Energie elastique du contact (J)',fontSize=11));fig.add(String(x+125,390,'Temps physique (ms)',fontSize=11))
    ch=LinePlot();ch.x=70;ch.y=97;ch.width=415;ch.height=206;ch.joinedLines=1;ch.xValueAxis.valueMin=0;ch.xValueAxis.valueMax=82;ch.yValueAxis.valueMin=0;ch.yValueAxis.valueMax=.01
    ch.data=[[(float((n+1)**2),by[f'{lab}_N{n}']['contact_duration_ms']) for n in [1,2,4,8]] for lab in ['RAW','AREA']];ch.lines[0].strokeColor=colors.HexColor('#a94d31');ch.lines[1].strokeColor=colors.HexColor('#218878');fig.add(ch)
    fig.add(String(70,334,'Duree du contact (ms)',fontSize=14));fig.add(String(70,311,'Rouge : par noeud ; vert : par surface',fontSize=11));fig.add(String(190,64,'Nombre de noeuds mobiles',fontSize=11))
    facts=['Surface et masse identiques sur les 4 niveaux.','Raideur totale native : 0,14 -> 2,835 MN/mm.','Raideur totale ponderee : 0,14 MN/mm fixe.','Ecart impulsion fin : 2,09 % -> 0,0017 %.','Ecart courbe energie fin : 84,31 % -> 0,75 %.','Maillage du mur : 1 / 9 / 16 mailles, identique.','Le critere temporel grossier reste echoue.','Transfert au radome encore non autorise.','Ce temoin ne represente pas l avion historique.']
    for i,t in enumerate(facts):fig.add(String(625,326-27*i,t,fontSize=12))
    renderSVG.drawToFile(fig,str(dst/'comparaison_contact.svg'))
    pdf=pdfium.PdfDocument(renderPDF.drawToString(fig));page=pdf[0];bitmap=page.render(scale=1.4);bitmap.to_pil().save(dst/'comparaison_contact.png');bitmap.close();page.close();pdf.close()
    payload=[];maxerr=0
    for case in ['RAW_N8','AREA_N8']:
        d=OUT/'r0'/case;g=json.loads((d/'generation.json').read_text());H=histories(d/(g['name']+'T01.csv'));nn=len(g['nodes_mm']);keys=[k for k in H if k.startswith('NATIVE_NODES')];N=np.column_stack([H[k] for k in keys]).reshape(len(H['time']),nn,9);ix=np.unique(np.r_[np.arange(0,len(H['time']),max(1,len(H['time'])//260)),len(H['time'])-1]);u=N[ix,:,:3];rounded=np.round(u,7);maxerr=max(maxerr,float(np.max(abs(u-rounded))))
        payload.append({'case':case,'label':'Par noeud' if case.startswith('RAW') else 'Par surface','nodes_mm':g['nodes_mm'],'moving_quads':[[v-1 for v in q] for q in g['moving_quads']],'wall_quads':[[v-1 for v in q] for q in g['wall_quads']],'time_ms':H['time'][ix].tolist(),'u_mm':rounded.tolist(),'contact_J':arrays[case]['contact_J'][ix].tolist(),'impulse_Ns':arrays[case]['impulse_Ns'][ix,0].tolist(),'failed':by[case]['failed_checks']})
    html='''<!doctype html><html lang="fr"><meta charset="utf-8"><title>A14 — contact et maillage</title><style>body{margin:0;background:#142130;color:#e8eef6;font:16px system-ui}main{max-width:1180px;margin:auto;padding:24px}h1{font-size:27px}p{line-height:1.5}.notice{padding:14px;background:#2b3c50;border-left:4px solid #e5af78}.controls{display:flex;gap:20px;align-items:center;margin:18px 0;flex-wrap:wrap}button{background:#37647e;border:1px solid #809da8;color:white;padding:10px;border-radius:6px}input{width:360px}canvas{width:100%;height:450px;background:#192c3e;border-radius:10px}a{color:#9ed7fa}.values{display:flex;gap:32px;margin:16px 0;flex-wrap:wrap}</style><main><h1>Contact : comparer deux maillages identiques</h1><p class="notice">Essai de vérification numérique : une plaque synthétique élastique rencontre un mur fixe à <b>200 m/s</b>. La fenêtre calculée est de <b>0,04 ms</b>. Les critères grossiers restent échoués et le transfert au nez de l’avion attend leur résolution.</p><div class="controls"><button id="play">Lecture ralentie</button><input id="time" type="range" min="0" max="400" value="0"><b id="label"></b></div><canvas id="canvas"></canvas><div id="values" class="values"></div><p>Gauche : pénalité constante par nœud. Droite : pénalité proportionnelle à la surface. Dans les deux cas : 64 mailles, 81 nœuds mobiles, même surface et même masse. Vert : plaque mobile ; orange : mur immobilisé ; trait gris : position initiale. Déplacements natifs ×1, vue oblique, lecture artificiellement ralentie.</p><p><a href="comparaison_contact.svg">Comparer les quatre niveaux de maillage</a> · <a href="../rapport_aircraft_a14.md">Rapport et critères échoués</a></p></main><script>const D=PAYLOAD;const cv=document.querySelector('#canvas'),ctx=cv.getContext('2d'),slider=document.querySelector('#time');let playing=false,last=0;function draw(){let b=cv.getBoundingClientRect(),t=.04*slider.value/400;cv.width=b.width*devicePixelRatio;cv.height=b.height*devicePixelRatio;ctx.setTransform(devicePixelRatio,0,0,devicePixelRatio,0,0);ctx.clearRect(0,0,b.width,b.height);let metrics=[];D.forEach((q,i)=>{let k=0;while(k+1<q.time_ms.length&&q.time_ms[k+1]<=t)k++;let x=q.nodes_mm.map((p,n)=>p.map((v,j)=>v+q.u_mm[k][n][j]));let ox=b.width*(i*.5+.25),sc=Math.min(b.width/78,b.height/48);function P(p){return[ox+sc*(.94*p[0]+.342*p[1]),b.height/2-sc*p[2]]}function faces(rows,pos,color,alpha){ctx.strokeStyle=color;ctx.globalAlpha=alpha;ctx.lineWidth=.8;for(let r of rows){ctx.beginPath();r.forEach((n,j)=>{let p=P(pos[n]);j?ctx.lineTo(...p):ctx.moveTo(...p)});ctx.closePath();ctx.stroke()}}faces(q.wall_quads,q.nodes_mm,'#efa96c',.55);faces(q.moving_quads,q.nodes_mm,'#aab4bc',.23);faces(q.moving_quads,x,'#59d9b2',.9);ctx.globalAlpha=1;ctx.fillStyle='#e4eff8';ctx.font='17px system-ui';ctx.fillText(q.label,ox-60,30);ctx.font='13px system-ui';ctx.fillText('État natif : '+q.time_ms[k].toFixed(7)+' ms',ox-110,b.height-18);metrics.push('<span>'+q.label+' : '+q.contact_J[k].toFixed(3)+' J ; '+q.impulse_Ns[k].toFixed(6)+' N·s</span>')});document.querySelector('#label').textContent=t.toFixed(6)+' ms';document.querySelector('#values').innerHTML=metrics.join('')}slider.oninput=draw;window.onresize=draw;document.querySelector('#play').onclick=()=>{playing=!playing;document.querySelector('#play').textContent=playing?'Pause':'Lecture ralentie'};function tick(t){if(playing&&t-last>40){slider.value=(+slider.value+1)%401;last=t;draw()}requestAnimationFrame(tick)}draw();requestAnimationFrame(tick);</script></html>'''.replace('PAYLOAD',json.dumps(payload,separators=(',',':')))
    (dst/'contact_plan.html').write_text(html,encoding='utf-8');(dst/'viewer_script_for_validation.js').write_text(html.split('<script>')[1].split('</script>')[0],encoding='utf-8')
    assert all(len(d['time_ms'])==len(d['u_mm'])==len(d['contact_J']) for d in payload) and maxerr<=5.1e-8
    (dst/'provenance.json').write_text(json.dumps({'native_displacement_scale':1,'native_time_unit':'ms','artificial_playback':True,'viewer_cases':['RAW_N8','AREA_N8'],'data_schema_pass':True,'maximum_position_rounding_error_mm':maxerr,'no_temporal_interpolation_of_geometry':True,'reportlab_version':reportlab.Version,'GUI_render_verified':False,'static_chart_rendered_to_PNG':True,'physical_impact_qualified':False},indent=2),encoding='utf-8')
    print({'plot':str(dst/'comparaison_contact.svg'),'viewer':str(dst/'contact_plan.html')})

if __name__=='__main__':main()
