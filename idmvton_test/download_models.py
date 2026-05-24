"""
Download OOTDiffusion checkpoints to repo/checkpoints/.
Run once before first inference.

Usage:
    python download_models.py          # download all required checkpoints
    python download_models.py --verify # verify all files present (no download)
"""

import argparse
import os
import sys
from pathlib import Path
from huggingface_hub import hf_hub_download, snapshot_download

REPO_ROOT = Path(__file__).parent / "repo"
CKPT_ROOT = REPO_ROOT / "checkpoints"

OOTD_REPO = "levihsu/OOTDiffusion"
CLIP_REPO = "openai/clip-vit-large-patch14"


# ── Required OOTD checkpoint files ──────────────────────────────────────────
OOTD_FILES = [
    # Scheduler
    "checkpoints/ootd/scheduler/scheduler_config.json",
    # Tokenizer
    "checkpoints/ootd/tokenizer/merges.txt",
    "checkpoints/ootd/tokenizer/special_tokens_map.json",
    "checkpoints/ootd/tokenizer/tokenizer_config.json",
    "checkpoints/ootd/tokenizer/vocab.json",
    # Text encoder (pytorch_model.bin — not safetensors)
    "checkpoints/ootd/text_encoder/config.json",
    "checkpoints/ootd/text_encoder/pytorch_model.bin",
    # VAE (diffusion_pytorch_model.bin — not safetensors)
    "checkpoints/ootd/vae/config.json",
    "checkpoints/ootd/vae/diffusion_pytorch_model.bin",
    # model_index + feature_extractor
    "checkpoints/ootd/model_index.json",
    "checkpoints/ootd/feature_extractor/preprocessor_config.json",
    # HD UNet garm
    "checkpoints/ootd/ootd_hd/checkpoint-36000/unet_garm/config.json",
    "checkpoints/ootd/ootd_hd/checkpoint-36000/unet_garm/diffusion_pytorch_model.safetensors",
    # HD UNet vton
    "checkpoints/ootd/ootd_hd/checkpoint-36000/unet_vton/config.json",
    "checkpoints/ootd/ootd_hd/checkpoint-36000/unet_vton/diffusion_pytorch_model.safetensors",
    # Human parsing ONNX
    "checkpoints/humanparsing/parsing_atr.onnx",
    "checkpoints/humanparsing/parsing_lip.onnx",
    # OpenPose config/weights
    "checkpoints/openpose/ckpts/body_pose_model.pth",
]

# CLIP ViT-L/14 files
CLIP_FILES = [
    "config.json",
    "model.safetensors",
    "preprocessor_config.json",
    "special_tokens_map.json",
    "tokenizer.json",
    "tokenizer_config.json",
    "vocab.json",
    "merges.txt",
]


def download_ootd():
    print("\n[1/2] Downloading OOTDiffusion checkpoints from levihsu/OOTDiffusion...")
    for remote_path in OOTD_FILES:
        local_target = REPO_ROOT / remote_path
        if local_target.exists():
            print(f"  [skip] {remote_path}")
            continue
        local_target.parent.mkdir(parents=True, exist_ok=True)
        print(f"  [dl]   {remote_path}")
        try:
            hf_hub_download(
                repo_id=OOTD_REPO,
                filename=remote_path,
                local_dir=str(REPO_ROOT),
            )
        except Exception as e:
            print(f"  [WARN] Failed: {e}")


def download_clip():
    print("\n[2/2] Downloading clip-vit-large-patch14...")
    clip_dir = CKPT_ROOT / "clip-vit-large-patch14"
    clip_dir.mkdir(parents=True, exist_ok=True)
    for fname in CLIP_FILES:
        local_target = clip_dir / fname
        if local_target.exists():
            print(f"  [skip] {fname}")
            continue
        print(f"  [dl]   {fname}")
        try:
            hf_hub_download(
                repo_id=CLIP_REPO,
                filename=fname,
                local_dir=str(clip_dir),
            )
        except Exception as e:
            print(f"  [WARN] Failed: {e}")


def verify():
    required = (
        [REPO_ROOT / p for p in OOTD_FILES]
        + [CKPT_ROOT / "clip-vit-large-patch14" / f for f in CLIP_FILES]
    )
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        print(f"MISSING ({len(missing)}):")
        for p in missing:
            print(f"  {p}")
        return False
    print(f"All {len(required)} required files present.")
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify", action="store_true", help="Check files without downloading")
    args = parser.parse_args()

    if args.verify:
        ok = verify()
        sys.exit(0 if ok else 1)

    download_ootd()
    download_clip()
    print("\nVerifying...")
    verify()
    print("\nDone. Run inference with:")
    print("  .venv\\Scripts\\python.exe run_ootd.py --model_path ... --cloth_path ...")
