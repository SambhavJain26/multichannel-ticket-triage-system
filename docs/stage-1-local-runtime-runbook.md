# Stage 1 Local Runtime Runbook

This stage creates the local runtime only. It does not create triage workflows, prompts, fixture data, a board, or tenant-facing automation.

## Start The Stack

From the repository root:

```powershell
.\scripts\start-local.ps1
```

The script creates `.env` from `.env.example` if it does not exist. Review `.env` before adding real credentials. Do not commit `.env`.

Local endpoints:

| Service | URL or host |
|---|---|
| n8n | `http://localhost:5678` |
| Postgres | `127.0.0.1:5432` |
| GreenMail SMTP | `127.0.0.1:3025` |
| GreenMail IMAP | `127.0.0.1:3143` |
| GreenMail UI/API | `http://localhost:8080` |

## Validate Stage 1

```powershell
.\scripts\validate-stage-1.ps1
```

This runs `docker compose config`, checks Postgres readiness, checks the n8n HTTP endpoint, confirms n8n and Postgres are listening on loopback, and sends then fetches a GreenMail test email.

## Stop The Stack

```powershell
.\scripts\stop-local.ps1
```

To remove local demo volumes as well:

```powershell
.\scripts\stop-local.ps1 -RemoveVolumes
```

Only use `-RemoveVolumes` for disposable local data.

## n8n First Login

Open `http://localhost:5678` and create the local owner account. n8n stores credentials in the `n8n-data` Docker volume and encrypts them with `N8N_ENCRYPTION_KEY` from `.env`.

If you change `N8N_ENCRYPTION_KEY` after creating credentials, existing credentials may become unreadable. Set the final local value before adding real OpenAI, Telegram, or mailbox credentials.

## n8n Credential Names

Use these names so later workflow exports can refer to credentials without embedding secrets:

| Credential | Name |
|---|---|
| Postgres | `maintenance-triage-postgres-local` |
| Local IMAP | `maintenance-triage-greenmail-imap-local` |
| Local SMTP | `maintenance-triage-greenmail-smtp-local` |
| OpenAI | `maintenance-triage-openai` |
| Telegram Bot | `maintenance-triage-telegram-bot` |

## Postgres Credential Values

Use the values from `.env`.

Default local values:

| Field | Value |
|---|---|
| Host | `postgres` |
| Port | `5432` |
| Database | `maintenance_triage` |
| User | `maintenance_triage` |
| Password | `POSTGRES_PASSWORD` from `.env` |
| SSL | Off |

Use host `postgres` from inside n8n. Use `127.0.0.1` only from the host machine.

## GreenMail IMAP/SMTP Credential Values

Default local values:

| Field | IMAP | SMTP |
|---|---|---|
| Host | `greenmail` | `greenmail` |
| Port | `3143` | `3025` |
| User | `maintenance@example.test` | `maintenance@example.test` |
| Password | `GREENMAIL_PASSWORD` from `.env` | `GREENMAIL_PASSWORD` from `.env` |
| SSL/TLS | Off | Off |

Use `greenmail` as the host from inside n8n. Use `127.0.0.1` only from the host machine.

GreenMail authentication is disabled in the local container so test users are auto-provisioned. Keep the credential fields populated anyway because n8n's IMAP/SMTP credential screens expect them.

## OpenAI Credential

Create the OpenAI credential manually in n8n as `maintenance-triage-openai`.

Rules:

- Do not put the OpenAI API key in `.env.example`, workflow JSON, docs, or scripts.
- Do not export n8n credentials into this repo.
- Stage 3 will verify the live model IDs and accepted API parameters.

## Telegram Bot And Chat ID

1. Create a bot with BotFather in Telegram.
2. Store the bot token only in the n8n credential named `maintenance-triage-telegram-bot`.
3. Send the bot a message from the demo phone/account.
4. Capture the chat ID using a temporary n8n Telegram Trigger or Telegram Bot API call outside committed files.
5. Do not commit Telegram tokens, chat IDs for real people, or callback URLs tied to secrets.

## Cloudflare Tunnel For Callback Testing

Use Cloudflare Tunnel only when a public HTTPS URL is required, such as Telegram callback testing.

```powershell
.\scripts\start-cloudflare-tunnel.ps1
```

The script runs:

```powershell
cloudflared tunnel --url http://localhost:5678
```

Copy the generated `https://*.trycloudflare.com` URL into n8n only for temporary testing. The URL changes between tunnel runs unless you configure a persistent Cloudflare Tunnel, which is not part of the local demo build.

## Stage 1 Manual Checks

- n8n owner account exists.
- Postgres credential connects in n8n.
- GreenMail IMAP/SMTP credentials work in n8n.
- OpenAI credential exists in n8n and is not exported.
- Telegram bot credential exists in n8n once a bot token is available.
- A temporary Cloudflare Tunnel can expose local n8n over HTTPS.
