"""Standalone scientific plot from saved native fields, not a visual history fit."""
import json
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'wtc1_simulation_v8/output/aircraft_a19'
def main():
    mapping_correction()
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
    except ModuleNotFoundError:
        print({'scientific_plot_not_rendered':'matplotlib absent from existing runtimes; no software installed','field_mapping_correction_written':True},flush=True);return
    z=np.load(OUT/'cached_radome_fields.npz');T=z['time_ms'];j=np.flatnonzero(z['element_ids']==174)[0];fig,ax=plt.subplots(2,2,figsize=(12,7),constrained_layout=True)
    ax[0,0].plot(T,z['part_IE_J']/1e6,label='Radôme : énergie interne native');ax[0,0].plot(T,z['element_IE_J'][:,j]/1e6,'--',label='Facette 174');ax[0,0].axhline(0,color='.4',lw=.6);ax[0,0].set_ylabel('Énergie interne (MJ)');ax[0,0].legend(fontsize=8)
    ax[0,1].plot(T,z['principal_stretches'][:,j,0],label='Étirement maximal, facette 174');ax[0,1].plot(T,z['principal_stretches'][:,:,0].max(axis=1),':',label='Maximum du radôme');ax[0,1].axhline(1,color='.4',lw=.6);ax[0,1].set_ylabel('Longueur / longueur initiale');ax[0,1].legend(fontsize=8)
    ax[1,0].plot(T,z['area_ratio'][:,j]);ax[1,0].set_ylabel('Aire / aire initiale, facette 174')
    ax[1,1].plot(T,z['damage_skin_core_skin'][:,0,j],label='Peau extérieure');ax[1,1].plot(T,z['damage_skin_core_skin'][:,1,j],label='Cœur');ax[1,1].plot(T,z['damage_skin_core_skin'][:,2,j],'--',label='Peau intérieure');ax[1,1].set_ylabel('Dommage natif, facette 174');ax[1,1].set_ylim(-.05,1.05);ax[1,1].legend(fontsize=8)
    for a in ax.ravel():a.set_xlabel('Temps physique simulé (ms)');a.grid(alpha=.2);a.set_xlim(0,20)
    fig.suptitle('Diagnostic A19 des sorties conservées A18 — défaut numérique après rupture des peaux',fontsize=13)
    fig.savefig(OUT/'diagnostic_A18_energie_deformation.png',dpi=150);plt.close(fig)
def mapping_correction():
    read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));d=read(OUT/'ply_observer/explicit_ply_diagnostic.json');q=d['selected_elements'][0]
    correction={'scope':'Clarify output mapping only; all original cached values retained.','native_time_ms':d['time_ms'],'element_id':174,
      'legacy_cached_layer2_values':[0,0,0],'legacy_field_is_not_validated_as_core_ply42':True,
      'explicit_core_ply42_IP2_stress_MPa':next(v for k,v in q['tensor_fields'].items() if k.startswith('Stress') and '42   2' in k),
      'explicit_core_ply42_IP2_strain_native':next(v for k,v in q['tensor_fields'].items() if k.startswith('Strain') and '42   2' in k),
      'explicit_core_all3_integration_points_nonzero':True,'core_intact_by_DAMA':q['damage']['DAMAGE,(Layer   2)']==0,
      'no_inference_core_unstrained_from_legacy_layer2':True,'old_solver_reruns':0,'checkpoint_unchanged':d['source_checkpoint_unchanged']}
    (OUT/'field_mapping_correction.json').write_text(json.dumps(correction,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print({'plot':'diagnostic_A18_energie_deformation.png','explicit_core_IP2_strain':correction['explicit_core_ply42_IP2_strain_native']},flush=True)
if __name__=='__main__':main()
