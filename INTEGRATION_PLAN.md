# OOTDiffusion Integration Plan
# StyleSenseAI → Local GPU Virtual Try-On

**Date**: 2026-05-20  
**Status**: Planning  
**Goal**: Replace Replicate cloud API with local OOTDiffusion inference

---

## 1. Current State Assessment

### What exists

| Component | Location | Status |
|-----------|----------|--------|
| Streamlit UI | `StyleSenseAI/app.py` | Working |
| CV analysis pipeline | `StyleSenseAI/cv_analyzer.py` | Working |
| Outfit recommender | `StyleSenseAI/recommender.py` | Working |
| Gemini LLM advisor | `StyleSenseAI/llm_advisor.py` | Working |
| Cloud try-on (Replicate) | `StyleSenseAI/replicate_tryon.py` | **To replace** |
| OOTDiffusion inference | `idmvton_test/run_ootd_local.py` | Working (CLI only) |
| OOTDiffusion venv | `idmvton_test/.venv/` | Stable |
| Model weights | `idmvton_test/repo/checkpoints/` + `D:\huggingface\hub\` | Cached |

### What does NOT exist (despite task description)
- No Flutter frontend — StyleSenseAI uses **Streamlit**
- No CatVTON integration in live code — `catvton_test.zip` is an unextracted archive, never integrated
- No REST API — OOTDiffusion runs as a pure CLI script

### Critical difference: current vs target try-on

**Current (Replicate/flux-schnell)**:  
`person_image + text_prompt → cloud API → styled image`  
→ Not a true try-on; generates a new image from prompt only; ignores person image entirely

**Target (OOTDiffusion)**:  
`person_image + cloth_image → local GPU → person wearing that cloth`  
→ True virtual try-on; preserves person identity and body shape

**UI implication**: OOTDiffusion requires a **cloth image** as input.  
The current UI only accepts a person image. This is the primary UI change required.

---

## 2. Architecture: Before vs After

### Before (Current)
```
User uploads person photo
         │
         ▼
  CV Analysis (OpenCV)
         │
         ▼
  Rule-based Recommender
  generates 3 outfit ideas (text prompts)
         │
         ▼
  Replicate API (flux-schnell)        ← CLOUD, no real try-on
  3× text-to-image calls
         │
         ▼
  Gemini LLM advice
         │
         ▼
  Display results
```

### After (Proposed)
```
User uploads person photo + cloth image
         │
         ▼
  CV Analysis (OpenCV)                ← unchanged
         │
         ▼
  Rule-based Recommender              ← unchanged (descriptions only)
         │
         ▼
  OOTDiffusion subprocess call        ← NEW (replaces Replicate)
  person + cloth → try-on image
         │
         ▼
  Gemini LLM advice                   ← unchanged
         │
         ▼
  Display results                     ← minor update
```

---

## 3. Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                  StyleSenseAI (Streamlit)                │
│                                                         │
│  ┌──────────────┐    ┌──────────────────────────────┐   │
│  │ Person Image │    │       Cloth Image             │   │
│  │  (upload)    │    │       (upload) ← NEW          │   │
│  └──────┬───────┘    └──────────────┬───────────────┘   │
│         │                           │                   │
│         ▼                           │                   │
│  ┌─────────────────┐                │                   │
│  │  cv_analyzer.py │                │                   │
│  │  (OpenCV/KMeans)│                │                   │
│  └────────┬────────┘                │                   │
│           │                         │                   │
│           ▼                         │                   │
│  ┌─────────────────┐                │                   │
│  │  recommender.py │                │                   │
│  │  (outfit ideas) │                │                   │
│  └────────┬────────┘                │                   │
│           │                         │                   │
│           └────────────┬────────────┘                   │
│                        ▼                                │
│           ┌────────────────────────┐                    │
│           │    ootd_tryon.py  ← NEW│                    │
│           │  (replaces replicate_  │                    │
│           │   tryon.py)            │                    │
│           └────────────┬───────────┘                    │
│                        │  subprocess call               │
└────────────────────────┼───────────────────────────────┘
                         │
            ┌────────────▼───────────────┐
            │   idmvton_test/ (isolated) │
            │                           │
            │  .venv/Scripts/python.exe │
            │  run_ootd_local.py        │
            │                           │
            │  ┌─────────────┐          │
            │  │  OpenPose   │          │
            │  │  Parsing    │          │
            │  │ OOTDiffusion│          │
            │  └──────┬──────┘          │
            │         │                 │
            │  outputs/ootd_*.png       │
            └─────────┼─────────────────┘
                      │ read PNG back
            ┌─────────▼─────────────────┐
            │   Streamlit display       │
            └───────────────────────────┘
```

---

## 4. Key Integration Decisions

### 4.1 Invocation strategy: Subprocess (Phase 1)

**Chosen**: Call `run_ootd_local.py` via subprocess using the isolated venv Python.

**Why not in-process import**:
- StyleSenseAI runs in its own Python environment (lightweight, no torch)
- OOTDiffusion venv has pinned, incompatible package versions
- Mixing them risks dependency conflicts
- Subprocess isolation is safer and preserves the working environment

**Why not FastAPI server**:
- Adds a server management problem (who starts it? port conflicts?)
- Subprocess is simpler and just as functional for this use case
- Can migrate to FastAPI in Phase 3 if throughput matters

**Subprocess call pattern**:
```python
import subprocess, os
from pathlib import Path

OOTD_VENV_PYTHON = Path(r"D:\cv_project_finals\idmvton_test\.venv\Scripts\python.exe")
OOTD_SCRIPT     = Path(r"D:\cv_project_finals\idmvton_test\run_ootd_local.py")
OOTD_OUTPUT_DIR = Path(r"D:\cv_project_finals\idmvton_test\outputs")

def run_ootd_tryon(person_path: str, cloth_path: str, steps: int = 20) -> Path | None:
    env = os.environ.copy()
    env["HF_HUB_CACHE"] = r"D:\huggingface\hub"
    result = subprocess.run(
        [str(OOTD_VENV_PYTHON), str(OOTD_SCRIPT),
         "--person", person_path,
         "--cloth",  cloth_path,
         "--steps",  str(steps),
         "--samples", "1",
         "--output_dir", str(OOTD_OUTPUT_DIR)],
        capture_output=True, text=True, env=env, timeout=300
    )
    if result.returncode != 0:
        print(result.stderr)
        return None
    # Find the output file
    person_stem = Path(person_path).stem
    cloth_stem  = Path(cloth_path).stem
    out = OOTD_OUTPUT_DIR / f"ootd_{person_stem}_{cloth_stem}_00.png"
    return out if out.exists() else None
```

### 4.2 Windows path issues

- All paths must use raw strings or `Path()` — no forward-slash assumptions
- `HF_HUB_CACHE` must be set in subprocess env (matches `run_ootd.ps1` behavior)
- Temp files saved to `idmvton_test/inputs/` (already structured) or `tempfile.mkstemp()`
- Output detection: use stem-based filename matching (already in `run_ootd_local.py`)

### 4.3 Image upload flow

**Current**: 1 image (person) → tempfile → Replicate → 3 styled images  
**New**: 2 images (person + cloth) → saved to disk → OOTDiffusion → 1 try-on image

The UI generates 3 outfit ideas from recommendations. With OOTDiffusion, 1 cloth → 1 try-on result. Options:
- **Simplest**: Run 1 try-on (the cloth they uploaded), show outfit descriptions for all 3 ideas
- **Later**: Allow uploading 3 cloth images for full lookbook

**Phase 1 choice**: 1 cloth image, 1 try-on result displayed in first outfit slot. Other slots show outfit descriptions without images.

### 4.4 Async/background inference concerns

OOTDiffusion inference takes **60–120 seconds** on cold model load, **20–40 seconds** on subsequent runs (if models stay in GPU memory — but subprocess kills the process each time).

Subprocess approach = cold load every time ≈ **90–120 seconds per inference**.

**Mitigation for Phase 1**: Streamlit spinner with a message like "Running local GPU inference (~90s)..." — set correct user expectations. No async needed for MVP.

**Phase 2 mitigation**: Persistent FastAPI server keeps models in VRAM between calls.

### 4.5 Model loading lifecycle

Each subprocess invocation:
1. Loads OpenPose (~few seconds)
2. Loads ONNX parsing model (~few seconds)  
3. Loads OOTDiffusion HD pipeline (~60s, 3.2 GB UNet with chunked loader)
4. Runs inference (~20–40s)
5. Saves output, exits (VRAM freed)

This is acceptable for Phase 1. Phase 2 would keep models resident in a server process.

### 4.6 Output handling

- OOTDiffusion saves PNG to `outputs/ootd_{person_stem}_{cloth_stem}_00.png`
- `ootd_tryon.py` reads this back with PIL and returns `Image.Image`
- Streamlit displays it directly — no URL downloading needed (unlike Replicate)
- Temp input files should be cleaned up after inference completes

---

## 5. Files to Create / Modify

### New files
| File | Purpose |
|------|---------|
| `StyleSenseAI/ootd_tryon.py` | OOTDiffusion subprocess wrapper (replaces replicate_tryon.py) |

### Modified files
| File | Change |
|------|--------|
| `StyleSenseAI/app.py` | Add cloth uploader, swap replicate → ootd, update sidebar status |
| `StyleSenseAI/requirements.txt` | Remove `replicate` dep (not needed locally) |

### Untouched files
- `cv_analyzer.py` — no change
- `recommender.py` — no change  
- `llm_advisor.py` — no change
- `ui_styles.py` — no change
- All of `idmvton_test/` — no change

---

## 6. Implementation Phases

### Phase 1: Stable Subprocess Integration (MVP)
**Goal**: Working local try-on with minimal code changes  
**Effort**: ~2–3 hours

- [ ] Create `StyleSenseAI/ootd_tryon.py` with subprocess wrapper
- [ ] Add cloth image uploader to `app.py` (above the analyze button)
- [ ] Replace `run_virtual_tryon` calls with `run_ootd_tryon`
- [ ] Update sidebar status section (remove Replicate status, add OOTD status check)
- [ ] Update spinner text to set correct inference time expectations
- [ ] Show try-on result in first outfit card; show descriptions-only for other 2 cards
- [ ] Add error handling: missing cloth image, inference timeout, output file not found
- [ ] Test end-to-end with a real person + cloth image pair
- [ ] Update `requirements.txt` (remove `replicate`, no new deps needed)

**Acceptance criteria**: Upload person + cloth → see real try-on result in Streamlit UI

---

### Phase 2: UX Polish
**Goal**: Better user experience around slow inference  
**Effort**: ~2 hours

- [ ] Show progress messages during inference (use `st.status` with step updates)
- [ ] Save temp inputs to `idmvton_test/inputs/` with unique names (avoid collisions)
- [ ] Clean up temp files reliably (try/finally)
- [ ] Allow uploading multiple cloth images (up to 3) for full lookbook
- [ ] Show VRAM usage or GPU status in sidebar
- [ ] Add fallback message when OOTD Python/script not found

---

### Phase 3: Persistent Inference Server (Performance)
**Goal**: Eliminate model cold-load on every inference  
**Effort**: ~4–6 hours

- [ ] Create `idmvton_test/ootd_server.py` — FastAPI server using the OOTD venv
- [ ] Load models once at startup, keep in VRAM
- [ ] Expose `POST /tryon` endpoint: `{person_b64, cloth_b64}` → `{result_b64}`
- [ ] Implement request queue (one inference at a time — GPU is single-tenant)
- [ ] Update `ootd_tryon.py` to call HTTP endpoint instead of subprocess
- [ ] Add server health check in sidebar (replace file-existence check)
- [ ] Document server startup in README

---

## 7. Risk Register

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| Subprocess timeout (90–120s) | High | UX only | Correct spinner message; increase timeout to 300s |
| Windows path with spaces in temp dir | Medium | Blocking | Use `idmvton_test/inputs/` (no spaces) instead of system temp |
| OOTDiffusion errors not surfaced to user | Medium | UX | Capture stderr, show abbreviated error in `st.error()` |
| VRAM OOM if other GPU processes running | Low | Blocking | Document: close other GPU apps before running |
| Output filename collision (concurrent users) | Low | Correctness | Add timestamp or UUID to output filenames |
| HF_HUB_CACHE not set → re-download models | Low | Slow | Always pass env var in subprocess call |

---

## 8. Quick Start (after Phase 1 implementation)

```powershell
# 1. Start StyleSenseAI (from StyleSenseAI directory)
cd D:\cv_project_finals\StyleSenseAI
pip install -r requirements.txt   # first time only
streamlit run app.py

# 2. In the UI:
#    - Upload person image (full body photo)
#    - Upload cloth image (garment on white background)
#    - Click "Analyze & Try On"
#    - Wait ~90s for GPU inference
#    - View try-on result + AI fashion advice
```

---

## 9. What We're NOT Doing (scope guard)

- Not rewriting the Streamlit UI from scratch
- Not converting to Flutter (no Flutter exists in this project)
- Not supporting multiple garment categories (upper body only in Phase 1)
- Not adding user accounts or image history
- Not deploying to cloud (local GPU only)
- Not optimizing inference speed in Phase 1
- Not touching `idmvton_test/` code at all in Phase 1
