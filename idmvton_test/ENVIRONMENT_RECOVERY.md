# OOTDiffusion — Environment Recovery Guide

## TL;DR — why "python" breaks but ".venv\Scripts\python.exe" works

The system `python` on PATH is `C:\python3.11\python` — it does **not** have the
project packages. The project lives inside `.venv\`. Always use the venv interpreter
explicitly, or activate the venv first.

---

## Verified working stack (2026-05-20)

| Component | Version |
|-----------|---------|
| Python | 3.11.8 (MSC, 64-bit) |
| CUDA toolkit | 12.1 |
| GPU | RTX 4050 Laptop 6 GB |
| torch | 2.5.1+cu121 |
| diffusers | 0.24.0 |
| transformers | 4.36.2 |
| accelerate | 0.26.1 |
| safetensors | 0.7.0 |
| huggingface-hub | 0.21.4 |
| onnxruntime | 1.26.0 |
| numpy | 2.4.4 |
| scipy | 1.17.1 |
| opencv-python | 4.13.0.92 |
| einops | 0.7.0 |

Full pin: `requirements_working.txt`

---

## Running inference (two equivalent methods)

### Method 1 — wrapper script (recommended, no activation needed)
```powershell
cd C:\Users\Lenovo\.vscode\cv_project_finals\idmvton_test
.\run_ootd.ps1 --person inputs/person/myphoto2.jpg --cloth inputs/cloth/shirt2.jpg --steps 10 --samples 1
```

### Method 2 — explicit venv Python
```powershell
cd C:\Users\Lenovo\.vscode\cv_project_finals\idmvton_test
$env:HF_HUB_CACHE = "D:\huggingface\hub"
.venv\Scripts\python.exe run_ootd_local.py --person inputs/person/myphoto2.jpg --cloth inputs/cloth/shirt2.jpg --steps 10 --samples 1
```

### Method 3 — activate venv, then use plain "python"
```powershell
cd C:\Users\Lenovo\.vscode\cv_project_finals\idmvton_test
.venv\Scripts\Activate.ps1
$env:HF_HUB_CACHE = "D:\huggingface\hub"
python run_ootd_local.py --person inputs/person/myphoto2.jpg --cloth inputs/cloth/shirt2.jpg --steps 10 --samples 1
```

---

## Recovery procedure (if .venv is broken or deleted)

### Step 1 — recreate the venv
```powershell
cd C:\Users\Lenovo\.vscode\cv_project_finals\idmvton_test
C:\python3.11\python.exe -m venv .venv
```

### Step 2 — install PyTorch (CUDA 12.1 wheel)
```powershell
.venv\Scripts\pip.exe install torch==2.5.1+cu121 torchaudio==2.5.1+cu121 torchvision==0.20.1+cu121 `
    --index-url https://download.pytorch.org/whl/cu121
```

### Step 3 — install remaining packages
```powershell
.venv\Scripts\pip.exe install -r requirements_working.txt
```

### Step 4 — verify imports
```powershell
.venv\Scripts\python.exe -c "
import safetensors, torch, diffusers, transformers, accelerate, onnxruntime, scipy, cv2, einops
print('All OK')
print('torch:', torch.__version__, '| CUDA:', torch.cuda.is_available())
print('diffusers:', diffusers.__version__)
print('safetensors:', safetensors.__version__)
"
```

Expected output:
```
All OK
torch: 2.5.1+cu121 | CUDA: True
diffusers: 0.24.0
safetensors: 0.7.0
```

### Step 5 — run verification inference
```powershell
.\run_ootd.ps1 --person inputs/person/myphoto2.jpg --cloth inputs/cloth/shirt2.jpg --steps 10 --samples 1
```
Expected: output saved to `outputs/ootd_myphoto2_shirt2_00.png`, no errors.

---

## Important environment notes

- **HF model cache lives on D:**  
  `D:\huggingface\hub\models--levihsu--OOTDiffusion` (~14 GB)  
  Always set `$env:HF_HUB_CACHE = "D:\huggingface\hub"` before running (the wrapper does this automatically).

- **Do not run `pip install` without the venv active** — it will install into the system Python and corrupt nothing in the venv, but confuse you about what's available.

- **Do not upgrade huggingface-hub past 0.21.4** — diffusers 0.24.0 is incompatible with newer hub versions.

- **safetensors loading uses a custom chunked reader** (in `run_ootd_local.py`) to work around Windows paging-file exhaustion for 3.4 GB UNet files. Do not remove it.

---

## Diagnosing "ModuleNotFoundError" after this doc was written

```powershell
# 1. confirm which python is running
(Get-Command python).Source
# should show C:\Users\Lenovo\.vscode\cv_project_finals\idmvton_test\.venv\Scripts\python.exe
# if it shows C:\python3.11\python  →  venv not activated; use run_ootd.ps1 or Activate.ps1

# 2. confirm the package is in the venv
.venv\Scripts\pip.exe show safetensors
```
