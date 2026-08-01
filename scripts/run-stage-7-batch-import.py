#!/usr/bin/env python3
import argparse
import csv
import datetime as dt
import email
import html
import json
import os
import pathlib
import subprocess
import sys
import urllib.error
import urllib.request
import uuid
from email import policy


ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "data"


def dotenv_value(name: str, default: str) -> str:
    path = ROOT / ".env"
    if not path.exists():
        return default
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip().startswith(f"{name}="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    return default


def psql(sql: str, capture: bool = False) -> str:
    user = dotenv_value("POSTGRES_USER", "maintenance_triage")
    db = dotenv_value("POSTGRES_DB", "maintenance_triage")
    cmd = [
        "docker",
        "compose",
        "exec",
        "-T",
        "postgres",
        "psql",
        "-U",
        user,
        "-d",
        db,
        "-v",
        "ON_ERROR_STOP=1",
    ]
    if capture:
        cmd.extend(["-At", "-c", sql])
        result = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, check=True)
        return result.stdout.strip()
    result = subprocess.run(cmd + ["-f", "-"], cwd=ROOT, text=True, input=sql, capture_output=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())
    return result.stdout


def sql_literal(value) -> str:
    if value is None:
        return "NULL"
    return "'" + str(value).replace("'", "''") + "'"


def parse_email_address(value) -> str:
    if not value:
        return ""
    addresses = email.utils.getaddresses([value])
    return addresses[0][1] if addresses else value


def strip_html(value: str) -> str:
    import re

    text = re.sub(r"<(script|style)[\s\S]*?</\1>", " ", value or "", flags=re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def parse_eml(path: pathlib.Path, attachment_dir: pathlib.Path):
    msg = email.message_from_bytes(path.read_bytes(), policy=policy.default)
    text_parts = []
    html_parts = []
    attachment_paths = []
    for part in msg.walk():
        disposition = part.get_content_disposition()
        ctype = part.get_content_type()
        if disposition == "attachment":
            filename = part.get_filename() or f"attachment-{len(attachment_paths)}.bin"
            safe = "".join(ch if ch.isalnum() or ch in "._-" else "-" for ch in filename)[:100] or "attachment.bin"
            target = attachment_dir / f"{path.stem}-{len(attachment_paths)}-{safe}"
            target.write_bytes(part.get_payload(decode=True) or b"")
            attachment_paths.append("/data/" + str(target.relative_to(DATA)).replace("\\", "/"))
            continue
        if ctype == "text/plain":
            text_parts.append(part.get_content())
        elif ctype == "text/html":
            html_parts.append(strip_html(part.get_content()))
    body = "\n\n".join(part.strip() for part in text_parts if part and part.strip())
    if not body:
        body = "\n\n".join(part.strip() for part in html_parts if part and part.strip())
    parsed_date = email.utils.parsedate_to_datetime(msg.get("Date")) if msg.get("Date") else None
    if parsed_date and parsed_date.tzinfo is None:
        parsed_date = parsed_date.replace(tzinfo=dt.timezone.utc)
    return {
        "from_address": parse_email_address(msg.get("From", "")),
        "subject": msg.get("Subject", path.stem),
        "body_raw": body or path.read_text(encoding="utf-8", errors="replace"),
        "received_at": (parsed_date or dt.datetime.now(dt.timezone.utc)).isoformat(),
        "attachment_paths": attachment_paths,
        "msg_id": msg.get("Message-ID") or f"<import-{path.stem}-{uuid.uuid4()}@maintenance-triage.local>",
        "in_reply_to": msg.get("In-Reply-To"),
        "refs": msg.get("References"),
    }


def parse_txt(path: pathlib.Path):
    text = path.read_text(encoding="utf-8", errors="replace").strip()
    subject = path.stem.replace("-", " ")
    return {
        "from_address": f"{path.stem}@prospect-sample.invalid",
        "subject": subject,
        "body_raw": text or "(empty text file)",
        "received_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "attachment_paths": [],
        "msg_id": f"<import-{path.stem}-{uuid.uuid4()}@maintenance-triage.local>",
        "in_reply_to": None,
        "refs": None,
    }


def post_import(payload: dict, token: str, n8n_port: str) -> dict:
    url = f"http://localhost:{n8n_port}/webhook/stage-7-import"
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "X-Import-Token": token},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=180) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Import bridge returned HTTP {exc.code}: {body}") from exc


def load_review(path: pathlib.Path | None):
    if not path:
        return {}
    rows = {}
    with path.open("r", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            key = row.get("filename") or row.get("source_path")
            if key:
                rows[key] = row
    return rows


def render_report(batch, rows, output_path: pathlib.Path, after_hours_rate: float, standard_rate: float):
    priority_rank = {"EMERGENCY": 0, "NEEDS_REVIEW": 1, "URGENT": 2, "ROUTINE": 3}
    rows = sorted(rows, key=lambda r: (priority_rank.get(r.get("actual_priority") or "", 9), r.get("message_date") or ""))
    alert_count = sum(1 for r in rows if r.get("actual_priority") in {"EMERGENCY", "NEEDS_REVIEW", "URGENT"})
    wrong_rows = [r for r in rows if r.get("is_wrong") is True]
    over_48 = [r for r in rows if r.get("over_48h") is True]
    after_hours_count = sum(1 for r in rows if r.get("after_hours") is True and r.get("actual_priority") != "EMERGENCY")
    arithmetic = after_hours_count * max(after_hours_rate - standard_rate, 0)

    def esc(value):
        return html.escape("" if value is None else str(value))

    cards = "\n".join(
        f"""
        <tr>
          <td>{esc(r['filename'])}</td>
          <td><strong>{esc(r.get('ref') or '')}</strong></td>
          <td>{esc(r.get('actual_priority') or '')}</td>
          <td>{esc(r.get('actual_trade') or '')}</td>
          <td>{esc(r.get('unit_match_display') or '')}</td>
          <td>{esc(r.get('subject') or '')}</td>
          <td>{esc('yes' if r.get('over_48h') else 'no')}</td>
          <td>{esc('yes' if r.get('is_wrong') else '')}</td>
        </tr>
        """
        for r in rows
    )
    html_doc = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Maintenance triage batch report</title>
  <style>
    body {{ margin: 0; font-family: Arial, sans-serif; color: #222; background: #f6f4ef; }}
    main {{ width: min(1120px, calc(100% - 32px)); margin: 0 auto; padding: 28px 0 48px; }}
    h1 {{ margin: 0 0 8px; font-size: 30px; }}
    .summary {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 10px; margin: 20px 0; }}
    .summary div, section {{ background: #fff; border: 1px solid #d2cabd; border-radius: 4px; padding: 14px; }}
    dt {{ color: #666; font-size: 12px; font-weight: 700; text-transform: uppercase; }}
    dd {{ margin: 4px 0 0; font-size: 26px; font-weight: 700; }}
    table {{ width: 100%; border-collapse: collapse; background: #fff; }}
    th, td {{ border-bottom: 1px solid #ddd; padding: 8px; text-align: left; vertical-align: top; }}
    th {{ font-size: 12px; text-transform: uppercase; color: #666; }}
    @media (max-width: 760px) {{ .summary {{ grid-template-columns: 1fr 1fr; }} table {{ font-size: 13px; }} }}
  </style>
</head>
<body>
<main>
  <h1>Maintenance triage batch report</h1>
  <p>Batch {esc(batch['id'])} from {esc(batch['source_dir'])}. Accuracy/miss counts appear only when reviewed labels are supplied.</p>
  <dl class="summary">
    <div><dt>Messages</dt><dd>{len(rows)}</dd></div>
    <div><dt>Would alert</dt><dd>{alert_count}</dd></div>
    <div><dt>Over 48h</dt><dd>{len(over_48)}</dd></div>
    <div><dt>Wrong</dt><dd>{len(wrong_rows) if wrong_rows else 'review'}</dd></div>
  </dl>
  <section>
    <h2>At your rates</h2>
    <p>{after_hours_count} non-emergency after-hours items at ${after_hours_rate:.0f} after-hours and ${standard_rate:.0f} standard callout rates means ${arithmetic:.0f} in avoidable after-hours spread. This is not labelled savings; it is arithmetic using the supplied rates.</p>
  </section>
  <section>
    <h2>Sorted week</h2>
    <table>
      <thead><tr><th>File</th><th>Ref</th><th>Priority</th><th>Trade</th><th>Roster</th><th>Subject</th><th>Over 48h</th><th>Wrong</th></tr></thead>
      <tbody>{cards}</tbody>
    </table>
  </section>
</main>
</body>
</html>
"""
    output_path.write_text(html_doc, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Import prospect .eml/.txt samples through the Stage 7 n8n import bridge.")
    parser.add_argument("source_dir", type=pathlib.Path)
    parser.add_argument("--label", default="prospect-sample")
    parser.add_argument("--reviewed-csv", type=pathlib.Path)
    parser.add_argument("--after-hours-rate", type=float, default=340.0)
    parser.add_argument("--standard-rate", type=float, default=150.0)
    args = parser.parse_args()

    if not args.source_dir.exists():
        raise SystemExit(f"Source directory not found: {args.source_dir}")

    token = psql("select value->>'import_token' from triage.config where key='ingestion';", capture=True)
    if not token:
        raise SystemExit("Missing triage.config.ingestion.import_token. Run .\\scripts\\apply-stage-7.ps1 first.")

    batch_id = str(uuid.uuid4())
    batch_dir = DATA / "import-batches" / batch_id
    attachment_dir = batch_dir / "attachments"
    batch_dir.mkdir(parents=True, exist_ok=True)
    attachment_dir.mkdir(parents=True, exist_ok=True)

    psql(
        f"""
        INSERT INTO triage.import_batches (id, label, source_dir)
        VALUES ({sql_literal(batch_id)}::uuid, {sql_literal(args.label)}, {sql_literal(str(args.source_dir.resolve()))});
        """
    )

    review = load_review(args.reviewed_csv)
    files = sorted([p for p in args.source_dir.iterdir() if p.suffix.lower() in {".eml", ".txt"}])
    if not files:
        raise SystemExit("No .eml or .txt files found.")

    imported_rows = []
    message_dates = []
    n8n_port = dotenv_value("N8N_PORT", "5678")
    for path in files:
        try:
            payload = parse_eml(path, attachment_dir) if path.suffix.lower() == ".eml" else parse_txt(path)
            payload["import_batch_id"] = batch_id
            result = post_import(payload, token, n8n_port)
            ticket_id = result.get("ticket_id")
            if not ticket_id:
                raise RuntimeError(f"No ticket_id returned for {path.name}: {result}")
            row_json = psql(
                f"""
                SELECT jsonb_build_object(
                  'ref', ref,
                  'actual_priority', priority,
                  'actual_trade', trade,
                  'actual_safety', safety_signals <> '["NONE"]'::jsonb,
                  'unit_match_display', unit_match_display,
                  'unit_match_status', unit_match_status
                )
                FROM triage.tickets
                WHERE id = {int(ticket_id)};
                """,
                capture=True,
            )
            details = json.loads(row_json)
            ref = details.get("ref") or result.get("ref")
            reviewed = review.get(path.name, {})
            expected_priority = reviewed.get("corrected_priority") or reviewed.get("expected_priority") or None
            expected_trade = reviewed.get("corrected_trade") or reviewed.get("expected_trade") or None
            expected_safety_raw = reviewed.get("corrected_safety") or reviewed.get("expected_safety") or None
            expected_safety = None if expected_safety_raw in (None, "") else str(expected_safety_raw).strip().lower() in {"1", "true", "yes", "y"}
            is_wrong = None
            if expected_priority or expected_trade or expected_safety is not None:
                checks = []
                if expected_priority:
                    checks.append(expected_priority != details.get("actual_priority"))
                if expected_trade:
                    checks.append(expected_trade != details.get("actual_trade"))
                if expected_safety is not None:
                    checks.append(expected_safety != bool(details.get("actual_safety")))
                is_wrong = any(checks)
            message_date = dt.datetime.fromisoformat(payload["received_at"].replace("Z", "+00:00"))
            message_dates.append(message_date)
            row = {
                "filename": path.name,
                "source_path": str(path.resolve()),
                "message_date": payload["received_at"],
                "from_address": payload["from_address"],
                "subject": payload["subject"],
                "ticket_id": ticket_id,
                "ref": ref,
                "expected_priority": expected_priority,
                "actual_priority": details.get("actual_priority"),
                "expected_trade": expected_trade,
                "actual_trade": details.get("actual_trade"),
                "expected_safety": expected_safety,
                "actual_safety": bool(details.get("actual_safety")),
                "unit_match_display": details.get("unit_match_display"),
                "is_wrong": is_wrong,
                "after_hours": message_date.hour < 8 or message_date.hour >= 18 or message_date.weekday() >= 5,
                "over_48h": False,
            }
            imported_rows.append(row)
            psql(
                f"""
                INSERT INTO triage.import_items (
                  batch_id, source_path, message_date, from_address, subject, ticket_id, ref,
                  expected_priority, actual_priority, expected_trade, actual_trade,
                  expected_safety, actual_safety, is_wrong
                )
                VALUES (
                  {sql_literal(batch_id)}::uuid, {sql_literal(str(path.resolve()))}, {sql_literal(payload['received_at'])}::timestamptz,
                  {sql_literal(payload['from_address'])}, {sql_literal(payload['subject'])}, {int(ticket_id)}, {sql_literal(ref)},
                  {sql_literal(expected_priority)}, {sql_literal(details.get('actual_priority'))},
                  {sql_literal(expected_trade)}, {sql_literal(details.get('actual_trade'))},
                  {('NULL' if expected_safety is None else str(expected_safety).lower())},
                  {str(bool(details.get('actual_safety'))).lower()},
                  {('NULL' if is_wrong is None else str(is_wrong).lower())}
                );
                """
            )
            print(f"{path.name}: {ref} {details.get('actual_priority')}")
        except Exception as exc:
            psql(
                f"""
                INSERT INTO triage.import_items (batch_id, source_path, error)
                VALUES ({sql_literal(batch_id)}::uuid, {sql_literal(str(path.resolve()))}, {sql_literal(str(exc))});
                """
            )
            print(f"{path.name}: ERROR {exc}", file=sys.stderr)

    newest = max(message_dates) if message_dates else None
    if newest:
        for row in imported_rows:
            message_date = dt.datetime.fromisoformat(row["message_date"].replace("Z", "+00:00"))
            row["over_48h"] = (newest - message_date) > dt.timedelta(hours=48)

    review_path = batch_dir / "review.csv"
    with review_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "filename",
                "ref",
                "actual_priority",
                "actual_trade",
                "actual_safety",
                "corrected_priority",
                "corrected_trade",
                "corrected_safety",
                "notes",
            ],
        )
        writer.writeheader()
        for row in imported_rows:
            writer.writerow({
                "filename": row["filename"],
                "ref": row["ref"],
                "actual_priority": row["actual_priority"],
                "actual_trade": row["actual_trade"],
                "actual_safety": row["actual_safety"],
                "corrected_priority": "",
                "corrected_trade": "",
                "corrected_safety": "",
                "notes": "",
            })

    report_path = batch_dir / "report.html"
    render_report({"id": batch_id, "source_dir": str(args.source_dir.resolve())}, imported_rows, report_path, args.after_hours_rate, args.standard_rate)
    wrong_count = sum(1 for row in imported_rows if row.get("is_wrong") is True)
    alert_count = sum(1 for row in imported_rows if row.get("actual_priority") in {"EMERGENCY", "NEEDS_REVIEW", "URGENT"})
    needs_review = sum(1 for row in imported_rows if row.get("actual_priority") == "NEEDS_REVIEW")
    over_48 = sum(1 for row in imported_rows if row.get("over_48h") is True)
    psql(
        f"""
        UPDATE triage.import_batches
        SET
          report_path = {sql_literal('/data/' + str(report_path.relative_to(DATA)).replace(chr(92), '/'))},
          review_csv_path = {sql_literal('/data/' + str(review_path.relative_to(DATA)).replace(chr(92), '/'))},
          finished_at = now(),
          item_count = {len(imported_rows)},
          alert_count = {alert_count},
          needs_review_count = {needs_review},
          over_48h_count = {over_48},
          wrong_count = {wrong_count if review else 'NULL'},
          status = 'COMPLETE'
        WHERE id = {sql_literal(batch_id)}::uuid;
        """
    )
    print(f"Report: {report_path}")
    print(f"Review CSV: {review_path}")


if __name__ == "__main__":
    main()
