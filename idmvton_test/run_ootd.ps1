# run_ootd.ps1 — convenience wrapper that uses the venv Python directly
# Usage (from idmvton_test/ in PowerShell):
#   .\run_ootd.ps1 --person inputs/person/myphoto2.jpg --cloth inputs/cloth/shirt2.jpg --steps 10 --samples 1
#
# No venv activation needed — this script calls the venv interpreter explicitly.

$env:HF_HUB_CACHE = "D:\huggingface\hub"
& "$PSScriptRoot\.venv\Scripts\python.exe" "$PSScriptRoot\run_ootd_local.py" @args
