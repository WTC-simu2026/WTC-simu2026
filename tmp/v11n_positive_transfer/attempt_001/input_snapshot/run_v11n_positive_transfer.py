"""V11N offline coupon qualification; thermal histories are read from V11M only."""
import argparse
import hashlib
import json
import platform
import time
from pathlib import Path
import numpy as np
import v11h_thermomechanical_model as section_model
import v11n_positive_transfer as model

ROOT=Path(__file__).resolve().parents[2]
CONFIG=ROOT/'wtc1_simulation_v8/data/v11n_positive_transfer.json'
def read(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,v): Path(p).write_text(json.dumps(v,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8')
def digest(v): return hashlib.sha256(json.dumps(v,sort_keys=True,allow_nan=False).encode()).hexdigest()


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--output',required=True); args=ap.parse_args()
    cfg=read(CONFIG); out=(ROOT/args.output).resolve()
    if not any(out==r or r in out.parents for r in [(ROOT/cfg[k]).resolve() for k in ('scratch_directory','output_directory')]): raise ValueError('Outside V11N roots')
    if out.exists(): raise FileExistsError(out)
    source_manifest=read(ROOT/cfg['source_manifest']); parent=(ROOT/cfg['source_manifest']).parent
    before=dict(source_manifest['input_sha256'])
    before.update({(parent/p).relative_to(ROOT).as_posix():h for p,h in source_manifest['output_sha256'].items()})
    if any(sha(ROOT/p)!=h for p,h in before.items()) or read(parent/'release_audit.json')['status']!='PASS': raise ValueError('Source/control hashes changed')
    for p in [CONFIG,ROOT/cfg['source_manifest'],parent/'release_audit.json',ROOT/'harness/handoffs/WTC1_V11M_HANDOFF.md',
              *[ROOT/'wtc1_simulation_v8/scripts'/n for n in ('v11n_positive_transfer.py','run_v11n_positive_transfer.py','audit_v11n_positive_transfer.py')]]:
        before[p.relative_to(ROOT).as_posix()]=sha(p)
    hc=read(ROOT/cfg['thermo_configuration']); ec=read(ROOT/hc['section_configuration'])
    sec_case={'id':'V11N_COUPON','rho_total':.002,'layout':'symmetric','mode':'FREE','alpha_mode':'differential','delta_t_bottom_c':0.,'delta_t_top_c':0.}
    sections={n:section_model.ElasticThermoSection(ec,hc,sec_case,n) for n in cfg['concrete_fiber_counts']}
    clock=time.perf_counter(); started=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()); out.mkdir(parents=True)
    tests=[]
    def check(name,condition,evidence): tests.append({'name':name,'pass':bool(condition),'evidence':evidence})
    def near(name,value,limit): check(name,value<=limit,{'value':float(value),'limit':limit})
    controls=[]
    # Uniform and affine fields have known exact reconstruction and projection.
    for mode in cfg['reconstruction_modes']:
        for label,bottom,top in [('cold',0.,0.),('uniform',100.,100.),('affine',0.,5.)]:
            ncell=64; h=sections[160].h; centres=(np.arange(ncell)+.5)*h/ncell
            values=bottom+(top-bottom)*centres/h
            x,t=model.reconstruct(centres,values,[bottom,top],mode)
            near(mode+'_'+label+'_affine_reconstruction',float(np.max(abs(t-(bottom+(top-bottom)*x/h)))),1e-10)
            for n,sec in sections.items():
                temp,meta=model.project(x,t,n)
                expected=bottom+(top-bottom)*(np.arange(n)+.5)/n
                near(mode+'_'+label+'_'+str(n)+'_affine_projection',float(np.max(abs(temp-expected))),1e-10)
                delta=np.r_[temp,np.interp(sec.y[n:]+h/2,x,t)]
                for restraint in cfg['section_modes']:
                    active_case={**sec_case,'mode':restraint,'delta_t_bottom_c':bottom,'delta_t_top_c':top}
                    inherited=section_model.ElasticThermoSection(ec,hc,active_case,n).solve(1.)
                    actual=model.section_response(sec,delta,restraint)
                    err=max(float(np.max(abs(np.array(actual['q'])-inherited['q']))),
                            abs(actual['stored_J_per_m']-inherited['stored_j_per_m'])/max(1,inherited['stored_j_per_m']))
                    near(mode+'_'+label+'_'+str(n)+'_'+restraint+'_V11H',err,1e-10)
                controls.append({'mode':mode,'field':label,'fibers':n,'projected_k':temp.tolist(),'expected_k':expected.tolist()})
    # Explicitly prove detection of infeasible target and source data.
    rejected_controls=[]
    for label,operation in [
        ('zero_average_positive_face',lambda:model.reconstruct(np.array([.25,.75]),[0.,0.],[0.,1.],'surface_cell_conservative')),
        ('unresolved_surface_layer',lambda:model.project(np.array([0.,.99,1.]),np.array([0.,0.,1.]),4)),
        ('negative_input',lambda:model.reconstruct(np.array([.25,.75]),[-1.,0.],[0.,0.],'surface_cell_conservative'))]:
        try: operation(); check(label,False,'Should reject')
        except model.Incompatible as err: rejected_controls.append({'id':label,**err.evidence}); check(label,True,err.evidence)
    sweep=[]; details=[]; coupons=[]; recon_summary=[]
    maxima={k:0. for k in ('mean_error_k','gradient_error_k','cell_mean_error_k','face_error_k',
                           'cycle_energy_relative','cycle_return_J_per_m','free_resultant_relative')}
    h=sections[160].h
    for job in cfg['source_jobs']:
        saved=read(ROOT/cfg['source_directory']/(job+'.json'))
        for mode in cfg['reconstruction_modes']:
            for index,(profile,history) in enumerate(zip(saved['profiles'],saved['history'])):
                centres=np.array(profile['x_m']); values=np.array(profile['temperature_c'])-20
                faces=np.array([history[f+'_surface_temperature_c']-20 for f in ('bottom','top')])
                base={'job':job,'reconstruction':mode,'step':index,'time_s':profile['time_s']}
                try: x,t=model.reconstruct(centres,values,faces,mode)
                except model.Incompatible as err:
                    recon_summary.append({**base,'status':'REJECTED',**err.evidence})
                    for n in cfg['concrete_fiber_counts']: sweep.append({**base,'fibers':n,'status':'RECONSTRUCTION_REJECTED',**err.evidence})
                    continue
                m0,m1=model.moments(x,t); cell_error=0.
                for i,c in enumerate(values):
                    a,b=i*h/len(values),(i+1)*h/len(values)
                    inside=(x>a)&(x<b); xx=np.r_[a,x[inside],b]; tt=np.interp(xx,x,t)
                    avg=float(np.sum(np.diff(xx)*(tt[:-1]+tt[1:])/2)/(b-a))
                    cell_error=max(cell_error,abs(avg-c))
                face_error=float(np.max(abs(t[[0,-1]]-faces)))
                recon_summary.append({**base,'status':'SUPPORTED','mean_k':m0,'first_moment_eta_k':m1,
                                      'minimum_k':float(min(t)),'maximum_k':float(max(t)),
                                      'cell_mean_error_k':cell_error,'face_error_k':face_error})
                if mode=='surface_cell_conservative':
                    maxima['cell_mean_error_k']=max(maxima['cell_mean_error_k'],cell_error)
                    maxima['face_error_k']=max(maxima['face_error_k'],face_error)
                for n,sec in sections.items():
                    try: temp,meta=model.project(x,t,n,cfg['acceptance']['centroid_solve_absolute'])
                    except model.Incompatible as err:
                        sweep.append({**base,'fibers':n,'status':'PROJECTION_REJECTED',**err.evidence}); continue
                    eta=sec.y[:n]/h; inertia=float(np.mean(eta**2))
                    mean_error=abs(float(np.mean(temp))-m0)
                    gradient_error=abs(float(np.mean(eta*temp))/inertia-12*m1)
                    maxima['mean_error_k']=max(maxima['mean_error_k'],mean_error)
                    maxima['gradient_error_k']=max(maxima['gradient_error_k'],gradient_error)
                    row={**base,'fibers':n,'status':'SUPPORTED','mean_error_k':mean_error,'gradient_error_k':gradient_error,
                         'minimum_k':float(min(temp)),'maximum_k':float(max(temp)),**meta}
                    sweep.append(row)
                    if index in cfg['saved_detail_step_indices']:
                        details.append({**row,'x_m':x.tolist(),'profile_delta_k':t.tolist(),'fiber_delta_k':temp.tolist()})
                    if n==cfg['section_fibers'] and index in cfg['section_step_indices']:
                        delta=np.r_[temp,np.interp(sec.y[n:]+h/2,x,t)]
                        for restraint in cfg['section_modes']:
                            states=[]; old=None; wth=wext=0.
                            for scale in cfg['section_cycle_scales']:
                                state=model.section_response(sec,delta*scale,restraint)
                                if old is not None:
                                    sig=np.array(state['stress_pa']); oldsig=np.array(old['stress_pa'])
                                    wth-=float(np.sum(sec.area*(sig+oldsig)/2*sec.alpha*(np.array(state['delta_k'])-old['delta_k'])))
                                    wext+=float((np.array(state['resultant_N_Nm'])+old['resultant_N_Nm'])/2@(np.array(state['q'])-old['q']))
                                state.update({'scale':scale,'thermal_work_J_per_m':wth,'external_work_J_per_m':wext})
                                residual=abs(state['stored_J_per_m']-wth-wext)/max(1,state['stored_J_per_m'],abs(wth),abs(wext))
                                maxima['cycle_energy_relative']=max(maxima['cycle_energy_relative'],residual)
                                if restraint=='FREE':
                                    force=np.array(state['resultant_N_Nm']); sig=np.array(state['stress_pa'])
                                    norm=np.array([max(1,float(sum(sec.area*abs(sig)))),max(1,float(sum(sec.area*abs(sig*sec.y))))])
                                    maxima['free_resultant_relative']=max(maxima['free_resultant_relative'],float(max(abs(force)/norm)))
                                states.append(state); old=state
                            maxima['cycle_return_J_per_m']=max(maxima['cycle_return_J_per_m'],abs(states[-1]['stored_J_per_m']))
                            peak=states[4]; sig=np.array(peak['stress_pa'])
                            ratios=[max(0,float(max(sig[:n])))/sec.ft,max(0,float(max(-sig[:n])))/sec.fc,float(max(abs(sig[n:])))/sec.fy]
                            coupons.append({**base,'fibers':n,'restraint':restraint,'cycle':states,
                                            'gross_sensible_J_per_m':sec.width*h*2160000*m0,
                                            'composite_minus_gross_J_per_m':peak['sensible_J_per_m']-sec.width*h*2160000*m0,
                                            'peak_cold_strength_ratios':ratios,'within_cold_strength_screen':max(ratios)<=1.,
                                            'constitutive_identity_only':True})
            print(job,mode,'completed',flush=True)
    for key,limit in [('mean_error_k',1e-10),('gradient_error_k',1e-10),('cell_mean_error_k',1e-10),('face_error_k',1e-12),
                      ('cycle_energy_relative',1e-10),('cycle_return_J_per_m',1e-8),('free_resultant_relative',1e-10)]:
        near(key,maxima[key],limit)
    supported=[r for r in sweep if r['status']=='SUPPORTED']
    check('positive_projected_fields',all(r['minimum_k']>=0 and r['maximum_k']<=cfg['acceptance']['temperature_upper_k'] for r in supported),
          {'minimum':min(r['minimum_k'] for r in supported),'maximum':max(r['maximum_k'] for r in supported)})
    check('sweep_complete',len(sweep)==3*2*641*3,len(sweep))
    # Exact deterministic replay on a stored non-affine field.
    replay=next(d for d in details if d['reconstruction']=='surface_cell_conservative' and d['step']==320 and d['fibers']==640)
    rr,rm=model.project(np.array(replay['x_m']),np.array(replay['profile_delta_k']),640)
    check('deterministic_replay',rr.tolist()==replay['fiber_delta_k'],digest(rr.tolist()))
    check('protected_inputs_unchanged',all(sha(ROOT/p)==v for p,v in before.items()),len(before))
    coverage=[]
    for job in cfg['source_jobs']:
        for mode in cfg['reconstruction_modes']:
            for n in cfg['concrete_fiber_counts']:
                rows=[r for r in sweep if r['job']==job and r['reconstruction']==mode and r['fibers']==n]
                failures=[r for r in rows if r['status']!='SUPPORTED']
                coverage.append({'job':job,'reconstruction':mode,'fibers':n,'supported':len(rows)-len(failures),
                                 'rejected':len(failures),'first_rejection':failures[0] if failures else None,
                                 'positive_time_rejections':sum(r['time_s']>0 for r in failures)})
    section_inventory={str(n):{k:getattr(sec,k).tolist() for k in ('y','area','E','alpha','density','cp','K')} for n,sec in sections.items()}
    payload={'sweep':sweep,'details':details,'coupons':coupons,'controls':controls,'reconstruction':recon_summary}
    result={'iteration':'V11N','status':'PASS' if all(t['pass'] for t in tests) else 'FAIL','test_count':len(tests),
            'tests_passed':sum(t['pass'] for t in tests),'sweep_count':len(sweep),'supported_count':len(supported),
            'rejected_count':len(sweep)-len(supported),'coupon_count':len(coupons),'coverage':coverage,'maxima':maxima,
            'numerical_digest_sha256':digest(payload),'runtime':{'seconds':time.perf_counter()-clock,'started_utc':started,
            'python':platform.python_version(),'numpy':np.__version__},'thermal_solver_rerun':False,'cold_V11F_preserved':True,
            'full_panel_history_solved':False,'startup_interface_validated':False,'coupled_first_law_closed':False,
            'heated_fracture_solved':False,'fire_solved':False,'blender_changed':False,'global_energy_credit_J':0.,
            'next_iteration':'V11O','next_objective':'Définir et qualifier le raccord initial entre champ froid, températures de surface sans masse et transfert positif ; ensuite seulement intégrer la projection au panneau élastique avec contrôles froids et raffinements croisés. Réutiliser V11M/V11N, sans recalcul de conduction ni fissuration chaude.'}
    for name,value in [('results_v11n.json',result),('projection_sweep.json',sweep),('selected_details.json',details),('section_coupons.json',coupons),
                       ('section_inventory.json',section_inventory),('reference_controls.json',controls),('rejected_controls.json',rejected_controls),
                       ('reconstruction_checks.json',recon_summary),('numerical_audit.json',tests),('source_manifest.json',{'input_sha256':before,'sources':cfg['sources']})]: write(out/name,value)
    lines=['# V11N — reconstruction positive et conservative sur éprouvettes','',
           f"Contrôles : {result['tests_passed']}/{result['test_count']}, statut {result['status']}. Aucun nouveau chemin du panneau ni temps de garde-fou.",'',
           '## 1. Faits observés dans les fichiers','',
           'Trois historiques fins V11M (64, 128 et 256 cellules, 641 états chacun) sont relus ; la conduction n’est pas recalculée. Les contrôles hérités, dont V11F, sont conservés et vérifiés par empreintes.','',
           '## 2. Modèles officiels','', 'Aucune nouvelle sortie officielle ni donnée physique importée.','',
           '## 3. Archives locales','', 'Aucune nouvelle analyse d’archive ou de vidéo.','',
           '## 4. Hypothèses numériques, propriétés et unités','',
           'La nouvelle reconstruction impose les températures de face sauvegardées et conserve séparément la moyenne de chaque cellule. Les faces internes sont la moyenne des cellules voisines limitée à deux fois la plus petite. Dans chaque cellule, deux rampes symétriques bordent un plateau ; leur largeur assure une température non négative et l’intégrale exacte. Un champ affine reste affine. Cette forme sous-maille est une hypothèse, pas une solution spatiale exacte de l’équation de chaleur.','',
           'La projection utilise T_i=n*m0*exp(log(Tbrut_i)+beta*eta_i)/somme(exp(...)), eta=y/h. Beta impose le barycentre cible. Les zéros sont préservés ; un barycentre hors du support des fibres positives est rejeté. La moyenne et le gradient linéaire équivalent sont conservés comme en V11L : le moment absolu conserve l’écart connu de quadrature, enregistré dans les sorties.','',
           'Propriétés constantes héritées : épaisseur 0,11049 m ; béton rho=2400 kg/m³, cp=900 J/(kg K), alpha=1e-5/K ; armatures rho=7850, cp=600, alpha=1,2e-5/K. E, aires et positions exactes sont dans section_inventory.json. Les armatures remplacent 0,2 % du volume de béton et échantillonnent le champ continu sans correction.','',
           'eps=eps0−y*kappa ; eps_th=alpha*DeltaT ; sigma=E*(eps−eps_th). Énergies par mètre longitudinal, en J/m ; réactions N et N·m. U=1/2*somme(A*sigma²/E). Wth=−intégrale sigma*d(eps_th)*A ; Wext=intégrale(N*d eps0+M*d kappa). Les cycles d’amplitude vérifient U=Wth+Wext, pas un refroidissement calculé. L’enthalpie sensible reste distincte.','',
           '## 5. Résultats dérivés','',
           '| Cellules | Reconstruction | Fibres | États supportés / 641 | Rejets à t>0 |','|---:|---|---:|---:|---:|']
    for r in coverage: lines.append(f"| {r['job']} | {r['reconstruction']} | {r['fibers']} | {r['supported']} | {r['positive_time_rejections']} |")
    lines += ['',f"{len(coupons)} éprouvettes de section libre/empêchée et cycles algébriques. Résidu relatif énergétique maximal : {maxima['cycle_energy_relative']:.3e}. Erreur de moyenne : {maxima['mean_error_k']:.3e} K ; erreur du gradient équivalent : {maxima['gradient_error_k']:.3e} K ; erreur maximale par cellule reconstruite : {maxima['cell_mean_error_k']:.3e} K.",'',
              'Les ratios aux résistances froides sont conservés pour chaque éprouvette. Une identité thermoélastique au-delà d’une résistance n’est pas un état matériel physique validé. Les énergies et réactions détaillées, ainsi que l’écart d’enthalpie composite moins coupon brut, figurent dans section_coupons.json.','',
              '## 6. Limites et informations manquantes','',
              'À t=0, la surface algébrique de V11M est déjà réchauffée alors que chaque cellule reste à 20 °C. Un champ continu non négatif de moyenne nulle ne peut satisfaire une face positive : la reconstruction est rejetée, sans écraser la température de face ni ajouter une chaleur fictive. Le contrôle tout-froid séparé n’efface pas cette incompatibilité de raccord initial.','',
              'Le raffinement des fibres et la projection positive ne prouvent pas une précision suffisante du champ sous-maille. La qualification porte sur les instants sauvegardés et les éprouvettes déclarées, pas sur tout instant arbitrairement proche de zéro ni sur une histoire mécanique du panneau. La projection peut avoir un barycentre inaccessible avec des fibres trop grossières.','',
              'Aucune propriété endommagée ou énergie historique n’est modifiée. Pas de fissuration chaude, de premier principe couplé fermé, d’incendie ou d’effondrement réel validé. La localisation en flexion après fracture complète reste non validée. Blender est inchangé et reste une visualisation ; crédit énergétique global nul.','',
              '## Suite','',result['next_objective'],'',f"CPU : {result['runtime']['seconds']:.2f} s ; graine 11014, sans tirage.",'']
    (out/'rapport_v11n.md').write_text('\n'.join(lines),encoding='utf-8')
    write(out/'offline_manifest.json',{'iteration':'V11N','implementation_status':result['status'],'input_sha256':before,
          'output_sha256':{p.name:sha(p) for p in sorted(out.iterdir()) if p.is_file()}})
    print(json.dumps({'status':result['status'],'tests':len(tests),'supported':len(supported),'rejected':result['rejected_count'],
                      'seconds':result['runtime']['seconds'],'failed':[t for t in tests if not t['pass']]}),flush=True)
    if result['status']!='PASS': raise SystemExit(1)

if __name__=='__main__': main()
