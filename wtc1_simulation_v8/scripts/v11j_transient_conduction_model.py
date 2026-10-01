"""Conservative one-dimensional constant-property conduction kernel for V11J.

The coordinate is x=0 at the idealized bottom face and x=L at the top
face.  Face heat fluxes are reported positive *into* the unit-area coupon.
Nothing in this module computes a fire, a mechanical response or damage.
"""
from __future__ import annotations

import math
from typing import Any

import numpy as np


def thermal_diffusivity(properties: dict[str, Any], conductivity: float) -> float:
    return float(conductivity) / (
        float(properties["density_kg_m3"])
        * float(properties["specific_heat_j_kg_k"])
    )


def cell_centres(length_m: float, cell_count: int) -> np.ndarray:
    dx = float(length_m) / int(cell_count)
    return (np.arange(int(cell_count), dtype=float) + 0.5) * dx


def initial_temperature(case: dict[str, Any], x_m: np.ndarray, length_m: float) -> np.ndarray:
    initial = case["initial"]
    kind = initial["kind"]
    if kind == "uniform":
        return np.full_like(x_m, float(initial["temperature_c"]), dtype=float)
    if kind == "linear":
        bottom = float(initial["bottom_temperature_c"])
        top = float(initial["top_temperature_c"])
        return bottom + (top - bottom) * x_m / float(length_m)
    if kind == "sine":
        reference = float(initial["reference_temperature_c"])
        amplitude = float(initial["amplitude_k"])
        mode = int(initial.get("mode", 1))
        return reference + amplitude * np.sin(mode * math.pi * x_m / float(length_m))
    raise ValueError(f"Unsupported initial field: {kind}")


def sensible_enthalpy_j_m2(
    temperature_c: np.ndarray,
    dx_m: float,
    properties: dict[str, Any],
) -> float:
    reference = float(properties["reference_temperature_c"])
    volumetric = (
        float(properties["density_kg_m3"])
        * float(properties["specific_heat_j_kg_k"])
    )
    return float(volumetric * dx_m * np.sum(temperature_c - reference))


def _boundary_value(boundary: dict[str, Any]) -> float | None:
    if boundary["kind"] == "prescribed_temperature":
        return float(boundary["temperature_c"])
    return None


def inward_face_fluxes_w_m2(
    temperature_c: np.ndarray,
    dx_m: float,
    conductivity_w_m_k: float,
    bottom_boundary: dict[str, Any],
    top_boundary: dict[str, Any],
) -> tuple[float, float]:
    def face(boundary: dict[str, Any], adjacent: float, side: str) -> float:
        kind = boundary["kind"]
        if kind == "adiabatic":
            return 0.0
        if kind == "prescribed_inward_flux":
            return float(boundary["inward_flux_w_m2"])
        if kind == "prescribed_temperature":
            value = float(boundary["temperature_c"])
            return 2.0 * float(conductivity_w_m_k) * (value - adjacent) / dx_m
        raise ValueError(f"Unsupported {side} boundary: {kind}")

    return (
        face(bottom_boundary, float(temperature_c[0]), "bottom"),
        face(top_boundary, float(temperature_c[-1]), "top"),
    )


def solve_tridiagonal(
    lower: np.ndarray,
    diagonal: np.ndarray,
    upper: np.ndarray,
    right_hand_side: np.ndarray,
) -> np.ndarray:
    """Thomas solve with explicit pivot checks and no SciPy dependency."""
    n = len(diagonal)
    if n < 1 or len(right_hand_side) != n or len(lower) != n - 1 or len(upper) != n - 1:
        raise ValueError("Inconsistent tridiagonal dimensions")
    c = np.empty(max(0, n - 1), dtype=float)
    d = np.empty(n, dtype=float)
    pivot = float(diagonal[0])
    if not math.isfinite(pivot) or abs(pivot) <= 1e-30:
        raise ArithmeticError("Invalid tridiagonal pivot at row 0")
    if n > 1:
        c[0] = float(upper[0]) / pivot
    d[0] = float(right_hand_side[0]) / pivot
    for i in range(1, n):
        pivot = float(diagonal[i]) - float(lower[i - 1]) * float(c[i - 1])
        if not math.isfinite(pivot) or abs(pivot) <= 1e-30:
            raise ArithmeticError(f"Invalid tridiagonal pivot at row {i}")
        if i < n - 1:
            c[i] = float(upper[i]) / pivot
        d[i] = (float(right_hand_side[i]) - float(lower[i - 1]) * float(d[i - 1])) / pivot
    result = np.empty(n, dtype=float)
    result[-1] = d[-1]
    for i in range(n - 2, -1, -1):
        result[i] = d[i] - c[i] * result[i + 1]
    return result


def backward_euler_step(
    old_temperature_c: np.ndarray,
    dt_s: float,
    dx_m: float,
    conductivity_w_m_k: float,
    properties: dict[str, Any],
    bottom_boundary: dict[str, Any],
    top_boundary: dict[str, Any],
) -> np.ndarray:
    n = len(old_temperature_c)
    if n < 2 or dt_s <= 0.0 or dx_m <= 0.0 or conductivity_w_m_k <= 0.0:
        raise ValueError("Positive dt, dx, k and at least two cells are required")
    heat_capacity = (
        float(properties["density_kg_m3"])
        * float(properties["specific_heat_j_kg_k"])
        * dx_m
    )
    transient = heat_capacity / dt_s
    internal = float(conductivity_w_m_k) / dx_m
    diagonal = np.full(n, transient, dtype=float)
    lower = np.full(n - 1, -internal, dtype=float)
    upper = np.full(n - 1, -internal, dtype=float)
    diagonal[:-1] += internal
    diagonal[1:] += internal
    rhs = transient * np.asarray(old_temperature_c, dtype=float)

    for index, boundary in ((0, bottom_boundary), (n - 1, top_boundary)):
        kind = boundary["kind"]
        if kind == "prescribed_temperature":
            conductance = 2.0 * float(conductivity_w_m_k) / dx_m
            diagonal[index] += conductance
            rhs[index] += conductance * float(boundary["temperature_c"])
        elif kind == "prescribed_inward_flux":
            rhs[index] += float(boundary["inward_flux_w_m2"])
        elif kind != "adiabatic":
            raise ValueError(f"Unsupported boundary condition: {kind}")
    return solve_tridiagonal(lower, diagonal, upper, rhs)


def analytical_temperature_c(
    case: dict[str, Any],
    x_m: np.ndarray,
    time_s: float,
    length_m: float,
    properties: dict[str, Any],
    conductivity_w_m_k: float,
    series_terms: int,
) -> np.ndarray | None:
    case_id = case["id"]
    if case_id == "UNIFORM_ADIABATIC_CONTROL":
        return np.full_like(x_m, float(case["initial"]["temperature_c"]))
    if case_id == "LINEAR_DIRICHLET_STEADY_CONTROL":
        initial = case["initial"]
        bottom = float(initial["bottom_temperature_c"])
        top = float(initial["top_temperature_c"])
        return bottom + (top - bottom) * x_m / float(length_m)
    alpha = thermal_diffusivity(properties, conductivity_w_m_k)
    if case_id == "SINE_DIRICHLET_TRANSIENT":
        initial = case["initial"]
        reference = float(initial["reference_temperature_c"])
        amplitude = float(initial["amplitude_k"])
        mode = int(initial.get("mode", 1))
        decay = math.exp(-alpha * (mode * math.pi / length_m) ** 2 * time_s)
        return reference + amplitude * np.sin(mode * math.pi * x_m / length_m) * decay
    if case_id == "CONSTANT_TOP_FLUX_BOTTOM_ADIABATIC":
        return None
    if case_id == "TOP_STEP_DIRICHLET_BOTTOM_ADIABATIC":
        initial_temperature_c = float(case["initial"]["temperature_c"])
        surface_temperature_c = float(case["top_boundary"]["temperature_c"])
        if time_s <= 0.0:
            return np.full_like(x_m, initial_temperature_c)
        mode_index = np.arange(int(series_terms), dtype=float)
        lambdas = (mode_index + 0.5) * math.pi
        fourier = alpha * time_s / length_m**2
        coefficients = (
            2.0
            * np.power(-1.0, mode_index)
            * np.exp(-lambdas**2 * fourier)
            / lambdas
        )
        theta = np.cos(np.outer(x_m / length_m, lambdas)) @ coefficients
        return surface_temperature_c + (initial_temperature_c - surface_temperature_c) * theta
    raise ValueError(f"No analytical mapping for {case_id}")


def analytical_mean_temperature_c(
    case: dict[str, Any],
    time_s: float,
    length_m: float,
    properties: dict[str, Any],
    conductivity_w_m_k: float,
    series_terms: int,
) -> float:
    case_id = case["id"]
    if case_id == "UNIFORM_ADIABATIC_CONTROL":
        return float(case["initial"]["temperature_c"])
    if case_id == "LINEAR_DIRICHLET_STEADY_CONTROL":
        initial = case["initial"]
        return 0.5 * (
            float(initial["bottom_temperature_c"])
            + float(initial["top_temperature_c"])
        )
    if case_id == "SINE_DIRICHLET_TRANSIENT":
        initial = case["initial"]
        alpha = thermal_diffusivity(properties, conductivity_w_m_k)
        mode = int(initial.get("mode", 1))
        decay = math.exp(-alpha * (mode * math.pi / length_m) ** 2 * time_s)
        if mode % 2 == 0:
            mode_average = 0.0
        else:
            mode_average = 2.0 / (mode * math.pi)
        return float(initial["reference_temperature_c"]) + float(initial["amplitude_k"]) * mode_average * decay
    if case_id == "CONSTANT_TOP_FLUX_BOTTOM_ADIABATIC":
        initial = float(case["initial"]["temperature_c"])
        flux = float(case["top_boundary"]["inward_flux_w_m2"])
        volumetric = (
            float(properties["density_kg_m3"])
            * float(properties["specific_heat_j_kg_k"])
        )
        return initial + flux * time_s / (volumetric * length_m)
    if case_id == "TOP_STEP_DIRICHLET_BOTTOM_ADIABATIC":
        initial = float(case["initial"]["temperature_c"])
        surface = float(case["top_boundary"]["temperature_c"])
        if time_s <= 0.0:
            return initial
        alpha = thermal_diffusivity(properties, conductivity_w_m_k)
        mode_index = np.arange(int(series_terms), dtype=float)
        lambdas = (mode_index + 0.5) * math.pi
        fourier = alpha * time_s / length_m**2
        theta_mean = float(np.sum(2.0 * np.exp(-lambdas**2 * fourier) / lambdas**2))
        return surface + (initial - surface) * theta_mean
    raise ValueError(f"No analytical mean mapping for {case_id}")


def analytical_inward_fluxes_w_m2(
    case: dict[str, Any],
    time_s: float,
    length_m: float,
    properties: dict[str, Any],
    conductivity_w_m_k: float,
    series_terms: int,
) -> tuple[float | None, float | None]:
    case_id = case["id"]
    k = float(conductivity_w_m_k)
    if case_id == "UNIFORM_ADIABATIC_CONTROL":
        return 0.0, 0.0
    if case_id == "LINEAR_DIRICHLET_STEADY_CONTROL":
        delta = float(case["initial"]["top_temperature_c"]) - float(case["initial"]["bottom_temperature_c"])
        return -k * delta / length_m, k * delta / length_m
    if case_id == "SINE_DIRICHLET_TRANSIENT":
        initial = case["initial"]
        alpha = thermal_diffusivity(properties, k)
        mode = int(initial.get("mode", 1))
        amplitude = float(initial["amplitude_k"])
        decay = math.exp(-alpha * (mode * math.pi / length_m) ** 2 * time_s)
        magnitude = k * amplitude * mode * math.pi / length_m * decay
        bottom = -magnitude
        top = ((-1.0) ** mode) * magnitude
        return bottom, top
    if case_id == "CONSTANT_TOP_FLUX_BOTTOM_ADIABATIC":
        return 0.0, float(case["top_boundary"]["inward_flux_w_m2"])
    if case_id == "TOP_STEP_DIRICHLET_BOTTOM_ADIABATIC":
        if time_s <= 0.0:
            return 0.0, None
        initial = float(case["initial"]["temperature_c"])
        surface = float(case["top_boundary"]["temperature_c"])
        alpha = thermal_diffusivity(properties, k)
        mode_index = np.arange(int(series_terms), dtype=float)
        lambdas = (mode_index + 0.5) * math.pi
        fourier = alpha * time_s / length_m**2
        top = -2.0 * k * (initial - surface) * float(np.sum(np.exp(-lambdas**2 * fourier))) / length_m
        return 0.0, top
    raise ValueError(f"No analytical flux mapping for {case_id}")


def _bounds(case: dict[str, Any], initial_c: np.ndarray) -> tuple[float, float | None]:
    values = [float(np.min(initial_c)), float(np.max(initial_c))]
    for boundary_name in ("bottom_boundary", "top_boundary"):
        value = _boundary_value(case[boundary_name])
        if value is not None:
            values.append(value)
    lower = min(values)
    if any(case[name]["kind"] == "prescribed_inward_flux" for name in ("bottom_boundary", "top_boundary")):
        return lower, None
    return lower, max(values)


def run_case(
    configuration: dict[str, Any],
    case: dict[str, Any],
    cell_count: int | None = None,
    step_count: int | None = None,
    conductivity_w_m_k: float | None = None,
    store_profiles: bool = True,
) -> dict[str, Any]:
    geometry = configuration["geometry"]
    properties = configuration["constant_properties"]
    discretization = configuration["discretization"]
    length = float(geometry["thickness_m"])
    n_cells = int(cell_count or discretization["reference_cells"])
    n_steps = int(step_count or discretization["reference_steps"])
    k = float(conductivity_w_m_k or properties["reference_conductivity_w_m_k"])
    duration = float(case["duration_s"])
    dt = duration / n_steps
    dx = length / n_cells
    x = cell_centres(length, n_cells)
    temperature = initial_temperature(case, x, length)
    initial_temperature_vector = temperature.copy()
    enthalpy_initial = sensible_enthalpy_j_m2(temperature, dx, properties)
    enthalpy = enthalpy_initial
    cumulative_heat = 0.0
    max_increment_absolute = 0.0
    max_increment_relative = 0.0
    max_total_absolute = 0.0
    max_total_relative = 0.0
    lower_bound, upper_bound = _bounds(case, temperature)
    maximum_principle_violation = 0.0
    mean_changes = []
    histories: list[dict[str, Any]] = []
    profiles: list[dict[str, Any]] = []
    intervals = int(discretization["stored_history_intervals"])
    stored_steps = sorted(set(int(round(i * n_steps / intervals)) for i in range(intervals + 1)))
    stored_set = set(stored_steps)
    terms = int(configuration["analytical_series_terms"])

    def store(step: int, current_time: float, current: np.ndarray, current_enthalpy: float) -> None:
        bottom_flux, top_flux = inward_face_fluxes_w_m2(
            current, dx, k, case["bottom_boundary"], case["top_boundary"]
        )
        exact = analytical_temperature_c(case, x, current_time, length, properties, k, terms)
        exact_mean = analytical_mean_temperature_c(case, current_time, length, properties, k, terms)
        exact_fluxes = analytical_inward_fluxes_w_m2(case, current_time, length, properties, k, terms)
        field_linf = None if exact is None else float(np.max(np.abs(current - exact)))
        field_rms = None if exact is None else float(np.sqrt(np.mean((current - exact) ** 2)))
        row = {
            "case_id": case["id"],
            "step": int(step),
            "time_s": float(current_time),
            "time_fraction": float(current_time / duration) if duration else 0.0,
            "mean_temperature_c": float(np.mean(current)),
            "minimum_temperature_c": float(np.min(current)),
            "maximum_temperature_c": float(np.max(current)),
            "bottom_cell_temperature_c": float(current[0]),
            "top_cell_temperature_c": float(current[-1]),
            "bottom_inward_flux_w_m2": float(bottom_flux),
            "top_inward_flux_w_m2": float(top_flux),
            "net_inward_flux_w_m2": float(bottom_flux + top_flux),
            "enthalpy_j_m2": float(current_enthalpy),
            "enthalpy_change_j_m2": float(current_enthalpy - enthalpy_initial),
            "cumulative_inward_heat_j_m2": float(cumulative_heat),
            "total_energy_residual_j_m2": float(current_enthalpy - enthalpy_initial - cumulative_heat),
            "analytical_mean_temperature_c": float(exact_mean),
            "mean_temperature_error_k": float(np.mean(current) - exact_mean),
            "field_linf_error_k": field_linf,
            "field_rms_error_k": field_rms,
            "analytical_bottom_inward_flux_w_m2": exact_fluxes[0],
            "analytical_top_inward_flux_w_m2": exact_fluxes[1],
        }
        histories.append(row)
        if store_profiles:
            profiles.append({
                "case_id": case["id"],
                "step": int(step),
                "time_s": float(current_time),
                "x_m": [float(value) for value in x],
                "depth_from_top_m": [float(length - value) for value in x],
                "temperature_c": [float(value) for value in current],
                "analytical_temperature_c": None if exact is None else [float(value) for value in exact],
            })

    store(0, 0.0, temperature, enthalpy)
    previous_mean = float(np.mean(temperature))
    for step in range(1, n_steps + 1):
        updated = backward_euler_step(
            temperature,
            dt,
            dx,
            k,
            properties,
            case["bottom_boundary"],
            case["top_boundary"],
        )
        updated_enthalpy = sensible_enthalpy_j_m2(updated, dx, properties)
        bottom_flux, top_flux = inward_face_fluxes_w_m2(
            updated, dx, k, case["bottom_boundary"], case["top_boundary"]
        )
        heat_increment = dt * (bottom_flux + top_flux)
        enthalpy_increment = updated_enthalpy - enthalpy
        residual = enthalpy_increment - heat_increment
        relative_residual = abs(residual) / max(1.0, abs(enthalpy_increment), abs(heat_increment))
        max_increment_absolute = max(max_increment_absolute, abs(residual))
        max_increment_relative = max(max_increment_relative, relative_residual)
        cumulative_heat += heat_increment
        total_residual = updated_enthalpy - enthalpy_initial - cumulative_heat
        total_relative = abs(total_residual) / max(
            1.0, abs(updated_enthalpy - enthalpy_initial), abs(cumulative_heat)
        )
        max_total_absolute = max(max_total_absolute, abs(total_residual))
        max_total_relative = max(max_total_relative, total_relative)
        violation = max(0.0, lower_bound - float(np.min(updated)))
        if upper_bound is not None:
            violation = max(violation, float(np.max(updated)) - upper_bound)
        maximum_principle_violation = max(maximum_principle_violation, violation)
        current_mean = float(np.mean(updated))
        mean_changes.append(current_mean - previous_mean)
        previous_mean = current_mean
        temperature = updated
        enthalpy = updated_enthalpy
        if step in stored_set:
            store(step, step * dt, temperature, enthalpy)

    exact_terminal = analytical_temperature_c(case, x, duration, length, properties, k, terms)
    exact_mean_terminal = analytical_mean_temperature_c(case, duration, length, properties, k, terms)
    field_linf = None if exact_terminal is None else float(np.max(np.abs(temperature - exact_terminal)))
    field_rms = None if exact_terminal is None else float(np.sqrt(np.mean((temperature - exact_terminal) ** 2)))
    initial_mean = float(np.mean(initial_temperature_vector))
    rise = temperature - float(case["initial"].get("temperature_c", properties["reference_temperature_c"]))
    penetration_mask = rise >= 1.0
    penetration_depth = 0.0 if not np.any(penetration_mask) else float(length - np.min(x[penetration_mask]))
    positive_rise = np.maximum(rise, 0.0)
    if float(np.sum(positive_rise)) > 0.0:
        thermal_centroid_depth = float(np.sum((length - x) * positive_rise) / np.sum(positive_rise))
    else:
        thermal_centroid_depth = 0.0
    alpha = thermal_diffusivity(properties, k)
    summary = {
        "id": case["id"],
        "cell_count": n_cells,
        "step_count": n_steps,
        "dx_m": dx,
        "dt_s": dt,
        "duration_s": duration,
        "conductivity_w_m_k": k,
        "thermal_diffusivity_m2_s": alpha,
        "terminal_fourier_number": alpha * duration / length**2,
        "step_fourier_number": alpha * dt / dx**2,
        "initial_mean_temperature_c": initial_mean,
        "final_mean_temperature_c": float(np.mean(temperature)),
        "final_minimum_temperature_c": float(np.min(temperature)),
        "final_maximum_temperature_c": float(np.max(temperature)),
        "final_bottom_cell_temperature_c": float(temperature[0]),
        "final_top_cell_temperature_c": float(temperature[-1]),
        "analytical_final_mean_temperature_c": float(exact_mean_terminal),
        "terminal_mean_error_k": float(np.mean(temperature) - exact_mean_terminal),
        "terminal_field_linf_error_k": field_linf,
        "terminal_field_rms_error_k": field_rms,
        "initial_enthalpy_j_m2": float(enthalpy_initial),
        "final_enthalpy_j_m2": float(enthalpy),
        "enthalpy_change_j_m2": float(enthalpy - enthalpy_initial),
        "cumulative_inward_heat_j_m2": float(cumulative_heat),
        "final_total_energy_residual_j_m2": float(enthalpy - enthalpy_initial - cumulative_heat),
        "maximum_increment_energy_residual_absolute_j_m2": float(max_increment_absolute),
        "maximum_increment_energy_residual_relative": float(max_increment_relative),
        "maximum_total_energy_residual_absolute_j_m2": float(max_total_absolute),
        "maximum_total_energy_residual_relative": float(max_total_relative),
        "maximum_principle_violation_k": float(maximum_principle_violation),
        "minimum_mean_step_change_k": float(min(mean_changes)) if mean_changes else 0.0,
        "maximum_mean_step_change_k": float(max(mean_changes)) if mean_changes else 0.0,
        "penetration_depth_above_1k_m": penetration_depth,
        "thermal_centroid_depth_from_top_m": thermal_centroid_depth,
        "sensible_enthalpy_only": True,
        "mechanical_energy_j_m2": 0.0,
        "global_energy_credit_j": 0.0,
    }
    return {"summary": summary, "history": histories, "profiles": profiles}


def observed_orders(rows: list[dict[str, Any]], error_key: str, resolution_key: str) -> list[float]:
    orders = []
    for coarse, fine in zip(rows, rows[1:]):
        coarse_error = float(coarse[error_key])
        fine_error = float(fine[error_key])
        coarse_resolution = float(coarse[resolution_key])
        fine_resolution = float(fine[resolution_key])
        if coarse_error <= 0.0 or fine_error <= 0.0:
            orders.append(float("nan"))
        else:
            orders.append(math.log(coarse_error / fine_error) / math.log(fine_resolution / coarse_resolution))
    return orders


def spatial_operator_refinement(configuration: dict[str, Any]) -> dict[str, Any]:
    cases = {case["id"]: case for case in configuration["cases"]}
    case = cases[configuration["discretization"]["space_refinement_case"]]
    geometry = configuration["geometry"]
    properties = configuration["constant_properties"]
    length = float(geometry["thickness_m"])
    duration = float(case["duration_s"])
    k = float(properties["reference_conductivity_w_m_k"])
    alpha = thermal_diffusivity(properties, k)
    amplitude = float(case["initial"]["amplitude_k"])
    reference = float(case["initial"]["reference_temperature_c"])
    continuous_lambda = alpha * (math.pi / length) ** 2
    rows = []
    for cell_count in configuration["discretization"]["space_refinement_cells"]:
        n = int(cell_count)
        dx = length / n
        x = cell_centres(length, n)
        discrete_lambda = 4.0 * alpha * math.sin(math.pi / (2.0 * n)) ** 2 / dx**2
        discrete = reference + amplitude * np.sin(math.pi * x / length) * math.exp(-discrete_lambda * duration)
        exact = reference + amplitude * np.sin(math.pi * x / length) * math.exp(-continuous_lambda * duration)
        rows.append({
            "case_id": case["id"],
            "cell_count": n,
            "dx_m": dx,
            "continuous_decay_rate_per_s": continuous_lambda,
            "discrete_decay_rate_per_s": discrete_lambda,
            "decay_rate_relative_error": abs(discrete_lambda - continuous_lambda) / continuous_lambda,
            "terminal_field_linf_error_k": float(np.max(np.abs(discrete - exact))),
            "terminal_field_rms_error_k": float(np.sqrt(np.mean((discrete - exact) ** 2))),
            "exact_time_integration": True,
        })
    orders = observed_orders(rows, "terminal_field_linf_error_k", "cell_count")
    for index, order in enumerate(orders):
        rows[index + 1]["observed_order_from_previous"] = order
    return {
        "mode": configuration["discretization"]["space_refinement_mode"],
        "case_id": case["id"],
        "rows": rows,
        "observed_orders": orders,
    }


def time_refinement(configuration: dict[str, Any]) -> dict[str, Any]:
    cases = {case["id"]: case for case in configuration["cases"]}
    result = {}
    for case_id in configuration["discretization"]["time_convergence_cases"]:
        rows = []
        for steps in configuration["discretization"]["time_refinement_steps"]:
            run = run_case(
                configuration,
                cases[case_id],
                cell_count=int(configuration["discretization"]["time_refinement_cells"]),
                step_count=int(steps),
                store_profiles=False,
            )
            rows.append(run["summary"])
        orders = observed_orders(rows, "terminal_field_linf_error_k", "step_count")
        for index, order in enumerate(orders):
            rows[index + 1]["observed_order_from_previous"] = order
        result[case_id] = {"rows": rows, "observed_orders": orders}
    return result


def conductivity_sensitivity(configuration: dict[str, Any]) -> list[dict[str, Any]]:
    cases = {case["id"]: case for case in configuration["cases"]}
    case = cases[configuration["discretization"]["conductivity_sensitivity_case"]]
    rows = []
    for conductivity in configuration["constant_properties"]["conductivity_sensitivity_w_m_k"]:
        run = run_case(
            configuration,
            case,
            conductivity_w_m_k=float(conductivity),
            store_profiles=False,
        )
        rows.append(run["summary"])
    return rows
