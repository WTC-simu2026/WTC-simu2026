"""Annotate solver-rendered frames, make a short labelled diagnostic movie."""
import json,subprocess,hashlib
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[2]; out=ROOT/'wtc1_3d_v4/renders/impact_i01/final'
audit=json.loads((out/'render_audit.json').read_text()); history=json.loads((ROOT/'wtc1_simulation_v8/output/impact_i01_first_contact/M050/history_si.json').read_text())
font=lambda n:ImageFont.truetype('C:/Windows/Fonts/arial.ttf',n)
ffmpeg=Path('C:/Program Files/Wondershare/UniConverter 15/ffmpeg.exe')
frames=[]
for i,s in enumerate(audit['states']):
    im=Image.new('RGB',(1400,860),'#14232f'); d=ImageDraw.Draw(im)
    raw=Image.open(out/f'raw_{i:03d}.png').convert('RGB'); im.paste(raw,(10,115))
    d.text((25,18),'IMPACT-I01 | Premier contact 3D : caisson simplifie / facade',font=font(31),fill='white')
    d.rectangle((0,65,1400,107),fill='#8a3428'); d.text((25,72),'DIAGNOSTIC NUMERIQUE - PAS UN BOEING COMPLET - RUPTURE DESACTIVEE',font=font(24),fill='white')
    x=1030; d.text((x,128),f"t = {s['time_ms']:.4f} ms",font=font(28),fill='white')
    for y,txt in [(185,'Vitesse initiale : 198 m/s'),(220,'Caisson : 3 x 2 x 0,4 m'),(255,'Peau uniforme : 4 mm'),(290,'Masse calculee : 172,8 kg'),(340,'Bleu : facade acier'),(375,'Jaune : caisson aluminium'),(410,'Rouge : plasticite > 2 %'),(445,'(repere, pas seuil de rupture)'),(505,'Ni carburant ni fuselage'),(540,'Ni soudures destructibles'),(595,'Deplacements du solveur'),(630,'Aucune penetration imposee')]: d.text((x,y),txt,font=font(21),fill='white' if y<505 else '#d9b889')
    d.text((25,777),'Etats sauvegardes, ralentis ; deformation a echelle reelle. Maillage nominal 50 mm.',font=font(24),fill='white')
    d.text((25,813),'Ecart 50 -> 25 mm hors seuil : cette sequence ne valide ni la penetration ni la survie des ailes.',font=font(22),fill='#ffb390')
    p=out/f'labelled_{i:03d}.png'; im.save(p); frames.append(im)
frames[0].save(out/'impact_i01_contact_final.gif',save_all=True,append_images=frames[1:],duration=250,loop=0,optimize=False)
frames[-1].save(out/'impact_i01_apercu_final.png')
cmd=[str(ffmpeg),'-hide_banner','-loglevel','error','-n','-framerate','4','-i',str(out/'labelled_%03d.png'),'-c:v','libx264','-pix_fmt','yuv420p','-r','24',str(out/'impact_i01_contact_final.mp4')]
r=subprocess.run(cmd,capture_output=True,text=True); (out/'encoding.log').write_text(r.stdout+r.stderr,encoding='utf-8')
if r.returncode: raise RuntimeError(r.stderr)
meta={'frames':len(frames),'presentation_seconds':len(frames)/4,'solver_first_ms':audit['states'][0]['time_ms'],'solver_last_ms':audit['states'][-1]['time_ms'],'repeat_only_no_temporal_interpolation':True,'encoding_command':cmd,'ffmpeg_sha256':hashlib.sha256(ffmpeg.read_bytes()).hexdigest(),'permanent_warning_all_frames':True}
(out/'presentation.json').write_text(json.dumps(meta,indent=2),encoding='utf-8'); print(meta)
