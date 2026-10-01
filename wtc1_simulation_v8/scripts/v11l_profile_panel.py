"""V11L one-way saved-profile adapter; no fire or damage evolution."""
import numpy as np
import v11i_thermoelastic_panel_model as panel


def moments(x, values):
    """Exact zeroth and centred first integrals of a piecewise affine field."""
    length = x[-1] - x[0]
    eta = (x - (x[0] + x[-1]) / 2) / length
    a, b = eta[:-1], eta[1:]
    va, vb = values[:-1], values[1:]
    m0 = np.sum((b-a)*(va+vb)/2)
    m1 = np.sum((b-a)*((2*a+b)*va+(a+2*b)*vb)/6)
    return float(m0), float(m1)


class SavedProfile:
    def __init__(self, saved, cfg):
        reference=cfg['reference_temperature_c']
        self.cfg=cfg
        self.times = np.array([r['time_s'] for r in saved['profiles']])
        self.centres = np.array(saved['profiles'][0]['x_m'])
        self.length = 2*self.centres[0]*len(self.centres)
        self.values = np.array([r['temperature_c'] for r in saved['profiles']])-reference
        self.heat = np.array([r['cumulative_total_inward_heat_j_m2'] for r in saved['history']])
        self.surface_delta = np.array([[r['bottom_surface_temperature_c']-reference,
                                       r['top_surface_temperature_c']-reference] for r in saved['history']])
        assert np.all(np.diff(self.times)>0)

    def at(self, time_s, mode='profile'):
        if time_s < 0 or time_s > self.times[-1]:
            raise ValueError('No extrapolation in time')
        j = min(len(self.times)-2, max(0, np.searchsorted(self.times,time_s,side='right')-1))
        fraction = (time_s-self.times[j])/(self.times[j+1]-self.times[j])
        v = (1-fraction)*self.values[j]+fraction*self.values[j+1]
        if mode == 'cold':
            v = np.zeros_like(v)
        elif mode == 'uniform':
            v = np.full_like(v,np.mean(v))
        elif mode == 'uniform_control':
            v = np.full_like(v,self.cfg['uniform_control_delta_k']*time_s/self.times[-1])
        elif mode == 'linear_control':
            v = self.cfg['linear_control_top_delta_k']*time_s/self.times[-1]*self.centres/self.length
        elif mode != 'profile':
            raise ValueError(mode)
        # The endpoint extension belongs to the mechanical reconstruction only.
        # In particular at t=0 the field remains identically zero.
        faces = [v[0]-(v[1]-v[0])/2, v[-1]+(v[-1]-v[-2])/2]
        x = np.r_[0.,self.centres,self.length]
        y = np.r_[faces[0],v,faces[1]]
        m0,m1 = moments(x,y)
        factor = float(np.mean(v)/m0) if abs(m0)>1e-14 else 1.
        correction = float(np.max(abs(y*(factor-1))))
        y *= factor
        m0,m1 = moments(x,y)
        env = (1-fraction)*self.surface_delta[j]+fraction*self.surface_delta[j+1]
        return x,y,{'mean_delta_k':float(np.mean(v)), 'first_moment_eta_k':m1,
                    'maximum_mean_rescale_change_k':correction,'mean_rescale_factor':factor,
                    'surface_extrapolation_difference_k':(y[[0,-1]]-env).tolist(),
                    'source_interval_s':self.times[j:j+2].tolist(),
                    'source_fraction':float(fraction),
                    'source_heat_j_m2':float((1-fraction)*self.heat[j]+fraction*self.heat[j+1])}


class ProfilePanel(panel.ThermoElasticPanel):
    def __init__(self, cfg, cold_cfg, thermo_cfg, section_cfg, inputs, source, mode, subdivisions=None):
        case = {'id':mode,'delta_t_bottom_c':0.,'delta_t_top_c':0.,'target_scale':1.}
        super().__init__(cfg,cold_cfg,thermo_cfg,section_cfg,inputs,case,subdivisions)
        self.source,self.mode = source,mode

    def mapped(self,time_s):
        x,v,meta = self.source.at(time_s,self.mode)
        eta = self.section.y/self.section.h
        temp = np.interp(self.section.y+self.section.h/2,x,v)
        c = self.concrete_mask
        m0,m1 = moments(x,v)
        # Preserve mean and equivalent gradient, using the inherited discrete I.
        i_discrete = float(np.mean(eta[c]**2))
        raw = temp[c].copy()
        # Multiplicative moment projection keeps exactly cold fibers cold.
        gram = np.array([[np.mean(raw),np.mean(raw*eta[c])],
                         [np.mean(raw*eta[c]),np.mean(raw*eta[c]**2)]])
        target = np.array([m0-np.mean(raw),12*m1*i_discrete-np.mean(raw*eta[c])])
        a,b = np.linalg.solve(gram,target) if np.max(abs(raw))>1e-14 else (0.,0.)
        change = raw*(a+b*eta[c])
        temp[c] += change
        if np.any(temp < -1e-10): raise ValueError('Heating remap creates temperature below reference')
        meta.update({'fiber_correction_a_dimensionless':float(a),'fiber_correction_b_dimensionless':float(b),
                     'mapped_mean_delta_k':float(np.mean(temp[c])),
                     'mapped_equivalent_gradient_k':float(np.mean(eta[c]*temp[c]))/i_discrete,
                     'reference_equivalent_gradient_k':12*m1,
                     'first_moment_quadrature_difference_k':float(np.mean(eta[c]*temp[c]))-m1,
                     'maximum_fiber_correction_k':float(np.max(abs(change))),
                     'x_m':x.tolist(),'delta_k':v.tolist()})
        return temp,meta

    def delta_temperature(self,time_s):
        return self.mapped(time_s)[0]

    def _section_screens(self,batch,u,time_s):
        # For a curved thermal field an interior knot may govern even when faces pass.
        qend = np.einsum('ejai,ei->eja',self.Bends,u[self.dofs[::2]]).reshape(-1,2)
        q = np.vstack([qend,batch['q']])
        temp,meta = self.mapped(time_s)
        yk = np.array(meta['x_m'])-self.section.h/2
        tk = np.array(meta['delta_k'])
        yc = self.section.y[self.concrete_mask]
        locations = np.r_[yk,yc]
        temperatures = np.r_[tk,temp[self.concrete_mask]]
        ec = self.section.E[self.concrete_mask][0]
        ac = self.section.alpha[self.concrete_mask][0]
        stress = ec*(q[:,0,None]-q[:,1,None]*locations-ac*temperatures)
        it,ic = np.unravel_index(np.argmax(stress),stress.shape), np.unravel_index(np.argmin(stress),stress.shape)
        result = [
            {'id':f'SLAB-Q{it[0]}-DEPTH{it[1]}','kind':'slab_concrete_tension_elastic_guard','DCR':float(max(0,stress[it])/self.section.ft)},
            {'id':f'SLAB-Q{ic[0]}-DEPTH{ic[1]}','kind':'slab_concrete_compression_elastic_guard','DCR':float(max(0,-stress[ic])/self.section.fc)}]
        s = self.steel_mask
        stress_s = self.section.E[s]*(q[:,0,None]-q[:,1,None]*self.section.y[s]-self.section.alpha[s]*temp[s])
        result.append({'id':'SLAB-REBAR-ALL-ENDS-AND-GAUSS','kind':'slab_reinforcement_yield_elastic_guard','DCR':float(np.max(abs(stress_s))/self.section.fy)})
        return result


def record(model,state,g,t,phase,work,thermal,increment):
    row = {k:state[k] for k in ('stored_J','sensible_enthalpy_J','max_DCR','governing','equilibrium_residual',
        'max_slab_down_m','max_slab_up_m','seat_vertical_reaction_N','seat_horizontal_reaction_N','gravity_load_N')}
    row.update({'phase':phase,'gravity':g,'profile_time_coordinate_s':t,'external_work_J':work,
                'thermal_work_J':thermal,'increment_residual_relative':increment,
                'energy_residual_J':state['stored_J']-work-thermal,
                'energy_residual_relative':abs(state['stored_J']-work-thermal)/max(1,abs(state['stored_J']),abs(work),abs(thermal))})
    temp,meta = model.mapped(t)
    row['section_q'] = state['batch']['q'].tolist()
    row['fiber_delta_temperature_k'] = temp.tolist()
    row['unit_gravity_displacement_work_J'] = float(model.force_unit@state['u'])
    row['spring_stored_J'] = state['spring_stored_J']
    gross = (model.section.width*model.model['span_m']*model.section.h
             *2160000*meta['mean_delta_k'])
    row['gross_coupon_sensible_J'] = gross
    row['composite_minus_gross_sensible_J'] = state['sensible_enthalpy_J']-gross
    row['mapping'] = meta
    return row


def trace(model,cfg,substeps=2,reverse=True):
    state = model.solve(0,0)
    work=thermal=0.
    history=[record(model,state,0,0,'ZERO',0,0,0)]
    g0=t0=0.
    gtarget = model.cfg['loading']['gravity_preload_factor']
    guard=cfg['guard_DCR']
    def advance(trial,g1,t1,phase):
        nonlocal state,work,thermal,g0,t0
        pieces=panel._refined_advance(model,state,g0,t0,trial,g1,t1,model.cfg['acceptance']['relative_incremental_energy'])
        for new,gn,tn,dw,dt,residual in pieces:
            if new['max_DCR']>guard+cfg['acceptance']['guard_absolute']:
                raise ValueError('Intermediate accepted state exceeds guard')
            work+=dw; thermal+=dt; state=new; g0=gn; t0=tn
            history.append(record(model,state,g0,t0,phase,work,thermal,residual))
    for gravity in np.linspace(0,gtarget,6)[1:]:
        advance(model.solve(gravity,0,state['u']),float(gravity),0.,'PRELOAD')
    preload = state
    bracket=None
    grid=np.concatenate([np.linspace(a,b,substeps+1)[1:] for a,b in zip(model.source.times[:-1],model.source.times[1:])])
    if model.mode=='cold': grid=[model.source.times[-1]]
    for value in grid:
        value=float(value)
        trial=model.solve(gtarget,value,state['u'])
        if trial['max_DCR']>=guard:
            lo,hi=t0,value
            low_state,high_state=state,trial
            while hi-lo>cfg['guard_time_tolerance_s']:
                mid=(lo+hi)/2
                middle=model.solve(gtarget,mid,(low_state['u']+high_state['u'])/2)
                if middle['max_DCR']>=guard: hi,high_state=mid,middle
                else: lo,low_state=mid,middle
            bracket={'accepted_time_s':lo,'rejected_time_s':hi,'accepted_DCR':low_state['max_DCR'],
                     'rejected_DCR':high_state['max_DCR'],'rejected_committed':False}
            if lo>t0: advance(low_state,gtarget,lo,'HEATING')
            break
        advance(trial,gtarget,value,'HEATING')
    terminal=state
    terminal_row=history[-1]
    terminal_time=t0
    if reverse and t0>0:
        # Synthetic reverse profile traversal, with every saved knot respected.
        knots=[terminal_time]+[float(v) for v in model.source.times[::-1] if 0<=v<terminal_time]
        for a,b in zip(knots[:-1],knots[1:]):
            for value in np.linspace(a,b,max(substeps,cfg['cycle_steps'])+1)[1:]:
                advance(model.solve(gtarget,value,state['u']),gtarget,float(value),'REVERSE_PROFILE_TEST')
    return {'mode':model.mode,'terminal':terminal_row,'guard_bracket':bracket,'history':history,
            'terminal_u_m_rad':terminal['u'].tolist(), 'returned_u_m_rad':state['u'].tolist(),
            'preload_u_m_rad':preload['u'].tolist(),
            'cycle_displacement_error':float(np.max(abs(state['u']-preload['u']))),
            'cycle_stored_error_J':float(abs(state['stored_J']-preload['stored_J'])),
            'terminal_fiber_temperature_k':terminal['batch']['delta_temperature_c'].tolist(),
            'terminal_fiber_stress_pa':terminal['batch']['stress_pa'].tolist(),
            'terminal_section_q':terminal['batch']['q'].tolist(),
            'terminal_section_resultants':terminal['batch']['Q'].tolist(),
            'terminal_section_stored_J_per_m':terminal['batch']['stored_J_per_m'].tolist(),
            'section':{k:getattr(model.section,k).tolist() for k in ('y','area','E','alpha','density','cp','K')},
            'longitudinal_weights_m':model.weights.tolist(),
            'terminal_spring_stored_J':terminal['spring_stored_J']}
