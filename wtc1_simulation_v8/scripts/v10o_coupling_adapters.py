from __future__ import annotations

import copy
import hashlib
import json
import math
import re
from typing import Any


SCHEMA_VERSION = "1.0.0"
SCENARIO_CLASS = "SYNTHETIC_SOFTWARE_CONTROL"
EPISTEMIC_CLASS = "ALGEBRAIC_SENTINEL_NOT_HISTORICAL"
INTERFACE_ORDER = [
    "I01_KINEMATICS_TO_DAMAGE",
    "I02_DAMAGE_TO_FIRE",
    "I03_DAMAGE_TO_COLD_STRUCTURE",
    "I04_FIRE_TO_THERMAL_SOLIDS",
    "I05_THERMAL_TO_INITIATION",
    "I06_COLD_STATE_TO_INITIATION",
    "I07_INITIATION_TO_PROPAGATION",
    "I08_PROPAGATION_TO_ENSEMBLE",
    "I09_ALL_VALIDATED_STATES_TO_BLENDER",
]


class ContractError(ValueError):
    pass


def _field(type_name: str, unit: str | None = None, **constraints: Any) -> dict[str, Any]:
    value: dict[str, Any] = {"type": type_name, "required": True}
    if unit is not None:
        value["unit"] = unit
    value.update(constraints)
    return value


CONTRACTS: dict[str, dict[str, Any]] = {
    "I01_KINEMATICS_TO_DAMAGE": {
        "producer": "IMPACT_KINEMATICS",
        "consumer": "IMPACT_DAMAGE_STATE",
        "schema_id": "impact_kinematics_v1",
        "physical_ready": False,
        "payload_fields": {
            "mass_kg": _field("number", "kg", minimum=0.0),
            "velocity_vector_m_s": _field("vector3_number", "m/s"),
            "attitude_rad": _field("vector3_number", "rad"),
            "contact_time_s": _field("number", "s", minimum=0.0),
            "kinetic_energy_J": _field("number", "J", minimum=0.0),
            "trajectory_frame": _field("string"),
            "module_status": _field("string", enum=["CONTROL_ZERO_INPUT"]),
            "provenance": _field("object"),
        },
    },
    "I02_DAMAGE_TO_FIRE": {
        "producer": "IMPACT_DAMAGE_STATE",
        "consumer": "FIRE_GAS_PHASE",
        "schema_id": "impact_damage_state_v1",
        "physical_ready": False,
        "payload_fields": {
            "member_states": _field("array_object"),
            "opening_polygons_m": _field("array"),
            "debris_mass_kg": _field("number", "kg", minimum=0.0),
            "fuel_mass_kg": _field("number", "kg", minimum=0.0),
            "damage_uncertainty": _field("object"),
            "module_status": _field("string", enum=["CONTROL_ZERO_DAMAGE"]),
            "provenance": _field("object"),
        },
    },
    "I03_DAMAGE_TO_COLD_STRUCTURE": {
        "producer": "IMPACT_DAMAGE_STATE",
        "consumer": "COLD_GRAVITY_REDISTRIBUTION",
        "schema_id": "impact_damage_state_v1",
        "physical_ready": False,
        "payload_fields": {
            "member_states": _field("array_object"),
            "opening_polygons_m": _field("array"),
            "debris_mass_kg": _field("number", "kg", minimum=0.0),
            "fuel_mass_kg": _field("number", "kg", minimum=0.0),
            "damage_uncertainty": _field("object"),
            "module_status": _field("string", enum=["CONTROL_ZERO_DAMAGE"]),
            "provenance": _field("object"),
        },
    },
    "I04_FIRE_TO_THERMAL_SOLIDS": {
        "producer": "FIRE_GAS_PHASE",
        "consumer": "THERMAL_SOLIDS",
        "schema_id": "fire_gas_history_v1",
        "physical_ready": False,
        "payload_fields": {
            "time_s": _field("array_number", "s"),
            "gas_temperature_K": _field("array_number", "K"),
            "incident_heat_flux_W_m2": _field("array_number", "W/m2"),
            "convection_coefficient_W_m2K": _field("array_number", "W/(m2 K)"),
            "fire_state": _field("string", enum=["CONTROL_NO_FIRE"]),
            "module_status": _field("string", enum=["CONTROL_ZERO_FIRE_LOAD"]),
            "provenance": _field("object"),
        },
    },
    "I05_THERMAL_TO_INITIATION": {
        "producer": "THERMAL_SOLIDS",
        "consumer": "THERMOMECHANICAL_INITIATION",
        "schema_id": "thermal_member_history_v1",
        "physical_ready": False,
        "payload_fields": {
            "time_s": _field("array_number", "s"),
            "member_histories": _field("array_object"),
            "reference_temperature_K": _field("number", "K", minimum=0.0),
            "thermal_state": _field("string", enum=["CONTROL_NO_TEMPERATURE_INCREMENT"]),
            "module_status": _field("string", enum=["CONTROL_THERMAL_NEUTRAL"]),
            "provenance": _field("object"),
        },
    },
    "I06_COLD_STATE_TO_INITIATION": {
        "producer": "COLD_GRAVITY_REDISTRIBUTION",
        "consumer": "THERMOMECHANICAL_INITIATION",
        "schema_id": "cold_structural_state_v1",
        "physical_ready": False,
        "payload_fields": {
            "node_displacements_m": _field("object", "m"),
            "element_forces_N": _field("object", "N"),
            "connection_state": _field("object"),
            "boundary_state": _field("string", enum=["CONTROL_UNASSIGNED"]),
            "equilibrium_residual_N": _field("number", "N", minimum=0.0),
            "structural_state": _field("string", enum=["CONTROL_ZERO_INCREMENT"]),
            "module_status": _field("string", enum=["CONTROL_COLD_NEUTRAL"]),
            "provenance": _field("object"),
        },
    },
    "I07_INITIATION_TO_PROPAGATION": {
        "producer": "THERMOMECHANICAL_INITIATION",
        "consumer": "PROPAGATION_OR_ARREST",
        "schema_id": "initiation_state_v1",
        "physical_ready": False,
        "payload_fields": {
            "time_s": _field("number", "s", minimum=0.0),
            "failed_members": _field("array_string"),
            "displacements_m": _field("object", "m"),
            "velocities_m_s": _field("object", "m/s"),
            "participating_mass_kg": _field("number", "kg", minimum=0.0),
            "energy_J": _field("number", "J", minimum=0.0),
            "instability_time_s_or_null": _field("nullable_number", "s"),
            "initiation_label": _field("string", enum=["CONTROL_NO_INITIATION"]),
            "module_status": _field("string", enum=["CONTROL_INITIATION_NEUTRAL"]),
            "provenance": _field("object"),
        },
    },
    "I08_PROPAGATION_TO_ENSEMBLE": {
        "producer": "PROPAGATION_OR_ARREST",
        "consumer": "UNCERTAINTY_ENSEMBLE",
        "schema_id": "propagation_outcome_v1",
        "physical_ready": False,
        "payload_fields": {
            "case_id": _field("string"),
            "outcome_label": _field("string", enum=["CONTROL_NO_PROPAGATION"]),
            "arrest_story_or_null": _field("nullable_number"),
            "energy_residual_J": _field("number", "J", minimum=0.0),
            "momentum_residual_kg_m_s": _field("number", "kg m/s", minimum=0.0),
            "validation_flags": _field("array_string"),
            "fraction_is_historical_probability": _field("boolean", enum=[False]),
            "module_status": _field("string", enum=["CONTROL_PROPAGATION_NEUTRAL"]),
            "parameter_provenance": _field("object"),
        },
    },
    "I09_ALL_VALIDATED_STATES_TO_BLENDER": {
        "producer": "VALIDATION_RELEASE_BUS",
        "consumer": "BLENDER_VISUALIZATION",
        "schema_id": "visualization_state_v1",
        "physical_ready": False,
        "payload_fields": {
            "source_module": _field("string"),
            "state_id": _field("string"),
            "time_s": _field("number", "s", minimum=0.0),
            "object_transforms": _field("array_object"),
            "display_class": _field("string", enum=["CONTROL_CARD_ONLY"]),
            "state_validation_status": _field("string", enum=["CONTROL_PASS_SOFTWARE_ONLY"]),
            "uncertainty_label": _field("string"),
            "source_hashes": _field("object"),
            "module_status": _field("string", enum=["CONTROL_VISUALIZATION_NOT_RENDERED"]),
            "provenance": _field("object"),
        },
    },
}


def exported_contracts() -> dict[str, Any]:
    return {
        "contract_format": "V10O_SIMPLE_TYPED_SCHEMA_V1",
        "schema_version": SCHEMA_VERSION,
        "validator": "Python standard-library validator in v10o_coupling_adapters.py",
        "common_envelope_required": [
            "record_id",
            "scenario_id",
            "scenario_class",
            "epistemic_class",
            "schema_id",
            "schema_version",
            "validation_status",
            "physical_credit",
            "source_hashes",
            "units",
            "payload",
        ],
        "interfaces": copy.deepcopy(CONTRACTS),
        "scope_warning": "A schema PASS establishes syntax, units, declared invariants and provenance carriage only. It does not validate physical input values or historical causality.",
    }


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def _type_matches(type_name: str, value: Any) -> bool:
    if type_name == "number":
        return _is_number(value)
    if type_name == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if type_name == "boolean":
        return isinstance(value, bool)
    if type_name == "string":
        return isinstance(value, str) and bool(value)
    if type_name == "object":
        return isinstance(value, dict)
    if type_name == "array":
        return isinstance(value, list)
    if type_name == "array_number":
        return isinstance(value, list) and all(_is_number(item) for item in value)
    if type_name == "array_string":
        return isinstance(value, list) and all(isinstance(item, str) for item in value)
    if type_name == "array_object":
        return isinstance(value, list) and all(isinstance(item, dict) for item in value)
    if type_name == "vector3_number":
        return isinstance(value, list) and len(value) == 3 and all(_is_number(item) for item in value)
    if type_name == "nullable_number":
        return value is None or _is_number(value)
    raise ContractError(f"Unknown contract type: {type_name}")


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ContractError(message)


def _validate_source_hashes(value: Any) -> None:
    _require(isinstance(value, dict) and bool(value), "source_hashes must be a non-empty object")
    for role, digest in value.items():
        _require(isinstance(role, str) and bool(role), "source hash role must be non-empty")
        _require(isinstance(digest, str) and bool(re.fullmatch(r"[0-9a-f]{64}", digest)), f"invalid SHA-256 for {role}")


def _validate_monotone(values: list[float], name: str) -> None:
    _require(bool(values), f"{name} must not be empty")
    for left, right in zip(values, values[1:]):
        _require(float(right) >= float(left), f"{name} must be monotone non-decreasing")


def _cross_field_validation(schema_id: str, payload: dict[str, Any]) -> None:
    if schema_id == "impact_kinematics_v1":
        velocity_squared = sum(float(value) ** 2 for value in payload["velocity_vector_m_s"])
        expected_energy = 0.5 * float(payload["mass_kg"]) * velocity_squared
        tolerance = max(1e-9, abs(expected_energy) * 1e-12)
        _require(abs(float(payload["kinetic_energy_J"]) - expected_energy) <= tolerance, "kinetic energy invariant failed")
    elif schema_id == "impact_damage_state_v1":
        if payload["module_status"] == "CONTROL_ZERO_DAMAGE":
            _require(payload["member_states"] == [], "zero-damage control must have no member states")
            _require(payload["opening_polygons_m"] == [], "zero-damage control must have no openings")
            _require(float(payload["debris_mass_kg"]) == 0.0, "zero-damage control must have zero debris")
            _require(float(payload["fuel_mass_kg"]) == 0.0, "zero-damage control must have zero fuel")
    elif schema_id == "fire_gas_history_v1":
        times = payload["time_s"]
        _validate_monotone(times, "time_s")
        length = len(times)
        _require(len(payload["gas_temperature_K"]) == length, "gas temperature/time length mismatch")
        _require(len(payload["incident_heat_flux_W_m2"]) == length, "heat flux/time length mismatch")
        _require(len(payload["convection_coefficient_W_m2K"]) == length, "convection/time length mismatch")
        _require(all(float(value) >= 0.0 for value in payload["gas_temperature_K"]), "negative absolute temperature")
        if payload["fire_state"] == "CONTROL_NO_FIRE":
            _require(all(float(value) == 0.0 for value in payload["incident_heat_flux_W_m2"]), "no-fire control requires zero heat flux")
    elif schema_id == "thermal_member_history_v1":
        _validate_monotone(payload["time_s"], "time_s")
        _require(float(payload["reference_temperature_K"]) >= 0.0, "negative absolute reference temperature")
        if payload["thermal_state"] == "CONTROL_NO_TEMPERATURE_INCREMENT":
            _require(payload["member_histories"] == [], "thermal neutral control must have no member histories")
    elif schema_id == "cold_structural_state_v1":
        if payload["structural_state"] == "CONTROL_ZERO_INCREMENT":
            _require(payload["node_displacements_m"] == {}, "cold neutral control requires no node displacement assignment")
            _require(payload["element_forces_N"] == {}, "cold neutral control requires no element force assignment")
            _require(float(payload["equilibrium_residual_N"]) == 0.0, "cold neutral residual must be zero")
    elif schema_id == "initiation_state_v1":
        if payload["initiation_label"] == "CONTROL_NO_INITIATION":
            _require(payload["failed_members"] == [], "no-initiation control must have no failed members")
            _require(payload["instability_time_s_or_null"] is None, "no-initiation control instability time must be null")
            _require(float(payload["participating_mass_kg"]) == 0.0, "no-initiation control participating mass must be zero")
            _require(float(payload["energy_J"]) == 0.0, "no-initiation control energy must be zero")
    elif schema_id == "propagation_outcome_v1":
        if payload["outcome_label"] == "CONTROL_NO_PROPAGATION":
            _require(payload["arrest_story_or_null"] is None, "control outcome must not invent an arrest story")
            _require(float(payload["energy_residual_J"]) == 0.0, "control energy residual must be zero")
            _require(float(payload["momentum_residual_kg_m_s"]) == 0.0, "control momentum residual must be zero")
            _require(payload["fraction_is_historical_probability"] is False, "control fraction cannot be a historical probability")
    elif schema_id == "visualization_state_v1":
        if payload["display_class"] == "CONTROL_CARD_ONLY":
            _require(payload["object_transforms"] == [], "card-only control must have no object transforms")


def validate_record(interface_id: str, record: dict[str, Any]) -> dict[str, Any]:
    if interface_id not in CONTRACTS:
        raise ContractError(f"Unknown interface: {interface_id}")
    contract = CONTRACTS[interface_id]
    common = exported_contracts()["common_envelope_required"]
    missing_common = [field for field in common if field not in record]
    _require(not missing_common, f"missing common fields: {missing_common}")
    _require(record["schema_id"] == contract["schema_id"], "schema_id does not match interface")
    _require(record["schema_version"] == SCHEMA_VERSION, "schema_version mismatch")
    _require(record["scenario_class"] == SCENARIO_CLASS, "only the predeclared software-control class is valid in V10O")
    _require(record["epistemic_class"] == EPISTEMIC_CLASS, "epistemic class mismatch")
    _require(record["validation_status"] == "CONTROL_PASS_SOFTWARE_ONLY", "validation status mismatch")
    _require(record["physical_credit"] == "NONE", "V10O record cannot carry physical credit")
    _require(isinstance(record["record_id"], str) and bool(record["record_id"]), "record_id missing")
    _require(isinstance(record["scenario_id"], str) and bool(record["scenario_id"]), "scenario_id missing")
    _validate_source_hashes(record["source_hashes"])
    _require(isinstance(record["units"], dict), "units must be an object")
    _require(isinstance(record["payload"], dict), "payload must be an object")
    payload = record["payload"]
    for field_name, specification in contract["payload_fields"].items():
        _require(field_name in payload, f"missing required payload field: {field_name}")
        value = payload[field_name]
        _require(_type_matches(specification["type"], value), f"wrong type for {field_name}: expected {specification['type']}")
        if "unit" in specification:
            _require(record["units"].get(field_name) == specification["unit"], f"unit mismatch for {field_name}")
        if "minimum" in specification and value is not None:
            _require(float(value) >= float(specification["minimum"]), f"value below minimum for {field_name}")
        if "enum" in specification:
            _require(value in specification["enum"], f"value outside enum for {field_name}")
    _cross_field_validation(contract["schema_id"], payload)
    return {
        "interface_id": interface_id,
        "schema_id": contract["schema_id"],
        "status": "PASS_SOFTWARE_CONTRACT_ONLY",
        "physical_ready": False,
        "physical_credit": "NONE",
        "required_payload_field_count": len(contract["payload_fields"]),
        "unit_field_count": sum("unit" in item for item in contract["payload_fields"].values()),
    }


def _units(interface_id: str) -> dict[str, str]:
    return {
        field_name: specification["unit"]
        for field_name, specification in CONTRACTS[interface_id]["payload_fields"].items()
        if "unit" in specification
    }


def _record(
    interface_id: str,
    scenario_id: str,
    source_hashes: dict[str, str],
    payload: dict[str, Any],
) -> dict[str, Any]:
    return {
        "record_id": f"{scenario_id}:{interface_id}",
        "scenario_id": scenario_id,
        "scenario_class": SCENARIO_CLASS,
        "epistemic_class": EPISTEMIC_CLASS,
        "schema_id": CONTRACTS[interface_id]["schema_id"],
        "schema_version": SCHEMA_VERSION,
        "validation_status": "CONTROL_PASS_SOFTWARE_ONLY",
        "physical_credit": "NONE",
        "source_hashes": copy.deepcopy(source_hashes),
        "units": _units(interface_id),
        "payload": payload,
    }


def _provenance(interface_id: str) -> dict[str, Any]:
    return {
        "kind": "SYNTHETIC_SOFTWARE_CONTROL",
        "interface_id": interface_id,
        "historical_event_claim": False,
        "values_are_wtc_properties": False,
        "purpose": "exercise serialization, unit, invariant, branch, join and stop-status handling",
    }


def build_control_records(control: dict[str, Any], source_hashes: dict[str, str]) -> dict[str, dict[str, Any]]:
    scenario_id = control["scenario_id"]
    mass = float(control["input_mass_kg"])
    velocity = [float(value) for value in control["input_velocity_vector_m_s"]]
    energy = 0.5 * mass * sum(value * value for value in velocity)
    temperature = float(control["reference_temperature_K"])
    records: dict[str, dict[str, Any]] = {}

    records["I01_KINEMATICS_TO_DAMAGE"] = _record(
        "I01_KINEMATICS_TO_DAMAGE",
        scenario_id,
        source_hashes,
        {
            "mass_kg": mass,
            "velocity_vector_m_s": velocity,
            "attitude_rad": [float(value) for value in control["input_attitude_rad"]],
            "contact_time_s": 0.0,
            "kinetic_energy_J": energy,
            "trajectory_frame": "SYNTHETIC_ZERO_FRAME",
            "module_status": "CONTROL_ZERO_INPUT",
            "provenance": _provenance("I01_KINEMATICS_TO_DAMAGE"),
        },
    )
    damage_payload = {
        "member_states": [],
        "opening_polygons_m": [],
        "debris_mass_kg": 0.0,
        "fuel_mass_kg": 0.0,
        "damage_uncertainty": {"class": "CONTROL_ONLY", "historical_damage": None},
        "module_status": "CONTROL_ZERO_DAMAGE",
    }
    for interface_id in ("I02_DAMAGE_TO_FIRE", "I03_DAMAGE_TO_COLD_STRUCTURE"):
        payload = copy.deepcopy(damage_payload)
        payload["provenance"] = _provenance(interface_id)
        records[interface_id] = _record(interface_id, scenario_id, source_hashes, payload)
    records["I04_FIRE_TO_THERMAL_SOLIDS"] = _record(
        "I04_FIRE_TO_THERMAL_SOLIDS",
        scenario_id,
        source_hashes,
        {
            "time_s": [0.0],
            "gas_temperature_K": [temperature],
            "incident_heat_flux_W_m2": [0.0],
            "convection_coefficient_W_m2K": [0.0],
            "fire_state": "CONTROL_NO_FIRE",
            "module_status": "CONTROL_ZERO_FIRE_LOAD",
            "provenance": _provenance("I04_FIRE_TO_THERMAL_SOLIDS"),
        },
    )
    records["I05_THERMAL_TO_INITIATION"] = _record(
        "I05_THERMAL_TO_INITIATION",
        scenario_id,
        source_hashes,
        {
            "time_s": [0.0],
            "member_histories": [],
            "reference_temperature_K": temperature,
            "thermal_state": "CONTROL_NO_TEMPERATURE_INCREMENT",
            "module_status": "CONTROL_THERMAL_NEUTRAL",
            "provenance": _provenance("I05_THERMAL_TO_INITIATION"),
        },
    )
    records["I06_COLD_STATE_TO_INITIATION"] = _record(
        "I06_COLD_STATE_TO_INITIATION",
        scenario_id,
        source_hashes,
        {
            "node_displacements_m": {},
            "element_forces_N": {},
            "connection_state": {},
            "boundary_state": "CONTROL_UNASSIGNED",
            "equilibrium_residual_N": float(control["incremental_force_N"]),
            "structural_state": "CONTROL_ZERO_INCREMENT",
            "module_status": "CONTROL_COLD_NEUTRAL",
            "provenance": _provenance("I06_COLD_STATE_TO_INITIATION"),
        },
    )
    records["I07_INITIATION_TO_PROPAGATION"] = _record(
        "I07_INITIATION_TO_PROPAGATION",
        scenario_id,
        source_hashes,
        {
            "time_s": 0.0,
            "failed_members": [],
            "displacements_m": {},
            "velocities_m_s": {},
            "participating_mass_kg": 0.0,
            "energy_J": 0.0,
            "instability_time_s_or_null": None,
            "initiation_label": "CONTROL_NO_INITIATION",
            "module_status": "CONTROL_INITIATION_NEUTRAL",
            "provenance": _provenance("I07_INITIATION_TO_PROPAGATION"),
        },
    )
    records["I08_PROPAGATION_TO_ENSEMBLE"] = _record(
        "I08_PROPAGATION_TO_ENSEMBLE",
        scenario_id,
        source_hashes,
        {
            "case_id": scenario_id,
            "outcome_label": "CONTROL_NO_PROPAGATION",
            "arrest_story_or_null": None,
            "energy_residual_J": 0.0,
            "momentum_residual_kg_m_s": 0.0,
            "validation_flags": ["SOFTWARE_CONTROL_ONLY", "NOT_HISTORICAL_NONCOLLAPSE"],
            "fraction_is_historical_probability": False,
            "module_status": "CONTROL_PROPAGATION_NEUTRAL",
            "parameter_provenance": _provenance("I08_PROPAGATION_TO_ENSEMBLE"),
        },
    )
    records["I09_ALL_VALIDATED_STATES_TO_BLENDER"] = _record(
        "I09_ALL_VALIDATED_STATES_TO_BLENDER",
        scenario_id,
        source_hashes,
        {
            "source_module": "VALIDATION_RELEASE_BUS",
            "state_id": f"{scenario_id}:CONTROL_CARD",
            "time_s": 0.0,
            "object_transforms": [],
            "display_class": "CONTROL_CARD_ONLY",
            "state_validation_status": "CONTROL_PASS_SOFTWARE_ONLY",
            "uncertainty_label": "SYNTHETIC SOFTWARE CONTROL — NO WTC EVENT OR PHYSICAL CONCLUSION",
            "source_hashes": copy.deepcopy(source_hashes),
            "module_status": "CONTROL_VISUALIZATION_NOT_RENDERED",
            "provenance": _provenance("I09_ALL_VALIDATED_STATES_TO_BLENDER"),
        },
    )
    return records


def missing_field_negative(interface_id: str, record: dict[str, Any]) -> tuple[dict[str, Any], str]:
    mutated = copy.deepcopy(record)
    field_name = next(iter(CONTRACTS[interface_id]["payload_fields"]))
    del mutated["payload"][field_name]
    return mutated, field_name


def canonical_digest(value: Any) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
