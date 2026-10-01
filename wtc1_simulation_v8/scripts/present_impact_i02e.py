"""Render an audited comparison of the three saved I02E native solver sequences.

The pictures use the saved nodal coordinates directly.  There is no temporal
interpolation, displacement amplification, camera animation or visual physics.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[2]
SOLVER_ROOT = ROOT / "wtc1_simulation_v8/output/impact_i02e_skin_stringer_zone"
EXPORT_AUDIT = ROOT / "wtc1_3d_v4/output/impact_i02e/native_export_audit_r10.json"
RENDER_ROOT = ROOT / "wtc1_3d_v4/renders/impact_i02e"
FRAME_ROOT = RENDER_ROOT / "frames_r10"

CASES = [
    ("CONTACT_MERGED_H127_R9", "Liaison fusionnée", "référence cinématique"),
    ("CONTACT_UNBREAKABLE_H127_R9", "Liaison non rompable", "interface cohésive sans suppression"),
    ("CONTACT_RUPTURABLE_H127_R9", "Liaison rompable", "LAW117, aucune cellule supprimée ici"),
]

PART_COLORS = {
    1: (111, 124, 137),  # representative steel facade column
    2: (50, 142, 181),   # wing skins
    3: (31, 116, 121),   # spars
    4: (218, 155, 64),   # ribs
    5: (180, 73, 113),   # stringer web
    6: (208, 76, 72),    # stringer lower flange
    7: (238, 127, 70),   # stringer upper flange
}


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    name = "arialbd.ttf" if bold else "arial.ttf"
    return ImageFont.truetype(f"C:/Windows/Fonts/{name}", size)


def interp(history: dict, key: str, time_ms: float) -> float:
    return float(np.interp(time_ms, history["time_ms"], history[key]))


def projection_basis() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    # Camera points toward the model from +x, +y and +z.  The returned vectors
    # form an orthonormal basis, so both displayed axes have the same scale.
    view = np.array([0.50, 0.35, 0.79], dtype=float)
    view /= np.linalg.norm(view)
    right = np.cross(np.array([0.0, 1.0, 0.0]), view)
    right /= np.linalg.norm(right)
    up = np.cross(view, right)
    up /= np.linalg.norm(up)
    return right, up, view


def main() -> None:
    export_audit = read_json(EXPORT_AUDIT)
    assert export_audit["status"] == "PASS"

    loaded: dict[str, dict] = {}
    npz_hashes: dict[str, str] = {}
    for case, title, subtitle in CASES:
        case_root = SOLVER_ROOT / case
        npz_path = case_root / "native_frames_r10.npz"
        archive = np.load(npz_path)
        loaded[case] = {
            "title": title,
            "subtitle": subtitle,
            "points": archive["points_mm"],
            "times": archive["times_ms"],
            "quads": archive["quads"],
            "parts": archive["parts"],
            "bricks": archive["bricks"],
            "active": archive["active"],
            "history": read_json(case_root / "history.json"),
            "results": read_json(case_root / "results.json"),
        }
        assert loaded[case]["results"]["status"] == "PASS"
        npz_hashes[case] = sha256(npz_path)

    reference = loaded[CASES[0][0]]
    times = reference["times"]
    assert len(times) == 30
    maximum_time_alignment_error_ms = 0.0
    for case, _, _ in CASES[1:]:
        maximum_time_alignment_error_ms = max(
            maximum_time_alignment_error_ms,
            float(np.max(np.abs(loaded[case]["times"] - times))),
        )
        assert maximum_time_alignment_error_ms <= 5.0e-6
        assert np.array_equal(loaded[case]["quads"], reference["quads"])
        assert np.array_equal(loaded[case]["parts"], reference["parts"])

    right, up, view = projection_basis()
    all_points = np.concatenate([loaded[case]["points"].reshape(-1, 3) for case, _, _ in CASES])
    all_u = all_points @ right
    all_v = all_points @ up
    u_min, u_max = float(all_u.min()), float(all_u.max())
    v_min, v_max = float(all_v.min()), float(all_v.max())

    width, height = 1800, 1000
    panel_lefts = [20, 615, 1210]
    panel_width = 570
    viewport_top, viewport_bottom = 190, 696
    viewport_height = viewport_bottom - viewport_top
    scale = min((panel_width - 34) / (u_max - u_min), (viewport_height - 24) / (v_max - v_min))
    u_mid, v_mid = (u_min + u_max) / 2, (v_min + v_max) / 2
    frame_records: list[dict] = []
    FRAME_ROOT.mkdir(parents=True, exist_ok=True)
    RENDER_ROOT.mkdir(parents=True, exist_ok=True)

    for state, time_ms in enumerate(times):
        image = Image.new("RGB", (width, height), "#eef3f6")
        draw = ImageDraw.Draw(image)
        draw.rectangle((0, 0, width, 110), fill="#122c42")
        draw.text((26, 15), "IMPACT-I02E | Premier contact local aile–colonne", font=font(34, True), fill="white")
        draw.text(
            (26, 61),
            "Trois assemblages, même géométrie et mêmes masses — états natifs du solveur",
            font=font(23),
            fill="#bfe3f4",
        )

        for panel_index, (case, _, _) in enumerate(CASES):
            case_data = loaded[case]
            panel_time_ms = float(case_data["times"][state])
            left = panel_lefts[panel_index]
            draw.rounded_rectangle((left, 126, left + panel_width, 902), radius=12, fill="#ffffff", outline="#b7c4cd", width=2)
            draw.text((left + 18, 137), case_data["title"], font=font(24, True), fill="#173a52")
            draw.text((left + 18, 166), case_data["subtitle"], font=font(17), fill="#667a88")
            draw.rectangle((left + 10, viewport_top, left + panel_width - 10, viewport_bottom), fill="#1e3445")

            points = case_data["points"][state]
            center_x = left + panel_width / 2
            center_y = (viewport_top + viewport_bottom) / 2
            projected = np.column_stack(
                [center_x + scale * (points @ right - u_mid), center_y - scale * (points @ up - v_mid)]
            )
            depths = np.array([points[quad].mean(axis=0) @ view for quad in case_data["quads"]])
            order = np.argsort(depths)
            for quad_id in order:
                quad = case_data["quads"][quad_id]
                part = int(case_data["parts"][quad_id])
                coords = [(float(projected[node, 0]), float(projected[node, 1])) for node in quad]
                color = PART_COLORS[part]
                outline = tuple(max(0, value - 30) for value in color)
                draw.polygon(coords, fill=color, outline=outline)

            # The markers visualize the numerically distributed connection cells;
            # they must not be interpreted as literal fasteners.
            for brick, active in zip(case_data["bricks"], case_data["active"][state]):
                lower = points[brick[:4]].mean(axis=0)
                upper = points[brick[4:]].mean(axis=0)
                p0 = (center_x + scale * (lower @ right - u_mid), center_y - scale * (lower @ up - v_mid))
                p1 = (center_x + scale * (upper @ right - u_mid), center_y - scale * (upper @ up - v_mid))
                marker = "#84f3af" if active >= 0.5 else "#ff826e"
                draw.line((p0, p1), fill=marker, width=2)

            history = case_data["history"]
            impulse = abs(interp(history, "contact_impulse_Ns", panel_time_ms))
            work = interp(history, "joint_work_J", panel_time_ms)
            relative = interp(history, "max_pair_relative_displacement_mm", panel_time_ms)
            if case_data["bricks"].shape[0]:
                active_fraction = interp(history, "active_area_fraction", panel_time_ms)
                active_text = f"Interface active : {100 * active_fraction:5.1f} %"
            else:
                active_text = "Interface active : liaison fusionnée"
            draw.text((left + 20, 717), f"État {state + 1:02d}/30  |  {1000 * panel_time_ms:7.1f} µs", font=font(21, True), fill="#153a53")
            draw.text((left + 20, 756), f"Impulsion de contact : {impulse:7.2f} N·s", font=font(20), fill="#235c7c")
            draw.text((left + 20, 789), f"Travail de liaison : {work:7.3f} J", font=font(20), fill="#8d4d21")
            draw.text((left + 20, 822), f"Déplacement relatif nodal max. : {relative:6.3f} mm", font=font(18), fill="#7b3e68")
            draw.text((left + 20, 855), active_text, font=font(18), fill="#2b6d4b")

        draw.rectangle((0, 915, width, height), fill="#f6dfc7")
        draw.text(
            (24, 927),
            "Vue sans amplification. Modèle local de 1,98 kg, pas un Boeing complet. Rupture des coques métalliques désactivée.",
            font=font(21, True),
            fill="#703e1e",
        )
        draw.text(
            (24, 961),
            "Attention : déformation plastique équivalente maximale de la peau ≈ 1,22 ; les formes tardives ne valident pas une aile intacte.",
            font=font(20),
            fill="#8a2c2c",
        )

        frame_path = FRAME_ROOT / f"state_{state:03d}.png"
        image.save(frame_path, optimize=True)
        frame_records.append(
            {
                "state": state,
                "time_ms_by_case": {case: float(loaded[case]["times"][state]) for case, _, _ in CASES},
                "sha256": sha256(frame_path),
            }
        )

    overview = RENDER_ROOT / "I02E_apercu_comparatif.png"
    shutil.copyfile(FRAME_ROOT / "state_029.png", overview)

    video = RENDER_ROOT / "I02E_premier_contact_comparatif.mp4"
    temporary_video = RENDER_ROOT / "I02E_premier_contact_comparatif.tmp.mp4"
    if temporary_video.exists():
        temporary_video.unlink()
    ffmpeg = shutil.which("ffmpeg")
    ffprobe = shutil.which("ffprobe")
    assert ffmpeg and ffprobe
    command = [
        ffmpeg,
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-framerate",
        "5",
        "-i",
        str(FRAME_ROOT / "state_%03d.png"),
        "-c:v",
        "libx264",
        "-crf",
        "18",
        "-pix_fmt",
        "yuv420p",
        "-r",
        "30",
        str(temporary_video),
    ]
    encoded = subprocess.run(command, capture_output=True, text=True, timeout=120)
    (RENDER_ROOT / "encoding_r10.log").write_text(encoded.stdout + encoded.stderr, encoding="utf-8")
    assert encoded.returncode == 0
    temporary_video.replace(video)
    probed = subprocess.run(
        [
            ffprobe,
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=width,height,codec_name,nb_frames,duration",
            "-of",
            "json",
            str(video),
        ],
        capture_output=True,
        text=True,
        timeout=30,
        check=True,
    )
    probe = json.loads(probed.stdout)["streams"][0]

    checks = {
        "native_export_pass": export_audit["status"] == "PASS",
        "three_solver_cases": len(loaded) == 3,
        "thirty_native_states": len(frame_records) == 30,
        "native_times_aligned_within_0_005_us": maximum_time_alignment_error_ms <= 5.0e-6,
        "identical_shell_topology": all(
            np.array_equal(loaded[c]["quads"], reference["quads"]) and np.array_equal(loaded[c]["parts"], reference["parts"])
            for c, _, _ in CASES
        ),
        "orthonormal_projection": bool(
            abs(right @ up) < 1e-12
            and abs(right @ view) < 1e-12
            and abs(up @ view) < 1e-12
            and abs(right @ right - 1.0) < 1e-12
            and abs(up @ up - 1.0) < 1e-12
            and abs(view @ view - 1.0) < 1e-12
        ),
        "h264": probe["codec_name"] == "h264",
        "dimensions": (int(probe["width"]), int(probe["height"])) == (width, height),
        "encoded_frames": int(probe["nb_frames"]) == 180,
        "duration_six_seconds": abs(float(probe["duration"]) - 6.0) < 0.001,
        "overview_matches_final_frame": sha256(overview) == frame_records[-1]["sha256"],
    }
    audit = {
        "iteration": "IMPACT-I02E",
        "status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "cases": [case for case, _, _ in CASES],
        "source_npz_sha256": npz_hashes,
        "maximum_time_alignment_error_ms": maximum_time_alignment_error_ms,
        "native_export_audit": rel(EXPORT_AUDIT),
        "native_export_audit_sha256": sha256(EXPORT_AUDIT),
        "frames": frame_records,
        "overview": rel(overview),
        "overview_sha256": sha256(overview),
        "video": rel(video),
        "video_sha256": sha256(video),
        "probe": probe,
        "ffmpeg_command": command,
        "mechanical_interpolation": False,
        "displacement_amplification": 1.0,
        "camera_motion": False,
        "scope": (
            "Three direct native solver sequences of the same bounded local wing-bay/facade-column model. "
            "Shell midsurfaces and distributed interface markers are visualized. This is not a full aircraft, "
            "a fracture-qualified metal model, or evidence that a real wing remains intact."
        ),
    }
    audit_path = RENDER_ROOT / "presentation_audit_r10.json"
    audit_path.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": audit["status"], "video": rel(video), "overview": rel(overview), "checks": checks}, indent=2))
    if audit["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
