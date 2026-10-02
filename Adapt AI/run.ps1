Write-Host "===================================================" -ForegroundColor Cyan
Write-Host "Starting AdaptAI - Personalised AI Tutor Server..." -ForegroundColor Yellow
Write-Host "===================================================" -ForegroundColor Cyan

if (Get-Command py -ErrorAction SilentlyContinue) {
    py app.py
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    python app.py
} elseif (Test-Path "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe") {
    & "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe" app.py
} else {
    Write-Host "[ERROR] Could not find Python or Python launcher." -ForegroundColor Red
}
