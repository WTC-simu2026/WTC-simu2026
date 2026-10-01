"""Scientific plots and projected shell-state film; no generated mechanics."""
import json,hashlib,shutil,subprocess
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'wtc1_simulation_v8/output/impact_i02c_deformable_joint';RENDER=ROOT/'wtc1_3d_v4/renders/impact_i02c';RENDER.mkdir(parents=True,exist_ok=True)
audit=json.loads((OUT/'campaign_audit.json').read_text());assert audit['status']=='PASS'
def read(p):return json.loads(p.read_text())
def hist(n):return read(OUT/n/'history.json')
def font(n,b=False):return ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf' if b else 'C:/Windows/Fonts/arial.ttf',n)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
colors=['#177da2','#d67422','#913e94']
im=Image.new('RGB',(1520,1040),'#edf2f6');d=ImageDraw.Draw(im)
d.rectangle((0,0,1520,126),fill='#142b40');d.text((34,25),'I02C | Plaques déformables et liaisons rompables',font=font(35,True),fill='white')
d.text((34,78),'15 cas vérifiés | états calculés, énergie suivie, limites de domaine conservées',font=font(23),fill='#d3e6f3')
def panel(rect,title,xlabel,ylabel,xmax,ymax):
    x0,y0,x1,y1=rect;d.rounded_rectangle(rect,12,fill='white');d.text((x0+20,y0+16),title,font=font(23,True),fill='#1d3c54')
    ax=(x0+78,y0+80,x1-28,y1-64)
    for k in range(6):
        x=ax[0]+(ax[2]-ax[0])*k/5;y=ax[3]-(ax[3]-ax[1])*k/5
        d.line((x,ax[1],x,ax[3]),fill='#dce4ec');d.line((ax[0],y,ax[2],y),fill='#dce4ec')
        d.text((x,ax[3]+10),f'{xmax*k/5:.2g}',anchor='mt',font=font(17),fill='#496376')
        d.text((ax[0]-10,y),f'{ymax*k/5:.2g}',anchor='rm',font=font(17),fill='#496376')
    d.text((ax[0],y0+48),ylabel,font=font(17),fill='#496376');d.text(((ax[0]+ax[2])/2,y1-25),xlabel,anchor='mm',font=font(18),fill='#496376')
    def curve(xs,ys,color):
        points=[(ax[0]+x/xmax*(ax[2]-ax[0]),ax[3]-y/ymax*(ax[3]-ax[1])) for x,y in zip(xs,ys)]
        if len(points)>1:d.line(points,fill=color,width=3)
    return curve
curve=panel((28,148,742,555),'Glissement : trois maillages de plaques','Déplacement de la prise (mm)','Force de liaison (kN)',1.2,7)
for n,color,label in zip(['SHEAR_MONO_H05_R1','SHEAR_MONO_H025_R2','SHEAR_MONO_H0125_R2'],colors,['5 mm','2,5 mm','1,25 mm']):
    h=hist(n);curve(h['grip_displacement_mm'],np.array(h['joint_force_N'])/1000,color)
    d.text((310+colors.index(color)*130,200),label,font=font(18,True),fill=color)
curve=panel((768,148,1492,555),'Essai libre : où vont les 2,5 J initiaux ?','Temps (ms)','Énergie (J)',.4,2.6)
h=hist('DYN_BASE_H025_R2')
for key,color,label in [('kinetic_J',colors[0],'cinétique'),('plate_energy_J','#2a875f','plaques'),('dissipation_J',colors[1],'dissipation')]:
    curve(h['time_ms'],h[key],color)
for x,color,label in [(1000,colors[0],'cinétique'),(1140,'#2a875f','plaques'),(1280,colors[1],'dissipation')]:d.text((x,200),label,font=font(18,True),fill=color)
d.rounded_rectangle((28,577,742,910),12,fill='white');d.text((48,598),'Ce qui est vérifié',font=font(25,True),fill='#1d3c54')
for y,text in [(655,'Glissement élastique : erreur de raideur < 0,005 %'),(702,'Flexion normale, maille fine : erreur ≈ 0,011 %'),(749,'Rupture tangentielle : énergie totale ≈ 1,632 J'),(796,'Repère tourné de 90° : coordonnées reproduites'),(843,'Masse conservée : 13,716 g ; aucun ajout imposé')]:d.text((48,y),text,font=font(21),fill='#345267')
d.rounded_rectangle((768,577,1492,910),12,fill='#fff0df');d.text((790,598),'Ce qui reste ouvert',font=font(25,True),fill='#773d1b')
for y,text in [(655,'Vibrations après rupture : écart résiduel de 14,4 %'),(702,'Deux essais stoppés avant le glissement inverse'),(749,'Pas de contact, de mode mixte ni de rivet géométrique'),(796,'Plaques élastiques : pas de déchirure du métal'),(843,'Pas encore une section d’aile contre une façade')]:d.text((790,y),text,font=font(21),fill='#773d1b')
d.rounded_rectangle((28,934,1492,1016),10,fill='#142b40');d.text((50,952),'Référence numérique à joint coplanaire. Propriétés post-pic hypothétiques ; aucune validation historique.',font=font(23,True),fill='white')
im.save(OUT/'synthese_impact_i02c.png')

CASE='DYN_BASE_H025_R2';source=OUT/CASE/'computed_frames.npz';before=sha(source);frames=np.load(source);h=hist(CASE)
folder=RENDER/'frames';folder.mkdir(exist_ok=True)
records=[]
for frame,t in enumerate(frames['times_ms']):
    picture=Image.new('RGB',(1280,800),'#edf2f6');draw=ImageDraw.Draw(picture)
    draw.rectangle((0,0,1280,112),fill='#132b40');draw.text((26,19),'I02C | Liaison couplée à deux bandes déformables',font=font(29,True),fill='white')
    draw.text((26,63),'ESSAI RÉDUIT — pas un avion ni un rivet réel — coordonnées sans amplification',font=font(20),fill='#ffd3a2')
    draw.rectangle((20,130,1260,513),fill='#233e53')
    xyz=frames['points_mm'][frame]
    projected=np.column_stack((620+11*(xyz[:,0]+.42*xyz[:,1]),328+5.5*(.43*xyz[:,0]-.85*xyz[:,1])-11*xyz[:,2]))
    for q,p in zip(frames['quads'],frames['parts']):
        draw.polygon([tuple(v) for v in projected[q]],fill='#398bb0' if p==1 else '#db9953',outline='#517188' if p==1 else '#a87e4c')
    for pair,active in zip(frames['links'],frames['active'][frame]):
        color='#89e3ae' if active else '#ff8a76'
        if active:draw.line([tuple(v) for v in projected[pair]],fill=color,width=3)
        for x,y in projected[pair]:draw.ellipse((x-3,y-3,x+3,y+3),fill=color)
    draw.text((49,153),'Peau, 2 mm',font=font(24,True),fill='#a1ddf5');draw.text((852,153),'Bande de semelle, 3 mm',font=font(24,True),fill='#ffdeb4')
    draw.text((45,462),'Points verts : liaison active | points rouges : extrémités séparées',font=font(20),fill='white')
    draw.text((40,535),f'État {frame+1:02d}/31 — temps physique : {t*1000:.2f} µs',font=font(25,True),fill='#16364e')
    values={k:float(np.interp(t,h['time_ms'],h[k])) for k in ('kinetic_J','plate_energy_J','dissipation_J','recoverable_joint_J')}
    for index,(key,label,color) in enumerate([('kinetic_J','Cinétique','#177da2'),('plate_energy_J','Plaques','#2a875f'),('dissipation_J','Dissipée, liaison','#b75d1b'),('recoverable_joint_J','Récupérable, liaison','#704d8c')]):
        x=40+(index%2)*620;y=593+(index//2)*64
        draw.text((x,y),f'{label} : {values[key]:.4f} J',font=font(23,True),fill=color)
    draw.rectangle((0,742,1280,800),fill='#f8dfc4');draw.text((24,759),'Énergie initiale 2,5 J | G supposé 1,632 J | vibrations après rupture non convergées',font=font(21,True),fill='#713914')
    path=folder/f'state_{frame:03d}.png';picture.save(path);records.append({'state':frame,'time_ms':float(t),'sha256':sha(path)})
ffmpeg=shutil.which('ffmpeg');video=RENDER/'I02C_liaison_couplee.mp4'
command=[ffmpeg,'-hide_banner','-loglevel','error','-n','-framerate','5','-i',str(folder/'state_%03d.png'),'-c:v','libx264','-crf','18','-pix_fmt','yuv420p','-r','30',str(video)]
if not video.exists():
    p=subprocess.run(command,capture_output=True,text=True,timeout=60);(RENDER/'encoding.log').write_text(p.stdout+p.stderr,encoding='utf-8');assert p.returncode==0
probe=subprocess.run([shutil.which('ffprobe'),'-v','error','-select_streams','v:0','-show_entries','stream=width,height,codec_name,nb_frames,duration','-of','json',str(video)],capture_output=True,text=True,timeout=30)
info=json.loads(probe.stdout)['streams'][0]
checks={'31_saved_states':len(records)==31,'source_unchanged':before==sha(source),'codec_h264':info['codec_name']=='h264','size':(info['width'],info['height'])==(1280,800),'186_frames':int(info['nb_frames'])==186,'duration_6p2s':abs(float(info['duration'])-6.2)<.001}
meta={'status':'PASS' if all(checks.values()) else 'FAIL','checks':checks,'source_npz':str(source.relative_to(ROOT)).replace('\\','/'),'source_sha256':before,'case':CASE,'frames':records,'video_sha256':sha(video),'probe':info,'command':command,'scope':'Direct parallel projection of saved nodal shell coordinates at 31 stored times. No amplification, no interpolated mechanical states; 30-fps encoding repeats images. Rotations/offset/contact of a real lap rivet are absent.'}
(RENDER/'presentation_audit.json').write_text(json.dumps(meta,indent=2)+'\n',encoding='utf-8');print(json.dumps({'status':meta['status'],'video':str(video),'checks':checks},indent=2))
