"""Plot already-computed V8D converged pre-critical force-displacement points."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "wtc1_simulation_v8" / "output" / "resultats_wtc1_v8d_force_deplacement.json"
TARGET = ROOT / "wtc1_simulation_v8" / "output" / "synthese_wtc1_v8d_force_deplacement.png"


def main() -> None:
    data = json.loads(SOURCE.read_text(encoding="utf-8"))
    fig, ax = plt.subplots(figsize=(10.5, 6.2), dpi=180)
    colors = ["#1769aa", "#ef6c00", "#c62828", "#6a1b9a"]
    for color, case in zip(colors, data["cases"]):
        x = [row["shortening_mm"] for row in case["curve"]]
        y = [row["compression_n"] / 1e6 for row in case["curve"]]
        label = f"{case['temperature_c']:.1f} °C — L/{case['imperfection_ratio']:.0f}"
        ax.plot(x, y, marker="o", markersize=4, linewidth=2, color=color, label=label)
        if x and y:
            peak_i = max(range(len(y)), key=y.__getitem__)
            ax.scatter([x[peak_i]], [y[peak_i]], s=42, color=color, zorder=4)
    ax.set_title("WTC 1 — V8D, colonne 705 (14WF43), niveau 95\nPoints convergés avant la perte de convergence post-critique")
    ax.set_xlabel("Raccourcissement imposé (mm)")
    ax.set_ylabel("Compression à l’appui (MN)")
    ax.grid(True, alpha=0.28)
    ax.legend(frameon=False)
    ax.text(
        0.01,
        0.02,
        "Membre isolé bi-articulé; températures uniformes de sensibilité.\n"
        "La courbe s’arrête au dernier incrément convergé : branche descendante non calculée.",
        transform=ax.transAxes,
        fontsize=8.5,
        color="#333333",
        va="bottom",
    )
    fig.tight_layout()
    fig.savefig(TARGET, bbox_inches="tight")
    print(TARGET)


if __name__ == "__main__":
    main()
