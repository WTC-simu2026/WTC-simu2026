"""Predeclare explicit full3D constitutive branch, without changing legacy LAW25."""
from run_aircraft_a29 import *

def main():
    h=harness();assert h['Status']=='PASS';dump(OUT/'harness_before_law12.json',h);r=read(OUT/'w3/PATCH_NORMAL_X_N12/review.json');assert r['checks']['native_full_balance'] and not r['checks']['independent_elastic_reference'];assert read(OUT/'w3/PATCH_NORMAL_X_N12/native_frame_gate.json')['pass']
    old=Path(__file__).with_name('test_aircraft_a29_native_readback.py');target=old.with_name('test_aircraft_a29_law12.py');cfg=CFG.with_name('aircraft_a29_law12.json');assert not cfg.exists() and not target.exists()
    u='https://help.altair.com/hwsolvers/rad/topics/solvers/rad/mat_law12_3d_comp_starter_r.htm';q=OUT/'sources/law12.html';assert not q.exists();q.write_bytes(urllib.request.urlopen(u,timeout=45).read())
    c=read(CFG.with_name('aircraft_a29_native_readback.json'));c.update(revision='w4',declared_utc=now(),parent_configuration_sha256=streamsha(CFG.with_name('aircraft_a29_native_readback.json')),purpose='Explicit LAW12 full3D elastic orthotropic solid branch. Same source scalar density,E11,E22,E33,G12,G23,G31,nu12; new transverse Poisson ratios nu23=nu31=.25 explicitly match the previously declared symmetric full3D compliance. Huge tensile/strength limits keep isolated elastic witness; no historical rupture or automatic LAW25 equivalence.',material={'law':'LAW12/4','rho_g_mm3':.00183,'E_MPa':[22000,22000,10000],'nu12_nu23_nu31':[.25,.25,.25],'transverse_Poisson_status':'new explicit assumptions, not historical measurements','G_MPa':[4000,4000,4000],'sigma_t_MPa':[1e12,1e12,1e12],'delta':.05,'B':0,'n':1,'fmax':1,'Wp_ref':1,'all_12_yield_stress_MPa':1e12,'alpha':0,'Ef':0,'c':0,'epsdot0':.001,'ICC':1},primary_source={'url':u,'path':rel(q),'sha256':streamsha(q),'redistribution':'exclude_third_party'},source_fields_unchanged=['rho','E11','E22','E33','nu12','G12','G23','G31'],legacy_LAW25_unchanged=True,constitutive_change_explicit=True)
    dump(cfg,c);dump(OUT/'law12_guard.json',{'created_utc':now(),'sha256':streamsha(cfg),'before_new_native_solvers':True})
    s=old.read_text(encoding='utf-8');audit=[]
    for a,b in [('aircraft_a29_native_readback.json','aircraft_a29_law12.json'),("OUT/'native_readback_guard.json'","OUT/'law12_guard.json'"),("(\"OUT/'w2'\",\"OUT/'w3'\")","(\"OUT/'w2'\",\"OUT/'w4'\")"),("d=OUT/'w3'/cid","d=OUT/'w4'/cid"),('native_case_summary_w3.json','native_case_summary_w4.json'),('runner_w3_derivation.json','runner_w4_derivation.json'),('review_w3_derivation.json','review_w4_derivation.json'),('A29_W3_3D_','A29_W4_3D_'),('"P[\'/MAT/LAW25/4\']+prop"','"law12_card()+prop"')]:
        n=s.count(a);assert n>0,a;s=s.replace(a,b);audit.append({'old':a,'new':b,'count':n})
    func='''def law12_card():
    return ['/MAT/LAW12/4','EXPLICIT_FULL3D_ELASTIC_REFERENCE_NOT_HISTORICAL',ff(.00183),ff(22000,22000,10000),ff(.25,.25,.25),ff(4000,4000,4000),ff(1e12,1e12,1e12,.05),ff(0,1,1,1),ff(1e12,1e12,1e12,1e12),ff(1e12,1e12,1e12,1e12),ff(1e12,1e12,1e12,1e12),ff(0,0,0,.001)+ii(1)]

'''
    point='def property_card():';assert s.count(point)==1;s=s.replace(point,func+point);ast.parse(s);target.write_text(s,encoding='utf-8',newline='\n');dump(OUT/'law12_derivation.json',{'created_utc':now(),'source':rel(old),'source_sha256':streamsha(old),'target':rel(target),'target_sha256':streamsha(target),'changes':audit,'new_material_card_source':func,'no_fit':True,'native_old_not_rerun':True});print({'A29_w4_LAW12_declared':True,'same_volume_density_and_source_moduli':True,'new_transverse_assumptions_explicit':True},flush=True)

if __name__=='__main__':main()
