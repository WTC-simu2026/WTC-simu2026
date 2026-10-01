from __future__ import annotations

import csv
import hashlib
import json
import math
import platform
from pathlib import Path


ROOT = Path(__file__).resolve().parent
inputs = json.loads((ROOT / "inputs.json").read_text(encoding="utf-8"))

low_um, high_um = inputs["containing_sieve_bin_um"]
target_um = inputs["target_threshold_um"]
linear_share = (target_um - low_um) / (high_um - low_um)
log_share = math.log(target_um / low_um) / math.log(high_um / low_um)

particle_rows = []
for sample in inputs["particle_size_samples"]:
    sieved = sample["sieved_mass_percent"]
    aerodynamic = sample["aerodynamic_mass_percent"]
    under_75 = sieved["lt_75_um"]
    in_bin = sieved["75_to_300_um"]
    particle_rows.append(
        {
            "sample": sample["sample"],
            "measured_lt_2_5_mass_percent": aerodynamic["lt_2_5_um"],
            "measured_lt_53_mass_percent": round(
                aerodynamic["lt_2_5_um"]
                + aerodynamic["2_5_to_10_um"]
                + aerodynamic["10_to_53_um"],
                3,
            ),
            "measured_lt_75_mass_percent": under_75,
            "strict_lt_100_lower_percent": under_75,
            "strict_lt_100_upper_percent": under_75 + in_bin,
            "linear_within_bin_lt_100_percent": round(under_75 + in_bin * linear_share, 3),
            "log_uniform_within_bin_lt_100_percent": round(under_75 + in_bin * log_share, 3),
        }
    )

chip = inputs["red_gray_chip_proxy"]
chip_energy_per_dust = [
    chip["chip_mass_fraction_of_hand_separated_dust"] * value * 1000.0
    for value in chip["dsc_energy_kj_per_g_chip"]
]

surface_rows = []
proxy = inputs["cohesive_fracture_surface_proxy"]
for density in proxy["concrete_density_kg_m3"]:
    for diameter_um in proxy["particle_diameter_um"]:
        surface_area_m2_kg = 6.0 / (density * diameter_um * 1e-6)
        for fracture_energy in proxy["fracture_energy_j_m2"]:
            surface_rows.append(
                {
                    "density_kg_m3": density,
                    "particle_diameter_um": diameter_um,
                    "fracture_energy_j_m2": fracture_energy,
                    "ideal_spherical_surface_area_m2_kg": round(surface_area_m2_kg, 6),
                    "cohesive_surface_proxy_kj_kg": round(
                        surface_area_m2_kg * fracture_energy / 1000.0, 6
                    ),
                }
            )

gravity = inputs["gravity_proxy"]
gravity_rows = [
    {
        "mass_weighted_drop_height_m": height,
        "gravitational_potential_kj_kg": round(gravity["g_m_s2"] * height / 1000.0, 6),
    }
    for height in gravity["mass_weighted_drop_height_m"]
]

results = {
    "schema_version": "1.0",
    "iteration_id": inputs["iteration_id"],
    "particle_size": {
        "threshold_um": target_um,
        "linear_share_of_75_300_bin_below_threshold": linear_share,
        "log_uniform_share_of_75_300_bin_below_threshold": log_share,
        "samples": particle_rows,
        "mean_linear_interpolation_percent": round(
            sum(row["linear_within_bin_lt_100_percent"] for row in particle_rows)
            / len(particle_rows),
            3,
        ),
        "mean_log_uniform_interpolation_percent": round(
            sum(row["log_uniform_within_bin_lt_100_percent"] for row in particle_rows)
            / len(particle_rows),
            3,
        ),
        "qualification": "Only <75, 75-300, and >300 micrometre sieve bins were measured. Values at 100 micrometres are conditional interpolations, not observations."
    },
    "red_gray_chip_energy_proxy_kj_per_kg_hand_separated_dust": chip_energy_per_dust,
    "cohesive_fracture_surface_proxy": surface_rows,
    "gravity_proxy": gravity_rows,
    "interpretation": "The sampled settled dust supports a large coarse/supercoarse powder fraction but does not identify the fraction of the original buildings converted into dust. The chip and fracture calculations are conditional scale checks; neither validates a thermitic, explosive, gravitational, or directed-energy mechanism."
}

(ROOT / "results.json").write_text(
    json.dumps(results, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
)

with (ROOT / "particle_size_results.csv").open("w", newline="", encoding="utf-8-sig") as stream:
    writer = csv.DictWriter(stream, fieldnames=particle_rows[0].keys())
    writer.writeheader()
    writer.writerows(particle_rows)

print(json.dumps(results, indent=2, ensure_ascii=False))


def file_record(path: Path) -> dict:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return {
        "path": str(path),
        "bytes": path.stat().st_size,
        "sha256": digest.hexdigest(),
    }


source_records = []
for source_name in inputs["local_source_files"]:
    source = Path(source_name)
    source_records.append(
        file_record(source)
        if source.exists()
        else {"path": str(source), "missing": True}
    )

output_names = [
    "inputs.json",
    "calculate.py",
    "report.md",
    "source_matrix.csv",
    "results.json",
    "particle_size_results.csv",
]
manifest = {
    "schema_version": "1.0",
    "iteration_id": inputs["iteration_id"],
    "runtime": {
        "python": platform.python_version(),
        "implementation": platform.python_implementation(),
        "platform": platform.platform(),
    },
    "sources": source_records,
    "outputs": [file_record(ROOT / name) for name in output_names],
    "archive_write_policy": "Source files were opened read-only. Derived files were written only under outputs/dust_mass_v1 and tmp/pdfs/dust_extract.",
}
(ROOT / "run_manifest.json").write_text(
    json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
)
