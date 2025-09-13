
# Container Image Vulnerability Scanner — Trivy + Gmail (+ CI/CD + Grafana)

An end-to-end starter to **scan Docker images with Trivy**, **fail the pipeline on HIGH/CRITICAL**,
**email results via Gmail**, and (optionally) **export metrics for Grafana**.

## Features
- Local run: build demo image → scan → HTML report → Gmail alert (SMTP App Password)
- Allowlist CVEs (exceptions)
- CI/CD: Jenkinsfile, GitHub Actions, GitLab CI — all fail on HIGH/CRITICAL (configurable)
- (Bonus) Prometheus exporter + Grafana dashboard for trends

---

## 0) Prereqs
- Docker Desktop/Engine running
- Python 3.10+
- **Gmail App Password** (2FA enabled → App passwords → create one)

---

## 1) Local quickstart (macOS/Linux)

```bash
cd ~/Downloads
unzip -o vuln-scanner-complete.zip -d ~/vuln-scanner-complete
cd ~/vuln-scanner-complete/vuln-scanner-complete

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# edit .env and set:
#   GMAIL_USER=youraddress@gmail.com
#   GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx
#   EMAIL_TO=youraddress@gmail.com
bash scripts/run_all.sh
```

### Windows (PowerShell)
```powershell
cd $HOME\Downloads
Expand-Archive .\vuln-scanner-complete.zip -DestinationPath $HOME\vuln-scanner-complete -Force
cd $HOME\vuln-scanner-complete\vuln-scanner-complete

py -3 -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt

Copy-Item .env.example .env
# Fill GMAIL_USER / GMAIL_APP_PASSWORD / EMAIL_TO
.\scripts\run_all.ps1
```

What happens:
- Builds demo image `demo-app:dev` (nginx base)
- Scans with **Trivy** (local binary if present; else dockerized)
- Saves JSON (raw + filtered) and HTML report in `reports/`
- Emails summary + attachments via Gmail
- Exits code **1** if severity gate is hit (default HIGH,CRITICAL)

Open the report:
- macOS: `open reports/demo-app.html`
- Linux: `xdg-open reports/demo-app.html`
- Windows: `start .\reports\demo-app.html`

---

## 2) Allowlist (exceptions)
Edit `allowlist.yml`:
```yaml
allowlist:
  - CVE-2021-12345
  - CVE-2022-99999
```
Re-run scan — allowlisted CVEs won’t fail or show in filtered report.

---

## 3) CI/CD
### Jenkins
- Create a Pipeline job → SCM points to this repo → Build
- Jenkinsfile builds image, scans with Trivy, generates reports, emails via Gmail, and fails on gate

### GitHub Actions
- Add repo secrets (if emailing from CI):
  - `GMAIL_USER`, `GMAIL_APP_PASSWORD`, `EMAIL_TO`
- Push to main → action builds, scans, uploads artifacts, emails

### GitLab CI (optional)
- Set CI/CD variables: `GMAIL_USER`, `GMAIL_APP_PASSWORD`, `EMAIL_TO`
- Push to the repo → pipeline runs

---

## 4) (Bonus) Prometheus + Grafana trends
```bash
docker compose up -d exporter prometheus grafana
# Grafana: http://localhost:3000 (admin/admin)
# Prometheus: http://localhost:9090
# Exporter scrapes latest reports/ to publish metrics
```
In Grafana, add Prometheus data source (URL `http://prometheus:9090`) and import `alerts/grafana_dashboard.json`.

---

## 5) Troubleshooting
- Gmail auth error → use **App Password** (not normal password), check `.env`
- No Trivy? → scripts auto-fallback to **dockerized Trivy**
- Windows Docker socket → ensure Docker Desktop is running (Linux containers)
- Port 587 blocked → set `SMTP_PORT=465` in `.env`

Enjoy!
