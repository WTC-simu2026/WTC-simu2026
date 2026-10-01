"""Project saved solved coordinates, with no mechanical interpolation or scaling."""
import json,hashlib,subprocess,shutil
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'wtc1_simulation_v8/output/impact_i02d_lap_joint';RENDER=ROOT/'wtc1_3d_v4/renders/impact_i02d'
CASE='LAP_SEPARATE_H025_R5'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def font(n,b=False):return ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf' if b else 'C:/Windows/Fonts/arial.ttf',n)
source=OUT/CASE/'computed_frames.npz';data=np.load(source);history=read(OUT/CASE/'history.json');results=read(OUT/CASE/'results.json')
assert results['status']=='PASS'
folder=RENDER/'frames';folder.mkdir(parents=True,exist_ok=True);records=[]
# Orthonormal camera projection: equal geometric scale on both screen axes.
az=np.deg2rad(20);el=np.deg2rad(30);hx=np.array([np.cos(az),-np.sin(az),0]);hy=np.array([np.sin(az)*np.sin(el),np.cos(az)*np.sin(el),np.cos(el)]);hz=np.cross(hx,hy)
for k,t in enumerate(data['times_ms']):
    im=Image.new('RGB',(1280,800),'#edf2f6');d=ImageDraw.Draw(im);xyz=data['points_mm'][k]
    d.rectangle((0,0,1280,113),fill='#132b40');d.text((26,18),'I02D | Recouvrement : flexion et séparation',font=font(31,True),fill='white')
    d.text((26,64),'Modèle réduit — propriétés hypothétiques — pas encore une aile contre la façade',font=font(21),fill='#ffd3a2')
    d.rectangle((20,130,1260,518),fill='#233e53')
    projected=np.column_stack([630+12*(xyz@hx),350-12*(xyz@hy)])
    order=np.argsort([xyz[q].mean(axis=0)@hz for q in data['quads']])
    for qid in order:
        q=data['quads'][qid];p=data['parts'][qid]
        d.polygon([tuple(v) for v in projected[q]],fill='#398bb0' if p==1 else '#d89951',outline='#567890' if p==1 else '#aa814f')
    for brick,active in zip(data['bricks'],data['active'][k]):
        bottom=xyz[brick[:4]].mean(axis=0);top=xyz[brick[4:]].mean(axis=0)
        points=[(630+12*v@hx,350-12*v@hy) for v in (bottom,top)]
        color='#82e4ad' if active else '#ff8b76'
        if active:d.line(points,fill=color,width=2)
        for x,y in points:d.ellipse((x-2,y-2,x+2,y+2),fill=color)
    d.text((44,153),'Tôle 2 mm',font=font(23,True),fill='#b0e6ff');d.text((969,153),'Tôle 3 mm',font=font(23,True),fill='#ffe0b9')
    d.text((44,473),'Vert : liaison active | rouge : séparée | surfaces moyennes des coques',font=font(20),fill='white')
    d.text((36,540),f'État {k+1:02d}/31 | temps du calcul : {t:.4f} ms',font=font(25,True),fill='#17364d')
    keys=[('joint_work_J','Travail de la liaison','#b75e21'),('plate_energy_J','Énergie des tôles','#247855'),('kinetic_J','Énergie cinétique','#157d9e'),('contact_energy_J','Énergie de contact','#805192')]
    for n,(key,label,color) in enumerate(keys):
        val=np.interp(t,history['time_ms'],history[key]);d.text((36+620*(n%2),600+57*(n//2)),f'{label} : {val:.5f} J',font=font(23,True),fill=color)
    d.rectangle((0,742,1280,800),fill='#f5dcc1');d.text((24,761),'Coordonnées sans amplification | chargement imposé aux prises, pas un impact balistique',font=font(21,True),fill='#713914')
    p=folder/f'state_{k:03d}.png';im.save(p);records.append({'state':k,'time_ms':float(t),'sha256':sha(p)})
video=RENDER/'I02D_recouvrement_calcule.mp4';command=[shutil.which('ffmpeg'),'-hide_banner','-loglevel','error','-n','-framerate','5','-i',str(folder/'state_%03d.png'),'-c:v','libx264','-crf','18','-pix_fmt','yuv420p','-r','30',str(video)]
if not video.exists():
    proc=subprocess.run(command,capture_output=True,text=True,timeout=60);(RENDER/'encoding.log').write_text(proc.stdout+proc.stderr);assert proc.returncode==0
probe=subprocess.run([shutil.which('ffprobe'),'-v','error','-select_streams','v:0','-show_entries','stream=width,height,codec_name,nb_frames,duration','-of','json',str(video)],capture_output=True,text=True,timeout=30)
info=json.loads(probe.stdout)['streams'][0]
checks={'31_solved_states':len(records)==31,'h264':info['codec_name']=='h264','dimensions':(info['width'],info['height'])==(1280,800),'frames':int(info['nb_frames'])==186,'duration':abs(float(info['duration'])-6.2)<.001,'orthonormal_projection':bool(abs(hx@hy)<1e-12 and abs(hx@hx-1)<1e-12 and abs(hy@hy-1)<1e-12)}
(RENDER/'presentation_audit.json').write_text(json.dumps({'status':'PASS' if all(checks.values()) else 'FAIL','checks':checks,'case':CASE,'source_npz':str(source.relative_to(ROOT)).replace('\\','/'),'source_sha256':sha(source),'frames':records,'video_sha256':sha(video),'probe':info,'command':command,'mechanical_interpolation':False,'displacement_amplification':1,'scope':'Orthographic shell midsurfaces, saved nodal coordinates and actual cohesive OFF flags. Distributed numerical patch markers are not physical rivets. Grip displacement, not ballistic impact.'},indent=2)+'\n')
print(json.dumps({'status':'PASS' if all(checks.values()) else 'FAIL','movie':str(video)}))
