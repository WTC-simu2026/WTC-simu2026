"""Analytic coupling checks and immutable V11E constitutive regressions."""
import copy
import numpy as np
import v11d_panel_model as old_panel
import v11f_panel_model as m
import test_v11e_section


def run(cfg,inputs):
    tests=[{**r,"test":"V11E_regression/"+r["test"]} for r in test_v11e_section.run(inputs["e"])]
    def check(name,ok,evidence):tests.append({"test":name,"pass":bool(ok),"evidence":evidence})
    def close(name,a,b,tol=1e-9):
        error=float(np.max(abs(np.asarray(a)-np.asarray(b)))/max(1.,float(np.max(abs(np.asarray(b))))))
        check(name,error<=tol,{"relative_error":error,"tolerance":tol})
    L=2.7
    for x in (0.,L*.231,L):
        B=m.beam_B(x,L)
        close(f"beam_translation_{x}",B@np.array([3.,5.,0.,3.,5.,0.]),[0.,0.])
        close(f"beam_rigid_rotation_{x}",B@np.array([0.,0.,.2,0.,L*.2,.2]),[0.,0.])
        close(f"beam_constant_axial_and_curvature_{x}",B@np.array([0.,0.,0.,.003*L,.02*L*L/2,.02*L]),[.003,.02])
    case={"id":"ANALYTIC","kind":"gravity","rho_total":.002,"layout":"top"}
    panel=m.Panel(cfg,inputs,case)
    s=panel.section;zero=panel.zero()
    q=np.column_stack((np.linspace(-.0002,.0004,len(panel.x)),np.linspace(-.015,.026,len(panel.x))))
    batch=panel.batch(zero,q);errors=[]
    for p in (0,len(q)//3,len(q)//2,len(q)-1):
        single=s.trial(s.zero(),q[p])
        for key,actual in (("N",batch["Q"][p,0]),("M",batch["Q"][p,1]),("stored",batch["stored"][p]),("dissipated",batch["dissipated"][p]),("work",batch["work"][p])):
            errors.append(abs(actual-single[key])/max(1.,abs(single[key])))
        close(f"batch_single_section_tangent_point{p}",batch["Ksec"][p],single["K"])
    check("batch_resultants_and_energies_equal_V11E",max(errors)<1e-10,max(errors))
    nextq=q*.2;second=panel.batch(batch,nextq)
    check("batch_unloading_preserves_all_fiber_history",np.array_equal(second["c"]["r"],batch["c"]["r"]),"No damage reset while unloading")
    # Regression against V11D nodal solutions and DISCRETE energy, no UDL bubble credit.
    plain=m.Panel(cfg,inputs,{"id":"ELASTIC_PLAIN","rho_total":0.,"layout":"symmetric"})
    for gravity in (.05,.25,1.):
        response=plain.solve(plain.zero(),gravity)
        old=old_panel.evaluate_panel(inputs["d"],inputs["c"],inputs["a"],inputs["transfer"],inputs["seats"],{**plain.spec,"gravity_factor":gravity})
        for label,dofs in (("vertical",plain.model["w"]),("axial",plain.model["ux"]),("rotation",plain.model["theta"])):
            error=float(np.max(abs(response["u"][dofs]-old["u"][dofs]))/max(1e-9,float(np.max(abs(old["u"][dofs])))))
            check(f"V11D_elastic_{label}_g{gravity}",error<cfg["acceptance"]["elastic_V11D_displacement_relative"],error)
        close(f"V11D_discrete_energy_g{gravity}",response["stored_J"],old["strain_energy_J"],tol=1e-4)
        check(f"V11D_regression_uncracked_g{gravity}",np.max(response["c"]["damage"])==0.,float(np.max(response["c"]["damage"])))
    inventories=[];coupon=[]
    for sub in (2,4,8):
        mm=m.Panel(cfg,inputs,case,sub);inventories.append(mm.inventory())
        close(f"longitudinal_weights_sum_span_sub{sub}",sum(mm.weights),mm.model["span_m"])
        close(f"load_80psf_applied_once_sub{sub}",-sum(mm.force_unit[mm.model["w"]]),80*m.elastic.PSF*mm.section.width*mm.model["span_m"])
        close(f"fixed_equivalent_contact_density_sub{sub}",sum(t["k"] for t in mm.terms if t["kind"]=="contact")/inputs["d"]["vertical_connection"]["contact_stiffness_per_equivalent_knuckle_N_m"],32.)
        material=mm.section.concrete
        one=m.section.concrete_trial(material,m.section.zero_concrete(1),[material.ef*1.1])
        bandwork=float(one["work"][0])*sum(mm.section.Ac)*mm.weights[0]
        expected=material.Gf*sum(mm.section.Ac)
        close(f"one_crack_band_work_Gf_Ac_sub{sub}",bandwork,expected)
        coupon.append({"subdivisions":sub,"band_length_m":mm.Lch,"section_count":len(mm.x),"one_fully_cracked_band_J":bandwork,"Gf_times_Ac_J":expected,
                       "if_every_band_fully_cracks_J":bandwork*len(mm.x),"meaning":"Single-band regularization only; total depends on crack number, which still needs a mesh test"})
    check("refinement_preserves_actuator_location_and_steel",len({i["slab_actuator_x_m"] for i in inventories})==1 and all(i["steel_members"]==63 and i["contact_stations"]==17 for i in inventories),inventories)
    # Tangent and virtual work assembly in a smooth all-contact state.
    r=plain.solve(plain.zero(),.25);u=r["u"];trial=plain.evaluate(plain.zero(),u,.25,{})
    close("assembled_tangent_symmetry",trial["K"],trial["K"].T)
    direction=np.sin(np.arange(plain.size)*.37)*1e-8
    plus=plain.evaluate(plain.zero(),u+direction,.25,{})
    minus=plain.evaluate(plain.zero(),u-direction,.25,{})
    close("global_tangent_directional_difference",(plus["reaction"]-minus["reaction"])/2,trial["K"]@direction,tol=1e-6)
    close("elastic_energy_gradient_virtual_work",(plus["stored_J"]-minus["stored_J"])/2,(trial["reaction"]+trial["force"])@direction,tol=1e-7)
    # Rigid rotation creates neither slab strain nor eccentric tie slip.
    rotation=np.zeros(plain.size);angle=1e-6;coords=plain.model["nodes"]
    rotation[:plain.model["steel_dofs"]:2]=-angle*coords[:,1]
    rotation[1:plain.model["steel_dofs"]:2]=angle*coords[:,0]
    slab_height=float(coords[0,1])+plain.model["eccentricity_m"]
    rotation[plain.model["ux"]]=-angle*slab_height;rotation[plain.model["w"]]=angle*plain.model["slab_x_m"];rotation[plain.model["theta"]]=angle
    rigid=plain.evaluate(plain.zero(),rotation,0.,{})
    close("rigid_rotation_slab_strains",rigid["batch"]["q"],np.zeros_like(rigid["batch"]["q"]))
    internal_forces=[n for t,n in zip(plain.terms,rigid["term_force"],strict=True) if not t["kind"].startswith("seat")]
    check("rigid_rotation_eccentric_ties_and_members_zero",max(abs(np.array(internal_forces)))<1e-6,float(max(abs(np.array(internal_forces)))))
    # Solver failure and direct trial excursions must never alter committed material histories.
    backup={k:{key:value.copy() for key,value in r[k].items()} for k in ("c","s")};saved_u=r["u"].copy()
    _=plain.evaluate(r,u+np.cos(np.arange(plain.size))*.005,.25,{})
    original_iterations=plain.cfg["solver"]["maximum_newton_iterations"]
    try:
        plain.cfg=copy.deepcopy(plain.cfg);plain.cfg["solver"]["maximum_newton_iterations"]=1
        failed=False
        try:plain.solve(r,.25,{plain.truss_actuator:r["u"][plain.truss_actuator]-.1})
        except m.Unresolved:failed=True
    finally:plain.cfg["solver"]["maximum_newton_iterations"]=original_iterations
    check("forced_solver_failure_is_explicit",failed,"No failed trial promoted")
    check("rejected_trials_preserve_each_committed_array",np.array_equal(r["u"],saved_u) and all(np.array_equal(r[k][key],backup[k][key]) for k in backup for key in backup[k]),"History rollback without healing or unintended plasticity")
    # Unilateral signs and contact recovery at fixed prescribed gaps.
    z=plain.zero();test_u=np.zeros(plain.size)
    for gap in (-1e-5,1e-5,-1e-5):
        test_u[plain.model["w"]]=gap
        t=plain.evaluate(z,test_u,0.,{})
        contact=[n for term,n in zip(plain.terms,t["term_force"],strict=True) if term["kind"]=="contact"]
        ties=[n for term,n in zip(plain.terms,t["term_force"],strict=True) if term["kind"]=="vertical_tie"]
        check(f"unilateral_gap_{gap}_step{len(tests)}",all(n<=0 for n in contact) and all(n>=0 for n in ties) and (all(n==0 for n in ties) if gap<0 else all(n==0 for n in contact)),{"gap_m":gap})
    bad=copy.deepcopy(cfg);bad["loading"]["temperature_c"]=200.;rejected=False
    try:m.Panel(bad,inputs,case)
    except ValueError:rejected=True
    check("thermal_input_rejected",rejected,"No unverified thermal coupling")
    return tests,coupon
