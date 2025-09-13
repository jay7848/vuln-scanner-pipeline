import os, json, argparse, smtplib, mimetypes
from email.message import EmailMessage
from scanner.utils import env, send_slack  # <-- use utils.send_slack

def summarize(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    res = data if isinstance(data, list) else data.get("Results", [])
    counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "UNKNOWN": 0}
    total = 0
    for r in res:
        for v in (r.get("Vulnerabilities", []) or []):
            sev = (v.get("Severity") or "UNKNOWN").upper()
            counts[sev] = counts.get(sev, 0) + 1
            total += 1
    return counts, total

def build_email(subject, body, from_addr, to_list, attachments):
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = ", ".join(to_list)
    msg.set_content(body)
    for p in (attachments or []):
        if not p or not os.path.exists(p):
            continue
        ctype, enc = mimetypes.guess_type(p)
        if ctype is None or enc is not None:
            ctype = "application/octet-stream"
        maintype, subtype = ctype.split("/", 1)
        with open(p, "rb") as fp:
            msg.add_attachment(
                fp.read(),
                maintype=maintype,
                subtype=subtype,
                filename=os.path.basename(p),
            )
    return msg

def send_gmail(msg):
    host = env("SMTP_HOST", "smtp.gmail.com")
    port = int(env("SMTP_PORT", "587"))  # 587 (STARTTLS) or 465 (SSL)
    user = env("GMAIL_USER")
    app_pw = env("GMAIL_APP_PASSWORD")
    if not user or not app_pw:
        raise SystemExit("GMAIL_USER or GMAIL_APP_PASSWORD not set")

    if port == 465:
        import ssl
        with smtplib.SMTP_SSL(host, port, context=ssl.create_default_context()) as s:
            s.login(user, app_pw)
            s.send_message(msg)
    else:
        with smtplib.SMTP(host, port) as s:
            s.ehlo()
            s.starttls()
            s.login(user, app_pw)
            s.send_message(msg)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--image", required=True)
    ap.add_argument("--report-json", required=True)
    ap.add_argument("--report-html", default=None)
    ap.add_argument("--to", default=None)
    ap.add_argument("--fail-on", default=os.getenv("SEVERITY", "HIGH,CRITICAL"))
    ap.add_argument("--subject-prefix", default=os.getenv("SUBJECT_PREFIX", "[VulnScan]"))
    args = ap.parse_args()

    counts, total = summarize(args.report_json)
    fail_on = [s.strip().upper() for s in args.fail_on.split(",") if s.strip()]
    should_fail = any(counts.get(s, 0) > 0 for s in fail_on)

    from_name = os.getenv("EMAIL_FROM_NAME", "Vuln Scanner")
    gmail_user = os.getenv("GMAIL_USER")
    from_addr = f"{from_name} <{gmail_user}>" if gmail_user else from_name

    # Accept --to or EMAIL_TO (comma-separated)
    to_list = [t.strip() for t in (args.to or os.getenv("EMAIL_TO", "")).split(",") if t.strip()]
    if not to_list:
        raise SystemExit("EMAIL_TO not set and --to not provided")

    subject = (
        f"{args.subject_prefix} "
        f"{'FAIL' if should_fail else 'PASS'} "
        f"{args.image} "
        f"C:{counts.get('CRITICAL', 0)} H:{counts.get('HIGH', 0)} (total {total})"
    )

    body = (
        f"Image: {args.image}\n"
        f"Summary: total {total} vulnerabilities\n"
        f"CRITICAL: {counts.get('CRITICAL',0)}, HIGH: {counts.get('HIGH',0)}, "
        f"MEDIUM: {counts.get('MEDIUM',0)}, LOW: {counts.get('LOW',0)}\n"
        f"Gate (fail-on): {', '.join(fail_on)}\n\nReports attached."
    )

    # Email
    attachments = [args.report_json] + ([args.report_html] if args.report_html else [])
    msg = build_email(subject, body, from_addr, to_list, attachments)
    send_gmail(msg)

    # Slack (optional; will no-op if SLACK_WEBHOOK not set)
    slack_msg = (
        f"{'❌ FAIL' if should_fail else '✅ PASS'}  *{args.image}*\n"
        f"*CRITICAL:* {counts.get('CRITICAL',0)}  "
        f"*HIGH:* {counts.get('HIGH',0)}  "
        f"*MEDIUM:* {counts.get('MEDIUM',0)}  "
        f"*LOW:* {counts.get('LOW',0)}  "
        f"(total {total})"
    )
    send_slack(slack_msg)

    if should_fail:
        raise SystemExit(1)

if __name__ == "__main__":
    main()
