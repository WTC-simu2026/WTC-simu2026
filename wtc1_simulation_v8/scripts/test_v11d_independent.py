"""Independent, generic analytical checks for the V11D numerical primitives.

These are closed-form beam/spring checks, NOT validation of WTC construction,
connector strength, slab cracking, historical temperatures or collapse. SI
units; transverse displacement and load are positive upward, theta = dw/dx.

No panel configuration, state, registry, source file or result file is changed.
The public entry point is run() -> [{test, pass, evidence}, ...].
"""
from __future__ import annotations

import json
import numpy as np


def run():
    from v11d_panel_model import beam_load, beam_terms, solve_terms, term

    checks = []

    def check(name, operation):
        try:
            evidence = operation()
            checks.append({"test": "INDEPENDENT_GENERIC_" + name,
                           "pass": True, "evidence": evidence})
        except Exception as error:
            checks.append({"test": "INDEPENDENT_GENERIC_" + name,
                           "pass": False,
                           "evidence": {"exception": type(error).__name__,
                                        "message": str(error)}})

    def close(actual, expected, rtol=2e-8, atol=1e-11):
        actual = np.asarray(actual, dtype=float)
        expected = np.asarray(expected, dtype=float)
        if not np.all(np.isfinite(actual)):
            raise AssertionError("Nonfinite numerical result")
        error = float(np.max(np.abs(actual - expected), initial=0.))
        scale = float(np.max(np.abs(expected), initial=0.))
        if error > atol + rtol * scale:
            raise AssertionError(f"Error {error:.15g}; scale {scale:.15g}; "
                                 f"actual {actual.tolist()}; expected {expected.tolist()}")
        return {"actual": actual.tolist(), "expected": expected.tolist(),
                "maximum_absolute_error": error, "relative_tolerance": rtol,
                "absolute_tolerance": atol}

    def audits(result):
        for name in ("energy_identity_residual", "equilibrium_residual"):
            if not np.isfinite(result[name]) or result[name] > 1e-9:
                raise AssertionError(f"{name}: {result[name]}")
        return {name: float(result[name])
                for name in ("energy_identity_residual", "equilibrium_residual")}

    def mesh(n, length, ei, q=0., curvature=0.):
        size, dx = 2 * (n + 1), length / n
        terms, force = [], np.zeros(size)
        for i in range(n):
            dofs = [2*i, 2*i+1, 2*i+2, 2*i+3]
            terms.extend(beam_terms(f"E{i}", *dofs, dx, ei, curvature=curvature))
            force[dofs] += np.asarray(beam_load(dx, q), dtype=float)
        return size, terms, force

    def stiffness_check():
        length, ei = 3.7, 2.3e6
        ts = beam_terms("MATRIX", 0, 1, 2, 3, length, ei)
        actual = np.zeros((4, 4))
        for row in ts:
            d, b = row["dofs"], np.asarray(row["b"], dtype=float)
            actual[np.ix_(d, d)] += row["k"] * np.outer(b, b)
        expected = ei / length**3 * np.array([
            [12, 6*length, -12, 6*length],
            [6*length, 4*length**2, -6*length, 2*length**2],
            [-12, -6*length, 12, -6*length],
            [6*length, 2*length**2, -6*length, 4*length**2]])
        return {"matrix": close(actual, expected),
                "formula": "EI/L^3 times the standard cubic Hermite beam matrix"}

    check("EB_LOCAL_STIFFNESS_MATRIX", stiffness_check)

    def rigid_mode_check():
        length, ei = 3.7, 2.3e6
        out = []
        for label, u in (("translation", [.025, 0., .025, 0.]),
                         ("rotation", [0., .003, .003*length, .003])):
            ts = beam_terms(label, 0, 1, 2, 3, length, ei)
            result = solve_terms(4, ts, np.zeros(4), dict(enumerate(u)))
            out.append({"mode": label,
                        "force": close([r["force_N"] for r in result["terms"]],
                                       np.zeros(len(ts)), atol=1e-8),
                        "energy_J": close(result["strain_energy_J"], 0., atol=1e-16),
                        **audits(result)})
        return out

    check("EB_RIGID_TRANSLATION_AND_ROTATION", rigid_mode_check)

    def load_check():
        length, q = 3.7, -173.
        expected = [q*length/2, q*length**2/12,
                    q*length/2, -q*length**2/12]
        actual = np.asarray(beam_load(length, q), dtype=float)
        return {"vector": close(actual, expected),
                "vertical_force": close(actual[0]+actual[2], q*length),
                "moment_about_left": close(actual[1]+actual[2]*length+actual[3],
                                            q*length**2/2)}

    check("EB_CONSISTENT_UNIFORM_LOAD_FORCE_AND_MOMENT", load_check)

    # With consistent uniform loading, these nodal displacements/slopes are
    # exact for this constant-EI benchmark, not merely a mesh trend assertion.
    def simply_supported(n):
        length, ei, q = 7.3, 2.7e7, -800.
        size, ts, force = mesh(n, length, ei, q)
        result = solve_terms(size, ts, force, {0: 0., 2*n: 0.})
        u = result["u"]
        expected_mid = 5*q*length**4/(384*ei)
        expected_slope = q*length**3/(24*ei)
        actual = [u[n], u[1], u[2*n+1]]
        return {"elements": n,
                "midspan_m_left_right_slope": close(
                    actual, [expected_mid, expected_slope, -expected_slope]),
                "reactions_N": close(result["reaction"][[0, 2*n]],
                                       [-q*length/2, -q*length/2]),
                "formulas": "w(L/2)=5qL^4/(384EI); theta(0)=qL^3/(24EI)",
                **audits(result)}

    for n in (2, 4, 8):
        check(f"EB_SIMPLY_SUPPORTED_UDL_{n}_ELEMENTS",
              lambda n=n: simply_supported(n))

    def cantilever(n):
        length, ei, load = 4.3, 1.9e7, -2300.
        size, ts, force = mesh(n, length, ei)
        force[2*n] = load
        result = solve_terms(size, ts, force, {0: 0., 1: 0.})
        return {"elements": n,
                "tip_m_and_rotation": close(result["u"][[2*n, 2*n+1]],
                                             [load*length**3/(3*ei),
                                              load*length**2/(2*ei)]),
                "root_force_N_moment_Nm": close(result["reaction"][[0, 1]],
                                                 [-load, -load*length]),
                "energy_J": close(result["strain_energy_J"],
                                    load**2*length**3/(6*ei)),
                **audits(result)}

    for n in (1, 4):
        check(f"EB_CANTILEVER_TIP_LOAD_{n}_ELEMENTS", lambda n=n: cantilever(n))

    def free_curvature(n):
        length, ei, curvature = 5.1, 3.2e7, .0013
        size, ts, force = mesh(n, length, ei, curvature=curvature)
        result = solve_terms(size, ts, force, {0: 0., 1: 0.})
        x = np.linspace(0., length, n+1)
        expected = np.empty(size)
        expected[0::2], expected[1::2] = curvature*x*x/2, curvature*x
        return {"elements": n, "all_dofs": close(result["u"], expected),
                "zero_bending_energy_J": close(result["strain_energy_J"], 0., atol=1e-14),
                "formula": "w(x)=kappa*x^2/2; theta(x)=kappa*x; free curvature",
                **audits(result)}

    for n in (1, 4):
        check(f"EB_FREE_IMPOSED_CURVATURE_{n}_ELEMENTS", lambda n=n: free_curvature(n))

    def restrained_curvature(n):
        length, ei, curvature = 5.1, 3.2e7, .0013
        size, ts, force = mesh(n, length, ei, curvature=curvature)
        result = solve_terms(size, ts, force, {0: 0., 1: 0., 2*n: 0., 2*n+1: 0.})
        return {"elements": n, "straight_beam": close(result["u"], np.zeros(size)),
                "energy_J": close(result["strain_energy_J"], .5*ei*curvature**2*length),
                "end_moments_Nm": close(result["reaction"][[1, 2*n+1]],
                                         [ei*curvature, -ei*curvature]),
                "formula": "M=-EI*kappa; U=EI*kappa^2*L/2",
                **audits(result)}

    for n in (1, 4):
        check(f"EB_RESTRAINED_IMPOSED_CURVATURE_{n}_ELEMENTS",
              lambda n=n: restrained_curvature(n))

    def branch_test(compression, load, anchor):
        background, branch_k = 1000., 9000.
        branch = term("BRANCH", "generic_contact", [0], [1.], branch_k,
                      e0=anchor, compression_only=compression,
                      tension_only=not compression)
        ts = [term("BACKGROUND", "generic_reference_spring", [0], [1.], background), branch]
        # A reference spring is an explicit part of this generic closed-form
        # problem, not an artificial stabilizer inserted into a WTC panel.
        free_u = load/background
        engaged = free_u < anchor if compression else free_u > anchor
        expected_u = ((load+branch_k*anchor)/(background+branch_k)
                      if engaged else free_u)
        expected_force = branch_k*(expected_u-anchor) if engaged else 0.
        result = solve_terms(1, ts, [load])
        return {"branch": "compression" if compression else "tension",
                "anchor_m": anchor, "external_load_N": load, "engaged": engaged,
                "displacement_m": close(result["u"][0], expected_u),
                "branch_force_N": close(result["terms"][1]["force_N"], expected_force),
                **audits(result)}

    for compression, label in ((True, "COMPRESSION"), (False, "TENSION")):
        for load, anchor, suffix in ((-100., 0., "NEGATIVE_LOAD"),
                                     (100., 0., "POSITIVE_LOAD"),
                                     (0., .02, "ANCHOR_UP"),
                                     (0., -.02, "ANCHOR_DOWN")):
            check(f"UNILATERAL_{label}_{suffix}",
                  lambda c=compression, f=load, a=anchor: branch_test(c, f, a))

    def gap_check():
        anchor, k = .01, 2000.
        out = []
        for u in (anchor-.003, anchor, anchor+.003):
            for compression in (True, False):
                ts = [term("GAP", "generic_spring", [0], [1.], k, e0=anchor,
                           compression_only=compression, tension_only=not compression)]
                result = solve_terms(1, ts, [0.], {0: u})
                extension = u-anchor
                elastic = min(extension, 0.) if compression else max(extension, 0.)
                out.append({"compression_only": compression, "u_m": u,
                            "force_N": close(result["terms"][0]["force_N"], k*elastic),
                            "energy_J": close(result["strain_energy_J"], .5*k*elastic**2),
                            **audits(result)})
        return out

    check("UNILATERAL_PRESCRIBED_GAP_AND_ZERO_FORCE", gap_check)

    def fracture_check():
        kb, kc, kt = 1000., 9000., 4000.
        reference = term("REFERENCE", "generic_reference_spring", [0], [1.], kb)
        contact = term("CONTACT", "generic_contact", [0], [1.], kc, compression_only=True)
        tie = term("TIE", "generic_tie", [0], [1.], kt, tension_only=True)
        out = []
        for load in (100., -100.):
            pre = solve_terms(1, [reference, contact, tie], [load])
            post = solve_terms(1, [reference, contact], [load])
            expected_pre = load/(kb+kt if load > 0 else kb+kc)
            expected_post = load/(kb if load > 0 else kb+kc)
            expected_contact = 0. if load > 0 else kc*expected_post
            out.append({"load_N": load,
                        "before_and_after_m": close([pre["u"][0], post["u"][0]],
                                                    [expected_pre, expected_post]),
                        "surviving_contact_force_N": close(post["terms"][1]["force_N"],
                                                             expected_contact),
                        "before_audits": audits(pre), "after_audits": audits(post)})
        return {"states": out,
                "scope": "Removing the tensile tie preserves compression contact; "
                         "this does not test fracture energy or physical pullout strength."}

    check("REMOVED_TENSILE_TIE_PRESERVES_COMPRESSION_CONTACT", fracture_check)
    return checks


if __name__ == "__main__":
    results = run()
    print(json.dumps({"scope": "GENERIC_NUMERICAL_CHECKS_NOT_WTC_PHYSICAL_VALIDATION",
                      "passed": sum(row["pass"] for row in results),
                      "total": len(results), "tests": results}, indent=2))
    raise SystemExit(0 if all(row["pass"] for row in results) else 1)
