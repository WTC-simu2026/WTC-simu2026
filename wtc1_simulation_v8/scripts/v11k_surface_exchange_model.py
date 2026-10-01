"""Bounded constant-property conduction with surface exchange for WTC1 V11K.

This is a verification coupon, not a fire model.  Temperatures supplied to the
surface laws are synthetic.  Flux is positive into the unit-area coupon.
"""
from __future__ import annotations

import copy
import math
from typing import Any

import numpy as np


def cell_centres(length_m: float, cell_count: int) -> np.ndarray:
    dx = float(length_m) / int(cell_count)
    return (np.arange(int(cell_count), dtype=float) + 0.5) * dx


def thermal_diffusivity(properties: dict[str, Any]) -> float:
    return float(properties["conductivity_w_m_k"]) / (
        float(properties["density_kg_m3"])
        * float(properties["specific_heat_j_kg_k"])
    )


def sensible_enthalpy_j_m2(
    temperature_c: np.ndarray,
    dx_m: float,
    properties: dict[str, Any],
) -> float:
    capacity = (
        float(properties["density_kg_m3"])
        * float(properties["specific_heat_j_kg_k"])
    )
    reference = float(properties["reference_temperature_c"])
    return float(capacity * dx_m * np.sum(np.asarray(temperature_c) - reference))


def solve_tridiagonal(
    lower: np.ndarray,
    diagonal: np.ndarray,
    upper: np.ndarray,
    right_hand_side: np.ndarray,
) -> np.ndarray:
    """Thomas solve with pivot checks and no SciPy dependency."""
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
    for index in range(1, n):
        pivot = float(diagonal[index]) - float(lower[index - 1]) * float(c[index - 1])
        if not math.isfinite(pivot) or abs(pivot) <= 1e-30:
            raise ArithmeticError(f"Invalid tridiagonal pivot at row {index}")
        if index < n - 1:
            c[index] = float(upper[index]) / pivot
        d[index] = (
            float(right_hand_side[index])
            - float(lower[index - 1]) * float(d[index - 1])
        ) / pivot
    result = np.empty(n, dtype=float)
    result[-1] = d[-1]
    for index in range(n - 2, -1, -1):
        result[index] = d[index] - c[index] * result[index + 1]
    return result


def environment_flux_w_m2(
    surface_temperature_c: float,
    boundary: dict[str, Any],
    exchange: dict[str, Any],
) -> tuple[float, float, float, float]:
    """Return inward convection, radiation, total and -dq/dTs (W/m2/K)."""
    if boundary["kind"] == "adiabatic":
        return 0.0, 0.0, 0.0, 0.0
    if boundary["kind"] != "surface_exchange":
        raise ValueError(f"Unsupported boundary kind: {boundary['kind']}")
    h_value = float(boundary["h_w_m2_k"])
    emissivity = float(boundary["emissivity"])
    sigma = float(exchange["stefan_boltzmann_w_m2_k4"])
    offset = float(exchange["celsius_to_kelvin_offset"])
    surface_k = float(surface_temperature_c) + offset
    radiation_k = float(boundary["radiative_temperature_c"]) + offset
    if surface_k <= 0.0 or radiation_k <= 0.0:
        raise ValueError("Radiative temperatures must be above absolute zero")
    convection = h_value * (float(boundary["gas_temperature_c"]) - float(surface_temperature_c))
    radiation = emissivity * sigma * (radiation_k**4 - surface_k**4)
    slope_magnitude = h_value + 4.0 * emissivity * sigma * surface_k**3
    return convection, radiation, convection + radiation, slope_magnitude


def surface_state(
    adjacent_cell_temperature_c: float,
    dx_m: float,
    conductivity_w_m_k: float,
    boundary: dict[str, Any],
    exchange: dict[str, Any],
) -> dict[str, float | int]:
    """Solve the zero-capacity face and return flux derivative for Newton."""
    if boundary["kind"] == "adiabatic":
        return {
            "surface_temperature_c": float(adjacent_cell_temperature_c),
            "convective_inward_flux_w_m2": 0.0,
            "radiative_inward_flux_w_m2": 0.0,
            "total_inward_flux_w_m2": 0.0,
            "conductive_inward_flux_w_m2": 0.0,
            "surface_balance_residual_w_m2": 0.0,
            "d_total_flux_d_cell_w_m2_k": 0.0,
            "iterations": 0,
        }
    conductance = 2.0 * float(conductivity_w_m_k) / float(dx_m)
    surface = float(adjacent_cell_temperature_c)
    iterations = 0
    for iterations in range(1, 31):
        convection, radiation, total, slope = environment_flux_w_m2(surface, boundary, exchange)
        residual = conductance * (surface - adjacent_cell_temperature_c) - total
        if abs(residual) <= 2e-12:
            break
        increment = -residual / (conductance + slope)
        trial = surface + increment
        if trial + float(exchange["celsius_to_kelvin_offset"]) <= 1e-6:
            trial = -float(exchange["celsius_to_kelvin_offset"]) + 1e-6
        surface = trial
    convection, radiation, total, slope = environment_flux_w_m2(surface, boundary, exchange)
    conductive = conductance * (surface - adjacent_cell_temperature_c)
    derivative = -conductance * slope / (conductance + slope)
    return {
        "surface_temperature_c": float(surface),
        "convective_inward_flux_w_m2": float(convection),
        "radiative_inward_flux_w_m2": float(radiation),
        "total_inward_flux_w_m2": float(total),
        "conductive_inward_flux_w_m2": float(conductive),
        "surface_balance_residual_w_m2": float(conductive - total),
        "d_total_flux_d_cell_w_m2_k": float(derivative),
        "iterations": int(iterations),
    }


def _residual_and_jacobian(
    temperature_c: np.ndarray,
    old_temperature_c: np.ndarray,
    dt_s: float,
    dx_m: float,
    properties: dict[str, Any],
    bottom_boundary: dict[str, Any],
    top_boundary: dict[str, Any],
    exchange: dict[str, Any],
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, dict[str, Any], dict[str, Any]]:
    n_cells = len(temperature_c)
    conductivity = float(properties["conductivity_w_m_k"])
    capacity = (
        float(properties["density_kg_m3"])
        * float(properties["specific_heat_j_kg_k"])
        * float(dx_m)
    )
    transient = capacity / float(dt_s)
    internal = conductivity / float(dx_m)
    residual = transient * (temperature_c - old_temperature_c)
    diagonal = np.full(n_cells, transient, dtype=float)
    lower = np.full(n_cells - 1, -internal, dtype=float)
    upper = np.full(n_cells - 1, -internal, dtype=float)
    differences = temperature_c[:-1] - temperature_c[1:]
    residual[:-1] += internal * differences
    residual[1:] -= internal * differences
    diagonal[:-1] += internal
    diagonal[1:] += internal
    bottom = surface_state(temperature_c[0], dx_m, conductivity, bottom_boundary, exchange)
    top = surface_state(temperature_c[-1], dx_m, conductivity, top_boundary, exchange)
    residual[0] -= float(bottom["total_inward_flux_w_m2"])
    residual[-1] -= float(top["total_inward_flux_w_m2"])
    diagonal[0] -= float(bottom["d_total_flux_d_cell_w_m2_k"])
    diagonal[-1] -= float(top["d_total_flux_d_cell_w_m2_k"])
    return residual, lower, diagonal, upper, bottom, top


def backward_euler_step(
    old_temperature_c: np.ndarray,
    dt_s: float,
    dx_m: float,
    properties: dict[str, Any],
    bottom_boundary: dict[str, Any],
    top_boundary: dict[str, Any],
    exchange: dict[str, Any],
) -> tuple[np.ndarray, dict[str, Any]]:
    if len(old_temperature_c) < 2 or dt_s <= 0.0 or dx_m <= 0.0:
        raise ValueError("Positive dt, dx and at least two cells are required")
    temperature = np.asarray(old_temperature_c, dtype=float).copy()
    line_search_reductions = 0
    converged = False
    iterations = 0
    for iterations in range(1, 21):
        residual, lower, diagonal, upper, bottom, top = _residual_and_jacobian(
            temperature, old_temperature_c, dt_s, dx_m, properties,
            bottom_boundary, top_boundary, exchange,
        )
        norm = float(np.max(np.abs(residual)))
        if norm <= 2e-10:
            converged = True
            break
        delta = solve_tridiagonal(lower, diagonal, upper, -residual)
        factor = 1.0
        accepted = False
        for reduction in range(13):
            trial = temperature + factor * delta
            trial_residual = _residual_and_jacobian(
                trial, old_temperature_c, dt_s, dx_m, properties,
                bottom_boundary, top_boundary, exchange,
            )[0]
            if float(np.max(np.abs(trial_residual))) < norm:
                temperature = trial
                line_search_reductions += reduction
                accepted = True
                break
            factor *= 0.5
        if not accepted:
            raise ArithmeticError("Newton line search failed")
    residual, _, _, _, bottom, top = _residual_and_jacobian(
        temperature, old_temperature_c, dt_s, dx_m, properties,
        bottom_boundary, top_boundary, exchange,
    )
    final_norm = float(np.max(np.abs(residual)))
    converged = converged or final_norm <= 1e-8
    if not converged:
        raise ArithmeticError(f"Newton did not converge: {final_norm:.6e} W/m2")
    return temperature, {
        "converged": bool(converged),
        "iterations": int(iterations),
        "line_search_reductions": int(line_search_reductions),
        "maximum_residual_w_m2": final_norm,
        "bottom": bottom,
        "top": top,
    }


def _inverse_environment_flux_temperature_c(
    boundary: dict[str, Any],
    target_inward_flux_w_m2: float,
    exchange: dict[str, Any],
) -> float:
    """Invert a monotone surface law independently by bisection."""
    low = -float(exchange["celsius_to_kelvin_offset"]) + 1e-7
    high = 3000.0
    target = float(target_inward_flux_w_m2)

    def value(temperature_c: float) -> float:
        return environment_flux_w_m2(temperature_c, boundary, exchange)[2] - target

    if value(low) < 0.0 or value(high) > 0.0:
        raise ArithmeticError("Surface-law inverse is not bracketed")
    for _ in range(160):
        middle = 0.5 * (low + high)
        if value(middle) > 0.0:
            low = middle
        else:
            high = middle
    return 0.5 * (low + high)


def steady_reference(
    configuration: dict[str, Any],
    case: dict[str, Any],
) -> dict[str, float]:
    """Continuous steady solution for two monotone exchange boundaries."""
    length = float(configuration["geometry"]["thickness_m"])
    conductivity = float(configuration["constant_properties"]["conductivity_w_m_k"])
    exchange = configuration["surface_exchange"]
    bottom_boundary = case["bottom_boundary"]
    top_boundary = case["top_boundary"]

    def at_heat_rate(rate: float) -> tuple[float, float, float]:
        bottom_surface = _inverse_environment_flux_temperature_c(bottom_boundary, -rate, exchange)
        top_surface = _inverse_environment_flux_temperature_c(top_boundary, rate, exchange)
        mismatch = conductivity * (top_surface - bottom_surface) / length - rate
        return mismatch, bottom_surface, top_surface

    zero = at_heat_rate(0.0)
    if abs(zero[0]) <= 1e-12:
        return {
            "heat_rate_top_to_bottom_w_m2": 0.0,
            "bottom_surface_temperature_c": zero[1],
            "top_surface_temperature_c": zero[2],
        }
    low = 0.0
    high = 1000.0
    while at_heat_rate(high)[0] > 0.0:
        high *= 2.0
        if high > 1e8:
            raise ArithmeticError("Steady heat-rate root not bracketed")
    bottom_surface = zero[1]
    top_surface = zero[2]
    for _ in range(160):
        middle = 0.5 * (low + high)
        mismatch, bottom_surface, top_surface = at_heat_rate(middle)
        if mismatch > 0.0:
            low = middle
        else:
            high = middle
    rate = 0.5 * (low + high)
    _, bottom_surface, top_surface = at_heat_rate(rate)
    return {
        "heat_rate_top_to_bottom_w_m2": float(rate),
        "bottom_surface_temperature_c": float(bottom_surface),
        "top_surface_temperature_c": float(top_surface),
    }


def robin_eigenvalue_zeta(configuration: dict[str, Any], case: dict[str, Any]) -> float:
    length = float(configuration["geometry"]["thickness_m"])
    conductivity = float(configuration["constant_properties"]["conductivity_w_m_k"])
    h_value = float(case["top_boundary"]["h_w_m2_k"])
    biot_half = h_value * (0.5 * length) / conductivity

    def residual(zeta: float) -> float:
        return zeta * math.tan(zeta) - biot_half

    low = 1e-14
    high = 0.5 * math.pi - 1e-12
    for _ in range(160):
        middle = 0.5 * (low + high)
        if residual(middle) < 0.0:
            low = middle
        else:
            high = middle
    return 0.5 * (low + high)


def analytical_temperature_c(
    configuration: dict[str, Any],
    case: dict[str, Any],
    x_m: np.ndarray,
    time_s: float,
) -> np.ndarray | None:
    case_id = case["id"]
    length = float(configuration["geometry"]["thickness_m"])
    if case_id == "COMBINED_EQUILIBRIUM_CONTROL":
        return np.full_like(x_m, float(case["initial"]["temperature_c"]))
    if case["initial"]["kind"] == "steady_reference":
        steady = steady_reference(configuration, case)
        bottom = steady["bottom_surface_temperature_c"]
        top = steady["top_surface_temperature_c"]
        return bottom + (top - bottom) * x_m / length
    if case_id == "CONVECTION_EIGENMODE_TRANSIENT":
        initial = case["initial"]
        ambient = float(initial["ambient_temperature_c"])
        amplitude = float(initial["amplitude_k"])
        half_length = 0.5 * length
        zeta = robin_eigenvalue_zeta(configuration, case)
        alpha = thermal_diffusivity(configuration["constant_properties"])
        decay = math.exp(-alpha * (zeta / half_length) ** 2 * float(time_s))
        return ambient + amplitude * np.cos(zeta * (x_m - half_length) / half_length) * decay
    if case_id == "COMBINED_STEP_TRANSIENT":
        return None
    raise ValueError(f"No analytical field mapping for {case_id}")


def analytical_mean_temperature_c(
    configuration: dict[str, Any],
    case: dict[str, Any],
    time_s: float,
) -> float | None:
    case_id = case["id"]
    if case_id == "COMBINED_STEP_TRANSIENT":
        return None
    if case_id == "COMBINED_EQUILIBRIUM_CONTROL":
        return float(case["initial"]["temperature_c"])
    if case["initial"]["kind"] == "steady_reference":
        steady = steady_reference(configuration, case)
        return 0.5 * (
            steady["bottom_surface_temperature_c"]
            + steady["top_surface_temperature_c"]
        )
    if case_id == "CONVECTION_EIGENMODE_TRANSIENT":
        initial = case["initial"]
        ambient = float(initial["ambient_temperature_c"])
        amplitude = float(initial["amplitude_k"])
        length = float(configuration["geometry"]["thickness_m"])
        half_length = 0.5 * length
        zeta = robin_eigenvalue_zeta(configuration, case)
        alpha = thermal_diffusivity(configuration["constant_properties"])
        decay = math.exp(-alpha * (zeta / half_length) ** 2 * float(time_s))
        return ambient + amplitude * math.sin(zeta) / zeta * decay
    raise ValueError(case_id)


def initial_temperature(
    configuration: dict[str, Any],
    case: dict[str, Any],
    x_m: np.ndarray,
) -> np.ndarray:
    kind = case["initial"]["kind"]
    if kind == "uniform":
        return np.full_like(x_m, float(case["initial"]["temperature_c"]))
    if kind in ("steady_reference", "robin_even_eigenmode"):
        value = analytical_temperature_c(configuration, case, x_m, 0.0)
        if value is None:
            raise ValueError("Initial analytical field missing")
        return value
    raise ValueError(f"Unsupported initial field: {kind}")


def _bounds(case: dict[str, Any], initial: np.ndarray) -> tuple[float, float]:
    values = [float(np.min(initial)), float(np.max(initial))]
    for name in ("bottom_boundary", "top_boundary"):
        boundary = case[name]
        if boundary["kind"] == "surface_exchange":
            values.extend([
                float(boundary["gas_temperature_c"]),
                float(boundary["radiative_temperature_c"]),
            ])
    return min(values), max(values)


def run_case(
    configuration: dict[str, Any],
    case: dict[str, Any],
    cell_count: int | None = None,
    step_count: int | None = None,
    store_profiles: bool = True,
) -> dict[str, Any]:
    geometry = configuration["geometry"]
    properties = configuration["constant_properties"]
    exchange = configuration["surface_exchange"]
    discretization = configuration["discretization"]
    length = float(geometry["thickness_m"])
    n_cells = int(cell_count or discretization["reference_cells"])
    n_steps = int(step_count or discretization["reference_steps"])
    duration = float(case["duration_s"])
    dt = duration / n_steps
    dx = length / n_cells
    x_m = cell_centres(length, n_cells)
    temperature = initial_temperature(configuration, case, x_m)
    initial_enthalpy = sensible_enthalpy_j_m2(temperature, dx, properties)
    enthalpy = initial_enthalpy
    cumulative = {
        "bottom_convective_j_m2": 0.0,
        "bottom_radiative_j_m2": 0.0,
        "top_convective_j_m2": 0.0,
        "top_radiative_j_m2": 0.0,
    }
    maximum_increment_absolute = 0.0
    maximum_increment_relative = 0.0
    maximum_total_absolute = 0.0
    maximum_total_relative = 0.0
    maximum_surface_balance = 0.0
    maximum_nonlinear_residual = 0.0
    maximum_newton_iterations = 0
    total_line_search_reductions = 0
    maximum_component_ledger_residual = 0.0
    maximum_principle_violation = 0.0
    lower_bound, upper_bound = _bounds(case, temperature)
    mean_changes: list[float] = []
    histories: list[dict[str, Any]] = []
    profiles: list[dict[str, Any]] = []
    intervals = int(discretization["stored_history_intervals"])
    stored_steps = sorted(set(int(round(index * n_steps / intervals)) for index in range(intervals + 1)))
    stored_set = set(stored_steps)

    def face_states(current: np.ndarray) -> tuple[dict[str, Any], dict[str, Any]]:
        conductivity = float(properties["conductivity_w_m_k"])
        return (
            surface_state(current[0], dx, conductivity, case["bottom_boundary"], exchange),
            surface_state(current[-1], dx, conductivity, case["top_boundary"], exchange),
        )

    def store(step: int, current_time: float, current: np.ndarray, current_enthalpy: float) -> None:
        bottom, top = face_states(current)
        exact = analytical_temperature_c(configuration, case, x_m, current_time)
        exact_mean = analytical_mean_temperature_c(configuration, case, current_time)
        field_linf = None if exact is None else float(np.max(np.abs(current - exact)))
        field_rms = None if exact is None else float(np.sqrt(np.mean((current - exact) ** 2)))
        cumulative_total = float(sum(cumulative.values()))
        row = {
            "case_id": case["id"],
            "step": int(step),
            "time_s": float(current_time),
            "mean_temperature_c": float(np.mean(current)),
            "minimum_temperature_c": float(np.min(current)),
            "maximum_temperature_c": float(np.max(current)),
            "bottom_cell_temperature_c": float(current[0]),
            "top_cell_temperature_c": float(current[-1]),
            "bottom_surface_temperature_c": float(bottom["surface_temperature_c"]),
            "top_surface_temperature_c": float(top["surface_temperature_c"]),
            "bottom_convective_inward_flux_w_m2": float(bottom["convective_inward_flux_w_m2"]),
            "bottom_radiative_inward_flux_w_m2": float(bottom["radiative_inward_flux_w_m2"]),
            "bottom_total_inward_flux_w_m2": float(bottom["total_inward_flux_w_m2"]),
            "top_convective_inward_flux_w_m2": float(top["convective_inward_flux_w_m2"]),
            "top_radiative_inward_flux_w_m2": float(top["radiative_inward_flux_w_m2"]),
            "top_total_inward_flux_w_m2": float(top["total_inward_flux_w_m2"]),
            "net_inward_flux_w_m2": float(bottom["total_inward_flux_w_m2"] + top["total_inward_flux_w_m2"]),
            "bottom_surface_balance_residual_w_m2": float(bottom["surface_balance_residual_w_m2"]),
            "top_surface_balance_residual_w_m2": float(top["surface_balance_residual_w_m2"]),
            "enthalpy_j_m2": float(current_enthalpy),
            "enthalpy_change_j_m2": float(current_enthalpy - initial_enthalpy),
            "cumulative_bottom_convective_j_m2": cumulative["bottom_convective_j_m2"],
            "cumulative_bottom_radiative_j_m2": cumulative["bottom_radiative_j_m2"],
            "cumulative_top_convective_j_m2": cumulative["top_convective_j_m2"],
            "cumulative_top_radiative_j_m2": cumulative["top_radiative_j_m2"],
            "cumulative_total_inward_heat_j_m2": cumulative_total,
            "total_energy_residual_j_m2": float(current_enthalpy - initial_enthalpy - cumulative_total),
            "analytical_mean_temperature_c": exact_mean,
            "mean_temperature_error_k": None if exact_mean is None else float(np.mean(current) - exact_mean),
            "field_linf_error_k": field_linf,
            "field_rms_error_k": field_rms,
        }
        histories.append(row)
        if store_profiles:
            profiles.append({
                "case_id": case["id"],
                "step": int(step),
                "time_s": float(current_time),
                "x_m": [float(value) for value in x_m],
                "depth_from_top_m": [float(length - value) for value in x_m],
                "temperature_c": [float(value) for value in current],
                "analytical_temperature_c": None if exact is None else [float(value) for value in exact],
            })

    store(0, 0.0, temperature, enthalpy)
    previous_mean = float(np.mean(temperature))
    for step in range(1, n_steps + 1):
        updated, diagnostics = backward_euler_step(
            temperature, dt, dx, properties,
            case["bottom_boundary"], case["top_boundary"], exchange,
        )
        updated_enthalpy = sensible_enthalpy_j_m2(updated, dx, properties)
        bottom = diagnostics["bottom"]
        top = diagnostics["top"]
        increments = {
            "bottom_convective_j_m2": dt * float(bottom["convective_inward_flux_w_m2"]),
            "bottom_radiative_j_m2": dt * float(bottom["radiative_inward_flux_w_m2"]),
            "top_convective_j_m2": dt * float(top["convective_inward_flux_w_m2"]),
            "top_radiative_j_m2": dt * float(top["radiative_inward_flux_w_m2"]),
        }
        heat_increment = float(sum(increments.values()))
        enthalpy_increment = updated_enthalpy - enthalpy
        increment_residual = enthalpy_increment - heat_increment
        increment_relative = abs(increment_residual) / max(1.0, abs(enthalpy_increment), abs(heat_increment))
        maximum_increment_absolute = max(maximum_increment_absolute, abs(increment_residual))
        maximum_increment_relative = max(maximum_increment_relative, increment_relative)
        for name, value in increments.items():
            cumulative[name] += value
        cumulative_total = float(sum(cumulative.values()))
        total_residual = updated_enthalpy - initial_enthalpy - cumulative_total
        total_relative = abs(total_residual) / max(
            1.0, abs(updated_enthalpy - initial_enthalpy), abs(cumulative_total)
        )
        maximum_total_absolute = max(maximum_total_absolute, abs(total_residual))
        maximum_total_relative = max(maximum_total_relative, total_relative)
        explicit_component_sum = (
            cumulative["bottom_convective_j_m2"]
            + cumulative["bottom_radiative_j_m2"]
            + cumulative["top_convective_j_m2"]
            + cumulative["top_radiative_j_m2"]
        )
        maximum_component_ledger_residual = max(
            maximum_component_ledger_residual,
            abs(cumulative_total - explicit_component_sum),
        )
        maximum_surface_balance = max(
            maximum_surface_balance,
            abs(float(bottom["surface_balance_residual_w_m2"])),
            abs(float(top["surface_balance_residual_w_m2"])),
        )
        maximum_nonlinear_residual = max(
            maximum_nonlinear_residual,
            float(diagnostics["maximum_residual_w_m2"]),
        )
        maximum_newton_iterations = max(maximum_newton_iterations, int(diagnostics["iterations"]))
        total_line_search_reductions += int(diagnostics["line_search_reductions"])
        violation = max(0.0, lower_bound - float(np.min(updated)), float(np.max(updated)) - upper_bound)
        maximum_principle_violation = max(maximum_principle_violation, violation)
        current_mean = float(np.mean(updated))
        mean_changes.append(current_mean - previous_mean)
        previous_mean = current_mean
        temperature = updated
        enthalpy = updated_enthalpy
        if step in stored_set:
            store(step, step * dt, temperature, enthalpy)

    exact_terminal = analytical_temperature_c(configuration, case, x_m, duration)
    exact_mean = analytical_mean_temperature_c(configuration, case, duration)
    bottom, top = face_states(temperature)
    cumulative_total = float(sum(cumulative.values()))
    steady = steady_reference(configuration, case) if case["initial"]["kind"] == "steady_reference" else None
    field_linf = None if exact_terminal is None else float(np.max(np.abs(temperature - exact_terminal)))
    field_rms = None if exact_terminal is None else float(np.sqrt(np.mean((temperature - exact_terminal) ** 2)))
    summary = {
        "id": case["id"],
        "cell_count": n_cells,
        "step_count": n_steps,
        "dx_m": dx,
        "dt_s": dt,
        "duration_s": duration,
        "thermal_diffusivity_m2_s": thermal_diffusivity(properties),
        "initial_mean_temperature_c": float(np.mean(initial_temperature(configuration, case, x_m))),
        "final_mean_temperature_c": float(np.mean(temperature)),
        "final_minimum_temperature_c": float(np.min(temperature)),
        "final_maximum_temperature_c": float(np.max(temperature)),
        "final_bottom_cell_temperature_c": float(temperature[0]),
        "final_top_cell_temperature_c": float(temperature[-1]),
        "final_bottom_surface_temperature_c": float(bottom["surface_temperature_c"]),
        "final_top_surface_temperature_c": float(top["surface_temperature_c"]),
        "final_bottom_convective_inward_flux_w_m2": float(bottom["convective_inward_flux_w_m2"]),
        "final_bottom_radiative_inward_flux_w_m2": float(bottom["radiative_inward_flux_w_m2"]),
        "final_bottom_total_inward_flux_w_m2": float(bottom["total_inward_flux_w_m2"]),
        "final_top_convective_inward_flux_w_m2": float(top["convective_inward_flux_w_m2"]),
        "final_top_radiative_inward_flux_w_m2": float(top["radiative_inward_flux_w_m2"]),
        "final_top_total_inward_flux_w_m2": float(top["total_inward_flux_w_m2"]),
        "terminal_field_linf_error_k": field_linf,
        "terminal_field_rms_error_k": field_rms,
        "terminal_analytical_mean_temperature_c": exact_mean,
        "terminal_mean_error_k": None if exact_mean is None else float(np.mean(temperature) - exact_mean),
        "steady_reference": steady,
        "enthalpy_change_j_m2": float(enthalpy - initial_enthalpy),
        "cumulative_bottom_convective_j_m2": cumulative["bottom_convective_j_m2"],
        "cumulative_bottom_radiative_j_m2": cumulative["bottom_radiative_j_m2"],
        "cumulative_top_convective_j_m2": cumulative["top_convective_j_m2"],
        "cumulative_top_radiative_j_m2": cumulative["top_radiative_j_m2"],
        "cumulative_total_inward_heat_j_m2": cumulative_total,
        "maximum_increment_energy_residual_absolute_j_m2": maximum_increment_absolute,
        "maximum_increment_energy_residual_relative": maximum_increment_relative,
        "maximum_total_energy_residual_absolute_j_m2": maximum_total_absolute,
        "maximum_total_energy_residual_relative": maximum_total_relative,
        "maximum_component_ledger_residual_j_m2": maximum_component_ledger_residual,
        "maximum_surface_balance_residual_w_m2": maximum_surface_balance,
        "maximum_nonlinear_residual_w_m2": maximum_nonlinear_residual,
        "maximum_newton_iterations": maximum_newton_iterations,
        "total_line_search_reductions": total_line_search_reductions,
        "maximum_principle_violation_k": maximum_principle_violation,
        "mean_temperature_changes_monotonic_nonnegative": all(value >= -1e-12 for value in mean_changes),
    }
    return {"summary": summary, "history": histories, "profiles": profiles}


def observed_orders(rows: list[dict[str, Any]]) -> list[float]:
    values = []
    for coarse, fine in zip(rows, rows[1:]):
        values.append(
            math.log(float(coarse["linf_error_k"]) / float(fine["linf_error_k"]))
            / math.log(float(fine["resolution"]) / float(coarse["resolution"]))
        )
    return values


def spatial_operator_refinement(configuration: dict[str, Any]) -> dict[str, Any]:
    case = next(item for item in configuration["cases"] if item["id"] == configuration["discretization"]["space_refinement_case"])
    length = float(configuration["geometry"]["thickness_m"])
    properties = configuration["constant_properties"]
    conductivity = float(properties["conductivity_w_m_k"])
    volumetric = float(properties["density_kg_m3"]) * float(properties["specific_heat_j_kg_k"])
    h_value = float(case["top_boundary"]["h_w_m2_k"])
    ambient = float(case["initial"]["ambient_temperature_c"])
    duration = float(case["duration_s"])
    rows = []
    for n_cells in configuration["discretization"]["space_refinement_cells"]:
        n_cells = int(n_cells)
        dx = length / n_cells
        x_m = cell_centres(length, n_cells)
        initial = initial_temperature(configuration, case, x_m) - ambient
        matrix = np.zeros((n_cells, n_cells), dtype=float)
        internal = conductivity / dx
        for index in range(n_cells - 1):
            matrix[index, index] += internal
            matrix[index + 1, index + 1] += internal
            matrix[index, index + 1] -= internal
            matrix[index + 1, index] -= internal
        effective_surface = 1.0 / (1.0 / h_value + dx / (2.0 * conductivity))
        matrix[0, 0] += effective_surface
        matrix[-1, -1] += effective_surface
        rates, vectors = np.linalg.eigh(matrix / (volumetric * dx))
        terminal = ambient + vectors @ (np.exp(-rates * duration) * (vectors.T @ initial))
        exact = analytical_temperature_c(configuration, case, x_m, duration)
        error = float(np.max(np.abs(terminal - exact)))
        rows.append({
            "case_id": case["id"],
            "cell_count": n_cells,
            "resolution": n_cells,
            "dx_m": dx,
            "linf_error_k": error,
            "method": "semi_discrete_symmetric_eigendecomposition_exact_time",
        })
    return {"rows": rows, "observed_orders": observed_orders(rows)}


def time_refinement(configuration: dict[str, Any]) -> dict[str, Any]:
    case = next(item for item in configuration["cases"] if item["id"] == configuration["discretization"]["time_refinement_case"])
    n_cells = int(configuration["discretization"]["time_refinement_cells"])
    rows = []
    for steps in configuration["discretization"]["time_refinement_steps"]:
        run = run_case(configuration, case, cell_count=n_cells, step_count=int(steps), store_profiles=False)
        rows.append({
            "case_id": case["id"],
            "step_count": int(steps),
            "resolution": int(steps),
            "dt_s": float(case["duration_s"]) / int(steps),
            "linf_error_k": run["summary"]["terminal_field_linf_error_k"],
        })
    return {"rows": rows, "observed_orders": observed_orders(rows)}


def surface_exchange_sensitivity(configuration: dict[str, Any]) -> list[dict[str, Any]]:
    base = next(item for item in configuration["cases"] if item["id"] == configuration["discretization"]["sensitivity_case"])
    rows = []
    definitions = [
        ("top_h_w_m2_k", configuration["discretization"]["convection_h_top_w_m2_k"]),
        ("top_emissivity", configuration["discretization"]["emissivity_top"]),
    ]
    for parameter, values in definitions:
        for value in values:
            case = copy.deepcopy(base)
            if parameter == "top_h_w_m2_k":
                case["top_boundary"]["h_w_m2_k"] = float(value)
            else:
                case["top_boundary"]["emissivity"] = float(value)
            run = run_case(
                configuration,
                case,
                step_count=int(configuration["discretization"]["sensitivity_steps"]),
                store_profiles=False,
            )
            summary = run["summary"]
            radiative = summary["cumulative_bottom_radiative_j_m2"] + summary["cumulative_top_radiative_j_m2"]
            total = summary["cumulative_total_inward_heat_j_m2"]
            rows.append({
                "parameter": parameter,
                "value": float(value),
                "top_h_w_m2_k": float(case["top_boundary"]["h_w_m2_k"]),
                "top_emissivity": float(case["top_boundary"]["emissivity"]),
                "final_mean_temperature_c": summary["final_mean_temperature_c"],
                "final_top_cell_temperature_c": summary["final_top_cell_temperature_c"],
                "final_top_surface_temperature_c": summary["final_top_surface_temperature_c"],
                "enthalpy_change_j_m2": summary["enthalpy_change_j_m2"],
                "cumulative_convective_j_m2": summary["cumulative_bottom_convective_j_m2"] + summary["cumulative_top_convective_j_m2"],
                "cumulative_radiative_j_m2": radiative,
                "cumulative_top_convective_j_m2": summary["cumulative_top_convective_j_m2"],
                "cumulative_top_radiative_j_m2": summary["cumulative_top_radiative_j_m2"],
                "cumulative_total_inward_heat_j_m2": total,
                "radiative_fraction_of_net_input": radiative / total,
                "maximum_energy_residual_relative": summary["maximum_total_energy_residual_relative"],
            })
    return rows
