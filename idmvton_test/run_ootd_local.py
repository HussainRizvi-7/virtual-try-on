"""
OOTDiffusion local inference wrapper.
Run from idmvton_test/ — handles all path setup.

Usage:
    python run_ootd_local.py --person inputs/person/photo.jpg --cloth inputs/cloth/shirt.jpg
    python run_ootd_local.py --person inputs/person/photo.jpg --cloth inputs/cloth/shirt.jpg --steps 20 --samples 1
"""

import argparse
import os
import sys
import traceback
from pathlib import Path

# ── Path setup ────────────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).parent.absolute()
REPO_ROOT   = SCRIPT_DIR / "repo"
RUN_DIR     = REPO_ROOT / "run"

# run_ootd.py expects to be executed from repo/run/ — add it to sys.path
sys.path.insert(0, str(RUN_DIR))
sys.path.insert(0, str(REPO_ROOT))

# ── Safetensors chunked-to-CUDA loader (Windows virtual-memory workaround) ───
# safetensors uses CreateFileMapping (mmap), which exhausts the Windows paging
# file for 3.2 GB UNet files (OSError 1455).  Reading all bytes at once also
# fails — Python needs to commit 3.2 GB of virtual memory in one shot.
# Fix: parse the safetensors header, read each tensor individually (≤ ~200 MB
# per chunk), cast to fp16 on the fly, and move immediately to CUDA — CPU
# commit never exceeds ~200 MB at once.
import struct as _struct, json as _json
import numpy as _np
import torch as _torch_patch
import safetensors.torch as _st

_DTYPE_MAP = {
    "F32":  (_np.float32,  _torch_patch.float32),
    "F16":  (_np.float16,  _torch_patch.float16),
    "BF16": (None,         _torch_patch.bfloat16),
    "I64":  (_np.int64,    _torch_patch.int64),
    "I32":  (_np.int32,    _torch_patch.int32),
    "I16":  (_np.int16,    _torch_patch.int16),
    "I8":   (_np.int8,     _torch_patch.int8),
    "U8":   (_np.uint8,    _torch_patch.uint8),
    "BOOL": (_np.bool_,    _torch_patch.bool),
}

def _cuda_stream_load_file(filename, device="cpu"):
    """Stream safetensors tensor-by-tensor → fp16 → CUDA, avoiding large CPU alloc."""
    cuda_dev = "cuda:0"
    state_dict = {}
    with open(filename, "rb") as fh:
        n = _struct.unpack("<Q", fh.read(8))[0]
        header = _json.loads(fh.read(n))
        data_start = 8 + n
        for name, meta in header.items():
            if name == "__metadata__":
                continue
            np_dtype, torch_src = _DTYPE_MAP[meta["dtype"]]
            shape = meta["shape"]
            beg, end = meta["data_offsets"]
            fh.seek(data_start + beg)
            raw = fh.read(end - beg)                # ≤ ~200 MB per tensor
            if meta["dtype"] == "BF16":
                t = _torch_patch.from_numpy(
                    _np.frombuffer(raw, dtype=_np.uint16).reshape(shape).copy()
                ).view(_torch_patch.bfloat16)
            else:
                t = _torch_patch.from_numpy(
                    _np.frombuffer(raw, dtype=np_dtype).reshape(shape).copy()
                )
            del raw
            if t.is_floating_point() and t.dtype != _torch_patch.float16:
                t = t.half()
            state_dict[name] = t.to(cuda_dev)
            del t
    return state_dict

_st.load_file = _cuda_stream_load_file

# ── Imports (after path setup) ────────────────────────────────────────────────
import torch
from PIL import Image
from utils_ootd import get_mask_location

from preprocess.openpose.run_openpose import OpenPose
from preprocess.humanparsing.run_parsing import Parsing
from ootd.inference_ootd_hd import OOTDiffusionHD

# ── Args ──────────────────────────────────────────────────────────────────────
parser = argparse.ArgumentParser(description="OOTDiffusion local inference")
parser.add_argument("--person",  required=True,  help="Path to person image")
parser.add_argument("--cloth",   required=True,  help="Path to garment image")
parser.add_argument("--gpu_id",  type=int, default=0)
parser.add_argument("--steps",   type=int, default=20)
parser.add_argument("--samples", type=int, default=1,  help="Number of output samples")
parser.add_argument("--scale",   type=float, default=2.0)
parser.add_argument("--seed",    type=int, default=42)
parser.add_argument("--output_dir", default=str(SCRIPT_DIR / "outputs"))
args = parser.parse_args()

os.makedirs(args.output_dir, exist_ok=True)

# Create images_output in run/ as run_ootd.py saves mask.jpg there
(RUN_DIR / "images_output").mkdir(exist_ok=True)

# ── VRAM report ───────────────────────────────────────────────────────────────
def vram():
    if torch.cuda.is_available():
        a = torch.cuda.memory_allocated() / 1e9
        r = torch.cuda.memory_reserved()  / 1e9
        print(f"[VRAM] allocated={a:.2f}GB  reserved={r:.2f}GB")

print(f"[info] person: {args.person}")
print(f"[info] cloth:  {args.cloth}")
print(f"[info] steps={args.steps}  samples={args.samples}  scale={args.scale}  seed={args.seed}")
vram()

# ── Load preprocessing models ─────────────────────────────────────────────────
print("\n[1/4] Loading OpenPose...")
openpose_model = OpenPose(args.gpu_id)
torch.cuda.empty_cache()
vram()

print("[2/4] Loading human parsing (ONNX / CPU)...")
parsing_model = Parsing(args.gpu_id)
vram()

# ── Load OOTDiffusion ─────────────────────────────────────────────────────────
print("[3/4] Loading OOTDiffusion HD pipeline...")
model = OOTDiffusionHD(args.gpu_id)
torch.cuda.empty_cache()
vram()

# ── Preprocess ────────────────────────────────────────────────────────────────
print("[4/4] Preprocessing images...")
cloth_img  = Image.open(args.cloth).convert("RGB").resize((768, 1024))
model_img  = Image.open(args.person).convert("RGB").resize((768, 1024))

keypoints  = openpose_model(model_img.resize((384, 512)))
model_parse, _ = parsing_model(model_img.resize((384, 512)))

mask, mask_gray = get_mask_location("hd", "upper_body", model_parse, keypoints)
mask      = mask.resize((768, 1024), Image.NEAREST)
mask_gray = mask_gray.resize((768, 1024), Image.NEAREST)

masked_vton_img = Image.composite(mask_gray, model_img, mask)
mask_path = os.path.join(args.output_dir, "ootd_mask.png")
masked_vton_img.save(mask_path)
print(f"  Mask saved: {mask_path}")

# ── Inference ─────────────────────────────────────────────────────────────────
print(f"\n[inference] Running {args.steps} steps, {args.samples} sample(s)...")
vram()

try:
    images = model(
        model_type="hd",
        category="upperbody",
        image_garm=cloth_img,
        image_vton=masked_vton_img,
        mask=mask,
        image_ori=model_img,
        num_samples=args.samples,
        num_steps=args.steps,
        image_scale=args.scale,
        seed=args.seed,
    )
except Exception:
    print("\n[ERROR] Inference failed:")
    traceback.print_exc()
    sys.exit(1)

torch.cuda.empty_cache()
vram()

# ── Save outputs ──────────────────────────────────────────────────────────────
from pathlib import Path as _P
person_stem = _P(args.person).stem
cloth_stem  = _P(args.cloth).stem

for i, img in enumerate(images):
    out_path = os.path.join(args.output_dir, f"ootd_{person_stem}_{cloth_stem}_{i:02d}.png")
    img.save(out_path)
    print(f"[saved] {out_path}")

print("\nDone.")
