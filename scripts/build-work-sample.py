"""Build a contact-free PDF case study from captured local n8n editor screenshots."""
from pathlib import Path
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader
import re

ROOT = Path(__file__).resolve().parents[1]
TMP = ROOT / "docs" / "work-sample-screenshots"
OUT = ROOT / "output" / "pdf" / "maintenance-triage-automation-work-sample.pdf"
OUT.parent.mkdir(parents=True, exist_ok=True)
W, H = 792, 612
INK, GREEN, MUTED, PALE, LINE = map(HexColor, ["#172334", "#006249", "#526173", "#e9f3ee", "#b8cec3"])
WHITE = HexColor("#ffffff")
fontdir = ROOT / "concept-brief" / "assets" / "fonts"
pdfmetrics.registerFont(TTFont("Geist", str(fontdir / "geist-variable.ttf")))
pdfmetrics.registerFont(TTFont("Manrope", str(fontdir / "manrope-variable.ttf")))
c = canvas.Canvas(str(OUT), pagesize=(W, H), pageCompression=1)
c.setTitle("Maintenance Request Triage | Automation Work Sample")
c.setAuthor("Automation work sample")
pages = []

def text(x,y,s,size=11,font="Manrope",color=INK):
    c.setFillColor(color); c.setFont(font,size); c.drawString(x,y,s)

def lines(s,max_width,size=11,font="Manrope"):
    words=s.split(); out=[]; row=""
    for word in words:
        cand=(row+" "+word).strip()
        if pdfmetrics.stringWidth(cand,font,size)>max_width and row:
            out.append(row); row=word
        else: row=cand
    if row: out.append(row)
    return out

def para(x,y,s,width=680,size=11,leading=16,color=INK):
    for row in lines(s,width,size): text(x,y,row,size,color=color); y-=leading
    return y

def header(kicker,title,sub=""):
    c.setStrokeColor(GREEN); c.setLineWidth(3); c.line(42,H-30,74,H-30)
    text(42,H-55,kicker.upper(),9,color=GREEN)
    text(42,H-88,title,25,"Geist")
    if sub: para(42,H-111,sub,700,10.5,15)

def footer(page,total):
    c.setStrokeColor(LINE); c.setLineWidth(.8); c.line(42,39,W-42,39)
    text(42,22,"LOCAL DEMO  /  SYNTHETIC DATA  /  WORK SAMPLE",8,color=MUTED)
    text(W-68,22,f"{page} / {total}",8,color=MUTED)

def end(): pages.append(1); c.showPage()

def box(x,y,w,h,fill=PALE):
    c.setFillColor(fill); c.roundRect(x,y,w,h,9,stroke=0,fill=1)

def screenshot(name,crop,x=42,y=130,w=708,max_h=None):
    img=Image.open(TMP / f"workflow-{name}-full.png").convert("RGB")
    img=img.crop(crop)
    h=w*img.height/img.width
    if max_h and h>max_h:
        h=max_h; w=h*img.width/img.height; x=(W-w)/2
    c.setFillColor(WHITE); c.setStrokeColor(LINE); c.roundRect(x-1,y-1,w+2,h+2,6,stroke=1,fill=1)
    c.drawImage(ImageReader(img),x,y,width=w,height=h,mask="auto")
    return h

def workflow_page(num,kicker,title,summary,name,crop,bullets,caption,image_x=42,image_w=708):
    header(kicker,title,summary)
    h=screenshot(name,crop,x=image_x,y=202,w=image_w)
    text(42,189,caption,9,color=GREEN)
    y=163
    for b in bullets:
        c.setFillColor(GREEN); c.circle(48,y+3,2.5,stroke=0,fill=1)
        y=para(62,y,b,680,10.5,15)-8
    end()

def detail_page(kicker,title,summary,name,crop,caption,body):
    header(kicker,title,summary)
    h=screenshot(name,crop,y=156,max_h=320)
    text(42,143,caption,9,color=GREEN)
    box(42,60,708,66)
    para(56,104,body,678,10.2,15)
    end()

# 1 - Overview
header("Automation case study","Maintenance request triage",
       "A local n8n demonstration that turns unstructured tenant messages into manager-controlled maintenance decisions.")
box(42,236,708,191)
text(62,389,"THE PROBLEM",10,color=GREEN)
para(62,365,"Maintenance requests arrive through email, forms and messages with no consistent priority, trade or property context. A manager must read, sort and follow up on each one - often after hours.",660,14,21)
text(62,294,"THE BUILD",10,color=GREEN)
para(62,270,"Five connected n8n workflows normalize intake, classify and store tickets, continue tenant clarification, prepare a manager decision, and run operational checks. Postgres owns durable state; Airtable is the manager view.",660,12,18)
text(42,189,"HUMAN APPROVAL IS THE SEND GATE",12,"Geist",GREEN)
para(42,168,"Vendor email is sent only after a manager selects a vendor in Telegram. A Hold or review-only path sends no vendor email. The tenant hears that a provider was contacted only after SMTP succeeds.",700,11,16)
end()

# 2 - architecture
header("System design","One connected decision flow",
       "The workflow exports, Postgres schema and local n8n editor show five published operational workflows. Historical exports remain in the repository but are not part of this live set.")
rows=[
 ("01","Tenant Intake","IMAP / form -> normalized request -> Triage Engine -> pairing link"),
 ("02","Triage Engine","Deduplicate -> strict model output -> safety rules -> Postgres ticket / draft"),
 ("03","Tenant Telegram","Pairing, direct issue intake, clarification and factual status replies"),
 ("04","Manager Desk","Vendor match -> Telegram choice -> one claimed SMTP send -> tenant update"),
 ("05","Operations","Digest, heartbeat, unanswered emergencies and Airtable conversation sync"),
]
y=423
for n,title,desc in rows:
    text(55,y,n,12,color=GREEN); text(98,y,title,14,"Geist"); text(98,y-20,desc,9.6,color=MUTED)
    c.setStrokeColor(LINE); c.line(55,y-32,739,y-32); y-=67
box(42,55,708,48)
para(56,85,"State and handoffs: Postgres is authoritative for tickets, messages, callbacks and one-send claims. Airtable mirrors requests and conversations and supplies demo vendor/tenant rosters. OpenAI output remains advisory.",675,9.7,14)
end()

# 3 intake
workflow_page(3,"Workflow 01 / Tenant Intake","Two sources, one triage path",
 "Email IMAP and the n8n form normalize into one message contract and invoke the Triage Engine.","intake",(145,355,1815,780),[
 "The intake context is preserved before the sub-workflow call so source identifiers and reply details survive database lookups.",
 "A stored ticket can trigger a one-time Telegram pairing email; the system subject prefix prevents shared-mailbox loops."
],"Actual n8n editor capture - complete 15-node workflow")

# 4 engine overview
workflow_page(4,"Workflow 02 / Triage Engine","Classify, check, persist",
 "The reusable core takes normalized text and returns a stored outcome or an existing-ticket/thread result.","engine",(160,385,1800,735),[
 "It deduplicates and threads before calling the Responses API through HTTP Request. The installed n8n node did not expose the required strict response contract.",
 "Fixed safety rules can raise urgency; model failure and sensitive requests route to human review."
],"Actual n8n editor capture - complete 25-node workflow")

detail_page("Workflow 02 / Detail A","The classifier and safety boundary",
 "This enlarged editor section shows the model branch joining the deterministic safety step.","engine",(500,395,1170,690),
 "Actual editor crop - classification, safety, persistence",
 "The model supplies structured priority, trade, missing information and rationale. Post-model rules handle known safety and maintenance edge cases. Postgres records the result and audit events before any draft path continues.")

detail_page("Workflow 02 / Detail B","Draft only when allowed",
 "The draft path branches from the persisted ticket and rejoins priority routing.","engine",(1100,405,1890,690),
 "Actual editor crop - draft and output routing",
 "Review-only and human-only requests bypass drafting. Eligible maintenance requests get a structured vendor draft; the workflow then routes emergency, urgent, routine and review outputs to downstream handling.")

# 7 tenant
workflow_page(7,"Workflow 03 / Tenant Telegram","A bounded tenant conversation",
 "The dedicated demo tenant bot handles pairing, direct requests, missing details, new-issue commands and status questions.","tenant",(155,260,1820,900),[
 "A generic opening is buffered until the tenant names a concrete symptom, so it creates no ticket or manager alert.",
 "Status intent is handled before new-ticket creation; clarification reuses the same request and calls the manager only once reviewable."
],"Actual n8n editor capture - complete 40-node workflow")

detail_page("Workflow 03 / Detail A","Pair or route the message",
 "This enlarged section shows the entry gate and conversation router.","tenant",(175,280,1015,790),
 "Actual editor crop - pairing and message routing",
 "The bot loads the chat and reattaches trigger context after Postgres lookup. Pairing claims a one-time token. Other messages are separated into welcome, new ticket, preliminary buffer, status and clarification paths.")

detail_page("Workflow 03 / Detail B","Keep one issue in one thread",
 "This enlarged section shows ticket creation, status reply and clarification routes.","tenant",(865,300,1840,885),
 "Actual editor crop - new ticket, status and clarification",
 "A concrete issue calls the Triage Engine and links the ticket to the chat. Missing fields prompt the tenant; a status question records one factual reply; a completed issue can invoke the Manager Desk.")

# 10 manager
workflow_page(10,"Workflow 04 / Manager Desk","Approval before vendor contact",
 "The manager path matches candidates from Airtable and sends a Telegram alert with only valid choices plus Hold.","manager",(155,175,1825,965),[
 "Review-only, incomplete and no-match tickets cannot expose a vendor-send button.",
 "The callback claims a unique Postgres send attempt before SMTP; successful delivery is recorded before any tenant provider-contacted update."
],"Actual n8n editor capture - complete 35-node workflow",image_x=86,image_w=620)

detail_page("Workflow 04 / Detail A","Candidate and alert path",
 "The upper route loads the ticket, finds matching vendors and assembles the manager choice.","manager",(170,315,1140,705),
 "Actual editor crop - ticket lookup, vendor matching, alert preparation",
 "Candidates match property and trade and are ordered by configured vendor priority. The request and conversation state are mirrored into Airtable, while Postgres retains the durable approval state.")

header("Workflow 04 / Detail B","One approved SMTP send",
       "The lower route is activated by a manager Telegram callback.")
screenshot("manager",(165,745,1000,950),y=323)
screenshot("manager",(960,745,1815,950),y=140)
text(42,129,"Actual editor crops - callback claim, SMTP and recorded outcomes",9,color=GREEN)
box(42,52,708,62)
para(56,92,"The unique vendor-send claim prevents a second tap from resending. On SMTP success, the result is persisted before the tenant update. A failed send leaves the tenant uninformed about provider contact.",678,10.2,15)
end()

# 13 operations
workflow_page(13,"Workflow 05 / Operations","Scheduled checks and sync",
 "Four clean lanes keep routine monitoring apart from ticket ingestion and manager approval.","operations",(260,230,1700,950),[
 "Daily digest and operator heartbeat are implemented but config-gated off in the clean demo state.",
 "Unanswered emergencies can re-alert the manager; conversation sync appends stored messages to Airtable. Age alone creates overdue visibility, not an emergency phone alert."
],"Actual n8n editor capture - complete 17-node workflow")

# 14 evidence
header("Verification and limits","What the demo actually proves",
       "All results below come from synthetic fixtures, controlled mailboxes or local workflow checks - not a client deployment.")
text(42,435,"VERIFIED",11,"Geist",GREEN)
facts=[
 "Stage 8 five-run rehearsal: 30/30 expected priorities across six fixtures x five clean runs; zero fixture-mode Telegram sends.",
 "Stage 9 conversation-routing regression and structural validation passed; live webhook status question created no extra ticket or manager action.",
 "Controlled live tests included form ingestion, Airtable request sync, Telegram manager alerts and an approved SMTP send.",
 "Six-fixture historical nano scorecard: 6/6 priority matches, zero under/over-escalations and zero missed safety signals; average call-plus-draft latency 10.9 s."
]
y=411
for f in facts:
    c.setFillColor(GREEN); c.circle(48,y+3,2.5,stroke=0,fill=1)
    y=para(62,y,f,670,10.4,15)-13
text(42,248,"LIMITATIONS + MANUAL STEPS",11,"Geist",GREEN)
limits=[
 "The full 30-fixture x three-run nano hardening gate failed with under-escalations and missed safety signals. The live workflow now uses gpt-5.6-luna; broad accuracy is unproven.",
 "Telegram callbacks need a current HTTPS tunnel and operator-controlled bot/chat setup. Final tenant-originated live checks remain operator actions.",
 "The demo bot represents one known tenant; pairing links do not verify identity. No PMS integration, appointment scheduling, automatic closure or production hosting is included."
]
y=225
for f in limits:
    c.setFillColor(GREEN); c.circle(48,y+3,2.5,stroke=0,fill=1)
    y=para(62,y,f,670,10.2,14)-10
end()

total=len(pages)
# Page numbers are added in a second pass to keep layout functions simple.
c.save()
from pypdf import PdfReader, PdfWriter
from io import BytesIO
r=PdfReader(str(OUT)); writer=PdfWriter()
for i,page in enumerate(r.pages,1):
    b=BytesIO(); fc=canvas.Canvas(b,pagesize=(W,H)); fc.setStrokeColor(LINE); fc.line(42,39,W-42,39)
    fc.setFont("Manrope",8); fc.setFillColor(MUTED)
    fc.drawString(42,22,"LOCAL DEMO  /  SYNTHETIC DATA  /  WORK SAMPLE")
    fc.drawRightString(W-42,22,f"{i} / {total}")
    fc.save(); b.seek(0); page.merge_page(PdfReader(b).pages[0]); writer.add_page(page)
with OUT.open("wb") as f: writer.write(f)
print(f"{OUT} ({total} pages)")
