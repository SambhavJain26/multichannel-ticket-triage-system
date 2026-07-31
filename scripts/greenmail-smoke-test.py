#!/usr/bin/env python3
import argparse
import email
import imaplib
import smtplib
import sys
import time
import uuid
from email.message import EmailMessage


def send_message(host, port, username, password, sender, recipient, subject):
    message = EmailMessage()
    message["From"] = sender
    message["To"] = recipient
    message["Subject"] = subject
    message.set_content(
        "Stage 1 GreenMail smoke test for maintenance triage local runtime."
    )

    with smtplib.SMTP(host, port, timeout=10) as smtp:
        smtp.ehlo()
        if username and password:
            try:
                smtp.login(username, password)
            except smtplib.SMTPException:
                # GreenMail local test SMTP may accept unauthenticated sends.
                pass
        smtp.send_message(message)


def fetch_message(host, port, username, password, subject, timeout_seconds):
    deadline = time.time() + timeout_seconds
    last_error = None

    while time.time() < deadline:
        try:
            with imaplib.IMAP4(host, port, timeout=10) as imap:
                imap.login(username, password)
                imap.select("INBOX")
                status, data = imap.search(None, "SUBJECT", f'"{subject}"')
                if status == "OK" and data and data[0]:
                    ids = data[0].split()
                    status, message_data = imap.fetch(ids[-1], "(RFC822)")
                    if status != "OK":
                        raise RuntimeError("IMAP fetch failed")
                    parsed = email.message_from_bytes(message_data[0][1])
                    return parsed["Subject"]
        except Exception as exc:
            last_error = exc

        time.sleep(1)

    raise RuntimeError(f"Timed out waiting for test email. Last error: {last_error}")


def main():
    parser = argparse.ArgumentParser(description="Send and fetch a GreenMail test email.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--smtp-port", type=int, default=3025)
    parser.add_argument("--imap-port", type=int, default=3143)
    parser.add_argument("--username", default="maintenance@example.test")
    parser.add_argument("--password", default="greenmail-local-password")
    parser.add_argument("--sender", default="tenant@example.test")
    parser.add_argument("--timeout-seconds", type=int, default=30)
    args = parser.parse_args()

    subject = f"maintenance-triage-stage-1-{uuid.uuid4()}"
    send_message(
        args.host,
        args.smtp_port,
        args.username,
        args.password,
        args.sender,
        args.username,
        subject,
    )
    fetched_subject = fetch_message(
        args.host,
        args.imap_port,
        args.username,
        args.password,
        subject,
        args.timeout_seconds,
    )

    print(f"GreenMail SMTP/IMAP smoke test passed: {fetched_subject}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"GreenMail SMTP/IMAP smoke test failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
