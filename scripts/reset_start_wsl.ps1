<#
PowerShell helper: reset and start services inside WSL2 for the 3D-PDR-agent project.

Usage (from Windows PowerShell):
  # Run without modifying Windows proxy (recommended first):
  .\scripts\reset_start_wsl.ps1 -WslPath "/home/xjiang/sw-onedrive/3D-PDR-agent"

  # Run and also reset the Windows WinHTTP proxy (requires Admin):
  Start-Process powershell -Verb runAs -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File .\scripts\reset_start_wsl.ps1 -WslPath '/home/xjiang/sw-onedrive/3D-PDR-agent' -ClearWinProxy"

Notes:
- The script runs commands inside WSL using `wsl` and defaults the WSL project path to "/home/xjiang/sw-onedrive/3D-PDR-agent".
- It attempts to: kill listeners on common ports, clear WSL http(s)_proxy env vars, install backend editable deps, start `uvicorn` and `vite` dev server, and report endpoint status.
- If you prefer to run commands interactively, inspect the WSL command shown in the output and run it inside your WSL shell.
#>
param(
    [string]$WslPath = "/home/xjiang/sw-onedrive/3D-PDR-agent",
    [switch]$ClearWinProxy
)

function Run-Wsl {
    param([string]$Cmd)
    Write-Host "== RUNNING IN WSL: $Cmd`n"
    wsl -- bash -lc "$Cmd"
}

if ($ClearWinProxy) {
    Write-Host "Resetting WinHTTP proxy (requires Admin)..."
    try {
        netsh winhttp reset proxy
        Write-Host "WinHTTP proxy reset. You may still have system/user proxy settings in Windows network settings or browser." -ForegroundColor Green
    } catch {
        Write-Warning "Failed to reset WinHTTP proxy: $_"
    }
}

# WSL-side omnibus script (keeps simple and robust)
$wslScript = @'
set -e
# Kill known dev processes but avoid killing the calling shell
echo "Killing node/vite/uvicorn/esbuild matches (may show errors)..."
pkill -f "vite" || true
pkill -f "npm run dev" || true
pkill -f "uvicorn" || true
pkill -f "esbuild" || true

# Free common ports
for port in 5173 5174 5175 5176 5177 5178 8000 8001; do
  if command -v fuser >/dev/null 2>&1; then
    fuser -k "$port"/tcp 2>/dev/null || true
  fi
done

# Unset proxy env vars for the session
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY
export NO_PROXY=127.0.0.1,localhost

# Change to project and install editable backend deps (non-fatal if already installed)
if [ -d "${WslPath}/app/backend" ]; then
  cd "${WslPath}/app/backend"
  echo "Installing backend (editable) and runtime deps..."
  /usr/bin/env python -m pip install -e . || /usr/bin/env python3 -m pip install -e . || true
else
  echo "WARNING: backend path not found: ${WslPath}/app/backend"
fi

# Start backend uvicorn (background)
if command -v python >/dev/null 2>&1; then
  PY_CMD="$(command -v python)"
elif command -v python3 >/dev/null 2>&1; then
  PY_CMD="$(command -v python3)"
else
  PY_CMD="python"
fi

if [ -d "${WslPath}/app/backend" ]; then
  cd "${WslPath}/app/backend"
  echo "Starting backend uvicorn on 127.0.0.1:8000..."
  nohup $PY_CMD -m uvicorn pdr_app.main:app --host 127.0.0.1 --port 8000 > /tmp/pdr_uvicorn.log 2>&1 &
  echo "backend_pid:$!"
  sleep 1
  tail -n 50 /tmp/pdr_uvicorn.log || true
else
  echo "Skipping backend start; backend folder missing"
fi

# Start frontend (vite) in project frontend
if [ -d "${WslPath}/app/frontend" ]; then
  cd "${WslPath}/app/frontend"
  echo "Starting frontend Vite dev server on 0.0.0.0:5173 (so host access possible)..."
  # use npm run dev (assumes node/npm available in WSL)
  nohup npm run dev -- --host 0.0.0.0 --port 5173 > /tmp/3dpdr_frontend.log 2>&1 &
  echo "frontend_pid:$!"
  sleep 1
  tail -n 50 /tmp/3dpdr_frontend.log || true
else
  echo "Skipping frontend start; frontend folder missing"
fi

# Report listeners and quick health checks
ss -ltnp 2>/dev/null | egrep ':(517|8000|8001)' || true
sleep 0.5
curl -sS -x '' -D - http://127.0.0.1:8000/api/health -m 5 || true
curl -sS -x '' -D - http://127.0.0.1:5173/ -m 5 || true
'@

# Replace template variable for WslPath inside the script before sending
$wslScript = $wslScript -replace '\$\{WslPath\}', $WslPath

Write-Host "About to run full reset/start sequence inside WSL at path: $WslPath" -ForegroundColor Cyan
Write-Host "If you prefer, run the following inside WSL manually for debugging:" -ForegroundColor Yellow
Write-Host "  wsl -- bash -lc '<the same commands>'" -ForegroundColor Yellow

# Execute inside WSL
Run-Wsl -Cmd $wslScript

Write-Host "Done. Check http://localhost:5173 and http://127.0.0.1:8000/api/health from Windows." -ForegroundColor Green
