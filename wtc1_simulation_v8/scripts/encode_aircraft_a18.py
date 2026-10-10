"""Encode labelled native-state replay; cannot claim10 physical seconds."""
import json,subprocess
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from run_aircraft_a18 import ROOT,OUT,CFG,read,dump,now,guard,execute,env,streamsha

def main():
    guard();c=read(CFG)['video'];d=OUT/'video';r=read(d/'render_manifest.json');assert r['unique_native_states']>1 and not r['objective1_complete'];ad=d/'labelled';ad.mkdir(exist_ok=True);z=np.load(ROOT/c['source']/'verified_states_SI.npz');times=z['time_s'];diagnostics=read(ROOT/c['source']/'review.json')['state_diagnostics'];count=len(times);duration=count*.3;font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',28);bold=ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf',30);small=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',25);frames=[]
    for i,t in enumerate(times):
        p=Image.new('RGB',(2560,720),(12,23,33))
        for j,view in enumerate(['whole','nose']):
            im=Image.open(d/view/f'state_{i:03d}.png').convert('RGB');assert im.size==(1280,720);p.paste(im,(j*1280,0));im.close()
        dr=ImageDraw.Draw(p);dr.rectangle((0,0,2560,80),fill=(12,23,33));dr.rectangle((0,650,2560,720),fill=(12,23,33));dr.line((1280,80,1280,650),fill=(99,115,129),width=2)
        dr.text((25,12),'Impact avion–façade · aperçu 3D des premières 20 millisecondes',font=bold,fill='#edf5fc');dr.text((1900,12),f'Temps simulé : {t*1000:8.4f} ms',font=bold,fill='#ffcf76');dr.text((25,49),'Avion complet et façade représentative',font=font,fill='#b6cedf');dr.text((1305,49),'Détail du nez · déplacements à échelle réelle',font=font,fill='#b6cedf')
        dr.text((25,659),f"Liaisons rompues : {diagnostics[i]['deleted_cohesive_strips']}/624 · groupes séparés du corps : {diagnostics[i]['detached_components']} · rouge/jaune : dommage de peau · rupture hypothétique",font=small,fill='#edb28e');dr.text((25,688),f'{times[-1]:.6f} s physique · ralenti en {duration:.1f} s · bilan énergétique échoué · modèle non validé · objectif final : 10 s physiques',font=small,fill='#b6cedf');fn=ad/f'state_{i:03d}.png'
        if fn.exists():
            with Image.open(fn) as saved:assert np.array_equal(np.asarray(saved.convert('RGB')),np.asarray(p))
        else:p.save(fn)
        frames.append(p)
    mp=d/'APERCU_A18_20ms_ralenti.mp4';fm=Path('C:/ProgramData/chocolatey/bin/ffmpeg.exe');fp=Path('C:/ProgramData/chocolatey/bin/ffprobe.exe')
    args=['-n','-framerate','10/3','-i',str(ad/'state_%03d.png'),'-c:v','libx264','-preset','medium','-crf','18','-pix_fmt','yuv420p','-r','30','-movflags','+faststart',str(mp)]
    if not mp.exists():assert execute(fm,args,d,'encode.log',180,env())
    else:
        assert (d/'encode.log').exists();dump(OUT/'external_metadata_failure_retained.json',{'created_utc':now(),'initial_wrapper_exit_code':1,'cause':'Shared native helper requires executables below workspace; Blender and FFmpeg are outside. Media outputs already exist and are verified, not rerendered or overwritten.','native_exit_code_and_exact_wall_seconds_not_recorded':True,'renderer_reported_seconds':r['render_seconds'],'encoder_arguments':args,'blender_executable':'C:/Program Files/Blender Foundation/Blender 5.2/blender.exe','blender_sha256':streamsha(Path('C:/Program Files/Blender Foundation/Blender 5.2/blender.exe')),'encoder_executable':str(fm),'encoder_sha256':streamsha(fm),'prior_logs_retained':['blender_render.log','video_encoding.log','video/encode.log'],'new_external_helper_corrected':True,'metadata_failure_is_not_hidden':True,'Blender_thumbnail_write_denied':'Renderer attempted optional thumbnail outside writable roots; PNG frames and blend file were created in workspace.'})
    gif=d/'APERCU_A18_20ms_ralenti.gif';assert not gif.exists();gf=[p.resize((1280,360),Image.Resampling.LANCZOS) for p in frames];gf[0].save(gif,save_all=True,append_images=gf[1:],duration=300,loop=0,disposal=2,optimize=False)
    for p in frames+gf:p.close()
    result=subprocess.run([str(fp),'-v','error','-count_frames','-show_entries','stream=codec_name,width,height,avg_frame_rate,nb_read_frames:format=duration','-of','json',str(mp)],capture_output=True,text=True,check=True);meta=json.loads(result.stdout);dump(d/'ffprobe.json',meta);v=meta['streams'][0];assert v['codec_name']=='h264' and (v['width'],v['height'])==(2560,720) and int(v['nb_read_frames'])==count*9 and v['avg_frame_rate']=='30/1';assert abs(float(meta['format']['duration'])-duration)<.001
    decoded=d/'decoded';decoded.mkdir();args=['-n','-i',str(mp),'-vf',f'select=eq(n\\,0)+eq(n\\,{count*9//2})+eq(n\\,{count*9-1})','-fps_mode','vfr','-frames:v','3',str(decoded/'check_%02d.png')];assert execute(fm,args,d,'decode.log',90,env());assert len(list(decoded.glob('check_*.png')))==3
    sheet=Image.new('RGB',(1280,1080))
    for i,fn in enumerate(sorted(decoded.glob('check_*.png'))):
        im=Image.open(fn).convert('RGB');assert im.size==(2560,720);sheet.paste(im.resize((1280,360)),(0,i*360));im.close()
    sheet.save(d/'video_verification_contact_sheet.png');sheet.close()
    with Image.open(gif) as im:
        assert im.n_frames==count;dur=[]
        for i in range(im.n_frames):im.seek(i);dur.append(im.info.get('duration'))
    assert dur==[300]*count
    dump(d/'video_audit.json',{'created_utc':now(),'pass':True,'objective1_complete':False,'physical_duration_s':float(times[-1]),'physical_target_s':10,'display_duration_s':duration,'fps':30,'MP4_frames':count*9,'unique_native_states':count,'GIF_frames':count,'GIF_duration_ms':dur,'geometry_interpolation':'none,9 identical frames per exact state','no_new_mechanics':'Blender and encoding only re-display saved native data','no_motion_extrapolation':True,'displacement_scale':1,'native_mesh_coordinates_verified':r['native_coordinate_max_abs_error_m']<1e-5,'files':[{'path':str(p.relative_to(ROOT)).replace('\\','/'),'sha256':streamsha(p),'bytes':p.stat().st_size} for p in [mp,gif]],'decoder_checked_frames':[0,count*9//2,count*9-1],'GUI_playback_verified':False,'source_solver_model_physical_qualification':False})
    print({'encoded':True,'physical_ms':float(times[-1]*1000),'display_s':duration,'target_physical_s':10},flush=True)

if __name__=='__main__':main()
