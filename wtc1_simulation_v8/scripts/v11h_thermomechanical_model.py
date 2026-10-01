"""V11H bounded linear thermoelastic references, SI units.

Temperature is prescribed relative to 20 C.  No heat transfer, material
degradation, fracture, plasticity, creep, geometric nonlinearity or global
energy credit is present.  Section energies are J/m of longitudinal length.
"""
from __future__ import annotations

import math
import numpy as np

IN = 0.0254
KSI = 4448.2216152605 / IN**2


def _finite_positive(name, value):
    if not math.isfinite(value) or value <= 0:
        raise ValueError(f"{name} must be positive and finite")
    return float(value)


class ElasticThermoSection:
    """Midpoint-fiber composite section with imposed thermal eigenstrain."""

    MODES = {
        "FREE",
        "AXIAL_RESTRAINED_ROTATION_FREE",
        "CURVATURE_RESTRAINED_AXIAL_FREE",
        "FULLY_RESTRAINED",
    }

    def __init__(self, section_cfg, thermo_cfg, case, nfibers=None):
        self.case = dict(case)
        geom = section_cfg["section"]
        concrete = section_cfg["concrete"]
        steel = section_cfg["reinforcement"]
        thermal = thermo_cfg["thermal_properties"]
        self.width = _finite_positive("width", geom["width_in"] * IN)
        self.h = _finite_positive("thickness", geom["equivalent_thickness_in"] * IN)
        self.span = _finite_positive("span", thermo_cfg["geometry"]["span_m"])
        self.reference_temperature_c = float(thermal["reference_temperature_c"])
        self.n = int(geom["reference_concrete_fibers"] if nfibers is None else nfibers)
        if self.n < 2:
            raise ValueError("At least two concrete fibers are required")
        rho_total = float(case["rho_total"])
        if not 0 <= rho_total < 1:
            raise ValueError("Reinforcement ratio outside [0,1)")
        layout = case["layout"]
        if layout not in ("symmetric", "top", "bottom"):
            raise ValueError("Unknown reinforcement layout")
        mode = case["mode"]
        if mode not in self.MODES:
            raise ValueError("Unknown restraint mode")
        self.mode = mode

        cover = float(steel["layer_center_distance_from_face_mm"]) / 1000.0
        if not 0 < cover < self.h / 2:
            raise ValueError("Invalid reinforcement cover")
        yc = (np.arange(self.n, dtype=float) + 0.5) * self.h / self.n - self.h / 2
        ac = np.full(self.n, self.width * self.h * (1 - rho_total) / self.n)
        if rho_total == 0:
            ys = np.empty(0)
        elif layout == "symmetric":
            ys = np.array([self.h / 2 - cover, cover - self.h / 2])
        elif layout == "top":
            ys = np.array([self.h / 2 - cover])
        else:
            ys = np.array([cover - self.h / 2])
        ass = np.full(len(ys), self.width * self.h * rho_total / max(1, len(ys)))

        alpha_common = float(thermal["common_alpha_control_per_k"])
        if case["alpha_mode"] == "common":
            alpha_c = alpha_s = alpha_common
        elif case["alpha_mode"] == "differential":
            alpha_c = float(thermal["concrete"]["thermal_expansion_per_k"])
            alpha_s = float(thermal["reinforcement"]["thermal_expansion_per_k"])
        else:
            raise ValueError("Unknown alpha mode")
        for name, value in (("alpha concrete", alpha_c), ("alpha steel", alpha_s)):
            _finite_positive(name, value)

        self.y = np.r_[yc, ys]
        self.area = np.r_[ac, ass]
        self.kind = np.array(["concrete"] * len(yc) + ["reinforcement"] * len(ys), dtype=object)
        self.E = np.r_[np.full(len(yc), concrete["E20_ksi"] * KSI), np.full(len(ys), steel["E_GPa"] * 1e9)]
        self.alpha = np.r_[np.full(len(yc), alpha_c), np.full(len(ys), alpha_s)]
        self.density = np.r_[np.full(len(yc), thermal["concrete"]["density_kg_m3"]),
                             np.full(len(ys), thermal["reinforcement"]["density_kg_m3"])]
        self.cp = np.r_[np.full(len(yc), thermal["concrete"]["specific_heat_j_kg_k"]),
                        np.full(len(ys), thermal["reinforcement"]["specific_heat_j_kg_k"])]
        if not all(np.isfinite(v).all() for v in (self.y, self.area, self.E, self.alpha, self.density, self.cp)):
            raise ValueError("Non-finite fiber property")
        if np.any(self.area <= 0) or np.any(self.E <= 0) or np.any(self.density <= 0) or np.any(self.cp <= 0):
            raise ValueError("Non-positive fiber property")

        self.B = np.column_stack((np.ones(len(self.y)), -self.y))
        self.EA = self.E * self.area
        assembled = self.B.T @ (self.EA[:, None] * self.B)
        skew_scale = max(1.0, float(np.max(np.abs(assembled))))
        if float(np.max(np.abs(assembled - assembled.T))) / skew_scale > 1e-14:
            raise ArithmeticError("Section stiffness assembly has excessive numerical skew")
        # B.T @ EA @ B is symmetric analytically. Remove only roundoff skew so
        # the linear solve does not retain an arbitrary integration-order bias.
        self.K = 0.5 * (assembled + assembled.T)
        if np.min(np.linalg.eigvalsh(self.K)) <= 0:
            raise ArithmeticError("Section stiffness must be symmetric positive definite")
        self.fc = float(concrete["fc20_ksi"]) * KSI
        self.ft = float(concrete["ft20_MPa"]) * 1e6
        self.fy = float(steel["fy_MPa"]) * 1e6

    def delta_temperature(self, scale):
        scale = float(scale)
        if not math.isfinite(scale):
            raise ValueError("Finite temperature scale required")
        bottom = scale * float(self.case["delta_t_bottom_c"])
        top = scale * float(self.case["delta_t_top_c"])
        return bottom + (top - bottom) * (self.y / self.h + 0.5)

    def solve(self, scale):
        dtemp = self.delta_temperature(scale)
        thermal_strain = self.alpha * dtemp
        thermal_resultant = self.B.T @ (self.EA * thermal_strain)
        if self.mode == "FREE":
            q = np.linalg.solve(self.K, thermal_resultant)
        elif self.mode == "AXIAL_RESTRAINED_ROTATION_FREE":
            q = np.array([0.0, thermal_resultant[1] / self.K[1, 1]])
        elif self.mode == "CURVATURE_RESTRAINED_AXIAL_FREE":
            q = np.array([thermal_resultant[0] / self.K[0, 0], 0.0])
        else:
            q = np.zeros(2)
        total_strain = self.B @ q
        mechanical_strain = total_strain - thermal_strain
        stress = self.E * mechanical_strain
        resultant = self.B.T @ (self.area * stress)
        stored = 0.5 * float(np.sum(self.area * stress * mechanical_strain))
        sensible = float(np.sum(self.density * self.cp * self.area * dtemp))
        concrete_mask = self.kind == "concrete"
        steel_mask = ~concrete_mask
        cstress = stress[concrete_mask]
        sstress = stress[steel_mask]
        tension_ratio = max(0.0, float(np.max(cstress, initial=0.0))) / self.ft
        compression_ratio = max(0.0, float(np.max(-cstress, initial=0.0))) / self.fc
        steel_ratio = float(np.max(np.abs(sstress), initial=0.0)) / self.fy
        force_scale = max(1.0, float(np.sum(self.EA * np.abs(thermal_strain))), float(np.sum(self.area * np.abs(stress))))
        moment_scale = max(1.0, float(np.sum(self.EA * np.abs(thermal_strain * self.y))),
                           float(np.sum(self.area * np.abs(stress * self.y))))
        axial_free = self.mode in ("FREE", "CURVATURE_RESTRAINED_AXIAL_FREE")
        curvature_free = self.mode in ("FREE", "AXIAL_RESTRAINED_ROTATION_FREE")
        return {
            "scale": float(scale), "q": q, "delta_temperature_c": dtemp,
            "thermal_strain": thermal_strain, "total_strain": total_strain,
            "mechanical_strain": mechanical_strain, "stress_pa": stress,
            "resultant": resultant, "thermal_resultant": thermal_resultant,
            "stored_j_per_m": stored, "sensible_enthalpy_j_per_m": sensible,
            "centroid_extension_m": float(q[0] * self.span),
            "simply_supported_free_bow_midspan_m": float(abs(q[1]) * self.span**2 / 8) if curvature_free else 0.0,
            "support_reaction_n": float(-resultant[0]) if not axial_free else 0.0,
            "support_reaction_nm": float(-resultant[1]) if not curvature_free else 0.0,
            "free_axial_residual_relative": abs(float(resultant[0])) / force_scale if axial_free else 0.0,
            "free_moment_residual_relative": abs(float(resultant[1])) / moment_scale if curvature_free else 0.0,
            "concrete_tension_ratio_ft20": tension_ratio,
            "concrete_compression_ratio_fc20": compression_ratio,
            "steel_stress_ratio_fy20": steel_ratio,
        }

    def snapshot(self, state, thermal_work, mechanical_work, energy_residual, index, segment):
        dtemp = state["delta_temperature_c"]
        stress = state["stress_pa"]
        return {
            "step": index, "segment": segment, "temperature_scale": state["scale"],
            "temperature_bottom_c": self.reference_temperature_c + float(state["scale"]) * float(self.case["delta_t_bottom_c"]),
            "temperature_top_c": self.reference_temperature_c + float(state["scale"]) * float(self.case["delta_t_top_c"]),
            "minimum_material_temperature_c": self.reference_temperature_c + float(np.min(dtemp)),
            "maximum_material_temperature_c": self.reference_temperature_c + float(np.max(dtemp)),
            "eps0": float(state["q"][0]), "kappa_per_m": float(state["q"][1]),
            "N_N": float(state["resultant"][0]), "M_Nm": float(state["resultant"][1]),
            "support_reaction_N": state["support_reaction_n"],
            "support_reaction_Nm": state["support_reaction_nm"],
            "centroid_extension_m": state["centroid_extension_m"],
            "simply_supported_free_bow_midspan_m": state["simply_supported_free_bow_midspan_m"],
            "stored_mechanical_J_per_m": state["stored_j_per_m"],
            "cumulative_thermoelastic_work_J_per_m": float(thermal_work),
            "cumulative_external_mechanical_work_J_per_m": float(mechanical_work),
            "mechanical_energy_residual_relative": float(energy_residual),
            "sensible_enthalpy_change_J_per_m": state["sensible_enthalpy_j_per_m"],
            "minimum_stress_Pa": float(np.min(stress)), "maximum_stress_Pa": float(np.max(stress)),
            "maximum_absolute_stress_Pa": float(np.max(np.abs(stress))),
            "free_axial_residual_relative": state["free_axial_residual_relative"],
            "free_moment_residual_relative": state["free_moment_residual_relative"],
            "concrete_tension_ratio_ft20": state["concrete_tension_ratio_ft20"],
            "concrete_compression_ratio_fc20": state["concrete_compression_ratio_fc20"],
            "steel_stress_ratio_fy20": state["steel_stress_ratio_fy20"],
            "dissipated_J_per_m": 0.0, "global_energy_credit_J": 0.0,
        }

    def trace(self, steps_per_segment):
        steps = int(steps_per_segment)
        if steps < 1:
            raise ValueError("Positive temperature step count required")
        vertices = [float(v) for v in self.case["scale_vertices"]]
        scales = [vertices[0]]
        segments = [-1]
        for segment, (left, right) in enumerate(zip(vertices[:-1], vertices[1:], strict=True)):
            values = np.linspace(left, right, steps + 1)[1:]
            scales.extend(float(v) for v in values)
            segments.extend([segment] * len(values))
        states = [self.solve(scales[0])]
        thermal_work = 0.0
        mechanical_work = 0.0
        initial_energy = states[0]["stored_j_per_m"]
        history = [self.snapshot(states[0], 0.0, 0.0, 0.0, 0, -1)]
        for index, (scale, segment) in enumerate(zip(scales[1:], segments[1:], strict=True), start=1):
            old = states[-1]
            new = self.solve(scale)
            thermal_work += -0.5 * float(np.sum(self.area * (old["stress_pa"] + new["stress_pa"])
                                                     * (new["thermal_strain"] - old["thermal_strain"])))
            mechanical_work += 0.5 * float((old["resultant"] + new["resultant"]) @ (new["q"] - old["q"]))
            scale_energy = max(1.0, abs(new["stored_j_per_m"] - initial_energy), abs(thermal_work), abs(mechanical_work))
            residual = abs(new["stored_j_per_m"] - initial_energy - thermal_work - mechanical_work) / scale_energy
            states.append(new)
            history.append(self.snapshot(new, thermal_work, mechanical_work, residual, index, segment))
        peak_index = max(range(len(scales)), key=lambda i: abs(scales[i]))
        peak = states[peak_index]
        final = states[-1]
        summary = {
            **self.case, "concrete_fibers": self.n, "state_count": len(history),
            "peak_step": peak_index, "peak": history[peak_index], "final": history[-1],
            "maximum_energy_residual_relative": max(r["mechanical_energy_residual_relative"] for r in history),
            "maximum_free_resultant_residual_relative": max(max(r["free_axial_residual_relative"], r["free_moment_residual_relative"]) for r in history),
            "maximum_elastic_screen_ratio": max(max(r["concrete_tension_ratio_ft20"], r["concrete_compression_ratio_fc20"], r["steel_stress_ratio_fy20"]) for r in history),
            "cycle_returned_to_reference": abs(history[-1]["temperature_scale"] - history[0]["temperature_scale"]) < 1e-15,
            "global_energy_credit_J": 0.0,
        }
        fibers = []
        for i in range(len(self.y)):
            fibers.append({
                "fiber": i, "kind": str(self.kind[i]), "y_m": float(self.y[i]), "area_m2": float(self.area[i]),
                "E_Pa": float(self.E[i]), "alpha_per_K": float(self.alpha[i]), "density_kg_m3": float(self.density[i]),
                "specific_heat_J_kg_K": float(self.cp[i]), "delta_temperature_C": float(peak["delta_temperature_c"][i]),
                "thermal_strain": float(peak["thermal_strain"][i]), "total_strain": float(peak["total_strain"][i]),
                "mechanical_strain": float(peak["mechanical_strain"][i]), "stress_Pa": float(peak["stress_pa"][i]),
                "stored_mechanical_J_per_m_contribution": float(0.5 * self.area[i] * peak["stress_pa"][i] * peak["mechanical_strain"][i]),
                "sensible_enthalpy_J_per_m_contribution": float(self.density[i] * self.cp[i] * self.area[i] * peak["delta_temperature_c"][i]),
            })
        return {"summary": summary, "history": history, "peak_fibers": fibers, "inventory": self.inventory()}

    def inventory(self):
        concrete = self.kind == "concrete"
        steel = ~concrete
        return {
            "case_id": self.case["id"], "mode": self.mode, "width_m": self.width,
            "equivalent_thickness_m": self.h, "span_m": self.span, "concrete_fibers": self.n,
            "concrete_area_m2": float(np.sum(self.area[concrete])), "steel_area_m2": float(np.sum(self.area[steel])),
            "gross_area_m2": float(np.sum(self.area)), "reinforcement_layers": int(np.count_nonzero(steel)),
            "E_concrete_Pa": float(self.E[concrete][0]),
            "E_steel_Pa": float(self.E[steel][0]) if np.any(steel) else None,
            "alpha_concrete_per_K": float(self.alpha[concrete][0]),
            "alpha_steel_per_K": float(self.alpha[steel][0]) if np.any(steel) else None,
            "section_stiffness": {"K_N": float(self.K[0, 0]), "K_Nm": float(self.K[0, 1]), "K_Nm2": float(self.K[1, 1])},
            "mass_kg_per_m": float(np.sum(self.density * self.area)),
            "heat_capacity_J_per_m_K": float(np.sum(self.density * self.cp * self.area)),
            "energy_units": "Mechanical and sensible quantities are J/m longitudinal length; no global energy credit",
        }


def cached_v10w_bar_replay(cached):
    declared = cached["declared_inputs"]
    geometry = declared["geometry"]
    material = declared["material"]
    delta_t = declared["temperature"]["maximum_temperature_change_c"]
    length_mm = geometry["length_mm"]
    area_mm2 = geometry["area_mm2"]
    modulus = material["young_modulus_mpa"]
    alpha = material["thermal_expansion_per_c"]
    free_mm = alpha * delta_t * length_mm
    restrained_n = modulus * area_mm2 * alpha * delta_t
    gradient_mm = 0.5 * alpha * delta_t * length_mm
    restrained_energy_j = 0.5 * restrained_n * (alpha * delta_t * length_mm) / 1000.0
    return {
        "iteration": "V11H", "reference_iteration": cached["iteration"],
        "uniform_free_tip_displacement_mm": free_mm,
        "uniform_restrained_force_magnitude_N": restrained_n,
        "uniform_restrained_stress_MPa": restrained_n / area_mm2,
        "axial_linear_gradient_free_tip_displacement_mm": gradient_mm,
        "uniform_restrained_stored_energy_J": restrained_energy_j,
        "uniform_restrained_thermoelastic_work_J": restrained_energy_j,
        "heat_transfer_solved": False, "wtc_attribution": False,
    }
