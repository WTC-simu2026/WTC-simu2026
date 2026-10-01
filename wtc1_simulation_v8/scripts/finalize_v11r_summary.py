"""Second non-overwriting figure, corrected frame and explicit energy-status flags."""
import argparse, hashlib, json, subprocess, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[2]
def read(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--output',required=True); args=ap.parse_args(); out=(ROOT/args.output).resolve()
    if not out.is_relative_to(ROOT/'tmp/v11r_integrated_panel'): raise ValueError('Scratch package only')
    target=out/'synthese_v11r_final.png'
    if target.exists(): raise ValueError('New figure already exists')
    r=read(out/'results_v11r.json'); ref=read(out/'REF_G025.json'); inv=read(out/'REF_G025_inventory.json'); last=ref['history'][-1]
    im=Image.new('RGB',(1500,1080),'#101923'); d=ImageDraw.Draw(im); fonts='C:/Windows/Fonts/'
    title=ImageFont.truetype(fonts+'segoeuib.ttf',30); normal=ImageFont.truetype(fonts+'segoeui.ttf',20); small=ImageFont.truetype(fonts+'segoeui.ttf',17)
    d.text((36,22),'V11R | Panneau intégré : ce qui est effectivement calculé',font=title,fill='white')
    d.text((36,70),'Dalle + ferme + contacts + attaches + appuis + gravité + profils thermiques V11P',font=normal,fill='#8edbc7')
    d.text((36,106),'Exposition synthétique, non WTC. Aucun incendie réel ni effondrement validé.',font=small,fill='#e2b77c')
    y=151
    for x,label in [(36,'Cas'),(300,'Charge'),(405,'Dernier temps thermique engagé'),(945,'Arrêt / qualification')]: d.text((x,y),label,font=normal,fill='white')
    for name,s in r['summaries'].items():
        y+=32; t=s['last']['time_s']; color='#57c6b1' if s['energy_qualified'] else '#e8a34e'
        d.text((36,y),name,font=small,fill='#d5e4ef'); d.text((300,y),str(s['spec']['gravity']),font=small,fill='white')
        d.rectangle((410,y+5,810,y+22),fill='#223447')
        if t>0: d.rectangle((410,y+5,410+int(t/90*400),y+22),fill=color)
        d.text((825,y),f'{t:.3f} s',font=small,fill='white')
        label='Fin de la fenêtre (90 s)' if s['status']=='REACHED_SOURCE_END' else 'Garde-fou élastique' if 'ELASTIC_GUARD' in s['status'] else s['status']
        if not s['energy_qualified']: label+=' ; énergie non qualifiée'
        d.text((945,y),label,font=small,fill=color)
    d.text((36,712),'Vert : bilan de travail/énergie qualifié sur les états engagés. Orange : précision insuffisante du travail.',font=small,fill='#d5e4ef')
    d.text((36,742),'Le garde-fou arrête le calcul avant fissuration ; il ne prédit ni rupture du panneau ni stabilité de la tour.',font=small,fill='#e2b77c')
    d.line((36,784,1464,784),fill='#40576b',width=2)
    d.text((36,803),f"Référence : g=0,25 ; t={last['time_s']:.6g} s ; dalle et ferme en équilibre avec leurs appuis",font=normal,fill='white')
    baseline=873; amplification=6000
    pts=[(65+xx/inv['span_m']*1360,baseline-last['u'][i]*amplification) for xx,i in zip(inv['slab_x_m'],inv['slab_w_dofs'])]
    if any(not (850<=y<=960) for x,y in pts): raise ValueError('Displacement curve outside reserved frame')
    d.line((65,baseline,1425,baseline),fill='#476073',width=2); d.line(pts,fill='#71dbc2',width=4)
    d.text((36,980),f"Flèche maximale de dalle : {last['max_slab_down_m']*1000:.4f} mm. Déformée amplifiée pour la lecture.",font=small,fill='#d5e4ef')
    d.text((36,1016),'État mécanique sauvegardé, pas une animation physique de la tour. Aucun essai refusé n’est dessiné.',font=small,fill='#e2b77c')
    im.save(target)
    metadata={'iteration':'V11R','image':target.name,'supersedes_visual_only':'synthese_v11r.png','reason':'First curve exceeded frame; energy failures now explicitly highlighted.',
        'source_results_sha256':sha(out/'results_v11r.json'),'source_reference_sha256':sha(out/'REF_G025.json'),
        'reference_energy_qualified':ref['summary']['energy_qualified'],'vertical_pixels_per_m':amplification,'curve_inside_frame':True,
        'energy_unqualified_cases':[n for n,s in r['summaries'].items() if not s['energy_qualified']]}
    meta=out/'render_metadata_final.json'; meta.write_text(json.dumps(metadata,indent=2)+'\n',encoding='utf-8')
    mf=read(out/'offline_manifest.json'); mf['input_sha256'][Path(__file__).resolve().relative_to(ROOT).as_posix()]=sha(__file__)
    for p in [target,meta]: mf['output_sha256'][p.name]=sha(p)
    (out/'offline_manifest.json').write_text(json.dumps(mf,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    audit=subprocess.run([sys.executable,str(ROOT/'wtc1_simulation_v8/scripts/audit_v11r_integrated_panel.py'),'--output',str(out),'--read-only'],check=True,capture_output=True,text=True)
    result=json.loads(audit.stdout); destination=out/'release_audit_final.json'
    if destination.exists(): raise ValueError('Final audit already exists')
    destination.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result))

if __name__=='__main__': main()
