"""Static scientific summary drawn from saved audited panel states, not Blender."""
import argparse, hashlib, json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[2]
def read(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--output',required=True); args=ap.parse_args(); out=(ROOT/args.output).resolve()
    if not out.is_relative_to(ROOT/'tmp/v11r_integrated_panel'): raise ValueError('Render new scratch artifacts only')
    if read(out/'release_audit.json')['status']!='PASS': raise ValueError('Independent audit required')
    target=out/'synthese_v11r.png'
    if target.exists(): raise ValueError('Do not overwrite image')
    r=read(out/'results_v11r.json'); im=Image.new('RGB',(1500,1060),'#101923'); d=ImageDraw.Draw(im)
    fonts='C:/Windows/Fonts/'; title=ImageFont.truetype(fonts+'segoeuib.ttf',30); normal=ImageFont.truetype(fonts+'segoeui.ttf',20); small=ImageFont.truetype(fonts+'segoeui.ttf',17)
    d.text((36,22),'V11R | Panneau intégré : ce qui est effectivement calculé',font=title,fill='white')
    d.text((36,70),'Dalle + ferme + contacts + attaches + appuis + gravité + profils thermiques V11P',font=normal,fill='#8edbc7')
    d.text((36,103),'Cas synthétiques. Aucun incendie réel ni effondrement validé. Arrêt avant sortie du domaine déclaré.',font=small,fill='#e2b77c')
    y=154; d.text((36,y),'Cas',font=normal,fill='white'); d.text((300,y),'Charge',font=normal,fill='white'); d.text((405,y),'Dernier temps thermique engagé',font=normal,fill='white'); d.text((950,y),'Cause d’arrêt',font=normal,fill='white')
    labels={'STOP_PRELOAD_ELASTIC_GUARD':'Garde-fou dès le chargement froid','STOP_HEATING_ELASTIC_GUARD':'Garde-fou élastique',
        'STOP_PRELOAD_UNQUALIFIED_SUPPORT_DIRECTION':'Direction d’appui non qualifiée (froid)',
        'STOP_HEATING_UNQUALIFIED_SUPPORT_DIRECTION':'Direction d’appui non qualifiée','REACHED_SOURCE_END':'Fin de la fenêtre sauvegardée',
        'UNRESOLVED_SOLVER_NOT_COLLAPSE':'Solveur non résolu'}
    for n,s in r['summaries'].items():
        y+=32; last=s['last']; d.text((36,y),n,font=small,fill='#d5e4ef'); d.text((300,y),str(s['spec']['gravity']),font=small,fill='white')
        width=int(last['time_s']/90*370); d.rectangle((410,y+5,810,y+22),fill='#223447')
        if width>0: d.rectangle((410,y+5,410+width,y+22),fill='#57c6b1')
        d.text((825,y),f"{last['time_s']:.3f} s",font=small,fill='white'); d.text((950,y),labels.get(s['status'],s['status']),font=small,fill='#e2b77c')
    ref=read(out/'REF_G025.json'); inv=read(out/'REF_G025_inventory.json'); last=ref['history'][-1]
    y0=785; d.line((40,y0,1460,y0),fill='#40576b',width=2)
    d.text((36,y0+15),f"Panneau de référence — dernier état engagé : t={last['time_s']:.6g} s ; g={last['gravity']}",font=normal,fill='white')
    pts=[(65+xx/inv['span_m']*1360,900-last['u'][i]*30000) for xx,i in zip(inv['slab_x_m'],inv['slab_w_dofs'])]
    d.line((65,900,1425,900),fill='#476073',width=2); d.line(pts,fill='#71dbc2',width=4)
    d.text((36,965),f"Déformée verticale de la dalle : {last['max_slab_down_m']*1000:.6g} mm vers le bas au maximum. Échelle verticale amplifiée.",font=small,fill='#d5e4ef')
    d.text((36,997),'La figure montre des états enregistrés, pas une animation physique de la tour. Les essais refusés ne sont pas dessinés.',font=small,fill='#e2b77c')
    im.save(target)
    meta={'iteration':'V11R','source_results_sha256':sha(out/'results_v11r.json'),'source_reference_sha256':sha(out/'REF_G025.json'),
          'displayed_phase':last['phase'],'displayed_time_s':last['time_s'],'displayed_gravity':last['gravity'],'vertical_pixels_per_m':30000,
          'reference_panel_energy_qualified':ref['summary']['energy_qualified'],'blender_changed':False,'physical_tower_animation':False}
    (out/'render_metadata.json').write_text(json.dumps(meta,indent=2)+'\n',encoding='utf-8')
    mf=read(out/'offline_manifest.json')
    for p in [target,out/'render_metadata.json']: mf['output_sha256'][p.name]=sha(p)
    # Package metadata only; none of the hashed numerical outputs are changed.
    (out/'offline_manifest.json').write_text(json.dumps(mf,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps(meta))

if __name__=='__main__': main()
