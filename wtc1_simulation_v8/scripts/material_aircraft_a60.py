"""Owned differentiable displacement/linear LAW117 contract with explicit trial state.

Only displacement criterion, linear evolution and power-law mixing are covered.
No native Engine integration, moving-frame geometry or rate law is claimed.
"""
import os
os.environ['OPENBLAS_NUM_THREADS']='1'
os.environ['OMP_NUM_THREADS']='1'
from dataclasses import dataclass
import numpy as np

class D:
    def __init__(self,v,g=None):self.v=float(v);self.g=np.zeros(3) if g is None else np.asarray(g,float)
    @staticmethod
    def cast(x):return x if isinstance(x,D) else D(x)
    def __add__(self,x):x=D.cast(x);return D(self.v+x.v,self.g+x.g)
    __radd__=__add__
    def __neg__(self):return D(-self.v,-self.g)
    def __sub__(self,x):return self+-D.cast(x)
    def __rsub__(self,x):return D.cast(x)+-self
    def __mul__(self,x):x=D.cast(x);return D(self.v*x.v,self.g*x.v+x.g*self.v)
    __rmul__=__mul__
    def __truediv__(self,x):x=D.cast(x);return D(self.v/x.v,(self.g*x.v-x.g*self.v)/(x.v*x.v))
    def __rtruediv__(self,x):return D.cast(x)/self
    def __pow__(self,p):return D(self.v**p,self.g*(p*self.v**(p-1)))

@dataclass(frozen=True)
class State:
    peak:float=0.
    damage:float=0.
    active:bool=True

def thresholds(vector,p):
    x,y,z=vector;n=z if z.v>0 else D(0);s2=x*x+y*y;r2=n*n+s2
    if r2.v==0:return D(p['TN_MPa']/p['EN_N_mm3']),D(2*p['GI_N_mm']/p['TN_MPa']),D(0)
    r=r2**.5;dn=p['TN_MPa']/p['EN_N_mm3'];ds=p['TT_MPa']/p['ET_N_mm3']
    d0=r/((n*n/(dn*dn)+s2/(ds*ds))**.5)
    exponent=p['power_exponent']
    Q=((p['EN_N_mm3']*n*n/p['GI_N_mm'])**exponent+(p['ET_N_mm3']*s2/p['GII_N_mm'])**exponent)**(1/exponent)
    df=2*r2/(d0*Q)
    return d0,df,r

def trial(gap,committed,p):
    vector=[D(value,np.eye(3)[j]) for j,value in enumerate(gap)];d0,df,r=thresholds(vector,p)
    peak=r if r.v>committed.peak else D(committed.peak)
    damage=D(committed.damage)
    if peak.v>d0.v and peak.v!=0:
        candidate=df*(peak-d0)/(peak*(df-d0))
        if candidate.v>damage.v:damage=candidate
    if damage.v>=1:damage=D(1)
    active=committed.active and not (peak.v>df.v)
    stiffness=[p['ET_N_mm3'],p['ET_N_mm3'],p['EN_N_mm3']]
    t=[]
    for j,q in enumerate(vector):
        value=q*stiffness[j]
        if not(j==2 and q.v<0):value=(1-damage)*value
        if not active:value=D(0)
        t.append(value)
    return np.asarray([a.v for a in t]),np.asarray([a.g for a in t]),State(peak.v,damage.v,active),{'d0':d0.v,'df':df.v,'radius':r.v}

def path_values(times,case,p):
    times=np.asarray(times);knot=np.asarray(case['knot_times_ms']);values=np.asarray(case['knot_gaps_mm']);result=np.zeros((len(times),3))
    for ta,tb,a,b in zip(knot[:-1],knot[1:],values[:-1],values[1:]):
        mask=(times>=ta)&(times<=tb);s=(times[mask]-ta)/(tb-ta);result[mask]=a+(b-a)*(3*s*s-2*s*s*s)[:,None]
    return result

def run_path(gaps,p):
    state=State();tractions=[];states=[];limits=[]
    for q in gaps:
        t,_,state,v=trial(q,state,p);tractions.append(t);states.append([state.peak,state.damage,float(state.active)]);limits.append([v['d0'],v['df']])
    return np.asarray(tractions),np.asarray(states),np.asarray(limits)
