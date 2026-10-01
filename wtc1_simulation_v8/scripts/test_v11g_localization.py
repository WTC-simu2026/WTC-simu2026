"""Analytical, fault-injection and complete-path verification for V11G."""
import copy
import numpy as np
import v11g_localization_model as model


def run(cfg, si, bars, replay, half, negative, panels, original_panels, eccentricity):
    tests = []

    def check(name, ok, evidence):
        tests.append({"test": name, "pass": bool(ok), "evidence": evidence})

    for x in (0., 2.5, 5., 7.5, 10.):
        loads = [{"x_m":0.,"Fx_N":0.,"Fy_N":10.,"couple_Nm":0.},
                 {"x_m":10.,"Fx_N":0.,"Fy_N":10.,"couple_Nm":0.}]
        n,m = model.equilibrated_resultants(x,-2.,loads)
        check(f"simply_supported_UDL_resultants_x{x}", abs(n)<1e-12 and abs(m-(10*x-x*x))<1e-12, {"N":n,"M":m})
    loads = [{"x_m":0.,"Fx_N":4.,"Fy_N":.3,"couple_Nm":3.},
             {"x_m":10.,"Fx_N":-4.,"Fy_N":-.3,"couple_Nm":0.}]
    n,m = model.equilibrated_resultants(5.,0.,loads)
    check("axial_sign_and_applied_couple_sign", abs(n+4)<1e-12 and abs(m+1.5)<1e-12, {"N":n,"M":m})
    n,m = model.equilibrated_resultants(10.,0.,loads)
    check("outside_section_balance_after_end_loads", abs(n)<1e-12 and abs(m)<1e-12, {"N":n,"M":m})
    # Gauss-point moment agreement alone is blind to the known quadratic UDL bubble.
    dx,q=2.,-3.
    gp=np.array([dx*(.5-.5/np.sqrt(3)),dx*(.5+.5/np.sqrt(3))])
    exact=lambda x: 7.+5.*x+q*x*x/2
    values=np.array([exact(x) for x in gp])
    slope=(values[1]-values[0])/(gp[1]-gp[0])
    interpolant=lambda x: values[0]+slope*(x-gp[0])
    sampled_error=max(abs(exact(x)-interpolant(x)) for x in gp)
    endpoint_gap=max(abs(exact(x)-interpolant(x)) for x in (0.,dx))
    check("two_Gauss_agreement_does_not_bound_between_point_moment_error",sampled_error<1e-12 and abs(endpoint_gap-abs(q)*dx*dx/12)<1e-12,
          {"Gauss_error_Nm":sampled_error,"endpoint_gap_Nm":endpoint_gap,"not_a_nonlinear_material_endpoint_stress":True})
    mat = model.concrete(si,.1)
    old = model.material.concrete_trial(mat,model.material.zero_concrete(1),[mat.e0])
    for fraction in (.1,.75,0.,.75,1.,1.1):
        previous = copy.deepcopy(old)
        trial,it = model.solve_opening(mat,old,fraction*2*mat.Gf/mat.ft,cfg["solver"])
        check(f"trial_does_not_mutate_old_{fraction}_{len(tests)}", all(np.array_equal(old[k],previous[k]) for k in old), it)
        check(f"damage_irreversible_{fraction}_{len(tests)}", trial["damage"][0]>=old["damage"][0]-1e-12, float(trial["damage"][0]))
        old=trial
    bad_options={**cfg["solver"],"maximum_iterations":0}
    failed=False
    previous=copy.deepcopy(old)
    try:
        model.solve_opening(mat,old,.0003,bad_options)
    except model.Unresolved:
        failed=True
    check("failed_opening_trial_not_committed", failed and all(np.array_equal(old[k],previous[k]) for k in old), "Explicit unresolved exception")
    for value in (-.001,float("nan")):
        rejected=False
        try:
            model.solve_opening(mat,old,value,cfg["solver"])
        except ValueError:
            rejected=True
        check(f"invalid_opening_rejected_{value}", rejected, str(value))
    bad_cfg=copy.deepcopy(cfg);bad_cfg["solver"]["temperature_c"]=200.
    rejected=False
    try:
        model.localized_bar(bad_cfg,si,2.,9,"monotonic")
    except ValueError:
        rejected=True
    check("unverified_temperature_rejected", rejected, "20 C only")
    check("sixteen_declared_bar_paths", len(bars)==16 and len({b["summary"]["id"] for b in bars})==16,len(bars))
    allbars=[*bars,*replay,*half]
    for key,tolerance_key in (("force_error_relative_Aft","bar_force_relative_to_Aft"),
                              ("displacement_error_relative_wc","bar_displacement_relative_to_wc"),
                              ("exact_energy_error_relative_AGf","bar_energy_relative_to_AGf"),
                              ("external_energy_error_relative_AGf","bar_energy_relative_to_AGf"),
                              ("equilibrium_relative_Aft","bar_equilibrium_relative_to_Aft"),
                              ("opening_error_relative_wc","bar_displacement_relative_to_wc")):
        worst=max(r[key] for b in allbars for r in b["history"])
        check("all_bar_runs_"+key,worst<=cfg["acceptance"][tolerance_key],worst)
    for b in bars:
        s=b["summary"]
        check("complete_fracture_energy_"+s["id"], abs(s["final_dissipation_J"]/s["target_single_fracture_energy_J"]-1)<cfg["acceptance"]["bar_energy_relative_to_AGf"],s["final_dissipation_J"])
        check("snapback_control_"+s["id"], (s["observed_postpeak_negative_delta_steps"]>0)==s["expected_snapback"],s["observed_postpeak_negative_delta_steps"])
    comparisons=[]
    for reference,other in zip(bars,half,strict=True):
        s=reference["summary"]
        area,ft,wc=cfg["bar"]["area_m2"],si["ft_Pa"],s["critical_opening_m"]
        errors={"force_N":0.,"end_displacement_m":0.,"dissipated_J":0.}
        for phase in sorted({r["phase"] for r in reference["history"]}):
            a=[r for r in reference["history"] if r["phase"]==phase]
            b=[r for r in other["history"] if r["phase"]==phase]
            for key,scale in (("force_N",area*ft),("end_displacement_m",wc),("dissipated_J",area*si["Gf_J_m2"])):
                for row in a:
                    value=np.interp(row["phase_parameter"],[r["phase_parameter"] for r in b],[r[key] for r in b])
                    errors[key]=max(errors[key],abs(row[key]-value)/scale)
        comparisons.append({"id":s["id"],"half_step_errors":errors})
    check("half_step_curves_unchanged",max(v for r in comparisons for v in r["half_step_errors"].values())<cfg["acceptance"]["bar_mesh_and_step_relative"],comparisons)
    mesh_errors=[]
    for length in cfg["bar"]["lengths_m"]:
        for path in ("monotonic","cyclic"):
            group=[b for b in bars if b["summary"]["length_m"]==length and b["summary"]["path"]==path]
            base=group[0]
            for other in group[1:]:
                for a,b in zip(base["history"],other["history"],strict=True):
                    mesh_errors.extend([abs(a["force_N"]-b["force_N"])/(cfg["bar"]["area_m2"]*si["ft_Pa"]),
                                        abs(a["end_displacement_m"]-b["end_displacement_m"])/base["summary"]["critical_opening_m"],
                                        abs(a["dissipated_J"]-b["dissipated_J"])/(cfg["bar"]["area_m2"]*si["Gf_J_m2"])])
    check("single_selected_crack_mesh_objectivity",max(mesh_errors)<cfg["acceptance"]["bar_mesh_and_step_relative"],max(mesh_errors))
    check("central_crack_plane_fixed",all(abs(b["summary"]["band_center_m"]-b["summary"]["length_m"]*.5)<1e-12 for b in bars),"Only the numerical band width changes")
    for row in negative:
        error=abs(row["D_J"]-row["expected_multi_band_energy_J"])/row["expected_multi_band_energy_J"]
        check(f"negative_control_expected_multiple_energy_n{row['cells']}_gp{row['gauss_per_cell']}",error<1e-10 and row["ratio_to_one_crack_energy"]>1.1
              and abs(row["D_J"]-row["external_work_J"])<1e-9,row)
    for field,tolerance in (("weak_nodal_relative","panel_weak_nodal_relative"),("slab_global_force_relative","panel_slab_global_force_relative"),("slab_global_moment_relative","panel_slab_global_moment_relative")):
        worst=max(p["summary"][field] for p in panels)
        check("saved_panels_"+field,worst<=cfg["acceptance"][tolerance],worst)
    example=next(p for p in original_panels if p["summary"]["id"]=="BEND_R02")
    omitted_couple=model.panel_recovery(example,"FAULT_OMIT_COUPLE",0.,cfg["acceptance"])
    check("audit_detects_omitted_eccentric_couple",omitted_couple["summary"]["weak_nodal_relative"]>1e-4,omitted_couple["summary"]["weak_nodal_relative"])
    omitted_act=copy.deepcopy(example);omitted_act["summary"]["actuator_reaction_N"]=0.
    missing=model.panel_recovery(omitted_act,"FAULT_OMIT_ACTUATOR",eccentricity,cfg["acceptance"])
    check("audit_detects_omitted_slab_actuator",missing["summary"]["slab_global_force_relative"]>1e-4,missing["summary"]["slab_global_force_relative"])
    return tests,comparisons
