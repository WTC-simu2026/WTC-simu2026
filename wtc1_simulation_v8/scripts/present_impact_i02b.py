"""Scientific summary of accepted I02B coupon histories; package cached I02A MP4."""
from __future__ import annotations
import hashlib
import json
import shutil
import subprocess
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'wtc1_simulation_v8/output/impact_i02b_joint_coupon'
MEDIA=ROOT/'wtc1_3d_v4/renders/impact_i02b'
MEDIA.mkdir(parents=True,exist_ok=True)
audit=json.loads((OUT/'campaign_audit.json').read_text())
assert audit['status']=='PASS'
res=audit['case_results']
FONT='C:/Windows/Fonts/arial.ttf'; BOLD='C:/Windows/Fonts/arialbd.ttf'
def font(n,b=False):return ImageFont.truetype(BOLD if b else FONT,n)
def hist(name):return json.loads((OUT/name/'history_si.json').read_text())
im=Image.new('RGB',(1520,1120),'#eff3f7');draw=ImageDraw.Draw(im)
draw.rectangle((0,0,1520,132),fill='#152c41')
draw.text((40,23),'I02B | Un assemblage qui peut se séparer',font=font(36,True),fill='white')
draw.text((40,77),'13 essais OpenRadioss : force, déchargement, énergie et rupture irréversible',font=font(23),fill='#c9deef')

COLORS=['#127e9b','#d06a13','#9b3681']
def panel(rect,title,xlabel,ylabel,xlim,ylim):
    x0,y0,x1,y1=rect
    draw.rounded_rectangle(rect,12,fill='white')
    draw.text((x0+22,y0+15),title,font=font(23,True),fill='#15314a')
    ax=(x0+75,y0+75,x1-28,y1-62)
    for i in range(6):
        xx=ax[0]+(ax[2]-ax[0])*i/5; yy=ax[3]-(ax[3]-ax[1])*i/5
        draw.line((xx,ax[1],xx,ax[3]),fill='#dce5ec')
        draw.line((ax[0],yy,ax[2],yy),fill='#dce5ec')
        draw.text((xx,ax[3]+10),f'{xlim[0]+(xlim[1]-xlim[0])*i/5:.2g}',anchor='mt',font=font(17),fill='#456075')
        draw.text((ax[0]-9,yy),f'{ylim[0]+(ylim[1]-ylim[0])*i/5:.3g}',anchor='rm',font=font(17),fill='#456075')
    draw.text((ax[0],y0+46),ylabel,font=font(17),fill='#456075')
    draw.text(((ax[0]+ax[2])/2,y1-25),xlabel,anchor='mm',font=font(18),fill='#456075')
    def xy(x,y):return (ax[0]+(x-xlim[0])/(xlim[1]-xlim[0])*(ax[2]-ax[0]),ax[3]-(y-ylim[0])/(ylim[1]-ylim[0])*(ax[3]-ax[1]))
    def line(x,y,color,width=3):
        stride=max(1,len(x)//2500)
        pts=[xy(float(xx),float(yy)) for xx,yy in zip(x[::stride],y[::stride])]
        if len(pts)>1:draw.line(pts,fill=color,width=width)
    return xy,line

xy,line=panel((30,155,745,555),'Énergie de séparation : hypothèses explicites','Ouverture de la liaison (mm)','Force (kN)',(0,1.1),(0,12))
for name,c,label in zip(['NORMAL_LOW_MONO_R2','NORMAL_BASE_MONO_R2','NORMAL_HIGH_MONO_R2'],COLORS,['1,139 J','2,848 J','5,696 J']):
    h=hist(name);line(h['separation_mm'],np.array(h['total_force_N'])/1000,c)
    idx=COLORS.index(c);draw.text((360+idx*118,213),label,font=font(17,True),fill=c)

xy,line=panel((775,155,1490,555),'Décharge et recharge avant rupture','Ouverture de la liaison (mm)','Force (kN)',(0,.22),(0,12))
h=hist('NORMAL_BASE_CYCLE_R2'); t=np.array(h['time_ms']);d=np.array(h['separation_mm']);F=np.array(h['total_force_N'])/1000
for lo,hi,c in [(0,1,'#127e9b'),(1,2,'#d06a13'),(2,3,'#9b3681')]:
    mask=(t>=lo)&(t<=hi);line(d[mask],F[mask],c,4)
draw.text((890,420),'Glissement conservé après décharge : 0,1875 mm',font=font(18),fill='#334d61')

xy,line=panel((30,580,745,980),'Même masse, même vitesse : réponse différente','Temps (ms)','Ouverture (mm)',(0,.2),(0,2.0))
dyn=['DYNAMIC_G_LOW_V10_R1','DYNAMIC_HIGH_ENERGY_R1','DYNAMIC_G_HIGH_V10_R1']
for name,c in zip(dyn,COLORS):
    h=hist(name);line(h['time_ms'],h['separation_mm'],c,4)
draw.text((130,691),'100 g à 10 m/s : énergie initiale 5,000 J',font=font(19,True),fill='#334d61')

draw.rounded_rectangle((775,580,1490,980),12,fill='white')
draw.text((800,599),'Résultat du test d’énergie à 5 J',font=font(23,True),fill='#15314a')
for col,x in [('Hypothèse',805),('Liaison',1010),('Énergie cinétique',1230)]:draw.text((x,653),col,font=font(19,True),fill='#456075')
for index,(name,c,label) in enumerate(zip(dyn,COLORS,['basse','centrale','haute'])):
    y=697+index*57; r=res[name]
    draw.text((805,y),f"{label} : {r['expected_full_separation_energy_J']:.3f} J",font=font(19),fill=c)
    draw.text((1010,y),'séparée' if r['any_complete_separation'] else 'arrêt / retour',font=font(19,True),fill=c)
    draw.text((1250,y),f"{r['final_kinetic_J']:.3f} J",font=font(19),fill=c)
draw.text((800,890),'Même force maximale : 11,392 kN',font=font(19,True),fill='#334d61')
draw.text((800,924),'Une force de rupture seule ne fixe pas l’issue.',font=font(19),fill='#334d61')

draw.rounded_rectangle((30,999,1490,1095),10,fill='#fbe8d5')
draw.text((52,1015),'Vérification numérique du connecteur. Les énergies de séparation restent des hypothèses.',font=font(22,True),fill='#6c371b')
draw.text((52,1053),'Pas encore de plaques déformables, de rupture mixte ni de prédiction de l’impact du Boeing complet.',font=font(21),fill='#6c371b')
path=OUT/'synthese_impact_i02b.png'; im.save(path)

# FFmpeg encodes cached verified frames only; all old files are read-only here.
ffmpeg=shutil.which('ffmpeg');ffprobe=shutil.which('ffprobe')
source=ROOT/'wtc1_3d_v4/renders/impact_i02a/annotated_frames'
video=MEDIA/'I02A_etats_verifies.mp4'
hash_before={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(source.glob('state_*.png'))}
assert len(hash_before)==25
command=[ffmpeg,'-hide_banner','-loglevel','error','-n','-framerate','5','-i',str(source/'state_%03d.png'),
         '-c:v','libx264','-crf','18','-pix_fmt','yuv420p','-r','30',str(video)]
if not video.exists():
    p=subprocess.run(command,capture_output=True,text=True,timeout=60)
    (MEDIA/'encoding.log').write_text(p.stdout+p.stderr,encoding='utf-8')
    if p.returncode:raise RuntimeError(p.stderr)
probe=subprocess.run([ffprobe,'-v','error','-select_streams','v:0','-show_entries','stream=codec_name,width,height,nb_frames,duration','-of','json',str(video)],capture_output=True,text=True,timeout=30)
info=json.loads(probe.stdout)['streams'][0]
checks={'codec_h264':info['codec_name']=='h264','size_960_620':(info['width'],info['height'])==(960,620),
        'frames_150':int(info['nb_frames'])==150,'duration_5s':abs(float(info['duration'])-5)<.001,
        'source_frames_unchanged':all(hashlib.sha256((source/n).read_bytes()).hexdigest()==h for n,h in hash_before.items())}
meta={'status':'PASS' if all(checks.values()) else 'FAIL','checks':checks,'summary_png':str(path.relative_to(ROOT)),
      'video':str(video.relative_to(ROOT)),'video_sha256':hashlib.sha256(video.read_bytes()).hexdigest(),
      'ffmpeg_version':subprocess.run([ffmpeg,'-version'],capture_output=True,text=True).stdout.splitlines()[0],
      'ffmpeg_executable':ffmpeg,'command':command,'probe':info,'source_frame_sha256':hash_before,
      'scope':'MP4 packages prior I02A states only. The new I02B joint is not yet applied to the wing; no frame interpolation.'}
(OUT/'presentation.json').write_text(json.dumps(meta,indent=2),encoding='utf-8')
print(json.dumps({'status':meta['status'],'summary':str(path),'video':str(video),'checks':checks},indent=2))
