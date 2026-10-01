"""Exact nodal thermal loads on the inherited reversible slab/truss/contact panel."""
import numpy as np
import v11i_thermoelastic_panel_model as inherited
import v11o_startup_bridge as exact

class NodalPanel(inherited.ThermoElasticPanel):
    def __init__(self,cfg,cold_cfg,thermo_cfg,section_cfg,inputs,spec,source):
        super().__init__(cfg,cold_cfg,thermo_cfg,section_cfg,inputs,
            {'id':spec['id'],'delta_t_bottom_c':0.,'delta_t_top_c':0.,'target_scale':1.},spec['subdivisions'])
        self.exact=exact.ContinuousSection(self.section); self.source=source; self.spec=spec
        self.depth=np.array(source['x_m']); self.fields={}
        mids=(np.arange(len(self.model['elements']))+.5)/len(self.model['elements'])
        element_zone=np.ones(len(mids)) if spec['zone']=='whole' else ((mids>=.375)&(mids<.625)).astype(float)
        self.zone=np.repeat(element_zone,2); self.end_zone=np.repeat(element_zone,2)
        self.tangent_cache={}

    def field(self,index):
        if index!=int(index) or not 0<=int(index)<len(self.source['profiles']): raise ValueError('Only saved integer thermal steps')
        index=int(index)
        if index not in self.fields:
            t=np.array(self.source['profiles'][index]['temperature_c'])-20
            r=self.exact.solve(self.depth,t,t[[0,-1]],'FULLY_RESTRAINED')
            self.fields[index]={'temperature':t,'f':np.array(r['thermal_force_N_Nm']),'S':r['thermal_square_energy_S_J_per_m'],
                'sensible':r['sensible_J_per_m'],'steel':np.array(r['steel_delta_k']),
                'mean':r['mean_delta_k'],'square':r['mean_square_delta_k2']}
        return self.fields[index]

    def section_batch(self,u,index):
        q=np.einsum('pai,pi->pa',self.B,u[self.dofs]); field=self.field(index)
        f=self.zone[:,None]*field['f']; S=self.zone**2*field['S']; K=self.exact.K
        stored=.5*np.einsum('pa,ab,pb->p',q,K,q)-np.sum(q*f,axis=1)+.5*S
        return {'q':q,'Q':q@K-f,'Ksec':np.broadcast_to(K,(len(q),2,2)),
            'stored_J_per_m':stored,'sensible_J_per_m':self.zone*field['sensible'],
            'thermal_resultant':f,'thermal_square':S,'field_index':int(index)}

    def _section_screens(self,batch,u,index):
        ends=np.einsum('ejai,ei->eja',self.Bends,u[self.dofs[::2]]).reshape(-1,2)
        q=np.vstack((ends,batch['q'])); zone=np.r_[self.end_zone,self.zone]; f=self.field(index); s=self.exact
        stress=s.Ec*(q[:,0,None]-q[:,1,None]*(self.depth-s.h/2)-s.alphac*zone[:,None]*f['temperature'])
        it=np.unravel_index(np.argmax(stress),stress.shape); ic=np.unravel_index(np.argmin(stress),stress.shape)
        steel=s.Es*(q[:,0,None]-q[:,1,None]*s.ys-s.alphas*zone[:,None]*f['steel'])
        return [
            {'id':f'SLAB-Q{it[0]}-DEPTH{it[1]}','kind':'slab_concrete_tension_elastic_guard','DCR':max(0,float(stress[it]))/s.ft},
            {'id':f'SLAB-Q{ic[0]}-DEPTH{ic[1]}','kind':'slab_concrete_compression_elastic_guard','DCR':max(0,float(-stress[ic]))/s.fc},
            {'id':'SLAB-REBAR-ENDS-AND-GAUSS','kind':'slab_reinforcement_yield_elastic_guard','DCR':float(np.max(np.abs(steel),initial=0))/s.fy}]

    def solve(self,gravity,index,initial=None):
        # Same line-search Newton equations as V11I; cache eigendecomposition of
        # each constant active-set tangent. No regularization or property edit.
        u=np.zeros(self.size) if initial is None else np.array(initial,copy=True)
        opt=self.cold_cfg['solver']; scale=self.scale
        for iteration in range(opt['maximum_newton_iterations']):
            r=self.evaluate(u,gravity,index); signature=r['active_signature']
            if signature not in self.tangent_cache:
                K=scale[:,None]*r['K']*scale[None,:]; values,vectors=np.linalg.eigh(.5*(K+K.T))
                self.tangent_cache[signature]=(values,vectors)
            values,vectors=self.tangent_cache[signature]
            if min(values)<=opt['scaled_tangent_minimum']: raise inherited.Unresolved('NONPOSITIVE_TANGENT_NOT_COLLAPSE')
            if r['equilibrium_residual']<=self.cfg['acceptance']['relative_equilibrium']:
                r.update({'newton_iterations':iteration+1,'minimum_scaled_tangent_eigenvalue':float(min(values))}); return r
            du=scale*(vectors@((vectors.T@(-scale*r['reaction']))/values))
            merit=np.linalg.norm(scale*r['reaction'])
            for halving in range(opt['maximum_line_search_halvings']+1):
                candidate=u+du*2.**(-halving); trial=self.evaluate(candidate,gravity,index)
                if np.linalg.norm(scale*trial['reaction'])<merit*(1-1e-4*2.**(-halving)) or trial['equilibrium_residual']<=self.cfg['acceptance']['relative_equilibrium']:
                    u=candidate; break
            else: raise inherited.Unresolved('LINE_SEARCH_EXHAUSTED_NOT_COLLAPSE')
        raise inherited.Unresolved('ITERATIONS_EXHAUSTED_NOT_COLLAPSE')

    def thermal_work_increment(self,old,new):
        a,b=old['batch'],new['batch']
        return float(self.weights@(-.5*np.sum((a['q']+b['q'])*(b['thermal_resultant']-a['thermal_resultant']),axis=1)+.5*(b['thermal_square']-a['thermal_square'])))

    def export_inventory(self):
        return {'spec':self.spec,'size':self.size,'section':self.exact.inventory(),'force_unit':self.force_unit.tolist(),
            'B':self.B.tolist(),'Bends':self.Bends.tolist(),'dofs':self.dofs.tolist(),'weights_m':self.weights.tolist(),
            'gauss_x_m':self.x.tolist(),'zone':self.zone.tolist(),'end_zone':self.end_zone.tolist(),
            'term_B':self.term_B.tolist(),'term_k':self.term_k.tolist(),'compression_only':self.compression.tolist(),
            'tension_only':self.tension.tolist(),'terms':self.terms,'span_m':self.model['span_m'],
            'slab_x_m':self.model['slab_x_m'].tolist(),'slab_w_dofs':list(map(int,self.model['w'])),
            'slab_ux_dofs':list(map(int,self.model['ux'])),'slab_theta_dofs':list(map(int,self.model['theta'])),
            'steel_nodes':self.model['nodes'],'steel_members':self.model['steel_members']}

def snapshot(model,state,gravity,index,phase,committed,work=0.,thermal_work=0.,increment_error=0.):
    keys=['stored_J','spring_stored_J','slab_stored_J','sensible_enthalpy_J','max_DCR','governing','equilibrium_residual',
          'max_slab_down_m','max_slab_up_m','max_truss_down_m','max_opening_m','max_overlap_m','contact_count','vertical_tension_count',
          'seat_vertical_reaction_N','seat_horizontal_reaction_N','gravity_load_N','vertical_balance_relative',
          'horizontal_balance_absolute_N','support_uplift_unchecked','support_horizontal_compression_unchecked',
          'minimum_scaled_tangent_eigenvalue','concrete_tension_ratio','concrete_compression_ratio','reinforcement_yield_ratio','component_max_DCR']
    r={k:state[k] for k in keys}; src=model.source['history'][index]
    gross=model.exact.width*float(model.weights@model.zone)*src['enthalpy_j_m2']
    r.update({'u':state['u'].tolist(),'term_force_N':state['term_force'].tolist(),'term_gap':state['term_gap'].tolist(),
        'term_DCR':state['term_DCR'].tolist(),'thermal_step':int(index),'time_s':src['time_s'],'phase':phase,'gravity':gravity,'committed':committed,
        'external_work_J':work,'thermal_work_J':thermal_work,'increment_energy_residual_relative':increment_error,
        'total_energy_residual_relative':abs(state['stored_J']-work-thermal_work)/max(1,abs(state['stored_J']),abs(work),abs(thermal_work)),
        'gross_coupon_sensible_J':gross,'composite_minus_gross_sensible_J':state['sensible_enthalpy_J']-gross,
        'top_temperature_c':src['top_surface_temperature_c']})
    return r
