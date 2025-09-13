
param()
$ErrorActionPreference = "Stop"

if (-not (Test-Path ".\.venv")) { py -3 -m venv .venv }
. .\.venv\Scripts\Activate.ps1
pip install -q -r requirements.txt

docker build -f DemoApp.Dockerfile -t demo-app:dev .

New-Item -ItemType Directory -Force -Path reports | Out-Null
python scanner/scan.py demo-app:dev reports/demo-app.json
python scanner/report.py reports/demo-app.filtered.json reports/demo-app.html

python scanner/notify_email.py --image demo-app:dev `
  --report-json reports/demo-app.filtered.json `
  --report-html reports/demo-app.html

Write-Host "Done. Reports in .\reports"
