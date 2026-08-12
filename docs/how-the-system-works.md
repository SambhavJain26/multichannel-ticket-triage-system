# How The System Works

This is a maintenance-triage assistant for a property manager. It reads requests, makes
the urgency clear, gathers missing details, suggests an appropriate vendor, and keeps the
manager in control of vendor contact. It is not a property-management system or an
automatic dispatch service.

## Where a tenant can start

A tenant can report a problem by email, web form, or Telegram.

Email and form requests are stored and triaged immediately. They receive one technical
email with a Telegram link so that the conversation can continue in one place. After that,
tenant updates and questions are handled in Telegram. A tenant can also start with the
Telegram bot directly.

The email link is a demo convenience, not a production identity check. Before a real
deployment, the link must be bound to a verified tenant identity.

An unpaired `/start` message only opens the bot and asks the tenant to describe the
issue. It does not create a request. A normal direct message creates a request; `/new`
opens a separate request after an existing conversation.

## What happens to a request

1. The Triage Engine reads the request and checks for safety concerns such as gas, fire,
   flooding, sewage, electrical danger, no heat, or a security issue.
2. It assigns a priority, records the request in Postgres, and creates a manager-facing
   record in Airtable.
3. If the description is too vague, the tenant Telegram bot asks focused follow-up
   questions. It asks at most two rounds, with no more than three questions in a round.
   A request still lacking enough detail becomes `NEEDS_REVIEW`; the manager receives a
   review alert, while no vendor email can be sent from it.
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
- answer status questions truthfully, for example that the request is with the manager or
  that a provider has been contacted.

It does not make up an ETA, promise that help will arrive soon, choose a vendor, or send a
free-form message that needs management judgment. Legal, accommodation, unreadable, and
otherwise sensitive cases stay with a person.

If a tenant asks, "When is someone coming?", the bot says either that the request is with
the manager or that a provider has been contacted and an update will follow. It does not
invent a time.

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

## What it does not do

It does not dispatch a vendor, create a work order in another system, confirm an
appointment, close a request, or decide that a request does not matter. It does not send a
vendor email without a manager selection. It does not send a tenant an automatic email
reply, apart from the single Telegram onboarding link used for email/form intake.

For the demo, all outbound vendor and onboarding emails use the controlled test mailbox
`sambhavn8n@gmail.com`. No real tenant or vendor should be contacted during rehearsal.
