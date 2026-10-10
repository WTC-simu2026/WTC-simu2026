"""Encode labelled native-state replay; cannot claim10 physical seconds."""
import json,subprocess
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from run_aircraft_a17 import ROOT,OUT,CFG,read,dump,now,guard,execute,env,streamsha

def main():
    guard();c=read(CFG)['video'];d=OUT/'video';r=read(d/'render_manifest.json');assert r['unique_native_states']==21 and not r['objective1_complete'];ad=d/'labelled';assert not ad.exists();ad.mkdir();z=np.load(ROOT/c['source']/'verified_states_SI.npz');times=z['time_s'];font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',28);bold=ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf',30);small=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',25);frames=[]
    for i,t in enumerate(times):
        p=Image.new('RGB',(2560,720),(12,23,33))
        for j,view in enumerate(['whole','nose']):
            im=Image.open(d/view/f'state_{i:03d}.png').convert('RGB');assert im.size==(1280,720);p.paste(im,(j*1280,0));im.close()
        dr=ImageDraw.Draw(p);dr.rectangle((0,0,2560,80),fill=(12,23,33));dr.rectangle((0,650,2560,720),fill=(12,23,33));dr.line((1280,80,1280,650),fill=(99,115,129),width=2)
        dr.text((25,12),'Impact avion–façade · aperçu 3D des premiers 10 millisecondes',font=bold,fill='#edf5fc');dr.text((1900,12),f'Temps simulé : {t*1000:8.4f} ms',font=bold,fill='#ffcf76');dr.text((25,49),'Avion complet et façade représentative',font=font,fill='#b6cedf');dr.text((1305,49),'Détail du nez · déplacements à échelle réelle',font=font,fill='#b6cedf')
        dr.text((25,659),'Rouge : point de peau totalement endommagé · jaune : dommage partiel · cœur encore intact',font=small,fill='#edb28e');dr.text((25,688),'0,010 s physique, lues en 6,3 s · pas de fragments libres · aperçu exploratoire · objectif final : 10 s physiques',font=small,fill='#b6cedf');fn=ad/f'state_{i:03d}.png';p.save(fn);frames.append(p)
    mp=d/'APERCU_A16_10ms_ralenti.mp4';assert not mp.exists();fm=Path('C:/ProgramData/chocolatey/bin/ffmpeg.exe');fp=Path('C:/ProgramData/chocolatey/bin/ffprobe.exe')
    args=['-n','-framerate','10/3','-i',str(ad/'state_%03d.png'),'-c:v','libx264','-preset','medium','-crf','18','-pix_fmt','yuv420p','-r','30','-movflags','+faststart',str(mp)];assert execute(fm,args,d,'encode.log',180,env())
    gif=d/'APERCU_A16_10ms_ralenti.gif';assert not gif.exists();gf=[p.resize((1280,360),Image.Resampling.LANCZOS) for p in frames];gf[0].save(gif,save_all=True,append_images=gf[1:],duration=300,loop=0,disposal=2,optimize=False)
    for p in frames+gf:p.close()
    result=subprocess.run([str(fp),'-v','error','-count_frames','-show_entries','stream=codec_name,width,height,avg_frame_rate,nb_read_frames:format=duration','-of','json',str(mp)],capture_output=True,text=True,check=True);meta=json.loads(result.stdout);dump(d/'ffprobe.json',meta);v=meta['streams'][0];assert v['codec_name']=='h264' and (v['width'],v['height'])==(2560,720) and int(v['nb_read_frames'])==189 and v['avg_frame_rate']=='30/1';assert abs(float(meta['format']['duration'])-6.3)<.001
    decoded=d/'decoded';decoded.mkdir();args=['-n','-i',str(mp),'-vf',r'select=eq(n\,0)+eq(n\,94)+eq(n\,188)','-fps_mode','vfr','-frames:v','3',str(decoded/'check_%02d.png')];assert execute(fm,args,d,'decode.log',90,env());assert len(list(decoded.glob('check_*.png')))==3
    sheet=Image.new('RGB',(1280,1080))
    for i,fn in enumerate(sorted(decoded.glob('check_*.png'))):
        im=Image.open(fn).convert('RGB');assert im.size==(2560,720);sheet.paste(im.resize((1280,360)),(0,i*360));im.close()
    sheet.save(d/'video_verification_contact_sheet.png');sheet.close()
    with Image.open(gif) as im:
        assert im.n_frames==21;dur=[]
        for i in range(im.n_frames):im.seek(i);dur.append(im.info.get('duration'))
    assert dur==[300]*21
    dump(d/'video_audit.json',{'created_utc':now(),'pass':True,'objective1_complete':False,'physical_duration_s':float(times[-1]),'physical_target_s':10,'display_duration_s':6.3,'fps':30,'MP4_frames':189,'unique_native_states':21,'GIF_frames':21,'GIF_duration_ms':dur,'geometry_interpolation':'none,9 identical frames per exact state','no_new_mechanics':'Blender and encoding only re-display saved native data','no_motion_extrapolation':True,'displacement_scale':1,'native_mesh_coordinates_verified':r['native_coordinate_max_abs_error_m']<1e-5,'files':[{'path':str(p.relative_to(ROOT)).replace('\\','/'),'sha256':streamsha(p),'bytes':p.stat().st_size} for p in [mp,gif]],'decoder_checked_frames':[0,94,188],'GUI_playback_verified':False,'source_solver_model_physical_qualification':False})
    print({'encoded':True,'physical_ms':float(times[-1]*1000),'display_s':6.3,'target_physical_s':10},flush=True)

if __name__=='__main__':main()
