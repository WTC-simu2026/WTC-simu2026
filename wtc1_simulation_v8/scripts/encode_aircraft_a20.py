"""Export honest replay of native states in MP4 and GIF, with physical timestamp."""
from run_aircraft_a20_whole import *
from run_aircraft_a17 import execute as external_execute
from PIL import Image,ImageDraw,ImageFont

def declare():
    whole_guard();p=OUT/'media_declaration.json';assert not p.exists()
    dump(p,{'declared_utc':now(),'iteration':'AIRCRAFT-A20','source':rel(D),'video_size':[2560,720],'fps':30,'hold_per_native_state_s':.3,'views':['whole','nose'],
        'physics':'Native coordinates and erosion only, no Blender dynamics, no ten-second extrapolation.',
        'physical_horizon_s':.02,'goal_target_physical_s':10,'objective1_complete':False,'labels':'Explicit physical timestamp, skin/core counts, local energy outcome, hypothetical rupture and material-domain failures.',
        'formats':['MP4/H264','GIF'],'render_CPU_threads':2,'native_reviews_not_physical_validation':True})

def main():
    whole_guard();d=OUT/'video';r=read(d/'render_manifest.json');review=read(D/'review.json');assert not (d/'video_audit.json').exists()
    z=np.load(D/'verified_states_SI.npz');times=z['time_s'];count=len(times);duration=count*.3;ad=d/'labelled';assert not ad.exists();ad.mkdir()
    bold=ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf',30);font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',28);small=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',25);frames=[]
    energy='bilan local réussi' if review['checks']['local_energy'] else 'bilan local échoué'
    for i,t in enumerate(times):
        p=Image.new('RGB',(2560,720),(12,23,33))
        for j,view in enumerate(['whole','nose']):
            with Image.open(d/view/f'state_{i:03d}.png') as im:assert im.size==(1280,720);p.paste(im.convert('RGB'),(j*1280,0))
        dr=ImageDraw.Draw(p);dr.rectangle((0,0,2560,80),fill=(12,23,33));dr.rectangle((0,645,2560,720),fill=(12,23,33));dr.line((1280,80,1280,645),fill=(99,115,129),width=2)
        dr.text((25,12),'Impact avion–façade · cœur du nez en 3D et ruptures natives',font=bold,fill='#edf5fc');dr.text((1900,12),f'Temps simulé : {t*1000:8.4f} ms',font=bold,fill='#ffcf76')
        dr.text((25,49),'Avion complet et façade représentative',font=font,fill='#b6cedf');dr.text((1305,49),'Détail du nez · cœur orange · peaux vertes · déplacements ×1',font=font,fill='#b6cedf')
        row=review['state_diagnostics'][i]
        dr.text((25,654),f"Éléments supprimés : peaux {row['deleted_skin_quads']}/1296 · cœur {row['deleted_core_bricks']}/648 · liaisons {row['deleted_cohesive_strips']}/624 · rupture hypothétique",font=small,fill='#edb28e')
        dr.text((25,685),f'{times[-1]:.6f} s physique · ralenti en {duration:.1f} s · {energy} · domaines matériels non validés · objectif : 10 s physiques',font=small,fill='#b6cedf')
        p.save(ad/f'state_{i:03d}.png');frames.append(p)
    mp=d/'APERCU_A20_20ms_ralenti.mp4';gif=d/'APERCU_A20_20ms_ralenti.gif';fm=Path('C:/ProgramData/chocolatey/bin/ffmpeg.exe');fp=Path('C:/ProgramData/chocolatey/bin/ffprobe.exe')
    assert external_execute(fm,['-n','-framerate','10/3','-i',str(ad/'state_%03d.png'),'-c:v','libx264','-preset','medium','-crf','18','-pix_fmt','yuv420p','-r','30','-movflags','+faststart',str(mp)],d,'encode.log',180,env())
    gf=[p.resize((1280,360),Image.Resampling.LANCZOS) for p in frames];gf[0].save(gif,save_all=True,append_images=gf[1:],duration=300,loop=0,disposal=2,optimize=False)
    for p in frames+gf:p.close()
    meta=json.loads(subprocess.run([str(fp),'-v','error','-count_frames','-show_entries','stream=codec_name,width,height,avg_frame_rate,nb_read_frames:format=duration','-of','json',str(mp)],capture_output=True,text=True,check=True).stdout);dump(d/'ffprobe.json',meta);v=meta['streams'][0]
    assert v['codec_name']=='h264' and [v['width'],v['height']]==[2560,720] and int(v['nb_read_frames'])==count*9 and v['avg_frame_rate']=='30/1' and abs(float(meta['format']['duration'])-duration)<.001
    decoded=d/'decoded';decoded.mkdir();assert external_execute(fm,['-n','-i',str(mp),'-vf',f'select=eq(n\\,0)+eq(n\\,{count*9//2})+eq(n\\,{count*9-1})','-fps_mode','vfr','-frames:v','3',str(decoded/'check_%02d.png')],d,'decode.log',90,env())
    sheet=Image.new('RGB',(1280,1080));files=sorted(decoded.glob('check_*.png'));assert len(files)==3
    for i,p in enumerate(files):
        with Image.open(p) as im:assert im.size==(2560,720);sheet.paste(im.convert('RGB').resize((1280,360)),(0,i*360))
    sheet.save(d/'video_verification_contact_sheet.png');sheet.close()
    with Image.open(gif) as im:
        assert im.n_frames==count
        for i in range(count):im.seek(i);assert im.info.get('duration')==300
    dump(d/'video_audit.json',{'created_utc':now(),'pass':True,'objective1_complete':False,'physical_duration_s':float(times[-1]),'physical_target_s':10,'display_duration_s':duration,'fps':30,'MP4_frames':count*9,'unique_native_states':count,'GIF_frames':count,
        'native_geometry_and_erosion_used':True,'native_coordinates_max_error_m':r['native_coordinate_max_abs_error_m'],'no_motion_extrapolation':True,'displacement_scale':1,'physics_engine_used':False,'source_solver_model_physical_qualification':False,
        'files':[{'path':rel(p),'sha256':streamsha(p),'bytes':p.stat().st_size} for p in [mp,gif]],'decoded_checked_frames':[0,count*9//2,count*9-1],'GUI_playback_verified':False})
    print({'physical_ms':float(times[-1]*1000),'display_s':duration,'objective1_complete':False},flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['declare','main']);globals()[p.parse_args().action]()
