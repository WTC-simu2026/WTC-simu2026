"""Bounded constant-property thermoelastic slab coupled to one V11F panel.

The slab temperature field is prescribed.  Truss members and connections stay
cold.  The model is reversible and stops at a DCR guard before any cracking,
yielding, component limit or material degradation.  Energies are panel J.
"""
from __future__ import annotations

import math
import numpy as np

import v11f_panel_model as cold
import v11h_thermomechanical_model as thermo


class Unresolved(RuntimeError):
    pass


class ThermoElasticPanel:
    def __init__(self, cfg, cold_cfg, thermo_cfg, section_cfg, inputs, thermal_case, subdivisions=None):
        self.cfg = cfg
        self.cold_cfg = cold_cfg
        self.thermal_case = dict(thermal_case)
        case = {
            "id": cfg["panel_case"]["id"],
            "kind": "gravity",
            "rho_total": cfg["panel_case"]["rho_total"],
            "layout": cfg["panel_case"]["layout"],
        }
        sub = cfg["discretization"]["reference_subdivisions_per_steel_panel"] if subdivisions is None else subdivisions
        base = cold.Panel(cold_cfg, inputs, case, sub)
        section_case = {
            "id": thermal_case["id"],
            "rho_total": case["rho_total"],
            "layout": case["layout"],
            "mode": "FREE",
            "delta_t_bottom_c": thermal_case["delta_t_bottom_c"],
            "delta_t_top_c": thermal_case["delta_t_top_c"],
            "scale_vertices": [0.0, thermal_case["target_scale"]],
            "alpha_mode": "differential",
        }
        self.section = thermo.ElasticThermoSection(
            section_cfg, thermo_cfg, section_case, cfg["discretization"]["concrete_depth_fibers"]
        )
        if abs(self.section.width - base.section.width) > 1e-14 or abs(self.section.h - base.section.h) > 1e-14:
            raise ValueError("V11H and V11F section geometries differ")
        if cfg["discretization"]["longitudinal_gauss_points_per_element"] != 2:
            raise ValueError("Only the inherited two-point longitudinal rule is declared")

        self.model = base.model
        self.size = base.size
        self.force_unit = base.force_unit.copy()
        self.terms = base.terms
        self.term_B = base.term_B
        self.term_k = base.term_k
        self.compression = base.compression
        self.tension = base.tension
        self.dx = base.dx
        self.dofs = base.dofs
        self.B = base.B
        self.x = base.x
        self.element = base.element
        self.Bends = base.Bends
        self.weights = base.weights
        self.assembly_i = base.assembly_i
        self.assembly_j = base.assembly_j
        self.scale = base.scale
        self.cold_zero_stiffness = base.evaluate(base.zero(), np.zeros(base.size), 0.0, {})["K"]
        self.concrete_mask = self.section.kind == "concrete"
        self.steel_mask = ~self.concrete_mask

    def delta_temperature(self, thermal_scale):
        return self.section.delta_temperature(float(thermal_scale))

    def section_batch(self, u, thermal_scale):
        q = np.einsum("pai,pi->pa", self.B, u[self.dofs])
        dtemp = self.delta_temperature(thermal_scale)
        eps_th_one = self.section.alpha * dtemp
        eps_th = np.broadcast_to(eps_th_one, (len(q), len(eps_th_one)))
        eps_total = q[:, 0, None] - q[:, 1, None] * self.section.y
        eps_mechanical = eps_total - eps_th
        stress = self.section.E * eps_mechanical
        n_force = stress @ self.section.area
        moment = -(stress * self.section.y) @ self.section.area
        stored = 0.5 * (stress * eps_mechanical) @ self.section.area
        sensible = np.broadcast_to(
            np.sum(self.section.density * self.section.cp * self.section.area * dtemp), len(q)
        ).copy()
        ksec = np.broadcast_to(self.section.K, (len(q), 2, 2)).copy()
        thermal_resultant = self.section.B.T @ (self.section.EA * eps_th_one)
        return {
            "q": q,
            "delta_temperature_c": dtemp,
            "thermal_strain": eps_th,
            "total_strain": eps_total,
            "mechanical_strain": eps_mechanical,
            "stress_pa": stress,
            "Q": np.column_stack((n_force, moment)),
            "Ksec": ksec,
            "stored_J_per_m": stored,
            "sensible_J_per_m": sensible,
            "thermal_resultant": thermal_resultant,
        }

    def _section_screens(self, batch, u, thermal_scale):
        limits = []
        concrete = batch["stress_pa"][:, self.concrete_mask]
        if concrete.size:
            tension = np.maximum(concrete, 0.0) / self.section.ft
            compression = np.maximum(-concrete, 0.0) / self.section.fc
            it = np.unravel_index(int(np.argmax(tension)), tension.shape)
            ic = np.unravel_index(int(np.argmax(compression)), compression.shape)
            limits.extend([
                {"id": f"SLAB-GAUSS-{it[0]:03d}", "kind": "slab_concrete_tension_elastic_guard", "DCR": float(tension[it])},
                {"id": f"SLAB-GAUSS-{ic[0]:03d}", "kind": "slab_concrete_compression_elastic_guard", "DCR": float(compression[ic])},
            ])
        steel = batch["stress_pa"][:, self.steel_mask]
        if steel.size:
            ratio = np.abs(steel) / self.section.fy
            index = np.unravel_index(int(np.argmax(ratio)), ratio.shape)
            limits.append({
                "id": f"SLAB-GAUSS-{index[0]:03d}",
                "kind": "slab_reinforcement_yield_elastic_guard",
                "DCR": float(ratio[index]),
            })

        qend = np.einsum("ejai,ei->eja", self.Bends, u[self.dofs[::2]])
        alpha_c = float(self.section.alpha[self.concrete_mask][0])
        face_rows = []
        for element in range(len(qend)):
            for endpoint in range(2):
                for face, y, dtemp in (
                    ("BOTTOM", -self.section.h / 2, thermal_scale * float(self.thermal_case["delta_t_bottom_c"])),
                    ("TOP", self.section.h / 2, thermal_scale * float(self.thermal_case["delta_t_top_c"])),
                ):
                    eps_m = qend[element, endpoint, 0] - qend[element, endpoint, 1] * y - alpha_c * dtemp
                    stress = float(self.section.E[self.concrete_mask][0] * eps_m)
                    face_rows.append((element, endpoint, face, stress))
        tensile = max(face_rows, key=lambda row: row[3])
        compressive = min(face_rows, key=lambda row: row[3])
        limits.extend([
            {
                "id": f"SLAB-{tensile[0]:03d}-END-{tensile[1]}-{tensile[2]}",
                "kind": "slab_concrete_tension_elastic_guard",
                "DCR": max(0.0, tensile[3]) / self.section.ft,
            },
            {
                "id": f"SLAB-{compressive[0]:03d}-END-{compressive[1]}-{compressive[2]}",
                "kind": "slab_concrete_compression_elastic_guard",
                "DCR": max(0.0, -compressive[3]) / self.section.fc,
            },
        ])
        if np.any(self.steel_mask):
            endpoint_ratios = []
            ys = self.section.y[self.steel_mask]
            alphas = self.section.alpha[self.steel_mask]
            moduli = self.section.E[self.steel_mask]
            for element in range(len(qend)):
                for endpoint in range(2):
                    bottom = thermal_scale * float(self.thermal_case["delta_t_bottom_c"])
                    top = thermal_scale * float(self.thermal_case["delta_t_top_c"])
                    dtemp = bottom + (top - bottom) * (ys / self.section.h + 0.5)
                    stress = moduli * (qend[element, endpoint, 0] - qend[element, endpoint, 1] * ys - alphas * dtemp)
                    for layer, value in enumerate(stress):
                        endpoint_ratios.append((abs(float(value)) / self.section.fy, element, endpoint, layer))
            ratio, element, endpoint, layer = max(endpoint_ratios)
            limits.append({
                "id": f"SLAB-{element:03d}-END-{endpoint}-REBAR-{layer}",
                "kind": "slab_reinforcement_yield_elastic_guard",
                "DCR": ratio,
            })
        return limits

    def evaluate(self, u, gravity, thermal_scale):
        u = np.asarray(u, dtype=float)
        if u.shape != (self.size,) or not np.isfinite(u).all():
            raise ValueError("Invalid panel displacement vector")
        batch = self.section_batch(u, thermal_scale)
        internal = np.zeros(self.size)
        absolute = np.zeros(self.size)
        stiffness = np.zeros((self.size, self.size))
        local = np.einsum("pai,pa,p->pi", self.B, batch["Q"], self.weights)
        np.add.at(internal, self.dofs.ravel(), local.ravel())
        local_absolute = np.einsum("pai,pa,p->pi", abs(self.B), abs(batch["Q"]), self.weights)
        np.add.at(absolute, self.dofs.ravel(), local_absolute.ravel())
        local_k = np.einsum("pai,pab,pbj,p->pij", self.B, batch["Ksec"], self.B, self.weights)
        np.add.at(stiffness, (self.assembly_i, self.assembly_j), local_k.ravel())

        gap = self.term_B @ u
        strain = np.where(self.compression, np.minimum(gap, 0.0), np.where(self.tension, np.maximum(gap, 0.0), gap))
        force = self.term_k * strain
        active = np.where(self.compression, gap <= 0.0, np.where(self.tension, gap > 0.0, True))
        internal += self.term_B.T @ force
        absolute += abs(self.term_B).T @ abs(force)
        stiffness += self.term_B.T @ ((self.term_k * active)[:, None] * self.term_B)

        spring_stored = float(0.5 * np.dot(self.term_k, strain**2))
        slab_stored = float(self.weights @ batch["stored_J_per_m"])
        stored = spring_stored + slab_stored
        sensible = float(self.weights @ batch["sensible_J_per_m"])
        external_force = float(gravity) * self.force_unit
        reaction = internal - external_force
        free = np.arange(self.size, dtype=int)
        eq_scale = np.maximum(1.0, np.maximum(abs(external_force), absolute))
        equilibrium = float(max(abs(reaction[free]) / eq_scale[free], default=0.0))

        limits = []
        component_dcr = []
        for term, value in zip(self.terms, force, strict=True):
            kind = term["kind"]
            dcr = 0.0
            if kind == "horizontal_tie":
                dcr = abs(value) / term["cap_abs_N"]
            elif kind == "vertical_tie":
                dcr = max(value, 0.0) / term["cap_tension_N"]
            elif kind == "seat_v":
                dcr = max(-value, 0.0) / term["cap_compression_N"]
            elif kind == "seat_h":
                dcr = max(value * term["tension_sign"], 0.0) / term["cap_signed_tension_N"]
            elif kind in ("top_chord", "bottom_chord", "web"):
                dcr = abs(value) / (term["cap_compression_N"] if value < 0 else term["cap_tension_N"])
            component_dcr.append(float(dcr))
            limits.append({"id": term["id"], "kind": kind, "DCR": float(dcr)})
        limits.extend(self._section_screens(batch, u, float(thermal_scale)))
        limits.sort(key=lambda row: (-row["DCR"], row["id"], row["kind"]))

        contact = np.array([term["kind"] == "contact" for term in self.terms])
        vertical_tie = np.array([term["kind"] == "vertical_tie" for term in self.terms])
        seat_vertical = -sum(value for term, value in zip(self.terms, force, strict=True) if term["kind"] == "seat_v")
        seat_horizontal = -sum(value for term, value in zip(self.terms, force, strict=True) if term["kind"] == "seat_h")
        gravity_load = float(-sum(external_force[self.model["w"]]))
        return {
            "u": u.copy(), "batch": batch, "K": stiffness, "force": external_force,
            "reaction": reaction, "free": free, "eq_scale": eq_scale,
            "equilibrium_residual": equilibrium, "term_force": force, "term_gap": gap,
            "term_active": active, "term_DCR": np.asarray(component_dcr),
            "stored_J": stored, "spring_stored_J": spring_stored, "slab_stored_J": slab_stored,
            "sensible_enthalpy_J": sensible, "limits": limits, "max_DCR": limits[0]["DCR"],
            "governing": limits[0], "component_max_DCR": max(component_dcr, default=0.0),
            "concrete_tension_ratio": max(row["DCR"] for row in limits if row["kind"] == "slab_concrete_tension_elastic_guard"),
            "concrete_compression_ratio": max(row["DCR"] for row in limits if row["kind"] == "slab_concrete_compression_elastic_guard"),
            "reinforcement_yield_ratio": max((row["DCR"] for row in limits if row["kind"] == "slab_reinforcement_yield_elastic_guard"), default=0.0),
            "max_slab_down_m": float(max(-u[self.model["w"]])),
            "max_slab_up_m": float(max(u[self.model["w"]])),
            "max_truss_down_m": float(max(-u[1:self.model["steel_dofs"]:2])),
            "max_opening_m": float(max(0.0, max(gap[contact]))),
            "max_overlap_m": float(max(0.0, max(-gap[contact]))),
            "contact_count": int(sum(force[contact] < -1e-5)),
            "vertical_tension_count": int(sum(force[vertical_tie] > 1e-5)),
            "seat_vertical_reaction_N": float(seat_vertical),
            "seat_horizontal_reaction_N": float(seat_horizontal),
            "gravity_load_N": gravity_load,
            "vertical_balance_relative": abs(float(seat_vertical) - gravity_load) / max(1.0, gravity_load),
            "horizontal_balance_absolute_N": abs(float(seat_horizontal)),
            "support_work_J": 0.0,
            "support_uplift_unchecked": any(value > 1e-5 for term, value in zip(self.terms, force, strict=True) if term["kind"] == "seat_v"),
            "support_horizontal_compression_unchecked": any(value * term["tension_sign"] < -1e-5 for term, value in zip(self.terms, force, strict=True) if term["kind"] == "seat_h"),
            "active_signature": tuple(bool(value) for value in active),
        }

    def solve(self, gravity, thermal_scale, initial=None):
        gravity = float(gravity)
        thermal_scale = float(thermal_scale)
        if not math.isfinite(gravity) or not math.isfinite(thermal_scale):
            raise ValueError("Finite load parameters required")
        u = np.zeros(self.size) if initial is None else np.array(initial, dtype=float, copy=True)
        options = self.cold_cfg["solver"]
        scaling = self.scale
        for iteration in range(options["maximum_newton_iterations"]):
            result = self.evaluate(u, gravity, thermal_scale)
            scaled = scaling[:, None] * result["K"] * scaling[None, :]
            eigenvalue = float(np.linalg.eigvalsh(0.5 * (scaled + scaled.T))[0])
            if result["equilibrium_residual"] <= self.cfg["acceptance"]["relative_equilibrium"]:
                result["minimum_scaled_tangent_eigenvalue"] = eigenvalue
                result["newton_iterations"] = iteration + 1
                return result
            if eigenvalue <= options["scaled_tangent_minimum"]:
                raise Unresolved("NONPOSITIVE_TANGENT_DIAGNOSTIC_NOT_COLLAPSE")
            try:
                delta = scaling * np.linalg.solve(scaled, -scaling * result["reaction"])
            except np.linalg.LinAlgError as error:
                raise Unresolved("SINGULAR_NEWTON_NOT_COLLAPSE") from error
            merit = float(np.linalg.norm(scaling * result["reaction"]))
            accepted = False
            for halvings in range(options["maximum_line_search_halvings"] + 1):
                candidate = u + delta * 2.0**(-halvings)
                trial = self.evaluate(candidate, gravity, thermal_scale)
                trial_merit = float(np.linalg.norm(scaling * trial["reaction"]))
                if trial_merit < merit * (1 - 1e-4 * 2.0**(-halvings)) or trial["equilibrium_residual"] <= self.cfg["acceptance"]["relative_equilibrium"]:
                    u = candidate
                    accepted = True
                    break
            if not accepted:
                raise Unresolved("NEWTON_LINE_SEARCH_EXHAUSTED_NOT_COLLAPSE")
        raise Unresolved("NEWTON_ITERATION_LIMIT_NOT_COLLAPSE")

    def thermal_work_increment(self, old, new):
        delta_eps_th = new["batch"]["thermal_strain"] - old["batch"]["thermal_strain"]
        average_stress = 0.5 * (old["batch"]["stress_pa"] + new["batch"]["stress_pa"])
        return -float(np.sum(self.weights[:, None] * self.section.area[None, :] * average_stress * delta_eps_th))

    def inventory(self):
        zero = self.evaluate(np.zeros(self.size), 0.0, 0.0)
        stiffness_difference = float(np.max(abs(zero["K"] - self.cold_zero_stiffness)) / max(1.0, np.max(abs(self.cold_zero_stiffness))))
        return {
            "case_id": self.thermal_case["id"],
            "panel_case": self.cfg["panel_case"],
            "subdivisions": self.model["subdivisions"],
            "degrees_of_freedom": self.size,
            "steel_nodes": len(self.model["nodes"]),
            "steel_members": len(self.model["steel_members"]),
            "slab_nodes": len(self.model["w"]),
            "slab_elements": len(self.model["elements"]),
            "gauss_sections": len(self.x),
            "contact_stations": sum(term["kind"] == "contact" for term in self.terms),
            "span_m": self.model["span_m"],
            "quadrature_weight_sum_m": float(sum(self.weights)),
            "section": self.section.inventory(),
            "cold_zero_tangent_relative_difference": stiffness_difference,
            "global_energy_credit_J": 0.0,
        }


def _increment(model, old, new):
    du = new["u"] - old["u"]
    mechanical = float(0.5 * (old["force"] + new["force"]) @ du)
    thermal = model.thermal_work_increment(old, new)
    delta_u = new["stored_J"] - old["stored_J"]
    scale = max(1.0, abs(delta_u), abs(mechanical), abs(thermal))
    residual = abs(delta_u - mechanical - thermal) / scale
    return mechanical, thermal, residual


def _refined_advance(model, old, g0, t0, new, g1, t1, tolerance, depth=0):
    mechanical, thermal, residual = _increment(model, old, new)
    if residual <= tolerance:
        return [(new, g1, t1, mechanical, thermal, residual)]
    if depth >= 40 or max(abs(g1 - g0), abs(t1 - t0)) < 1e-11:
        raise Unresolved("INCREMENTAL_ENERGY_REFINEMENT_EXHAUSTED_NOT_COLLAPSE")
    gm = 0.5 * (g0 + g1)
    tm = 0.5 * (t0 + t1)
    middle = model.solve(gm, tm, 0.5 * (old["u"] + new["u"]))
    return (
        _refined_advance(model, old, g0, t0, middle, gm, tm, tolerance, depth + 1)
        + _refined_advance(model, middle, gm, tm, new, g1, t1, tolerance, depth + 1)
    )


def snapshot(model, result, phase, gravity, thermal_scale, mechanical_work, thermal_work, max_increment_residual):
    total_residual = abs(
        result["stored_J"] - mechanical_work - thermal_work
    ) / max(1.0, abs(result["stored_J"]), abs(mechanical_work), abs(thermal_work))
    bottom = model.section.reference_temperature_c + thermal_scale * float(model.thermal_case["delta_t_bottom_c"])
    top = model.section.reference_temperature_c + thermal_scale * float(model.thermal_case["delta_t_top_c"])
    fields = (
        "equilibrium_residual", "stored_J", "spring_stored_J", "slab_stored_J", "sensible_enthalpy_J",
        "max_DCR", "component_max_DCR", "concrete_tension_ratio", "concrete_compression_ratio",
        "reinforcement_yield_ratio", "max_slab_down_m", "max_slab_up_m", "max_truss_down_m",
        "max_opening_m", "max_overlap_m", "contact_count", "vertical_tension_count",
        "seat_vertical_reaction_N", "seat_horizontal_reaction_N", "gravity_load_N",
        "vertical_balance_relative", "horizontal_balance_absolute_N", "support_work_J",
        "minimum_scaled_tangent_eigenvalue", "newton_iterations", "support_uplift_unchecked",
        "support_horizontal_compression_unchecked",
    )
    row = {
        "case_id": model.thermal_case["id"], "phase": phase,
        "gravity_factor": float(gravity), "thermal_scale": float(thermal_scale),
        "slab_bottom_temperature_c": float(bottom), "slab_top_temperature_c": float(top),
        "mechanical_external_work_J": float(mechanical_work),
        "thermoelastic_work_J": float(thermal_work),
        "total_mechanical_energy_residual_relative": float(total_residual),
        "maximum_increment_energy_residual_relative": float(max_increment_residual),
        "dissipated_J": 0.0, "global_energy_credit_J": 0.0,
        "governing_id": result["governing"]["id"], "governing_kind": result["governing"]["kind"],
    }
    row.update({key: result[key] for key in fields})
    return row


def trace_case(cfg, cold_cfg, thermo_cfg, section_cfg, inputs, thermal_case, subdivisions=None, thermal_steps=None):
    model = ThermoElasticPanel(cfg, cold_cfg, thermo_cfg, section_cfg, inputs, thermal_case, subdivisions)
    tolerance = cfg["acceptance"]["relative_incremental_energy"]
    guard = cfg["loading"]["accepted_DCR_guard"]
    state = model.solve(0.0, 0.0)
    mechanical_work = 0.0
    thermal_work = 0.0
    max_increment_residual = 0.0
    history = [snapshot(model, state, "ZERO", 0.0, 0.0, 0.0, 0.0, 0.0)]

    gravity_target = cfg["loading"]["gravity_preload_factor"]
    g0 = 0.0
    for raw in np.linspace(0.0, gravity_target, cfg["loading"]["gravity_steps"] + 1)[1:]:
        g1 = float(raw)
        trial = model.solve(g1, 0.0, state["u"])
        pieces = _refined_advance(model, state, g0, 0.0, trial, g1, 0.0, tolerance)
        for next_state, next_g, next_t, dw, dth, residual in pieces:
            mechanical_work += dw
            thermal_work += dth
            max_increment_residual = max(max_increment_residual, residual)
            state = next_state
            g0 = next_g
            history.append(snapshot(model, state, "GRAVITY_PRELOAD", g0, next_t, mechanical_work, thermal_work, max_increment_residual))
    preload_state = state
    preload_snapshot = history[-1]

    steps = cfg["loading"]["thermal_steps"] if thermal_steps is None else int(thermal_steps)
    target = float(thermal_case["target_scale"])
    t0 = 0.0
    guard_bracket = None
    terminal = "TARGET_REACHED_WITHIN_ELASTIC_GUARD_NOT_SAFETY_PROOF"
    if float(thermal_case["delta_t_bottom_c"]) == 0.0 and float(thermal_case["delta_t_top_c"]) == 0.0:
        history.append(snapshot(model, state, "THERMAL", gravity_target, target, mechanical_work, thermal_work, max_increment_residual))
        t0 = target
    else:
        for raw in np.linspace(0.0, target, steps + 1)[1:]:
            t1 = float(raw)
            trial = model.solve(gravity_target, t1, state["u"])
            if trial["max_DCR"] >= guard:
                lo, hi = t0, t1
                lo_state, hi_state = state, trial
                while hi - lo > cfg["loading"]["guard_bisection_tolerance_scale"]:
                    mid = 0.5 * (lo + hi)
                    middle = model.solve(gravity_target, mid, 0.5 * (lo_state["u"] + hi_state["u"]))
                    if middle["max_DCR"] >= guard:
                        hi, hi_state = mid, middle
                    else:
                        lo, lo_state = mid, middle
                if lo > t0 + 1e-14:
                    pieces = _refined_advance(model, state, gravity_target, t0, lo_state, gravity_target, lo, tolerance)
                    for next_state, next_g, next_t, dw, dth, residual in pieces:
                        mechanical_work += dw
                        thermal_work += dth
                        max_increment_residual = max(max_increment_residual, residual)
                        state = next_state
                        t0 = next_t
                        history.append(snapshot(model, state, "THERMAL", next_g, t0, mechanical_work, thermal_work, max_increment_residual))
                guard_bracket = {
                    "accepted_scale": float(lo), "accepted_DCR": float(lo_state["max_DCR"]),
                    "rejected_scale": float(hi), "rejected_DCR": float(hi_state["max_DCR"]),
                    "rejected_state_committed": False,
                    "accepted_governing_id": lo_state["governing"]["id"],
                    "accepted_governing_kind": lo_state["governing"]["kind"],
                }
                terminal = "SAFE_DCR_GUARD_REACHED_BEFORE_NOMINAL_LIMIT"
                break
            pieces = _refined_advance(model, state, gravity_target, t0, trial, gravity_target, t1, tolerance)
            for next_state, next_g, next_t, dw, dth, residual in pieces:
                mechanical_work += dw
                thermal_work += dth
                max_increment_residual = max(max_increment_residual, residual)
                state = next_state
                t0 = next_t
                history.append(snapshot(model, state, "THERMAL", next_g, t0, mechanical_work, thermal_work, max_increment_residual))

    history[-1]["state"] = terminal
    for row in history[:-1]:
        row["state"] = "WITHIN_ELASTIC_GUARD"
    summary = {
        **thermal_case,
        "terminal": terminal,
        "history_point_count": len(history),
        "guard_bracket": guard_bracket,
        "preload": preload_snapshot,
        "final": history[-1],
        "maximum_equilibrium_residual": max(row["equilibrium_residual"] for row in history),
        "maximum_increment_energy_residual_relative": max(row["maximum_increment_energy_residual_relative"] for row in history),
        "maximum_total_energy_residual_relative": max(row["total_mechanical_energy_residual_relative"] for row in history),
        "maximum_DCR_accepted": max(row["max_DCR"] for row in history),
        "dissipated_J": 0.0,
        "global_energy_credit_J": 0.0,
    }
    batch = state["batch"]
    section_rows = []
    for point in range(len(model.x)):
        concrete_stress = batch["stress_pa"][point, model.concrete_mask]
        steel_stress = batch["stress_pa"][point, model.steel_mask]
        section_rows.append({
            "case_id": thermal_case["id"], "point": point, "element": int(model.element[point]),
            "x_m": float(model.x[point]), "weight_m": float(model.weights[point]),
            "eps0": float(batch["q"][point, 0]), "kappa_per_m": float(batch["q"][point, 1]),
            "N_N": float(batch["Q"][point, 0]), "M_Nm": float(batch["Q"][point, 1]),
            "thermal_resultant_N": float(batch["thermal_resultant"][0]),
            "thermal_resultant_Nm": float(batch["thermal_resultant"][1]),
            "stored_J_per_m": float(batch["stored_J_per_m"][point]),
            "sensible_enthalpy_J_per_m": float(batch["sensible_J_per_m"][point]),
            "minimum_concrete_stress_Pa": float(np.min(concrete_stress)),
            "maximum_concrete_stress_Pa": float(np.max(concrete_stress)),
            "minimum_reinforcement_stress_Pa": float(np.min(steel_stress)) if steel_stress.size else None,
            "maximum_reinforcement_stress_Pa": float(np.max(steel_stress)) if steel_stress.size else None,
        })
    critical_point = max(
        range(len(model.x)),
        key=lambda point: float(np.max(abs(batch["stress_pa"][point]) / np.where(model.concrete_mask, model.section.ft, model.section.fy))),
    )
    critical_fibers = []
    for fiber in range(len(model.section.y)):
        critical_fibers.append({
            "case_id": thermal_case["id"], "point": int(critical_point),
            "x_m": float(model.x[critical_point]), "fiber": fiber,
            "kind": str(model.section.kind[fiber]), "y_m": float(model.section.y[fiber]),
            "area_m2": float(model.section.area[fiber]), "E_Pa": float(model.section.E[fiber]),
            "alpha_per_K": float(model.section.alpha[fiber]),
            "delta_temperature_C": float(batch["delta_temperature_c"][fiber]),
            "thermal_strain": float(batch["thermal_strain"][critical_point, fiber]),
            "total_strain": float(batch["total_strain"][critical_point, fiber]),
            "mechanical_strain": float(batch["mechanical_strain"][critical_point, fiber]),
            "stress_Pa": float(batch["stress_pa"][critical_point, fiber]),
        })
    term_rows = [
        {
            "case_id": thermal_case["id"], "id": term["id"], "kind": term["kind"],
            "force_N": float(state["term_force"][index]), "extension_or_gap_m": float(state["term_gap"][index]),
            "DCR": float(state["term_DCR"][index]), "active": bool(state["term_active"][index]),
            "station": term.get("station"),
        }
        for index, term in enumerate(model.terms)
    ]
    node_rows = [
        {
            "case_id": thermal_case["id"], "node": node, "x_m": float(x),
            "axial_m": float(state["u"][model.model["ux"][node]]),
            "vertical_m": float(state["u"][model.model["w"][node]]),
            "rotation_rad": float(state["u"][model.model["theta"][node]]),
        }
        for node, x in enumerate(model.model["slab_x_m"])
    ]
    data = {
        "summary": summary, "history": history, "sections": section_rows,
        "critical_fibers": critical_fibers, "terms": term_rows, "slab_nodes": node_rows,
        "inventory": model.inventory(),
    }
    return data, model, state
