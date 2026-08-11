# How The System Works

A plain-language explanation of what this automation does, written to be read by anyone,
technical or not. It names the specific piece responsible for each part, because "the
system did it" is not a real answer. But it stays out of the wiring: no code, no database
field names, no internal jargon. If you run a property management company, this document
is written for you.

## The Problem This Solves

A tenant notices something wrong and tells you however feels natural to them. A rambling
email at 11pm. A text to the manager's personal mobile. A voicemail. A portal submission
typed in a panic. There is no standard format, and the tenant often does not know how
serious their own problem actually is.

Those messages land undifferentiated in one inbox. A person reads every single one,
decides in their head how urgent it is, works out which trade is needed, judges whether it
can wait until Monday, and writes a reply. Dozens of times a day, while doing four other
jobs. Outside business hours, not at all.

That reading-and-sorting step is what this automation does. It does not decide whether the
repair gets done well, how fast a vendor arrives, or whether the owner approves the spend.
Those stay yours. Every request still reaches a person exactly as it does today. The only
difference is that it arrives already read, already sorted, with the dangerous ones at the
top.

**Getting this wrong is expensive in both directions.** A genuine emergency sits unread
because it looked like routine noise, and a $150 repair becomes a $12,000 claim. Or a
trivial issue gets treated as urgent, and a $60 fix turns into a $340 weekend call-out.
Slow response is also the single biggest reason tenants do not renew, and a lost tenant
costs roughly $4,000 once vacancy, marketing, and re-leasing are added up. This automation
exists to catch both kinds of mistake before they cost you anything.

## The One-Paragraph Version

A maintenance message arrives by email or through a web form. An automation reads it,
strips out signatures and quoted history, and sends the clean text to an AI reading model
for classification. Separately, a fixed safety check scans the same message for a list of
dangerous words and phrases, and it is allowed to raise the urgency the AI chose but never
lower it. The request is recorded either way, even if the AI call fails. If a reply is
appropriate, the AI drafts one, along with a short note for whichever contractor would
handle it. Another automation checks which unit the message is about, then decides whether
to alert you, based on how urgent it is, the time of day, and how many alerts have already
gone out recently. A genuine emergency reaches your phone with a button to approve a reply.
Nothing goes to a tenant until you tap that button. A board shows everything currently open,
updating itself automatically.

The one sentence that matters: it tells you what a message says and what a fixed rule
concluded from it. It never decides on its own that something can wait.

## The Automations That Do The Work

Everything below is one of these. Naming them is deliberate, because it means every claim
in this document can be traced to a specific, real piece of the build rather than a vague
"the system."

| Automation | What it's responsible for |
|---|---|
| **Email Intake** | Watches the maintenance mailbox and picks up new messages |
| **Web Form Intake** | Receives a submission from the online report form |
| **The Core** | Reads and classifies every message, runs the safety check, writes the reply drafts |
| **Unit Matching & Routing** | Works out which unit a message is about, and decides whether an alert is needed |
| **Alert Sending** | Sends the manager alert and its approve/hold buttons |
| **Approval Handling** | Receives your button tap and is the only place a reply is ever sent from |
| **Unanswered-Emergency Check** | Runs every 15 minutes and re-alerts if a genuine emergency hasn't been acknowledged |
| **The Board** | Renders the current list of open requests, and the detail page for each one |
| **Daily Summary** | An optional once-a-day email of open emergencies and anything overdue, switched off by default |
| **Quiet-Inbox Check** | An optional alert to you, not the tenant-facing side, if new messages stop arriving for an unusually long time, switched off by default |

Two channels carry the human side of this: **Telegram** is where the manager alert and the
approve/hold buttons live, and **email**, through your own mailbox, is the only channel a
tenant ever hears back on. Everything is recorded in one secure database, so nothing depends
on anyone's memory of what happened.

## The Journey Of One Request

**A message arrives.** Whether it came in by email or through the web form, it lands in the
same place: **the Core**. The Core strips out quoted reply chains, email signatures, and
footer boilerplate, so what gets read is just the tenant's actual words.

**It checks whether this is new.** Before anything else happens, the Core checks whether
this exact message was already reported in the last 24 hours, and separately whether it is
actually a reply to a request that is already open. A tenant answering "thanks, when's
someone coming?" does not create a second card on the board or trigger a second alert. It
attaches to the original request instead.

**The AI reads it.** The cleaned message is sent to an AI reading model, provided by OpenAI,
which returns a structured judgment: how urgent this is, which trade it needs, whether a
unit number was given, and whether the message touches anything legally sensitive, like a
disability accommodation request. The AI is never told it can override a safety rule. It
only ever describes what the message says.

**A fixed safety check runs afterward.** Separately from the AI, a list of specific
dangerous words and phrases, things like a gas smell, active flooding, no heat, or a smoke
smell, is checked against the same message. If one matches, the priority is raised to the
highest level, regardless of what the AI decided. This check can only push urgency up, never
down, and every time it fires, it's recorded as an event so there is a record of exactly why
something was flagged. See "What The Safety Check Looks For" below.

**The request is recorded no matter what.** Even if the AI call fails outright, times out,
or returns something unusable, the request is still saved and marked for your review. There
is no path where a message simply disappears because something went wrong upstream.

**A reply gets drafted, unless it shouldn't.** If the request is a normal maintenance issue,
the AI writes a short tenant reply and a separate note for a contractor. If the request
touches something legally sensitive, like a disability accommodation, no draft is written at
all. That decision is never left to a machine, and the reason is explained on the board.

**The unit gets matched, and a decision is made about alerting you.** A separate step checks
the unit mentioned against your property list, and decides whether this needs to reach your
phone right now, based on the urgency, the time of day, and how many alerts have already
gone out in the last hour. A true emergency always reaches you, day or night. See "How
Alerts Are Decided" below.

**You get a tap-to-approve alert, or you don't.** For anything urgent, an alert reaches your
phone through Telegram with the tenant's own words, the unit, and buttons. For a genuine
emergency, those buttons are approve, hold, and not an emergency. Routine items go straight
to the board with no alert at all, so your phone only makes noise when it should.

**Nothing reaches a tenant until you tap approve.** When you approve, the drafted reply is
sent through your mailbox, and the alert on your phone updates to show it's done. A second
tap on the same alert does nothing; the system will not send the same reply twice, because
it checks whether it's already been sent before it does anything.

## Why The AI Never Has The Final Say

This is the most important design choice in the whole build, so it's worth explaining
directly.

The AI's only job is to read a message and describe what it says. It is never asked, and
never allowed, to decide on its own that a safety rule should be ignored. The list of
dangerous words and phrases runs completely separately, after the AI, using plain fixed
rules rather than any kind of judgment call. It can only raise urgency, never lower it.

This matters for a reason beyond consistency. A forwarded newsletter, a marketing email, or
someone who has read too much about chatbots online could, in theory, put text into a
message designed to talk an AI out of its instructions. Even if that worked, the fixed
safety check runs afterward and doesn't reason about anything; it's checking whether a word
is present. There's nothing to talk it out of.

## What The Safety Check Looks For

The check scans for specific, unambiguous language: a gas smell, carbon monoxide, smoke or
a burning smell, active flooding or a burst pipe, sewage backup, no heat, no water, no air
conditioning during a heat event, a security or lock failure, and exposed or sparking
wiring. Any of these forces the request to the top of the list, no matter what the AI
concluded on its own.

It's also careful about wording that looks dangerous but isn't. "There's no smell of gas"
does not trigger the gas check, because the check understands negation, not just keywords.
The bar is set to fire more often than strictly necessary rather than less: an unnecessary
alert costs you a phone call, but a missed one costs far more, and every fire is logged so
you can see exactly why something happened.

A few boundaries were tuned specifically after watching how the AI handled real edge cases.
A squeaky door stays routine unless the message also mentions being locked out, blocked in,
or hurt. A ceiling drip that's contained with a bucket stays urgent rather than an emergency,
unless the message also describes spreading water or a hazard near electrical wiring.

There is also a fallback for messages that simply don't say enough to act on, whether
because they're garbled, unreadable, or missing basic detail. Those are never guessed at.
They're flagged for a person to read, the same as anything the AI itself couldn't classify.

## How Alerts Are Decided

Every message is read and sorted the instant it arrives, day or night. What's decided
separately is whether anything makes a sound.

| Urgency | During business hours | Outside business hours |
|---|---|---|
| Emergency | Alerts you immediately | Alerts you immediately, no exception |
| Urgent | A quiet notification | Held until morning |
| Needs a person's judgment, with a safety word present | A quiet notification | Alerts you immediately |
| Needs a person's judgment, nothing safety-related | A quiet notification | Held until morning |
| Routine | Shows on the board only | Shows on the board only |

Five messages arriving overnight, three routine, one urgent, one possible gas smell,
produce exactly one buzz on your phone. That's deliberate. The one channel that's supposed
to wake you up only earns your trust if it never cries wolf.

There's also a cap on how many alerts can go out in an hour, so a burst of messages during a
real incident doesn't flood your phone, and a request that's already been handled is never
alerted on again, so re-checking something doesn't accidentally re-open it.

One more thing worth being direct about: how old a request is never triggers a phone alert
by itself. An old routine item just gets flagged as overdue on the board and in the daily
summary. Putting a two-week-old squeaky door on the same alert channel as a gas leak would
ruin the one thing that makes that channel worth having.

## Nothing Sends Twice, And Nothing Sends Without You

This is the guarantee the entire advisory-only design rests on: nothing reaches a tenant
unless you tap approve, and a second tap can never send a second reply.

Both are enforced the same way. Before anything is sent, the system checks whether this
request has already been marked as answered. If it has, nothing happens, and you see a
message telling you it was already sent. There's no separate check bolted on afterward; the
send step itself is conditional on that lookup succeeding.

The same protection covers the cases where nothing should ever be sent at all. A request
flagged as legally sensitive cannot be approved into a reply, no matter what. A request the
AI or the safety check couldn't confidently classify cannot either. Those aren't settings
someone could accidentally switch off; they're conditions checked at the moment of sending.

## What It Deliberately Refuses To Do

These aren't gaps. They're the design.

It never contacts a vendor. It writes the note you would have written, and you send it.

It never hides, filters, or closes anything on its own. Every message that arrives gets a
record, including spam and vendor mail, sorted to the bottom rather than deleted.

It never sends a reply without your tap, in every case, with no setting anywhere to change
that.

Age alone never triggers a phone alert. An old request only ever becomes a flag on the board
and in the daily summary.

A request touching disability accommodation or another legally sensitive area never gets a
drafted reply at all. That decision belongs to a person who knows your properties and your
obligations, not a model with an opinion.

A request that's already been handled can never be re-alerted or re-sent by a later check.

## What It Genuinely Cannot Do Yet

These are honest limits, not policy choices.

It does not write anything into your property management software. You still create the
work order the way you do today. What it saves is the reading, the sorting, and the first
draft, not the data entry.

It cannot look up a real tenant, unit, or lease on its own. It only knows what the message
itself says. If a tenant writes "2B," the record says "2B." If they don't mention a unit, it
says so honestly rather than guessing.

It does not interpret a photo. It notices one was attached and shows that on the board,
nothing more. It does not transcribe a phone call or a voicemail.

It has only been tested in English and Spanish. Any other language is untested, not
unsupported.

It cannot tell you what your legal obligations are. Response time targets are numbers you
set, treated as operational goals, never as a legal deadline, and nothing it writes states
or implies a legal obligation on your behalf.

It does not learn from your corrections by itself. If you mark something as not actually an
emergency, that correction is recorded as a note for a person to review. Nothing about how
it behaves changes on its own, ever, without someone deliberately changing the rules and
telling you what changed.

The only outbound channel to a tenant today is email. There is no text-message option in
this build yet.

## Running This Inside Your Business

### The short version

Everything you've seen demonstrated runs using stand-ins for a real business's accounts.
Putting it into your business means swapping each stand-in for the thing you already use.
The logic that reads and sorts your messages doesn't change at all.

Nothing here asks you to move into a new platform, retrain your tenants, or upgrade your
property management software.

### What changes, item by item

| In the demonstration | In your business |
|---|---|
| An alert to a test phone | An alert to your team's actual phones |
| A dedicated demo mailbox | Your existing maintenance email address, forwarded |
| Replies sent from a demo address | Replies sent from your own domain, so they land in the inbox rather than spam |
| A sample list of units | Your real unit list, exported once from whatever software you already use |
| Response targets I chose | The response targets you actually promise your owners |
| Quiet hours set to a generic window | Your hours, your timezone, your on-call rules |
| A shared, temporary link to the board | A private link for each person on your team |
| Running on a laptop | A small server in a US data center, in your company's name |

### What you'd need to provide

1. **A forwarding rule on your maintenance inbox.** A copy of incoming mail goes to the
   automation. Takes about five minutes to add, and about five minutes to remove.
2. **Your unit list.** One export from whatever software you already use: property name,
   unit label, and the tenant's contact details if you have them.
3. **Your escalation contacts.** Who gets the emergency alert, and who's the backup.
4. **Your response targets.** What you already tell owners for an emergency, an urgent
   request, and a routine one.
5. **Your company details.** The name that appears on a tenant reply, your office hours, and
   whether replies should sound formal or warm.

No software access, no admin credentials to your property management system, and no IT
involvement required.

### What does not change

**Your property management software.** Nothing is written into it, nothing is read from it,
and no plan upgrade is required. You still create the work order the way you do now.

**Your tenants.** They keep reporting problems exactly where they report them today. No
portal to teach, no app to install, no new address to remember.

**Your vendors.** Nothing here contacts a vendor directly. It writes the note, and you send
it.

**Everything after triage.** Cost estimates, owner approval, vendor selection, scheduling,
invoicing, and closing the job all stay exactly as they are.

### What a first month looks like

**Week one, watching only.** The forwarding rule goes on and nothing sends. Every message
gets read and sorted, and drafts get written, but nobody receives anything and your phone
stays quiet. At the end of the week, you compare what it flagged against what your team
actually did. This is the cheapest way to find out whether it's reading your mail correctly,
and it costs you nothing but a forwarding rule.

**Week two, alerts on.** Emergency alerts start reaching your phone. Replies still aren't
sending. You get a feel for how often it buzzes, and whether the things it escalates are the
things you'd escalate.

**Week three, replies on, to a test inbox.** Approved replies start sending, but only to an
address you control, not to tenants yet. You approve a few and read exactly what went out.

**Week four, live.** Approved replies reach tenants. By this point you've watched it read
three weeks of your real mail, and you know what it does.

At every stage, the tap is yours. There is no stage where it starts sending on its own.

### How you turn it off

Remove the forwarding rule. That's the whole procedure, and you're back to exactly the
inbox you have today, in about five minutes. Nothing has been moved, nothing has been
migrated, and none of your data is trapped anywhere.

This is worth saying up front rather than at the end. The reason this is a reasonable thing
to try is that trying it is fully reversible.

### Where your information is kept, and who can see it

Everything lives on one server in a US data center, reachable only over an encrypted
connection, with access limited to whoever administers it for you. Message text is sent to
OpenAI for the reading step. OpenAI does not train its models on that data and deletes it
within 30 days. Message content is kept on your own server for 30 days and then removed, and
that window is something you can change.

What's stored: tenant name, unit, contact details, the message itself, the classification,
the drafts, and timestamps. What's never intentionally stored: social security numbers,
lease documents, payment or bank details, screening reports, or identity documents. If a
tenant happens to include one of those in a message, the message is stored as written, which
is worth knowing when you decide on your retention window.

If you ever want everything deleted, it can be done within a day, and you can be shown that
it's gone.

### What it will not do for you

It will not create the work order in your software. It will not contact a vendor. It will
not reply to a tenant without you tapping approve. It will not catch every emergency, and
some days it will escalate something that turns out to be nothing, which costs you a phone
call. It will not read a photo, only tell you one's attached. It will not handle a phone
call or a voicemail; email and the web form only, today. It will not text a tenant, because
there is no text-message channel built yet. It will not tell you what your legal obligations
are; that's not something any tool should claim.

And it does not improve itself overnight. When it gets something wrong, that's recorded,
someone changes a rule, and you're told what changed. Nothing about how it behaves shifts
without a person deciding it should.
