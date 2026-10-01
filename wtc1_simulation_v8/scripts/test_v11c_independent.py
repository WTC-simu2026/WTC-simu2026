"""Independent scalar analytical checks of the V11C kernel; no tower verdict.

Only prints JSON to stdout. All expected values use closed-form equations,
not the panel assembly or runner's own test helpers.
"""
from __future__ import annotations

import json
import math
import numpy as np

from v11c_panel_model import UnresolvedEquilibrium, solve_terms, term


def run_checks():
    checks = []

    def check(name, okay, evidence):
        checks.append({"name": name, "pass": bool(okay), "evidence": evidence})

    def close(x, y):
        return math.isclose(float(x), float(y), rel_tol=1e-10, abs_tol=1e-10)

    def audit(name, result):
        check(name + "_equilibrium", result["equilibrium_residual"] < 1e-10,
              result["equilibrium_residual"])
        check(name + "_thermal_state_energy_identity", result["energy_identity_residual"] < 1e-10,
              result["energy_identity_residual"])

    stiffness, eigenextension = 1000.0, 0.02
    bar = term("BAR", "bar", [0, 1], [-1, 1], stiffness, eigenextension)
    free = solve_terms(2, [bar], [0., 0.], {0: 0.})
    check("free_thermal_bar_extension_and_zero_force",
          close(free["u"][1], eigenextension) and close(free["terms"][0]["force_N"], 0),
          {"extension": float(free["u"][1]), "force": free["terms"][0]["force_N"]})
    audit("free_bar", free)

    restrained = solve_terms(2, [bar], [0., 0.], {0: 0., 1: 0.})
    check("restrained_thermal_bar_force_energy_reaction",
          close(restrained["terms"][0]["force_N"], -20.)
          and close(restrained["strain_energy_J"], 0.2)
          and np.allclose(restrained["reaction"], [20., -20.], rtol=1e-10),
          {"force": restrained["terms"][0]["force_N"], "energy": restrained["strain_energy_J"],
           "reaction": restrained["reaction"].tolist()})
    audit("restrained_bar", restrained)

    imposed = solve_terms(2, [bar], [0., 0.], {0: 0.01, 1: 0.04})
    check("thermal_bar_relative_imposed_displacement",
          close(imposed["terms"][0]["force_N"], 10.), imposed["terms"][0]["force_N"])
    audit("imposed_bar", imposed)

    series_k = 400.0
    series = solve_terms(2, [bar, term("SPRING", "spring", [1], [1], series_k)],
                         [0., 0.], {0: 0.})
    force_expected = -eigenextension / (1/stiffness + 1/series_k)
    displacement_expected = eigenextension * stiffness/(stiffness+series_k)
    check("thermal_bar_finite_end_spring_series_formula",
          close(series["terms"][0]["force_N"], force_expected)
          and close(series["u"][1], displacement_expected),
          {"force_N": series["terms"][0]["force_N"], "expected_N": force_expected,
           "u_m": float(series["u"][1]), "expected_m": displacement_expected})
    audit("series_thermal_bar", series)

    moved_anchor = solve_terms(1, [term("GROUND", "spring", [0], [1], 100., 0.03)], [2.])
    check("moving_support_spring_offset", close(moved_anchor["u"][0], 0.05)
          and close(moved_anchor["terms"][0]["force_N"], 2.)
          and close(moved_anchor["strain_energy_J"], 0.02),
          {"u_m": float(moved_anchor["u"][0]), "energy_J": moved_anchor["strain_energy_J"]})
    audit("moving_anchor", moved_anchor)

    ks, kc, kb, load = 200., 300., 600., -100.
    terms = [term("STEEL", "bar", [0, 1], [-1, 1], ks),
             term("SLAB", "slab", [2, 3], [-1, 1], kc, compression_only=True),
             term("BONDLEFT", "bond", [0, 2], [-1, 1], kb),
             term("BONDRIGHT", "bond", [1, 3], [-1, 1], kb)]
    composite = solve_terms(4, terms, [0., load, 0., 0.], {0: 0.})
    slab_effective = 1/(1/kc+2/kb)
    dx_expected = load/(ks+slab_effective)
    slab_force_expected = slab_effective*dx_expected
    check("finite_bond_two_line_compressed_exact_stiffness",
          close(composite["u"][1], dx_expected)
          and close(composite["terms"][1]["force_N"], slab_force_expected),
          {"u_m": float(composite["u"][1]), "expected_m": dx_expected,
           "slab_force_N": composite["terms"][1]["force_N"], "expected_N": slab_force_expected})
    check("finite_bond_end_slips_opposite_equal", close(composite["terms"][2]["extension_m"],
          -composite["terms"][3]["extension_m"])
          and close(abs(composite["terms"][2]["extension_m"]), abs(slab_force_expected/kb)),
          [composite["terms"][i]["extension_m"] for i in [2, 3]])
    audit("finite_bond_compressed", composite)

    tension = solve_terms(4, terms, [0., -load, 0., 0.], {0: 0.})
    check("unilateral_tension_opens_slab_and_unloads_bonds",
          close(tension["u"][1], -load/ks)
          and all(close(tension["terms"][i]["force_N"], 0.) for i in [1, 2, 3])
          and tension["terms"][1]["state"] == "OPEN_ZERO_TENSION",
          {"u_m": float(tension["u"][1]), "slab_state": tension["terms"][1]["state"],
           "forces_N": [t["force_N"] for t in tension["terms"]]})
    audit("finite_bond_tension", tension)

    released = solve_terms(4, [t for t in terms if t["id"] != "BONDLEFT"],
                           [0., load, 0., 0.], {0: 0.})
    check("single_bond_release_unloads_slab_and_remaining_bond",
          close(released["u"][1], load/ks)
          and all(close(t["force_N"], 0.) for t in released["terms"] if t["kind"] != "bar"),
          {"u_m": float(released["u"][1]), "forces_N": [t["force_N"] for t in released["terms"]]})
    audit("single_release", released)

    no_bonds_rejected = False
    try:
        solve_terms(4, terms[:2], [0., load, 0., 0.], {0: 0.})
    except UnresolvedEquilibrium as exc:
        no_bonds_rejected = str(exc)
    check("fully_disconnected_slab_rejected_not_hidden_stiffness", bool(no_bonds_rejected), no_bonds_rejected)

    heated = [dict(t) for t in terms]
    heated[1]["e0"] = 0.1
    compressed_thermal = solve_terms(4, heated, [0., 0., 0., 0.], {0: 0., 1: -0.2})
    expected_thermal_slab = (-0.2-0.1)/(1/kc+2/kb)
    check("finite_bond_slab_eigenextension_with_prescribed_steel_compression",
          close(compressed_thermal["terms"][1]["force_N"], expected_thermal_slab),
          {"force_N": compressed_thermal["terms"][1]["force_N"], "expected_N": expected_thermal_slab})
    audit("composite_imposed_thermal", compressed_thermal)

    for name, result in [("compression", composite), ("tension", tension), ("heated", compressed_thermal)]:
        slab = next(t for t in result["terms"] if t["kind"] == "slab")
        check("unilateral_law_" + name,
              close(slab["force_N"], slab["k"]*min(slab["extension_m"], 0.))
              and slab["force_N"] <= 0.,
              {"force_N": slab["force_N"], "extension_m": slab["extension_m"]})

    return {"suite": "INDEPENDENT_ANALYTICAL_V11C", "checks": checks,
            "passed": sum(c["pass"] for c in checks), "total": len(checks),
            "all_passed": all(c["pass"] for c in checks)}


if __name__ == "__main__":
    result = run_checks()
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["all_passed"] else 1)
