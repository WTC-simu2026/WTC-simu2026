"""Reduced 1D motion bookkeeping, not a structural collapse solver.

Downward is positive. Constant resistance is a passive motion resistance:
at rest, its available capacity can prevent departure, not accelerate upward.
The integration and stationary-mass capture kernels are independent of tower ID.
"""
from __future__ import annotations

import math


def norm_residual(value: float, *terms: float) -> float:
    return abs(value) / max(1.0, sum(abs(t) for t in terms))


def advance_interval(mass: float, speed: float, distance: float, gravity: float,
                     resistance: float, capture_mass: float) -> dict:
    """Exact constant-acceleration segment followed by a stationary-mass capture.

    A zero-speed arrival at the exact endpoint is an arrest without capture.
    No continuation or temperature evolution is inferred after any arrest.
    """
    if not all(math.isfinite(x) for x in (mass, speed, distance, gravity, resistance, capture_mass)):
        raise ValueError("Non-finite interval input")
    if mass <= 0 or distance <= 0 or min(speed, gravity, resistance, capture_mass) < 0:
        raise ValueError("Invalid interval domain")
    force_net = mass*gravity-resistance
    acceleration = force_net/mass
    initial_ke = 0.5*mass*speed**2
    end_trial_ke = initial_ke+force_net*distance
    if speed == 0 and force_net <= 0:
        event, travel, duration, before_speed, captured = "NO_DOWNWARD_START", 0.0, 0.0, 0.0, 0.0
    elif end_trial_ke <= 0:
        if force_net >= 0:
            raise ArithmeticError("Arrest with nonnegative force and positive initial speed")
        travel = min(distance, max(0.0, -initial_ke/force_net))
        duration = -speed/acceleration
        before_speed, captured = 0.0, 0.0
        event = "ARREST_AT_INTERVAL_END" if math.isclose(travel, distance, rel_tol=1e-12, abs_tol=1e-12) else "ARREST_INSIDE_INTERVAL"
    else:
        travel = distance
        before_speed = math.sqrt(2*end_trial_ke/mass)
        duration = 2*distance/(speed+before_speed)
        captured = capture_mass
        event = "INTERVAL_COMPLETED_AND_CAPTURED" if captured else "INTERVAL_COMPLETED_WITHOUT_CAPTURE"
    gravity_work = mass*gravity*travel
    resistance_work = resistance*travel
    before_ke = 0.5*mass*before_speed**2
    new_mass = mass+captured
    after_speed = mass*before_speed/new_mass
    final_ke = 0.5*new_mass*after_speed**2
    # Independent closed-form inelastic loss, rather than a forced balancing term.
    capture_loss = 0.5*(mass*captured/new_mass)*before_speed**2
    energy_error = initial_ke+gravity_work-resistance_work-capture_loss-final_ke
    motion_momentum_error = mass*(before_speed-speed)-force_net*duration
    capture_momentum_error = mass*before_speed-new_mass*after_speed
    return {
        "event": event, "requested_distance_m": distance, "distance_m": travel,
        "duration_s": duration, "mass_before_kg": mass, "mass_captured_kg": captured,
        "mass_after_kg": new_mass, "speed_start_m_s": speed,
        "speed_before_capture_m_s": before_speed, "speed_after_m_s": after_speed,
        "resistance_capacity_N": resistance, "gravity_force_N": mass*gravity,
        "potential_acceleration_at_full_resistance_capacity_m_s2": acceleration,
        "realized_motion_acceleration_m_s2": 0.0 if event == "NO_DOWNWARD_START" else acceleration,
        "realized_resistance_force_N": mass*gravity if event == "NO_DOWNWARD_START" else resistance,
        "kinetic_start_J": initial_ke, "gravity_work_J": gravity_work,
        "resistance_work_J": resistance_work, "kinetic_before_capture_J": before_ke,
        "capture_loss_J": capture_loss, "kinetic_end_J": final_ke,
        "energy_error_J": energy_error,
        "normalized_energy_error": norm_residual(energy_error, initial_ke, gravity_work, resistance_work, capture_loss, final_ke),
        "motion_momentum_error_kg_m_s": motion_momentum_error,
        "normalized_motion_momentum_error": norm_residual(motion_momentum_error, mass*speed, mass*before_speed, mass*gravity*duration, resistance*duration),
        "capture_momentum_error_kg_m_s": capture_momentum_error,
        "normalized_capture_momentum_error": norm_residual(capture_momentum_error, mass*before_speed, new_mass*after_speed),
        "max_speed_m_s": max(speed, before_speed, after_speed),
        "reached_interval_end_with_positive_speed": event.startswith("INTERVAL_COMPLETED"),
    }


def story_resistance(floor: int, snapshot: dict, baseline: dict, scenario: dict) -> tuple[float, float]:
    gradient = float(baseline["exploratory_model"]["story_resistance_gradient_to_ground"])
    intact = float(scenario["intact_story_resistance_at_floor98_GJ"])*1e9*(1+gradient*max(0, 98-float(floor))/97)
    retention = float(snapshot[floor]["combined_capacity_retention"]) if floor in snapshot else 1.0
    return intact*retention, retention


def run_stack(scenario: dict, trigger: dict | None, snapshot: dict,
              baseline: dict, variant: dict, keep_rows: bool = False) -> tuple[dict, list, list]:
    tower, model = baseline["documented_inputs"]["tower"], baseline["exploratory_model"]
    count, height = int(tower["above_grade_floor_count"]), float(tower["upper_office_story_height_m"])
    gravity, unit_mass = float(model["gravity_m_s2"]), float(scenario["floor_mass_kg"])
    alpha = float(model["initial_upper_block_floor_equivalent_offset"])
    fraction = float(scenario["initial_drop_fraction_of_story"])
    if not 0 <= alpha <= 1 or not 0 < fraction <= 1 or count < 1 or unit_mass <= 0:
        raise ValueError("Invalid stack mass or gap convention")
    total = count*unit_mass
    summary = {
        "scenario_id": scenario["scenario_id"], "variant_id": variant["id"],
        "outcome": "NO_CAPACITY_TRIGGER_IN_WINDOW",
        "capacity_trigger_time_s": None if trigger is None else float(trigger["time_s"]),
        "capacity_trigger_floor": None if trigger is None else int(trigger["floor"]),
        "actual_motion_start_time_s": None, "motion_duration_s": None,
        "initial_cluster_mass_kg": None, "cluster_mass_kg": 0.0,
        "unaccreted_mass_kg": total, "diagnostic_omitted_mass_kg": 0.0,
        "total_tower_mass_kg": total, "total_captured_mass_kg": 0.0,
        "initial_velocity_m_s": 0.0, "final_velocity_m_s": 0.0, "maximum_velocity_m_s": 0.0,
        "displacement_m": 0.0, "first_interval_duration_s": None,
        "initial_resistance_capacity_N": None, "initial_weight_N": None,
        "initial_force_capacity_to_weight": None,
        "gravity_work_total_J": 0.0, "resistance_work_total_J": 0.0,
        "capture_loss_total_J": 0.0, "final_kinetic_energy_J": 0.0,
        "global_energy_error_J": 0.0, "normalized_global_energy_error": 0.0,
        "maximum_interval_energy_error": 0.0, "maximum_momentum_error": 0.0,
        "maximum_mass_inventory_error": 0.0, "completed_full_stories": 0,
        "completed_initial_interval": False, "arrest_story": None,
        "arrest_distance_within_interval_m": None, "terminal_event": "NO_CAPACITY_TRIGGER",
        "debris_settled_simulated": False, "restart_after_arrest_simulated": False,
    }
    ledger, timeline = [], []
    if trigger is None:
        return summary, ledger, timeline
    start_floor = int(trigger["floor"])
    if not 1 <= start_floor <= count:
        raise ValueError("Trigger floor outside model")
    cluster = (count-start_floor+alpha)*unit_mass
    if cluster <= 0:
        raise ValueError("Initial cluster must have positive mass")
    omitted = 0.0 if variant["complete_mass_inventory"] else (1-alpha)*unit_mass
    unaccreted = total-cluster-omitted
    summary.update(initial_cluster_mass_kg=cluster, cluster_mass_kg=cluster,
                   unaccreted_mass_kg=unaccreted, diagnostic_omitted_mass_kg=omitted,
                   motion_duration_s=0.0)
    time_now, drop, speed = 0.0, 0.0, 0.0
    gravity_terms, resistance_terms, loss_terms = [], [], []
    def state(event_index: int, floor: int, event: str):
        return {"scenario_id": scenario["scenario_id"], "variant_id": variant["id"],
                "event_index": event_index, "floor": floor, "event": event,
                "time_since_trigger_s": time_now, "time_after_impact_s": float(trigger["time_s"])+time_now,
                "downward_displacement_m": drop, "velocity_m_s": speed,
                "cluster_mass_kg": cluster, "unaccreted_mass_kg": unaccreted,
                "diagnostic_omitted_mass_kg": omitted, "total_mass_kg": total,
                "kinetic_energy_J": 0.5*cluster*speed**2}
    if keep_rows:
        timeline.append(state(0, start_floor, "CAPACITY_TRIGGER_AT_REST"))
    intervals = [(start_floor, fraction*height, (1-alpha)*unit_mass if variant["complete_mass_inventory"] else 0.0)]
    intervals += [(floor, height, unit_mass) for floor in range(start_floor-1, 0, -1)]
    for index, (floor, distance, capture) in enumerate(intervals, 1):
        resistance_energy, retention = story_resistance(floor, snapshot, baseline, scenario)
        force = resistance_energy/height
        if index == 1 and not variant["initial_resistance_active"]:
            force = 0.0
        if index == 1:
            summary.update(initial_resistance_capacity_N=force, initial_weight_N=cluster*gravity,
                           initial_force_capacity_to_weight=force/(cluster*gravity) if gravity else None)
        step = advance_interval(cluster, speed, distance, gravity, force, capture)
        time_start, drop_start = time_now, drop
        time_now += step["duration_s"]
        drop += step["distance_m"]
        cluster = step["mass_after_kg"]
        unaccreted -= step["mass_captured_kg"]
        speed = step["speed_after_m_s"]
        mass_error = cluster+unaccreted+omitted-total
        mass_norm = abs(mass_error)/total
        gravity_terms.append(step["gravity_work_J"])
        resistance_terms.append(step["resistance_work_J"])
        loss_terms.append(step["capture_loss_J"])
        summary["maximum_mass_inventory_error"] = max(summary["maximum_mass_inventory_error"], mass_norm)
        summary["maximum_interval_energy_error"] = max(summary["maximum_interval_energy_error"], step["normalized_energy_error"])
        summary["maximum_momentum_error"] = max(summary["maximum_momentum_error"], step["normalized_capture_momentum_error"], step["normalized_motion_momentum_error"])
        summary["maximum_velocity_m_s"] = max(summary["maximum_velocity_m_s"], step["max_speed_m_s"])
        if index == 1:
            summary["first_interval_duration_s"] = step["duration_s"]
        if step["distance_m"] > 0:
            summary["actual_motion_start_time_s"] = float(trigger["time_s"])
        if keep_rows:
            ledger.append({"scenario_id": scenario["scenario_id"], "variant_id": variant["id"],
                "event_index": index, "story": floor, "is_initial_interval": index == 1,
                "time_start_s": time_start, "time_end_s": time_now,
                "displacement_start_m": drop_start, "displacement_end_m": drop,
                "full_story_resistance_reference_J": resistance_energy,
                "frozen_capacity_retention": retention,
                "unaccreted_mass_after_kg": unaccreted, "diagnostic_omitted_mass_kg": omitted,
                "mass_inventory_error_kg": mass_error, "normalized_mass_inventory_error": mass_norm,
                **step})
            timeline.append(state(index, floor, step["event"]))
        if not step["reached_interval_end_with_positive_speed"]:
            summary["outcome"] = "CAPACITY_TRIGGER_NO_DOWNWARD_START_UNDER_CONSTANT_RESISTANCE" if step["event"] == "NO_DOWNWARD_START" else "DOWNWARD_MOTION_ARRESTED"
            summary.update(arrest_story=floor, arrest_distance_within_interval_m=step["distance_m"], terminal_event=step["event"])
            break
        if index == 1:
            summary["completed_initial_interval"] = True
        else:
            summary["completed_full_stories"] += 1
    else:
        summary.update(outcome="LOWER_MODEL_BOUNDARY_REACHED_WITH_RESIDUAL_MOTION", terminal_event="LOWER_MODEL_BOUNDARY_WITH_NONZERO_VELOCITY")
    wg, wr, loss = math.fsum(gravity_terms), math.fsum(resistance_terms), math.fsum(loss_terms)
    final_ke = 0.5*cluster*speed**2
    energy_error = wg-wr-loss-final_ke
    summary.update(motion_duration_s=time_now, cluster_mass_kg=cluster, unaccreted_mass_kg=unaccreted,
                   total_captured_mass_kg=cluster-summary["initial_cluster_mass_kg"], final_velocity_m_s=speed,
                   displacement_m=drop, gravity_work_total_J=wg, resistance_work_total_J=wr,
                   capture_loss_total_J=loss, final_kinetic_energy_J=final_ke,
                   global_energy_error_J=energy_error,
                   normalized_global_energy_error=norm_residual(energy_error, wg, wr, loss, final_ke))
    return summary, ledger, timeline


def analytical_tests() -> list:
    rows = []
    def check(name, actual, expected, tolerance=1e-12):
        ok = actual == expected if isinstance(expected, (str, bool)) else math.isclose(actual, expected, rel_tol=tolerance, abs_tol=tolerance)
        rows.append({"name": name, "pass": ok, "actual": actual, "expected": expected})
    a = advance_interval(2, 0, 3, 10, 4, 1)
    for key, expected in [("duration_s", math.sqrt(.75)), ("speed_before_capture_m_s", math.sqrt(48)),
                          ("gravity_work_J", 60), ("resistance_work_J", 12),
                          ("kinetic_before_capture_J", 48), ("kinetic_end_J", 32), ("capture_loss_J", 16)]:
        check("accelerating_capture_"+key, a[key], expected)
    for distance, event in [(5, "ARREST_INSIDE_INTERVAL"), (3, "ARREST_AT_INTERVAL_END")]:
        a = advance_interval(2, 6, distance, 10, 32, 1)
        for key, expected in [("event", event), ("distance_m", 3), ("duration_s", 1), ("mass_captured_kg", 0), ("capture_loss_J", 0), ("kinetic_end_J", 0)]:
            check(f"arrest_requested_{distance}_"+key, a[key], expected)
    for force in (20, 24):
        a = advance_interval(2, 0, 3, 10, force, 1)
        for key, expected in [("event", "NO_DOWNWARD_START"), ("distance_m", 0), ("duration_s", 0), ("gravity_work_J", 0), ("resistance_work_J", 0), ("mass_captured_kg", 0)]:
            check(f"no_start_force_{force}_"+key, a[key], expected)
    a = advance_interval(2, 3, 9, 10, 20, 0)
    check("constant_speed_duration", a["duration_s"], 3)
    check("constant_speed_speed", a["speed_after_m_s"], 3)
    a = advance_interval(2, 0, 1.8288, 9.80665, 0, 0)
    check("freefall_duration", a["duration_s"], math.sqrt(2*1.8288/9.80665))
    check("freefall_speed", a["speed_after_m_s"], math.sqrt(2*9.80665*1.8288))
    a = advance_interval(2, 3, 9, 0, 0, 1)
    check("zero_gravity_coast_time", a["duration_s"], 3)
    check("zero_gravity_capture_speed", a["speed_after_m_s"], 2)
    check("zero_gravity_capture_momentum", 2*3, a["mass_after_kg"]*a["speed_after_m_s"])
    rejected = 0
    for args in [(0,0,1,10,0,0), (1,-1,1,10,0,0), (1,0,0,10,0,0), (1,0,1,10,-1,0), (1,0,1,10,0,-1)]:
        try:
            advance_interval(*args)
        except ValueError:
            rejected += 1
    check("invalid_physical_domains_rejected", rejected, 5)
    a = advance_interval(2, 0, 3, 10, 24, 1)
    check("passive_resistance_no_upward_acceleration_at_rest", a["realized_motion_acceleration_m_s2"], 0)
    check("passive_resistance_at_rest_equals_weight", a["realized_resistance_force_N"], 20)
    baseline = {"documented_inputs": {"tower": {"above_grade_floor_count": 2, "upper_office_story_height_m": 1}},
                "exploratory_model": {"gravity_m_s2": 10, "initial_upper_block_floor_equivalent_offset": .5,
                                       "story_resistance_gradient_to_ground": 0}}
    scenario = {"scenario_id": "TWO_STORY_ANALYTICAL", "floor_mass_kg": 1,
                "initial_drop_fraction_of_story": .5, "intact_story_resistance_at_floor98_GJ": 0}
    variant = {"id": "TEST", "complete_mass_inventory": True, "initial_resistance_active": True}
    a, _, _ = run_stack(scenario, {"floor": 2, "time_s": 0}, {}, baseline, variant)
    for key, expected in [("cluster_mass_kg", 2), ("gravity_work_total_J", 12.5),
                          ("capture_loss_total_J", 6.875), ("final_kinetic_energy_J", 5.625),
                          ("motion_duration_s", 2/math.sqrt(10)), ("unaccreted_mass_kg", 0)]:
        check("two_story_independent_"+key, a[key], expected)
    for fraction in (.25, .75):
        b, _, _ = run_stack({**scenario, "initial_drop_fraction_of_story": fraction}, {"floor": 2, "time_s": 0}, {}, baseline, variant)
        check(f"gap_{fraction}_does_not_change_initial_mass", b["initial_cluster_mass_kg"], .5)
        check(f"gap_{fraction}_closes_total_mass", b["cluster_mass_kg"], 2)
    b, _, _ = run_stack(scenario, {"floor": 2, "time_s": 0}, {}, baseline, {**variant, "complete_mass_inventory": False})
    check("diagnostic_omitted_half_mass_explicit", b["diagnostic_omitted_mass_kg"], .5)
    check("diagnostic_mass_accounts_close", b["cluster_mass_kg"]+b["unaccreted_mass_kg"]+b["diagnostic_omitted_mass_kg"], 2)
    for count, floor in ((110, 1), (110, 110)):
        baseline["documented_inputs"]["tower"]["above_grade_floor_count"] = count
        b, _, _ = run_stack(scenario, {"floor": floor, "time_s": 0}, {}, baseline, variant)
        check(f"floor_boundary_{floor}_mass_closure", b["cluster_mass_kg"], 110)
    b, _, _ = run_stack(scenario, None, {}, baseline, variant)
    check("no_trigger_all_mass_stays_unaccreted", b["unaccreted_mass_kg"], 110)
    check("no_trigger_outcome", b["outcome"], "NO_CAPACITY_TRIGGER_IN_WINDOW")
    return rows
