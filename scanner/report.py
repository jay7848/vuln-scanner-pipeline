
import sys, json
from jinja2 import Template

TEMPLATE = '''
<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <title>Vulnerability Report</title>
  <style>
    body { font-family: system-ui, -apple-system, "Segoe UI", Roboto, Arial, sans-serif; margin: 24px; }
    h1 { margin-bottom: 4px; }
    .sev { padding: 2px 8px; border-radius: 8px; font-size: 12px; display: inline-block; }
    .CRITICAL { background: #ffe5e5; border: 1px solid #ff7a7a; }
    .HIGH { background: #fff1e6; border: 1px solid #ffb067; }
    .MEDIUM { background: #fff9e6; border: 1px solid #ffd667; }
    .LOW { background: #e9f7ff; border: 1px solid #78c7ff; }
    table { border-collapse: collapse; width: 100%; margin-top: 16px; }
    th, td { border: 1px solid #ddd; padding: 8px; font-size: 14px; vertical-align: top; }
    th { background: #f7f7f7; }
    code { background: #f3f3f3; padding: 2px 4px; border-radius: 4px; }
  </style>
</head>
<body>
  <h1>Vulnerability Report</h1>
  <p>Generated from Trivy JSON (after allowlist filtering).</p>

  {% if not results %}
    <p><strong>No vulnerabilities detected (or all were allowlisted).</strong></p>
  {% endif %}

  {% for target in results %}
    <h2>{{ target.Target }}</h2>
    {% if target.Vulnerabilities %}
      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>Severity</th>
            <th>Pkg</th>
            <th>Installed</th>
            <th>Fixed</th>
            <th>Title</th>
            <th>URL</th>
          </tr>
        </thead>
        <tbody>
          {% for v in target.Vulnerabilities %}
          <tr>
            <td><code>{{ v.VulnerabilityID }}</code></td>
            <td><span class="sev {{ v.Severity }}">{{ v.Severity }}</span></td>
            <td>{{ v.PkgName }}</td>
            <td>{{ v.InstalledVersion }}</td>
            <td>{{ v.FixedVersion or '-' }}</td>
            <td>{{ v.Title or '' }}</td>
            <td>
              {% if v.PrimaryURL %}
                <a href="{{ v.PrimaryURL }}">{{ v.PrimaryURL }}</a>
              {% elif v.References and v.References[0] %}
                <a href="{{ v.References[0] }}">{{ v.References[0] }}</a>
              {% else %}
                -
              {% endif %}
            </td>
          </tr>
          {% endfor %}
        </tbody>
      </table>
    {% else %}
      <p>No vulnerabilities for this target.</p>
    {% endif %}
  {% endfor %}
</body>
</html>
'''

def main():
    if len(sys.argv) < 3:
        print("Usage: python scanner/report.py <in_json_filtered> <out_html>")
        sys.exit(2)
    in_json, out_html = sys.argv[1], sys.argv[2]
    with open(in_json, "r", encoding="utf-8") as f:
        raw = json.load(f)
    results = raw if isinstance(raw, list) else raw.get("Results", [])
    html = Template(TEMPLATE).render(results=results)
    with open(out_html, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Wrote HTML report: {out_html}")

if __name__ == "__main__":
    main()
