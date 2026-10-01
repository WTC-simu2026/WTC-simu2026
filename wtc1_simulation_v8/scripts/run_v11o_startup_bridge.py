"""V11O bounded first-interval bridges and exact section energy, SI units."""
import argparse
import hashlib
import json
import platform
import time
from pathlib import Path
import numpy as np
import v11h_thermomechanical_model as old
import v11n_positive_transfer as prior
import v11o_startup_bridge as model

ROOT=Path(__file__).resolve().parents[2]
CONFIG=ROOT/'wtc1_simulation_v8/data/v11o_startup_bridge.json'
def read(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,v): Path(p).write_text(json.dumps(v,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8')
def digest(v): return hashlib.sha256(json.dumps(v,sort_keys=True,allow_nan=False).encode()).hexdigest()


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--output',required=True); args=ap.parse_args(); cfg=read(CONFIG)
    out=(ROOT/args.output).resolve()
    if not any(out==r or r in out.parents for r in [(ROOT/cfg[k]).resolve() for k in ('scratch_directory','output_directory')]): raise ValueError('Outside V11O roots')
    if out.exists(): raise FileExistsError(out)
    manifest=read(ROOT/cfg['protected_manifest']); parent=(ROOT/cfg['protected_manifest']).parent
    before=dict(manifest['input_sha256']); before.update({(parent/p).relative_to(ROOT).as_posix():h for p,h in manifest['output_sha256'].items()})
    if any(sha(ROOT/p)!=h for p,h in before.items()) or read(parent/'release_audit.json')['status']!='PASS': raise ValueError('Invalid protected source')
    for p in [CONFIG,ROOT/cfg['protected_manifest'],parent/'release_audit.json',ROOT/'harness/handoffs/WTC1_V11N_HANDOFF.md',
              *[ROOT/'wtc1_simulation_v8/scripts'/n for n in ('v11o_startup_bridge.py','run_v11o_startup_bridge.py','audit_v11o_startup_bridge.py')]]:
        before[p.relative_to(ROOT).as_posix()]=sha(p)
    hc=read(ROOT/cfg['thermo_configuration']); ec=read(ROOT/hc['section_configuration'])
    case={'id':'V11O_SECTION','rho_total':cfg['reinforcement_ratio'],'layout':'symmetric','mode':'FREE',
          'alpha_mode':'differential','delta_t_bottom_c':0.,'delta_t_top_c':0.}
    sec=model.ContinuousSection(old.ElasticThermoSection(ec,hc,case,640))
    started=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()); clock=time.perf_counter(); out.mkdir(parents=True)
    tests=[]
    def check(n,c,e): tests.append({'name':n,'pass':bool(c),'evidence':e})
    def near(n,v,l): check(n,v<=l,{'value':float(v),'limit':l})
    controls=[]; stiffness=[]
    check('symmetric_positive_energy_hessian',np.array_equal(sec.K,sec.K.T) and min(np.linalg.eigvalsh(sec.K))>0,sec.K.tolist())
    for n in cfg['closed_form_reference_fibers']:
        discrete=old.ElasticThermoSection(ec,hc,case,n)
        delta=sec.K-discrete.K; expected=sec.Ec*sec.Ac*sec.h**2/(12*n*n)
        # Test K_continuous = K_midpoint + the analytic correction on the scale of K.
        # Normalizing a subtraction of close stiffnesses by the tiny deficit
        # magnifies inherited assembly roundoff; retain the raw deficit below.
        near('midpoint_stiffness_closure_'+str(n),abs(delta[1,1]-expected)/abs(sec.K[1,1]),1e-10)
        stiffness.append({'fibers':n,'midpoint_K':discrete.K.tolist(),'continuous_K':sec.K.tolist(),
                          'curvature_stiffness_deficit_Nm2':float(delta[1,1]),'expected_deficit_Nm2':expected,
                          'relative_bending_change':float(delta[1,1]/sec.K[1,1])})
    # Exact plain-section references; do not substitute a new stiffness into old files.
    plain=model.ContinuousSection(old.ElasticThermoSection(ec,hc,{**case,'rho_total':0.},640))
    for name,a,b in [('cold',0.,0.),('uniform',100.,100.),('linear',0.,5.)]:
        x=np.array([0.,plain.h]); t=np.array([a,b])
        for restraint in cfg['restraints']:
            state=plain.solve(x,t,t,restraint)
            mean=(a+b)/2; first=(b-a)/12; square=(a*a+a*b+b*b)/3
            force=plain.Ec*plain.Ac*plain.alphac*np.array([mean,-plain.h*first])
            if restraint=='FREE':
                q=plain.alphac*np.array([mean,-(b-a)/plain.h]); energy=0.; reaction=np.zeros(2)
            else: q=np.zeros(2); energy=.5*plain.Ec*plain.Ac*plain.alphac**2*square; reaction=force
            err=max(float(np.max(abs(np.array(state['q'])-q))),abs(state['stored_J_per_m']-energy)/max(1,energy),
                    float(np.max(abs(np.array(state['support_reaction_N_Nm'])-reaction)))/max(1,float(np.max(abs(force)))))
            near('closed_form_'+name+'_'+restraint,err,1e-10)
            controls.append({'field':name,'restraint':restraint,'inventory':plain.inventory(),'state':state,
                             'expected_q':q.tolist(),'expected_stored_J_per_m':energy,'expected_reaction_N_Nm':reaction.tolist()})
    cold=sec.solve(np.array([0.,sec.h]),np.zeros(2),np.zeros(2),'FREE')
    near('independent_cold_reference',max(abs(cold['stored_J_per_m']),float(np.max(np.abs(cold['q']))),cold['sensible_J_per_m']),1e-12)
    paths=[]; projections=[]; bridge_comparisons=[]; flux_diagnostics=[]
    maxima={k:0. for k in ('mean_error_k','heat_error_j_m2','energy_relative','free_resultant_relative',
                           'weak_moment_bound_excess','weak_square_bound_excess','energy_bound_excess_J_per_m','maximum_strength_ratio')}
    fractions=cfg['fractions_first_step']; sequence=fractions+fractions[-2::-1]
    for job in cfg['source_jobs']:
        source=read(ROOT/cfg['source_directory']/(job+'.json'))
        # Verify the old continuous t=0 incompatibility has not been relabelled as repaired.
        p0=source['profiles'][0]; h0=source['history'][0]
        try:
            prior.reconstruct(np.array(p0['x_m']),np.array(p0['temperature_c'])-20,
                              [h0[s+'_surface_temperature_c']-20 for s in ('bottom','top')],'surface_cell_conservative')
            check(job+'_continuous_zero_rejected',False,'Unexpected continuous field')
        except prior.Incompatible as err: check(job+'_continuous_zero_rejected',err.evidence['reason']=='zero_cell_mean_positive_face',err.evidence)
        for bridge in cfg['bridges']:
            fields={}
            for a in fractions:
                x,t,face,meta=model.bridge(source,a,bridge); fields[a]=(x,t,face,meta)
                m0,m1,m2=model.moments3(x,t); maximum=max(float(max(t)),float(max(face)))
                maxima['mean_error_k']=max(maxima['mean_error_k'],abs(m0-meta['expected_mean_delta_k']))
                maxima['heat_error_j_m2']=max(maxima['heat_error_j_m2'],abs(sec.h*2160000*m0-meta['expected_inward_heat_j_m2']))
                maxima['weak_moment_bound_excess']=max(maxima['weak_moment_bound_excess'],abs(m1)-m0/2)
                maxima['weak_square_bound_excess']=max(maxima['weak_square_bound_excess'],m2-maximum*m0)
                if min(t)<0 or min(face)<0: raise ValueError('Negative bridge temperature')
                if a>0:
                    for n in cfg['projection_fibers_for_diagnostic']:
                        try:
                            temp,projection=prior.project(x,t,n)
                            projected_square=float(np.mean(temp**2))
                            projections.append({'job':job,'bridge':bridge,'fraction':a,'fibers':n,'status':'SUPPORTED',
                                'exact_mean_square_k2':m2,'projected_mean_square_k2':projected_square,
                                'projected_to_exact_square_ratio':projected_square/m2 if m2>0 else None,
                                'square_relative_error':abs(projected_square-m2)/max(m2,1e-30),
                                'projection':projection,'committed_to_section':False})
                        except prior.Incompatible as err:
                            projections.append({'job':job,'bridge':bridge,'fraction':a,'fibers':n,'status':'REJECTED',**err.evidence})
                    # A transfer interpolation is not a spatial heat-equation solution.
                    face_slope=(t[-1]-t[-2])/(x[-1]-x[-2])
                    row0,row1=source['history'][:2]
                    flux_reference=row0['top_total_inward_flux_w_m2']+a*(row1['top_total_inward_flux_w_m2']-row0['top_total_inward_flux_w_m2'])
                    flux_diagnostics.append({'job':job,'bridge':bridge,'fraction':a,
                        'reconstructed_top_gradient_flux_w_m2':float(face_slope),
                        'interpolated_saved_top_flux_w_m2':flux_reference,
                        'difference_w_m2':float(face_slope-flux_reference),
                        'conductivity_w_m_k':1.,'is_heat_equation_solution':False})
            for restraint in cfg['restraints']:
                rows=[]; oldstate=None; wth=wext=0.
                for i,a in enumerate(sequence):
                    x,t,face,meta=fields[a]; state=sec.solve(x,t,face,restraint)
                    q=np.array(state['q']); f=np.array(state['thermal_force_N_Nm']); S=state['thermal_square_energy_S_J_per_m']
                    R=np.array(state['resultant_N_Nm'])
                    if oldstate is not None:
                        oq,of,oS,oR=oldstate
                        wth+=float(-.5*(oq+q)@(f-of)+.5*(S-oS)); wext+=float(.5*(oR+R)@(q-oq))
                    residual=abs(state['stored_J_per_m']-wth-wext)/max(1,abs(state['stored_J_per_m']),abs(wth),abs(wext))
                    maxima['energy_relative']=max(maxima['energy_relative'],residual)
                    maxima['energy_bound_excess_J_per_m']=max(maxima['energy_bound_excess_J_per_m'],
                        -state['stored_J_per_m'],state['stored_J_per_m']-.5*S)
                    maxima['maximum_strength_ratio']=max(maxima['maximum_strength_ratio'],state['maximum_cold_strength_ratio'])
                    if restraint=='FREE': maxima['free_resultant_relative']=max(maxima['free_resultant_relative'],float(max(abs(R)))/max(1,float(max(abs(f)))))
                    rows.append({**meta,**state,'sequence_index':i,'phase':'ASCENDING' if i<len(fractions) else 'REVERSE_SYNTHETIC',
                                 'x_m':x.tolist(),'bulk_delta_k':t.tolist(),'face_delta_k':face.tolist(),
                                 'thermal_work_J_per_m':wth,'external_work_J_per_m':wext,'energy_residual_relative':residual})
                    oldstate=q,f,S,R
                path={'job':job,'bridge':bridge,'restraint':restraint,'history':rows,'first_step_state':rows[len(fractions)-1]}
                paths.append(path)
                near(job+'_'+bridge+'_'+restraint+'_return',abs(rows[-1]['stored_J_per_m'])+abs(rows[-1]['thermal_work_J_per_m'])+abs(rows[-1]['external_work_J_per_m']),1e-10)
        for restraint in cfg['restraints']:
            a,b=[p for p in paths if p['job']==job and p['restraint']==restraint]
            sa,sb=a['first_step_state'],b['first_step_state']
            error=max(abs(sa['stored_J_per_m']-sb['stored_J_per_m']),float(np.max(abs(np.array(sa['q'])-sb['q']))))
            near(job+'_'+restraint+'_shared_endpoint',error,1e-10)
            bridge_comparisons.append({'job':job,'restraint':restraint,'endpoint_error':error,
                 'weak_smallest_energy_J_per_m':a['history'][1]['stored_J_per_m'],
                 'ramp_smallest_energy_J_per_m':b['history'][1]['stored_J_per_m'],
                 'weak_smallest_q':a['history'][1]['q'],'ramp_smallest_q':b['history'][1]['q'],
                 'weak_surface_stress_at_zero_pa':a['history'][0]['face_stress_pa'],
                 'ramp_surface_stress_at_zero_pa':b['history'][0]['face_stress_pa']})
        print(job,'startup paths complete',flush=True)
    for key,limit in [('mean_error_k',1e-10),('heat_error_j_m2',1e-4),('energy_relative',1e-10),('free_resultant_relative',1e-10),
                      ('weak_moment_bound_excess',1e-10),('weak_square_bound_excess',1e-10),('energy_bound_excess_J_per_m',1e-10)]: near(key,maxima[key],limit)
    check('startup_below_cold_guard',maxima['maximum_strength_ratio']<.9,maxima['maximum_strength_ratio'])
    check('protected_sources_unchanged',all(sha(ROOT/p)==h for p,h in before.items()),len(before))
    payload={'paths':paths,'controls':controls,'stiffness':stiffness,'projections':projections,'comparisons':bridge_comparisons,'flux':flux_diagnostics}
    result={'iteration':'V11O','status':'PASS' if all(t['pass'] for t in tests) else 'FAIL','test_count':len(tests),'tests_passed':sum(t['pass'] for t in tests),
            'path_count':len(paths),'state_count':sum(len(p['history']) for p in paths),'maxima':maxima,
            'projection_diagnostic_count':len(projections),'projection_rejections':sum(p['status']=='REJECTED' for p in projections),
            'numerical_digest_sha256':digest(payload),'runtime':{'seconds':time.perf_counter()-clock,'started_utc':started,'python':platform.python_version(),'numpy':np.__version__},
            'weak_mechanical_zero_limit_qualified':True,'continuous_initial_temperature_reconstruction_validated':False,
            'newly_resolved_thermal_time':False,'heat_equation_bridge_validated':False,'panel_history_solved':False,
            'thermal_compatibility_status':'NOT_QUALIFIED_FLUX_MISMATCH','panel_integration_ready':False,
            'cold_V11F_preserved':True,'coupled_first_law_closed':False,'heated_fracture_solved':False,'fire_solved':False,'blender_changed':False,'global_energy_credit_J':0.,
            'next_iteration':'V11P','next_objective':'Qualifier une formulation thermique de démarrage cohérente avant le panneau : tester notamment des températures nodales de surface avec demi-volumes de contrôle, à masse et capacité thermique totales inchangées ; vérifier flux, enthalpie, état initial et raffinements, puis comparer aux sorties V11M sauvegardées. Conserver les intégrales exactes de température et de température au carré pour le futur transfert mécanique. Ne pas intégrer le raccord V11O comme une conduction validée.'}
    for name,obj in [('results_v11o.json',result),('startup_paths.json',paths),('section_inventory.json',sec.inventory()),('closed_form_controls.json',controls),
                     ('stiffness_comparison.json',stiffness),('projection_square_diagnostics.json',projections),('bridge_comparisons.json',bridge_comparisons),
                     ('flux_mismatch_diagnostics.json',flux_diagnostics),('numerical_audit.json',tests),('source_manifest.json',{'input_sha256':before,'sources':cfg['sources']})]: write(out/name,obj)
    lines=['# V11O — raccord faible initial et énergie de section','',f"Contrôles : {result['tests_passed']}/{result['test_count']} ; statut {result['status']}. Qualification numérique du raccord mécanique, pas d’un nouveau champ thermique physique.",'',
      '## 1. Faits observés dans les fichiers','',
      'Les deux premiers états sauvegardés V11M encadrent 0 à 0,140625 s. La température de surface algébrique est positive dès zéro alors que les cellules sont froides. Sources V11M/N et contrôle V11F sont conservés par empreintes. Aucun solveur de conduction ni ancien pilote complet relancé.','',
      '## 2. Modèles officiels','', 'Aucun nouveau résultat officiel importé.','',
      '## 3. Archives locales','', 'Aucune nouvelle analyse d’archive, de photographie ou de vidéo.','',
      '## 4. Hypothèses et équations','',
      'Le raccord principal interpole les moyennes de cellules et les températures de face entre les deux états sauvegardés ; pour chaque fraction positive, il utilise la reconstruction conservative V11N. À zéro, le volume est froid presque partout et la face positive reste une sonde de mesure volumique nulle. Ce champ initial est discontinu : l’ancien rejet de reconstruction continue reste correct. Le témoin multiplie tout le premier profil positif par la fraction ; il conserve la chaleur mais viole la température de face intermédiaire. Il n’est pas retenu comme champ respectant cette condition.','',
      'La section intègre exactement le béton continu à propriétés constantes et conserve les armatures discrètes. Les trois intégrales sont m0=moyenne(DeltaT), m1=moyenne((y/h)*DeltaT), m2=moyenne(DeltaT²). U=1/2*qᵀKq−qᵀf+S/2, avec f=intégrale(E*alpha*DeltaT*B*dA) et S=intégrale(E*alpha²*DeltaT²*dA). B=(1,−y), q=(eps0,kappa). Réactions en N et N·m ; énergies par mètre longitudinal en J/m. Les contraintes sont calculées aussi aux faces, même lorsqu’elles ont une mesure volumique nulle.','',
      'Travail thermique incrémental : −(qancien+qnouveau)ᵀ*(fnouveau−fancien)/2+(Snouveau−Sancien)/2. Travail extérieur : (Rancien+Rnouveau)ᵀ*(qnouveau−qancien)/2. La chaleur sensible et l’écart de capacité thermique composite restent séparés ; aucun premier principe thermo-mécanique couplé n’est revendiqué.','',
      'Hypothèses héritées : épaisseur 0,11049 m ; largeur 80 in × 0,0254=2,032 m ; béton E=2500 ksi, alpha=1e-5/K, rho=2400 kg/m³, cp=900 J/(kg K) ; armatures E=200 GPa, alpha=1,2e-5/K, rho=7850, cp=600, fraction de section 0,002. Les conversions et constantes effectives figurent dans section_inventory.json et les configurations sources.','',
      'Cette intégration retire l’erreur de quadrature au milieu des fibres sur l’inertie du béton : DeltaK22=Ec*Ac*h²/(12*n²). Cet écart est mesuré séparément ; aucune ancienne raideur ni histoire V11F/H/N n’est réécrite. Le futur panneau devra comparer explicitement son contrôle froid.','',
      '## 5. Résultats dérivés','',
      '| Source | Liaison | Énergie au plus petit paramètre, raccord faible (J/m) | Témoin proportionnel (J/m) | Écart final (unités SI) |',
      '|---|---|---:|---:|---:|']
    for c in bridge_comparisons: lines.append(f"| {c['job']} | {c['restraint']} | {c['weak_smallest_energy_J_per_m']:.9g} | {c['ramp_smallest_energy_J_per_m']:.9g} | {c['endpoint_error']:.3e} |")
    lines += ['',f"{len(paths)} chemins de section, {result['state_count']} états. Résidu énergétique relatif maximal : {maxima['energy_relative']:.3e}. Ratio maximal aux résistances froides (faces incluses) : {maxima['maximum_strength_ratio']:.6f}.",'',
      'Pour 0≤T≤Tmax, |m1|≤m0/2 et m2≤Tmax*m0. Puisque m0 tend linéairement vers zéro, les charges thermiques et S tendent vers zéro ; déformations libres et réactions empêchées s’annulent. 0≤Ulibre≤Uempêchée=S/2. Les contraintes ponctuelles de face peuvent garder une limite non nulle. Le raccord est donc cohérent pour ces grandeurs intégrées, pas continu point par point en température.','',
      'Les deux raccords atteignent le même état final mais peuvent avoir des énergies très différentes dans l’intervalle. Une projection conservant moyenne et gradient peut manquer le terme moyen de température au carré : projection_square_diagnostics.json mesure cet écart sans engager ces projections dans le calcul de section.','',
      '## 6. Limites et informations manquantes','',
      'Les fractions de l’intervalle sont des coordonnées d’interpolation, pas des microsecondes thermiques nouvellement résolues. Le gradient du profil reconstruit à la surface ne reproduit pas en général le flux sauvegardé ; cet écart est mesuré dans flux_mismatch_diagnostics.json. La reconstruction n’est donc pas une nouvelle solution de l’équation de chaleur. La température algébrique initiale reste un effet du maillage thermique et de sa convention de surface sans masse.','',
      'Exemple décisif : à 256 cellules et fraction 1/65536 du premier pas, le gradient reconstruit donne environ 5,02e8 W/m² contre 8,38e3 W/m² dans le flux sauvegardé interpolé. Cet écart est un artefact de reconstruction, pas une exposition physique. Malgré les identités mécaniques réussies, la compatibilité thermique reste NON QUALIFIÉE et l’intégration au panneau est différée. La prochaine étape doit tester un démarrage thermique cohérent, par exemple des volumes de contrôle nodaux incluant la surface sans ajouter de masse.','',
      'Aucun nouveau panneau chargé, temps de rupture ou garde-fou global n’est calculé. Pas de dommage chaud, de modification d’historique endommagé, d’incendie réel ou d’effondrement validé. Localisation en flexion après fracture complète non validée. Blender inchangé, visualisation seulement ; crédit énergétique global nul.','',
      '## Suite','',result['next_objective'],'',f"Calcul CPU : {result['runtime']['seconds']:.2f} s ; graine 11015, sans tirage.",'']
    (out/'rapport_v11o.md').write_text('\n'.join(lines),encoding='utf-8')
    write(out/'offline_manifest.json',{'iteration':'V11O','implementation_status':result['status'],'input_sha256':before,
           'output_sha256':{p.name:sha(p) for p in sorted(out.iterdir()) if p.is_file()}})
    print(json.dumps({'status':result['status'],'tests':len(tests),'seconds':result['runtime']['seconds'],'failed':[t for t in tests if not t['pass']]}),flush=True)
    if result['status']!='PASS': raise SystemExit(1)

if __name__=='__main__': main()
