"""Source-bounded hardening input candidates, not a fitted fracture law."""
from run_aircraft_a22 import ROOT,OUT,PREV,read,dump,rel,now,streamsha,guard
from pathlib import Path
import numpy as np,shutil

def main():
    guard();p=OUT/'material_preparation.json';assert not p.exists();source=ROOT/'work/official_sources/ncstar1-3d.pdf';loc=read(ROOT/'tmp/a22_steel_page_locator.json');assert streamsha(source)==loc['sha256']
    # Table3-13, PDF100 (printed66), visually inspected along with its PDF101 footnote.
    columns=['specified_Fy_ksi','estimated_static_yield_ksi','TS_ksi','true_necking_strain','b','Rinf_ksi','R0_ksi']
    values=[[36,35.6,61.2,.190,30.337,24.467,67.973],[45,53.1,74.9,.153,24.965,27.198,62.245],[50,54,75.6,.220,28.659,27.870,74.790],[55,60.8,82.6,.259,18.479,24.698,76.770],[60,62,87.3,.176,27.535,24.543,74.925],[65,69.6,90.4,.138,38.284,23.847,89.520],[70,76.7,92,.103,19.499,26.777,10.714],[75,82.5,96.8,.070,29.008,17.463,17.826],[80,91.5,99.4,.079,32.567,14.203,29.522],[85,104.8,116,.081,13.857,32.500,1.793]]
    rows=[];ksi_to_MPa=6.894757293168361
    for raw in values:
        r=dict(zip(columns,raw));r['source']='NIST NCSTAR1-3D Table3-13 PDF100, printed66';r['constitutive_parameter_kind']='official estimated model using measurements and other evidence, not a direct event result';r['yield_MPa']=r['estimated_static_yield_ksi']*ksi_to_MPa;r['Rinf_MPa']=r['Rinf_ksi']*ksi_to_MPa;r['R0_MPa']=r['R0_ksi']*ksi_to_MPa
        r['scope']='perimeter plates1,2,4;55ksi thickness<=1.5in;60ksi<=1.25in;65ksi<=.5in;80ksi allplates;85row groups85/90/100ksi'
        r['true_plastic_necking_candidate']=r['true_necking_strain']-(r['TS_ksi']*ksi_to_MPa*np.exp(r['true_necking_strain']))/205000
        r['candidate_necking_conversion']='Assume TS is engineering stress at peak, true stress TS*exp(true strain), subtract elastic true strain. Must check mapping before use. Not a fracture strain.'
        rows.append(r)
    nasa=read(PREV/'material_reference_assessment.json')
    result={'created_utc':now(),'iteration':'AIRCRAFT-A22','source':{'path':rel(source),'sha256':streamsha(source),'bytes':source.stat().st_size,'url':'https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=101021','table_pdf_page':100,'footnote_pdf_page':101,'printed_pages':[66,67],'visually_inspected':True,'read_only_source':True},
      'units':{'ksi_to_MPa':ksi_to_MPa,'inch_to_mm':25.4,'E_GPa':205,'E_MPa':205000},'steel_model_table':rows,
      'hardening_expression':'increment_sigma_MPa=R0*epsilon_p+Rinf*(1-exp(-b*epsilon_p)); add estimated static yield for a candidate curve. Source fitting shifts stress/strain to zero before fitting Eq3-7.',
      'limits':{'epsilon_max_in_table':'true strain at tensile strength; beginning of necking; not fracture','true_necking_range':[.070,.259],'local_geometry_grade_mapping_complete':False,'rate_law_assigned':False,'ductile_triaxiality_and_Lode_locus_measured':False,'post_necking_fracture_energy_and_mesh_regularization_available':False,'numerical_damage_target_used':False,'material_values_adopted_in_whole':False},
      'NASA_aluminium_reference':{'assessment':rel(PREV/'material_reference_assessment.json'),'assessment_sha256':streamsha(PREV/'material_reference_assessment.json'),'source':'ATR42 vertical drop9.14m/s, not AA11 material identification or200m/s fracture measurement','failure_numbers_are_source_model_ultimate_strains_not_a_validated_ductile_locus':True},
      'next_required_coupons':['LAW36 strain-controlled elastic/hardening/yield response and work balance','unload/reload without element deletion','mesh2x comparison','rate bounds from measured relevant grade','finite fracture-energy regularization and mass/deletion ledger before impact'],
      'physical_fracture_qualified':False,'source_or_NIST_damage_target_used':False}
    dump(p,result);d=OUT/'sources'
    for src,name in [(ROOT/'tmp/a22_steel_table_100.png','steel_table_100.png'),(ROOT/'tmp/a22_steel_footnote_101.png','steel_footnote_101.png'),(ROOT/'tmp/a22_steel_selected_pages.json','steel_selected_pages.json')]:
        shutil.copy2(src,d/name)
    # Curves are source-bounded candidates only and terminate before the strain at necking.
    curves=[]
    for i,r in enumerate(rows):
        eps=np.linspace(0,r['true_plastic_necking_candidate'],401);sig=r['yield_MPa']+r['R0_MPa']*eps+r['Rinf_MPa']*(-np.expm1(-r['b']*eps));curves.append({'candidate':i,'grade_Fy_ksi':r['specified_Fy_ksi'],'plastic_strain':eps.tolist(),'flow_stress_MPa':sig.tolist(),'ends_at_necking_candidate':True,'no_fracture_assigned':True})
    dump(OUT/'steel_hardening_candidates.json',{'created_utc':now(),'source_preparation_sha256':streamsha(p),'curves':curves,'not_adopted_in_solver':True})
    print({'steel_source_rows_prepared':len(rows),'fracture_not_confused_with_necking':True,'whole_materials_changed':False},flush=True)

if __name__=='__main__':main()
