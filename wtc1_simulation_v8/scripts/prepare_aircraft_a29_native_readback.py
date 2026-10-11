"""Keep w2 Starter-only rejection and use the actual TYPE6 readback format."""
from run_aircraft_a29 import *

def main():
    h=harness();assert h['Status']=='PASS';dump(OUT/'harness_before_native_readback.json',h)
    old=Path(__file__).with_name('test_aircraft_a29_frame_corrected.py');target=old.with_name('test_aircraft_a29_native_readback.py');cfg=CFG.with_name('aircraft_a29_native_readback.json')
    d=OUT/'w2/PATCH_NORMAL_X_N12';assert (d/'retained_failure.json').exists() and not (d/'engine.log').exists();assert not cfg.exists() and not target.exists()
    c=read(CFG.with_name('aircraft_a29_frame_corrected.json'));c.update(revision='w3',declared_utc=now(),parent_configuration_sha256=streamsha(CFG.with_name('aircraft_a29_frame_corrected.json')),native_reader_correction='w2 produced correct material axes and zero-warning Starter, but the validation reader expected TYPE22 flags. TYPE6 SOLID-HEXA reports Isolid,Ismstr,Icpre,Iframe,IHKT,Itetra4,Itetra10,IMATVIS,ICONTROL. Only reader changes; material, geometry, frames, loading and references unchanged. w2 Engine never launched, its outputs retained.')
    dump(cfg,c);dump(OUT/'native_readback_guard.json',{'created_utc':now(),'sha256':streamsha(cfg),'before_new_native_solvers':True})
    s=old.read_text(encoding='utf-8');changes=[]
    for a,b in [('aircraft_a29_frame_corrected.json','aircraft_a29_native_readback.json'),("OUT/'frame_corrected_guard.json'","OUT/'native_readback_guard.json'"),("(\"OUT/'w2'\",\"OUT/'w2'\")","(\"OUT/'w2'\",\"OUT/'w3'\")"),("d=OUT/'w2'/cid","d=OUT/'w3'/cid"),('native_case_summary_w2.json','native_case_summary_w3.json'),('runner_w2_derivation.json','runner_w3_derivation.json'),('review_w2_derivation.json','review_w3_derivation.json'),('A29_W2_3D_','A29_W3_3D_')]:
        n=s.count(a);assert n>0,a;s=s.replace(a,b);changes.append({'old':a,'new':b,'count':n})
    start=s.index('def validate_native_frame(d,n):');end=s.index("if __name__=='__main__':",start)
    reader='''def validate_native_frame(d,n):
    t=(d/(n+'_0000.out')).read_text();m=re.search(r'SKEW SYSTEM SETS.*?VECTORS.*?ORIGIN\\s+1\\s+0\\s+0\\s+0\\s+([^\\n]+)\\n\\s+([^\\n]+)\\n\\s+([^\\n]+)',t,re.S);assert m,'Missing native skew readback'
    axes=np.array([[float(v) for v in line.split()][:3] for line in m.groups()]);expected=np.array([[0,1,0],[-1,0,0],[0,0,1]])
    header='Isolid  Ismstr   Icpre  Iframe    IHKT Itetra4 Itetra10 IMATVIS ICONTROL';p=re.search(re.escape(header)+r'\\s+'+r'\\s+'.join([r'(\\d+)']*9),t);assert p,'Missing TYPE6 part flags'
    flags=list(map(int,p.groups()));checks={'axes':bool(np.allclose(axes,expected,atol=1e-6,rtol=0)),'native_flags':flags==[18,2,3,2,0,0,0,0,0]};dump(d/'native_frame_gate.json',{'created_utc':now(),'axes_rows':axes.tolist(),'expected_axes_rows':expected.tolist(),'native_flags_names':header.split(),'native_flags':flags,'checks':checks,'pass':all(checks.values()),'before_Engine':True});assert all(checks.values()),checks

'''
    s=s[:start]+reader+s[end:];ast.parse(s);target.write_text(s,encoding='utf-8',newline='\n')
    dump(OUT/'native_readback_derivation.json',{'created_utc':now(),'source':rel(old),'source_sha256':streamsha(old),'target':rel(target),'target_sha256':streamsha(target),'changes':changes,'new_reader_source':reader,'native_input_fields_unchanged_from_w2':True,'old_native_not_rerun':True})
    ns={};exec(compile(s,target.name,'exec'),ns);ns['validate_native_frame'](d,'A29_W2_3D_PATCH_NORMAL_X_N12')
    dump(OUT/'retained_w2_gate_audit.json',{'created_utc':now(),'native_frame_gate':read(d/'native_frame_gate.json'),'original_reader_failure_retained':True,'Engine_not_run':True,'audit_is_read_only_native':True})
    print({'A29_w3_declared':True,'w2_correct_native_frame_confirmed':True},flush=True)

if __name__=='__main__':main()
