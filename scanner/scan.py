
import os, sys, json, subprocess
from scanner.utils import env, load_allowlist

def trivy_json(image: str, severity: str):
    cmd = ["trivy", "image", "--format", "json", "--severity", severity, image]
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return json.loads(p.stdout)
    except (FileNotFoundError, subprocess.CalledProcessError):
        # Dockerized fallback
        p = subprocess.run([
            "docker","run","--rm",
            "-v","/var/run/docker.sock:/var/run/docker.sock",
            "aquasec/trivy:latest",
            "image", image, "--format","json","--severity", severity
        ], capture_output=True, text=True, check=True)
        return json.loads(p.stdout)

def apply_allowlist(raw, allowset):
    results = raw if isinstance(raw, list) else raw.get("Results", [])
    kept, skipped = [], 0
    for r in results:
        vulns = r.get("Vulnerabilities") or []
        kv = []
        for v in vulns:
            if v.get("VulnerabilityID") in allowset:
                skipped += 1
                continue
            kv.append(v)
        if kv:
            nr = dict(r)
            nr["Vulnerabilities"] = kv
            kept.append(nr)
    return kept, skipped

def main():
    if len(sys.argv) < 3:
        print("Usage: python scanner/scan.py <image> <out_json>")
        sys.exit(2)
    image, out_json = sys.argv[1], sys.argv[2]
    sev = env("SEVERITY","HIGH,CRITICAL")
    raw = trivy_json(image, sev)

    os.makedirs(os.path.dirname(out_json) or ".", exist_ok=True)
    with open(out_json,"w",encoding="utf-8") as f:
        json.dump(raw, f, indent=2)

    allow = load_allowlist(env("ALLOWLIST_FILE","allowlist.yml"))
    kept, skipped = apply_allowlist(raw, allow)
    filtered = out_json.replace(".json","") + ".filtered.json"
    with open(filtered,"w",encoding="utf-8") as f:
        json.dump(kept, f, indent=2)
    print(f"Wrote: {out_json}\nFiltered: {filtered} (allowlisted skipped: {skipped})")

if __name__ == "__main__":
    main()
