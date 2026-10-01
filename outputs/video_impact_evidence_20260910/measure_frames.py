"""Pixel-level diagnostics; approximate repeat tests are not source authenticity tests."""
import json, hashlib, time, subprocess
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from audit_video import ROOT, CFG, digest, save
t0=time.perf_counter()
font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',20)
small=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',17)
report={}
for key,folder in [('Evidence1','Evidence1_0_359'),('Evidence2','Evidence2_2790_2940')]:
    files=sorted((ROOT/folder).glob('*.png')); rows=[]; prev=None
    for p in files:
        a=np.asarray(Image.open(p).convert('RGB'))
        idx=int(p.stem.split('_f')[1].split('_')[0])
        row={'index':idx,'seconds_nominal':idx/CFG['fps'][key],'file':str(p.relative_to(ROOT)),'pixel_sha256':hashlib.sha256(a.tobytes()).hexdigest()}
        if prev is not None:
            row['adjacent_mae_rgb_0_255']=float(np.abs(a.astype(float)-prev).mean())
        rows.append(row); prev=a
    report[key]={'frames':len(rows),'unique_decoded_pixel_hashes':len({r['pixel_sha256'] for r in rows}),'adjacent_identical_pairs':sum(r.get('adjacent_mae_rgb_0_255',-1)==0 for r in rows),'rows':rows}
    if key=='Evidence1':
        # Very small fixed thumbnails identify candidate repeated whole views.
        thumb=[np.asarray(Image.open(p).convert('L').resize((72,48)),dtype=float) for p in files]
        matches=[]
        for i in range(60,len(files)):
            ds=[float(np.abs(thumb[i]-thumb[j]).mean()) for j in range(i-45)]
            j=int(np.argmin(ds))
            if ds[j]<2.0: matches.append({'index':i,'earlier_index':j,'thumbnail_mae':ds[j]})
        report[key]['nonadjacent_near_repeat_candidates_mae_lt_2']=matches
save('pixel_diagnostics.json',report)
# Identical, fixed crop and nearest-neighbour enlargement: no enhancement.
indices=[2862,2865,2868,2871,2875,2879]
rect=(580,0,790,440)
out=Image.new('RGB',(3*430,2*920),(24,28,34)); d=ImageDraw.Draw(out)
for j,i in enumerate(indices):
    p=next((ROOT/'Evidence2_2790_2940').glob(f'*_f{i:05d}_*.png'))
    im=Image.open(p).convert('RGB').crop(rect).resize((420,880),Image.Resampling.NEAREST)
    x=(j%3)*430; y=(j//3)*920
    out.paste(im,(x,y+30)); d.text((x+5,y+3),f'f{i} - {i/30:.3f} s - x2 pixels',font=small,fill='white')
out.save(ROOT/'aile_six_images_pixels.png')
save('crop_manifest.json',{'indices':indices,'crop_xyxy':rect,'resize':'nearest neighbour 2x','no_denoising_no_interpolation_no_ai':True})
# Compact annotated three-frame evidence. Regions indicate the question, not a segmented wing.
out=Image.new('RGB',(1260,570),(24,28,34)); d=ImageDraw.Draw(out)
moving_crops={2868:(600,100,790,345),2872:(595,220,785,465),2879:(560,345,750,590)}
for j,(i,box) in enumerate(moving_crops.items()):
    p=next((ROOT/'Evidence2_2790_2940').glob(f'*_f{i:05d}_*.png'))
    im=Image.open(p).convert('RGB').crop(box).resize((380,490),Image.Resampling.NEAREST)
    x=j*420; out.paste(im,(x+10,50)); d.text((x+10,12),f'Evidence2 : {i/30:.3f} s | f{i}',font=font,fill='white')
    d.text((x+10,545),'Recadrage mobile x2, sans amelioration',font=small,fill='white')
out.save(ROOT/'aile_comparaison_finale.png')
save('moving_crop_manifest.json',{'crop_xyxy_by_frame':moving_crops,'scale':2,'interpolation':'nearest neighbour','supersedes':'aile_comparaison.png whose fixed crop clipped the last aircraft'})
# Encoded presentation timestamps (stts+ctts); the sequencer labels use nominal fps.
intake=json.loads((ROOT/'intake.json').read_text(encoding='utf-8'))
timing={}
for key in ['Evidence1','Evidence2']:
    tables=intake['sources'][key]['mp4_tables']; md=next(x for x in tables if x['path'].endswith('/mdhd'))
    st=next(x for x in tables if x['path'].endswith('/stts'))
    ct=next((x for x in tables if x['path'].endswith('/ctts')),None)
    durations=[v for n,v in st['entries'] for _ in range(n)]
    offsets=[v for n,v in ct['entries'] for _ in range(n)] if ct else [0]*len(durations)
    dts=0; pts=[]
    for duration,offset in zip(durations,offsets): pts.append(dts+offset); dts+=duration
    pts=sorted(pts); start=pts[0]; times=[(x-start)/md['timescale'] for x in pts]
    timing[key]={'sample_count':len(times),'pts_relative_to_first_s':times,'max_deviation_from_nominal_s':max(abs(t-i/CFG['fps'][key]) for i,t in enumerate(times)),'note':'Relative media PTS; absolute edit-list origin not used. No capture clock inference.'}
save('presentation_timing.json',timing)
r=subprocess.run(['C:/Program Files/PowerShell/7/pwsh.exe','-NoProfile','-File',str(ROOT.parents[1]/'harness/tools/Test-WtcHarness.ps1')],capture_output=True,text=True,encoding='utf-8')
(ROOT/'harness_recheck.txt').write_text(r.stdout+r.stderr,encoding='utf-8'); assert r.returncode==0
save('analysis_runtime.json',{'seconds':time.perf_counter()-t0,'numpy':np.__version__})
print({k:{a:b for a,b in v.items() if a not in ['rows','nonadjacent_near_repeat_candidates_mae_lt_2']} for k,v in report.items()})
print({k:{a:b for a,b in v.items() if a!='pts_relative_to_first_s'} for k,v in timing.items()})
