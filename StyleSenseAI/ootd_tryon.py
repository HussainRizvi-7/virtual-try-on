"""
OOTDiffusion subprocess wrapper for StyleSenseAI.
Calls the isolated idmvton_test venv Python to run local GPU inference.
"""

import os
import subprocess
import uuid
import shutil
from pathlib import Path
from PIL import Image

OOTD_ROOT       = Path(r"D:\cv_project_finals\idmvton_test")
OOTD_VENV_PY    = OOTD_ROOT / ".venv" / "Scripts" / "python.exe"
OOTD_SCRIPT     = OOTD_ROOT / "run_ootd_local.py"
OOTD_INPUT_DIR  = OOTD_ROOT / "inputs"
OOTD_OUTPUT_DIR = OOTD_ROOT / "outputs"
HF_HUB_CACHE    = r"D:\huggingface\hub"

INFERENCE_TIMEOUT = 1200  # seconds — RTX 4050 cold load: ~9-10 min total


def check_ootd_status() -> dict:
    """Return availability info for the sidebar."""
    return {
        "venv_found": OOTD_VENV_PY.exists(),
        "script_found": OOTD_SCRIPT.exists(),
        "ready": OOTD_VENV_PY.exists() and OOTD_SCRIPT.exists(),
    }


def run_ootd_tryon(person_img: Image.Image, cloth_img: Image.Image, steps: int = 15) -> Image.Image | None:
    """
    Run OOTDiffusion inference via subprocess.
    Returns PIL Image on success, None on failure.
    Raises RuntimeError with stderr on inference failure.
    """
    tag = uuid.uuid4().hex[:8]
    person_path = OOTD_INPUT_DIR / "person" / f"person_{tag}.jpg"
    cloth_path  = OOTD_INPUT_DIR / "cloth"  / f"cloth_{tag}.jpg"
    out_path    = OOTD_OUTPUT_DIR / f"ootd_person_{tag}_cloth_{tag}_00.png"

    person_path.parent.mkdir(parents=True, exist_ok=True)
    cloth_path.parent.mkdir(parents=True, exist_ok=True)
    OOTD_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    try:
        person_img.convert("RGB").save(str(person_path), format="JPEG")
        cloth_img.convert("RGB").save(str(cloth_path), format="JPEG")

        env = os.environ.copy()
        env["HF_HUB_CACHE"] = HF_HUB_CACHE

        result = subprocess.run(
            [
                str(OOTD_VENV_PY),
                str(OOTD_SCRIPT),
                "--person",     str(person_path),
                "--cloth",      str(cloth_path),
                "--steps",      str(steps),
                "--samples",    "1",
                "--output_dir", str(OOTD_OUTPUT_DIR),
            ],
            capture_output=True,
            text=True,
            env=env,
            timeout=INFERENCE_TIMEOUT,
        )

        if result.returncode != 0:
            raise RuntimeError(result.stderr[-2000:] if result.stderr else "OOTDiffusion exited with non-zero code")

        if not out_path.exists():
            raise RuntimeError(f"Inference finished but output not found: {out_path}")

        return Image.open(str(out_path)).convert("RGB")

    finally:
        for p in (person_path, cloth_path):
            try:
                p.unlink(missing_ok=True)
            except OSError:
                pass
