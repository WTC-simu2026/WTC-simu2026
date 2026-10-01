"""V11M sampling and zero-measure face-screen diagnostic; frozen V11L mechanics."""
import numpy as np
import v11l_profile_panel as legacy


def sampled(saved, interval):
    times=np.array([r['time_s'] for r in saved['profiles']])
    selected=np.linspace(0,times[-1],round(times[-1]/interval)+1)
    indices=[int(np.argmin(abs(times-t))) for t in selected]
    if max(abs(times[indices]-selected))>1e-10:
        raise ValueError('Requested snapshots must be actual saved thermal steps')
    return {'profiles':[saved['profiles'][i] for i in indices],
            'history':[saved['history'][i] for i in indices]}


class EarlyPanel(legacy.ProfilePanel):
    def __init__(self,*args,boundary_face_screen=False,**kwargs):
        self.boundary_face_screen=boundary_face_screen
        super().__init__(*args,**kwargs)

    def probes(self,batch,u,t):
        qend=np.einsum('ejai,ei->eja',self.Bends,u[self.dofs[::2]]).reshape(-1,2)
        q=np.vstack([qend,batch['q']])
        temp,meta=self.mapped(t)
        tk=np.array(meta['delta_k'])
        if self.boundary_face_screen and self.mode!='cold':
            surfaces=self.source.surface_delta.copy()
            surfaces[0]=0.  # No mechanical preload impulse at t=0.
            tk[[0,-1]]=[np.interp(t,self.source.times,surfaces[:,i]) for i in range(2)]
        return q,np.r_[np.array(meta['x_m'])-self.section.h/2,self.section.y[self.concrete_mask]],np.r_[tk,temp[self.concrete_mask]],temp

    def _section_screens(self,batch,u,time_s):
        q,y,tc,temp=self.probes(batch,u,time_s)
        c,s=self.concrete_mask,self.steel_mask
        stress=self.section.E[c][0]*(q[:,0,None]-q[:,1,None]*y-self.section.alpha[c][0]*tc)
        it=np.unravel_index(np.argmax(stress),stress.shape)
        ic=np.unravel_index(np.argmin(stress),stress.shape)
        steel=self.section.E[s]*(q[:,0,None]-q[:,1,None]*self.section.y[s]-self.section.alpha[s]*temp[s])
        return [
            {'id':f'SLAB-Q{it[0]}-DEPTH{it[1]}','kind':'slab_concrete_tension_elastic_guard','DCR':float(max(0,stress[it])/self.section.ft)},
            {'id':f'SLAB-Q{ic[0]}-DEPTH{ic[1]}','kind':'slab_concrete_compression_elastic_guard','DCR':float(max(0,-stress[ic])/self.section.fc)},
            {'id':'SLAB-REBAR-ALL-ENDS-AND-GAUSS','kind':'slab_reinforcement_yield_elastic_guard','DCR':float(np.max(abs(steel))/self.section.fy)}]

    def saved_probes(self,run):
        u=np.array(run['terminal_u_m_rad'])
        batch={'q':np.array(run['terminal_section_q'])}
        t=run['terminal']['profile_time_coordinate_s']
        q,y,tc,temp=self.probes(batch,u,t)
        return {'q':q.tolist(),'concrete_y_m':y.tolist(),'concrete_delta_k':tc.tolist(),
                'ft_pa':float(self.section.ft),'fc_pa':float(self.section.fc),'fy_pa':float(self.section.fy),
                'screens':self._section_screens(batch,u,t),
                'boundary_face_screen':self.boundary_face_screen,
                'initial_mechanical_face_increment_k':0.}
