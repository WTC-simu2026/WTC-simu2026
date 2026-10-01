"""Assembly regressions, unit/sign checks and limiting V11A comparisons.

These compare numerical models, not the constructed tower. Layout variation
does not stand for a discretization-convergence study of a known truss.
"""
import copy
import math
import numpy as np
import v11a_component_model as old
import v11c_panel_model as new


def run(cfg,base,transfer,seats):
    tests=[]
    def check(name,ok,evidence):
        tests.append({"test":name,"pass":bool(ok),"evidence":evidence})
    def close(a,b,tol=1e-9):
        return math.isclose(float(a),float(b),rel_tol=tol,abs_tol=1e-8)
    def evaluate(**spec): return new.evaluate_panel(cfg,base,transfer,seats,spec)

    result=evaluate()
    model=result["model"]
    expected_load=cfg["panel"]["load_psf"]*old.PSF*(80*old.IN)*(713*old.IN)
    check("paired_load_80psf_width80in_no_double_self_weight",close(-sum(model["force"]),expected_load),expected_load)
    check("paired_vertical_reactions_equal_total_load",close(result["vertical_pair_reaction_N"],expected_load),result["vertical_pair_reaction_N"])
    check("each_paired_seat_reaction_15_844_kip",all(close(-r["force_N"]/old.KIP,15.844444444444445,1e-9) for r in result["terms"] if r["kind"]=="seat_v"),[-r["force_N"]/old.KIP for r in result["terms"] if r["kind"]=="seat_v"])
    for side in ("interior","exterior"):
        item=next(r for r in result["terms"] if r["kind"]=="seat_v" and r["side"]==side)
        expected=seats[side+"_vertical_capacity_kip"][cfg["panel"]["seat_detail_"+side]][0]*old.KIP
        check("complete_pair_seat_capacity_once_"+side,close(item["cap_compression_N"],expected),expected)
    young,_=old.steel(20,transfer)
    area,_=old.opposed_angles(base["floor_bay"]["top_chord_angle_in"],1.09)
    chord=next(r for r in result["terms"] if r["kind"]=="top_chord")
    check("symmetric_pair_steel_EA_doubled",close(chord["k"]*chord["length_m"],2*young*area),chord["k"]*chord["length_m"])
    zero=evaluate(gravity_factor=0.)
    check("zero_load_temperature_anchor_zero_state",max(abs(zero["u"]))==0 and zero["strain_energy_J"]==0 and zero["max_DCR"]==0,zero["strain_energy_J"])
    totals=[]
    for p in (12,16,20):
        variant=new.build_panel(cfg,base,transfer,seats,{"panels":p})
        bonds=[r for r in variant["terms"] if r["kind"]=="bond"]
        totals.append([sum(r[key] for r in bonds) for key in ("equivalent_knuckles","k","cap_abs_N")])
        check(f"bond_half_end_tributary_P{p}",close(bonds[0]["equivalent_knuckles"]*2,bonds[1]["equivalent_knuckles"]) and close(bonds[-1]["k"],bonds[0]["k"]),[r["equivalent_knuckles"] for r in bonds[:2]])
    check("fixed_bond_density_32_equivalent_units_for_all_layouts",all(close(r[0],32) for r in totals),totals)
    check("integrated_bond_stiffness_and_capacity_layout_invariant",np.allclose(totals,np.array(totals[1])[None,:],rtol=1e-12),totals)
    soft=evaluate(kv_N_m=1e7)
    rigid=evaluate(kv_N_m=1e9)
    predicted_settlement_difference=expected_load/2*(1/1e7-1/1e9)
    check("vertical_support_compliance_adds_rigid_settlement",close(soft["max_down_m"]-rigid["max_down_m"],predicted_settlement_difference),{"difference_m":soft["max_down_m"]-rigid["max_down_m"],"expected_m":predicted_settlement_difference})
    check("roller_reactions_not_changed_by_equal_vertical_compliance",close(soft["vertical_pair_reaction_N"],rigid["vertical_pair_reaction_N"]),soft["vertical_pair_reaction_N"])
    stiffness_results=[evaluate(bond_k_N_m=k) for k in cfg["bond"]["stiffness_per_equivalent_knuckle_N_m"]]
    displacements=[r["max_down_m"] for r in stiffness_results]
    check("increasing_bond_stiffness_reduces_cold_deflection",all(a>b for a,b in zip(displacements,displacements[1:])),displacements)
    check("increasing_bond_stiffness_reduces_cold_slip",all(a["max_slip_m"]>b["max_slip_m"] for a,b in zip(stiffness_results,stiffness_results[1:])),[r["max_slip_m"] for r in stiffness_results])
    # Independent old solver: pair->one truss, ideal pin + roller, no support settlement.
    steel_terms=[r for r in model["terms"] if r["kind"] in ("top_chord","bottom_chord","web")]
    ea=[r["k"]*r["length_m"]/2 for r in steel_terms]
    force=model["force"][:model["steel_dofs"]]/2
    p=model["panels"]
    bare=old.truss_solve(model["nodes"],model["members"],ea,force,[0,1,2*p+1])
    concrete=base["floor_bay"]["concrete_hypotheses"]
    ecac=concrete["elastic_modulus_20c_ksi"]*old.KSI*40*4.35*old.IN**2
    ideal=old.truss_solve(model["nodes"],model["members"],[e+(ecac if m[2]=="top_chord" else 0) for e,m in zip(ea,model["members"])],force,[0,1,2*p+1])
    support_settlement=expected_load/(2*cfg["panel"]["vertical_support_stiffness_pair_N_m"])
    low=evaluate(bond_k_N_m=100.)
    high=evaluate(bond_k_N_m=1e12)
    dbare=max(-bare["displacement"][1::2])
    dideal=max(-ideal["displacement"][1::2])
    low_error=abs(low["max_down_m"]-support_settlement-dbare)/dbare
    high_error=abs(high["max_down_m"]-support_settlement-dideal)/dideal
    check("weak_bond_limit_matches_V11A_bare_displacement",low_error<1e-4,{"relative_error":low_error,"V11A_m":float(dbare)})
    check("stiff_bond_limit_matches_V11A_ideal_axial_slab_displacement",high_error<1e-4,{"relative_error":high_error,"V11A_m":float(dideal)})
    ideal_braced=evaluate(ideal_lateral_bracing=True)
    check("bracing_assumption_changes_screen_not_axial_stiffness",np.allclose(result["u"],ideal_braced["u"],rtol=1e-12,atol=1e-12),"No bond-derived bracing credit")
    diff=evaluate(gravity_factor=0.5,horizontal_mode="restrained",right_anchor_x_m=.006)
    slab=[r for r in diff["terms"] if r["kind"]=="slab"]
    check("opened_slab_segments_have_zero_tension_energy",any(r["state"]=="OPEN_ZERO_TENSION" for r in slab) and all(r["force_N"]<=0 and (r["state"]!="OPEN_ZERO_TENSION" or r["strain_energy_J"]==0) for r in slab),sum(r["state"]=="OPEN_ZERO_TENSION" for r in slab))
    # Building terms avoids accepting an over-limit hot panel as a valid path state.
    hotsteel=new.build_panel(cfg,base,transfer,seats,{"steel_c":600.,"slab_c":20.})
    hotconcrete=new.build_panel(cfg,base,transfer,seats,{"steel_c":20.,"slab_c":600.})
    cold_bond=next(r for r in model["terms"] if r["kind"]=="bond")
    hs_bond=next(r for r in hotsteel["terms"] if r["kind"]=="bond")
    hc_bond=next(r for r in hotconcrete["terms"] if r["kind"]=="bond")
    check("knuckle_capacity_not_indexed_on_steel_temperature",close(cold_bond["cap_abs_N"],hs_bond["cap_abs_N"]),hs_bond["cap_abs_N"])
    check("knuckle_capacity_600C_concrete_is_19_over_30_reference",close(hc_bond["cap_abs_N"]/cold_bond["cap_abs_N"],19/30),hc_bond["cap_abs_N"]/cold_bond["cap_abs_N"])
    for field in ("steel_c","slab_c","support_c"):
        rejected=False
        try: new.build_panel(cfg,base,transfer,seats,{field:601.})
        except ValueError: rejected=True
        check("reject_temperature_domain_"+field,rejected,601)
    compressed=evaluate(gravity_factor=0.,steel_c=100.,slab_c=100.,horizontal_mode="restrained")
    hterms=[r for r in compressed["terms"] if r["kind"]=="seat_h"]
    check("thermal_support_push_not_tested_as_tensile_failure",all(r["force_N"]*r["tension_sign"]<0 and r["DCR"]==0 for r in hterms) and compressed["support_compression_capacity_unchecked"],[(r["side"],r["force_N"],r["DCR"]) for r in hterms])
    tension_h=[r for r in diff["terms"] if r["kind"]=="seat_h"]
    check("support_pull_checks_signed_tension_limit",all(r["force_N"]*r["tension_sign"]>0 and r["DCR"]>0 for r in tension_h),[(r["side"],r["DCR"]) for r in tension_h])
    # Equal expansion coefficients are an analytic free-expansion sentinel, not the default concrete law.
    equal=copy.deepcopy(cfg)
    equal["panel"]["concrete_expansion_per_K"]=equal["panel"]["steel_expansion_per_K"]
    expansion=new.evaluate_panel(equal,base,transfer,seats,{"gravity_factor":0.,"steel_c":200.,"slab_c":200.})
    expected_extension=12e-6*180*model["span_m"]
    actual_extension=expansion["u"][2*p]-expansion["u"][0]
    check("whole_panel_equal_alpha_free_horizontal_expansion",close(actual_extension,expected_extension),{"actual_m":float(actual_extension),"expected_m":expected_extension})
    check("whole_panel_free_uniform_heat_has_negligible_forces",max(abs(t["force_N"]) for t in expansion["terms"])<1e-4,max(abs(t["force_N"]) for t in expansion["terms"]))
    check("whole_panel_free_heat_energy_identity",expansion["energy_identity_residual"]<1e-8,expansion["energy_identity_residual"])
    return tests
