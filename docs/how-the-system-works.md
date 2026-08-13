# How The System Works

This is a maintenance-triage assistant for a property manager. Its main value is turning
messy tenant maintenance messages into a safe, manager-controlled workflow without staff
having to manually triage every first message. It identifies urgency, gathers the details
needed to act, suggests an appropriate vendor, and keeps the manager in control of vendor
contact. It is not a property-management system or an automatic dispatch service.

## Where a tenant can start

A tenant can report a problem by email, web form, or Telegram.

Email and form requests are stored and triaged immediately. They receive one technical
email with a Telegram link so that the conversation can continue in one place. After that,
tenant updates and questions are handled in Telegram. A tenant can also start with the
Telegram bot directly.

For this demo, the tenant Telegram bot is dedicated to one known tenant, equivalent to a
dedicated SMS number. Its configured tenant name, email, property, and unit are added to
every direct Telegram request automatically. It therefore never asks that tenant who they
are or which property they live in. A multi-tenant production version would use a separate
verified identity or a separate configured bot/number for each tenant.

The email link is a demo convenience, not a production identity check. Before a real
deployment, the link must be bound to a verified tenant identity.

An unpaired `/start` message only opens the bot and asks the tenant to describe the
issue. It does not create a request. A normal direct message creates a request; `/new`
opens a separate request after an existing conversation.

## What happens to a request

1. The Triage Engine reads the request and checks for safety concerns such as gas, fire,
   flooding, sewage, electrical danger, no heat, or a security issue.
   A standalone fan failure without a hazard is routine appliance maintenance; an
   electrical classification requires actual electrical-danger context, not merely that an
   item uses power.
2. It assigns a priority, records the request in Postgres, and creates a manager-facing
   record in Airtable.
3. If the description is too vague, the tenant Telegram bot keeps asking focused follow-up
   questions until it has the details needed to classify the request, with no more than
   three questions in a round. It treats the active email or Telegram chat as the tenant
   contact channel, so it does not ask for a phone number. The dedicated tenant bot also
   already knows the property and unit, so it asks only about the issue or maintenance
   access details. A vague new issue does not alert the manager until it is sufficiently
   described; the classifier sees the accumulated conversation each time. It does not send
   a vendor email while details are missing.
   Sensitive or human-only cases go to manager review instead.
4. For a complete maintenance request, it selects up to three active vendors whose trade
   and property coverage match the request.
5. The manager receives a Telegram approval message containing the exact vendor email and
   vendor choices. Selecting a vendor sends one email to that vendor. Selecting Hold sends
   nothing.
6. After the vendor email succeeds, the tenant receives a Telegram update that a provider
   has been contacted. The system never claims an arrival time until a person has one.

## Conversation behavior

The tenant bot can do three limited things on its own:

- confirm that a request was received;
- ask deterministic questions needed to classify it safely;
- answer status questions truthfully in one consolidated message across the chat's open
  requests, identifying each request and whether it is with the manager or a provider has
  been contacted.

It does not make up an ETA, promise that help will arrive soon, choose a vendor, or send a
free-form message that needs management judgment. Legal, accommodation, unreadable, and
otherwise sensitive cases stay with a person.

If a tenant asks, "When will all these issues be resolved?", the bot lists each open
request once with its current status. It does not create another request, notify the
manager again, or invent a completion time.

## What the manager sees

Airtable is the manager workspace. It contains requests, conversation history, the tenant
roster, vendor roster, priority, missing details, proposed vendors, and the vendor-send
result. Postgres is the durable automation record behind it, so a duplicate Telegram button
tap cannot send a second vendor email.

Telegram is the manager decision channel. For each complete maintenance request, the
manager gets the request summary, safety/priority context, the drafted vendor note, and
only the vendor-selection buttons that have an active matching vendor. A selected vendor
is the explicit approval to send that email. When there is no match, the manager sees a
manual-assignment message and Hold only. Incomplete, sensitive, or `NEEDS_REVIEW`
requests also send a manager review message with Hold only, never a vendor-selection
button.

## Why both Airtable and Telegram are used

Airtable is the manager's visible workspace: it makes open requests, conversations,
tenant context, vendor coverage, priority, and send outcomes easy to inspect. Telegram is
the fast decision channel: the manager can approve one proposed vendor without opening a
separate tool. Postgres sits behind both systems as the durable source of ticket identity,
conversation history, duplicate protection, and one-send-only approval state.

## What it does not do

It does not dispatch a vendor, create a work order in another system, confirm an
appointment, close a request, or decide that a request does not matter. It does not send a
vendor email without a manager selection. It does not send a tenant an automatic email
reply, apart from the single Telegram onboarding link used for email/form intake.

For the demo, all outbound vendor and onboarding emails use the controlled test mailbox
`sambhavn8n@gmail.com`. No real tenant or vendor should be contacted during rehearsal.
The full technical design, implementation map, setup, validation, and maintenance rules
are in `docs/build-description.md`.
