
import os, time, json, glob
from prometheus_client import Gauge, start_http_server

PORT = int(os.getenv("EXPORTER_PORT","9100"))
REPORTS_DIR = "reports"
g_total = Gauge("image_vulnerabilities_total","Total vulns by severity",["image","severity"])

def update():
    files = sorted(glob.glob(os.path.join(REPORTS_DIR,"*.filtered.json")), reverse=True) or             sorted(glob.glob(os.path.join(REPORTS_DIR,"*.json")), reverse=True)
    seen = set()
    for f in files:
        image = os.path.basename(f).replace(".filtered.json","").replace(".json","")
        if image in seen: continue
        try:
            with open(f,"r",encoding="utf-8") as fp: data = json.load(fp)
            results = data if isinstance(data, list) else data.get("Results", [])
            counts = {"CRITICAL":0,"HIGH":0,"MEDIUM":0,"LOW":0,"UNKNOWN":0}
            for r in results:
                for v in (r.get("Vulnerabilities") or []):
                    sev = (v.get("Severity") or "UNKNOWN").upper()
                    counts[sev] = counts.get(sev,0)+1
            for sev,val in counts.items():
                g_total.labels(image=image, severity=sev).set(val)
            seen.add(image)
        except Exception as e:
            print("Error:", f, e)

if __name__ == "__main__":
    start_http_server(PORT); print(f"Exporter :{PORT}")
    while True: update(); time.sleep(30)
