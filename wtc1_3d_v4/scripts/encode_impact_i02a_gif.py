"""Package exact IMPACT-I02A PNG states into a five-second animated GIF."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[2]
FRAME_DIR = ROOT / "wtc1_3d_v4/renders/impact_i02a/frames"
OUTPUT = ROOT / "wtc1_3d_v4/renders/impact_i02a/IMPACT_I02A_solver_states.gif"
AUDIT = ROOT / "wtc1_3d_v4/output/impact_i02a/animation_audit.json"
ANNOTATED_DIR = ROOT / "wtc1_3d_v4/renders/impact_i02a/annotated_frames"
SOURCE = (
    ROOT
    / "wtc1_simulation_v8/output/impact_i02a_structured_wing/CONTACT_M050_R1/computed_frames.npz"
)
FRAME_DURATION_MS = 200


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    ANNOTATED_DIR.mkdir(parents=True, exist_ok=True)
    paths = sorted(FRAME_DIR.glob("state_*.png"))
    if len(paths) != 25:
        raise RuntimeError(f"Expected 25 state images, received {len(paths)}")
    times_ms = np.load(SOURCE)["times_ms"]
    if len(times_ms) != len(paths):
        raise RuntimeError("Solver time vector does not match rendered state count")
    font_path = Path(r"C:\Windows\Fonts\arial.ttf")
    bold_path = Path(r"C:\Windows\Fonts\arialbd.ttf")
    font = ImageFont.truetype(str(font_path), 18)
    bold = ImageFont.truetype(str(bold_path), 18)
    images = []
    for state_index, path in enumerate(paths):
        frame = Image.open(path).convert("RGB")
        draw = ImageDraw.Draw(frame)
        draw.rectangle((0, 0, frame.width, 42), fill=(18, 20, 24))
        draw.rectangle((0, frame.height - 66, frame.width, frame.height), fill=(18, 20, 24))
        draw.text(
            (frame.width // 2, 21),
            "I02A - ETATS OPENRADIOSS  |  RUPTURE DESACTIVEE  |  PAS UNE VALIDATION DU WTC1",
            font=bold,
            fill=(245, 76, 52),
            anchor="mm",
        )
        draw.text(
            (18, frame.height - 59),
            f"Etat {state_index + 1:02d}/25  |  t = {times_ms[state_index]:.3f} ms",
            font=bold,
            fill=(238, 242, 250),
        )
        draw.text(
            (18, frame.height - 31),
            "Rouge: epsp > 0,20 (seuil visuel) | pas d'interpolation | grandes deformations finales hors validite constitutive",
            font=font,
            fill=(255, 191, 72),
        )
        annotated_path = ANNOTATED_DIR / path.name
        frame.save(annotated_path)
        images.append(frame)
    dimensions = {image.size for image in images}
    if dimensions != {(960, 620)}:
        raise RuntimeError(f"Unexpected or inconsistent dimensions: {dimensions}")

    images[0].save(
        OUTPUT,
        save_all=True,
        append_images=images[1:],
        duration=FRAME_DURATION_MS,
        loop=0,
        optimize=False,
        disposal=2,
    )
    for image in images:
        image.close()

    # Stable human-facing still names point to annotated exact states.
    for state_index, name in (
        (0, "I02A_initial.png"),
        (5, "I02A_contact_0p25ms.png"),
        (24, "I02A_final_1p20ms.png"),
    ):
        with Image.open(ANNOTATED_DIR / f"state_{state_index:03d}.png") as still:
            still.save(OUTPUT.parent / name)

    with Image.open(OUTPUT) as animation:
        frame_count = animation.n_frames
        size = animation.size
        durations = []
        for frame_index in range(frame_count):
            animation.seek(frame_index)
            durations.append(int(animation.info.get("duration", 0)))

    checks = {
        "source_png_count_25": len(paths) == 25,
        "gif_frame_count_25": frame_count == 25,
        "dimensions_960_by_620": size == (960, 620),
        "duration_200ms_each": all(value == FRAME_DURATION_MS for value in durations),
        "gif_nonempty": OUTPUT.stat().st_size > 10000,
        "solver_time_count_25": len(times_ms) == 25,
    }
    result = {
        "iteration": "IMPACT-I02A",
        "status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "animation": str(OUTPUT.relative_to(ROOT)).replace("\\", "/"),
        "animation_sha256": sha256(OUTPUT),
        "bytes": OUTPUT.stat().st_size,
        "frames": frame_count,
        "dimensions": list(size),
        "duration_ms_per_state": durations,
        "display_duration_s": sum(durations) / 1000.0,
        "geometry_interpolation": "none; one exact saved solver state per GIF frame",
        "physical_duration_ms": 1.2,
        "time_scale_note": "1.2 ms physical solver interval is displayed over 5.0 s.",
        "scope": "Visualization packaging only; no mechanics are calculated here.",
    }
    AUDIT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    if result["status"] != "PASS":
        raise RuntimeError("Animation audit failed")


if __name__ == "__main__":
    main()
