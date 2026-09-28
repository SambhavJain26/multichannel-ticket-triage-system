"""Build a contact-free PDF case study from captured local n8n editor screenshots."""
from pathlib import Path
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader

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
    path=TMP / f"workflow-{name}-full.png"
    if not path.exists(): path=TMP / f"workflow-{name}.png"
    img=Image.open(path).convert("RGB")
    img=img.crop(crop)
    h=w*img.height/img.width
    if max_h and h>max_h:
        h=max_h; w=h*img.width/img.height; x=(W-w)/2
    c.setFillColor(WHITE); c.setStrokeColor(LINE); c.roundRect(x-1,y-1,w+2,h+2,6,stroke=1,fill=1)
    c.drawImage(ImageReader(img),x,y,width=w,height=h,mask="auto")
    return h

def output_shot(filename,crop,x=42,y=130,w=708):
    img=Image.open(TMP / filename).convert("RGB").crop(crop)
    h=w*img.height/img.width
    c.setFillColor(WHITE); c.setStrokeColor(LINE); c.roundRect(x-1,y-1,w+2,h+2,6,stroke=1,fill=1)
    c.drawImage(ImageReader(img),x,y,width=w,height=h)
    return h

def workflow_page(kicker,title,summary,name,crop,flow,caption,image_x=42,image_w=708):
    header(kicker,title,summary)
    screenshot(name,crop,x=image_x,y=202,w=image_w)
    text(42,189,caption,9,color=GREEN)
    for i,(label,body) in enumerate(flow):
        y=166-i*29
        text(42,y,label.upper(),9.4,"Geist",GREEN)
        para(119,y,body,629,9.7,13)
    end()

def detail_page(kicker,title,summary,name,crop,caption,body,shot_y=156):
    header(kicker,title,summary)
    screenshot(name,crop,y=shot_y,max_h=320)
    text(42,shot_y-13,caption,9,color=GREEN)
    box(42,60,708,66)
    para(56,104,body,678,10.2,15)
    end()

# 1 - Prospect overview with a genuine output screenshot
header("Automation case study","Maintenance request triage",
       "A working local demo that sorts incoming maintenance requests and brings clear, actionable choices to the property manager.")
output_shot("airtable-requests.png",(52,48,1090,335),y=218)
text(42,204,"LIVE DEMO OUTPUT  /  AIRTABLE REQUESTS  /  SYNTHETIC RECORDS",9,color=GREEN)
text(42,170,"The problem",12,"Geist")
para(42,151,"Tenant messages arrive through different channels, in different words, without a reliable priority or next step. A manager still has to read, sort and chase details before acting.",708,10.4,15)
text(42,105,"What I built",12,"Geist")
para(42,86,"Five connected n8n workflows organize each request, ask for missing detail, surface the right manager decision and record what happened. Vendor contact stays behind a human approval.",708,10.4,15)
end()

# 2 - architecture
header("System design","One connected decision flow",
       "Email, a web form and a tenant Telegram bot feed one triage process. The manager sees the result in Airtable and approves any vendor email in Telegram.")
rows=[
 ("01","Tenant Intake","Email or form -> one standard request -> Triage Engine"),
 ("02","Triage Engine","Read issue -> check urgency and trade -> save ticket"),
 ("03","Tenant Telegram","Collect missing detail or answer a status question"),
 ("04","Manager Desk","Show vendor choices -> manager approves or holds -> record outcome"),
 ("05","Operations","Summaries, unanswered-emergency checks and conversation sync"),
]
y=423
for n,title,desc in rows:
    text(55,y,n,12,color=GREEN); text(98,y,title,14,"Geist"); text(98,y-20,desc,9.6,color=MUTED)
    c.setStrokeColor(LINE); c.line(55,y-32,739,y-32); y-=67
box(42,55,708,48)
para(56,85,"Behind the screens: n8n routes work; Postgres keeps the ticket and conversation history; Airtable is the manager's visible workspace. The AI suggests an interpretation, while fixed safety rules and manager approval control action.",675,9.7,14)
end()

# 3 intake
workflow_page("Workflow 01 / Tenant Intake","Two sources, one intake path",
 "Email and web-form requests enter the same triage process.","intake",(145,355,1815,780),[
 ("Trigger","A new maintenance email or form submission starts the flow."),
 ("Steps","Normalize the message, keep its source context and pass it to the Triage Engine."),
 ("Decision","Send one onboarding message when a tenant can continue the request in Telegram."),
 ("Output","A saved request, manager handoff and form confirmation or pairing email.")
],"Actual n8n editor capture - every node visible in the full canvas")

# 4 engine overview
workflow_page("Workflow 02 / Triage Engine","Read, check and save",
 "One engine handles the request after any intake channel has normalized it.","engine",(160,385,1800,735),[
 ("Trigger","Tenant Intake or Tenant Telegram submits a concrete maintenance issue."),
 ("Steps","Check for an existing ticket, classify priority and trade, then save the result."),
 ("Decision","Fixed safety checks can raise urgency; sensitive or unclear cases go to review."),
 ("Output","A ticket with a summary, priority, trade, history and an eligible draft.")
],"Actual n8n editor capture - every node visible in the full canvas")

detail_page("Workflow 02 / Detail A","The classifier and safety boundary",
 "The model's reading is checked before the ticket becomes a manager decision.","engine-detail-a",(125,225,950,540),
 "Actual editor crop - classification, safety check and saved request",
 "The AI identifies the issue, priority, trade and missing details. Separate fixed rules then check for safety signals and can raise urgency. The ticket and the reason for its priority are saved before any draft is prepared.",shot_y=180)

detail_page("Workflow 02 / Detail B","Draft only when allowed",
 "The saved result determines whether a vendor note should be drafted.","engine-detail-b",(300,210,1125,530),
 "Actual editor crop - draft and output routing",
 "A request that needs human review skips the automatic draft. For eligible maintenance work, the system prepares a vendor note and routes the saved ticket by priority for the next workflow.",shot_y=180)

# 7 tenant
workflow_page("Workflow 03 / Tenant Telegram","Continue the conversation",
 "The tenant bot keeps clarification and status questions tied to the right request.","tenant",(155,260,1820,900),[
 ("Trigger","A tenant sends a Telegram message or opens a one-time pairing link."),
 ("Steps","Load the conversation, recognize the intent and keep each issue in one thread."),
 ("Decision","A vague opening prompts for a symptom; a status question does not create a ticket."),
 ("Output","A clarification, factual status reply or complete request for manager review.")
],"Actual n8n editor capture - every node visible in the full canvas")

detail_page("Workflow 03 / Detail A","Pair or route the message",
 "The first decision distinguishes a pairing link from an ordinary tenant message.","tenant",(175,280,1015,790),
 "Actual editor crop - pairing and message routing",
 "A pairing link connects the chat to an existing request. Other messages are routed to a welcome, new issue, clarification or status path, using the saved conversation so the tenant does not have to start over.")

detail_page("Workflow 03 / Detail B","Keep one issue in one thread",
 "The route for a concrete issue stays separate from status and missing-detail replies.","tenant",(865,300,1840,885),
 "Actual editor crop - new ticket, status and clarification",
 "A concrete symptom becomes one saved request. Missing details prompt targeted questions; a progress question returns the recorded status. When the request is complete, the manager receives it for a decision.")

# 10 manager
workflow_page("Workflow 04 / Manager Desk","The manager makes the call",
 "A complete request becomes a clear choice of matching vendors or Hold.","manager",(155,175,1825,965),[
 ("Trigger","The Triage Engine or Tenant Telegram submits a reviewable request."),
 ("Steps","Match vendors by property and trade; show the summary and draft to the manager."),
 ("Decision","The manager selects a vendor or Holds. Review-only cases show no send choice."),
 ("Output","One approved vendor email, a recorded result and a tenant update after send success.")
],"Actual n8n editor capture - every node visible in the full canvas",image_x=86,image_w=620)

detail_page("Workflow 04 / Detail A","Match vendors before alerting",
 "This route prepares a manager message from the saved request and vendor roster.","manager-detail-a",(195,110,1030,370),
 "Actual editor crop - ticket lookup and vendor matching",
 "The flow finds vendors serving the request's property and trade, then presents only those valid options. The request also appears in the manager's Airtable workspace, while the approval remains recorded with the ticket.",shot_y=215)

header("Workflow 04 / Detail B","One approved vendor email",
       "The lower route starts when the manager taps a vendor button in Telegram.")
screenshot("manager",(165,745,1000,950),y=323)
screenshot("manager",(960,745,1815,950),y=140)
text(42,129,"Actual editor crops - approval, email and recorded outcome",9,color=GREEN)
box(42,52,708,62)
para(56,92,"The ticket can claim only one vendor send, so a repeat tap cannot resend it. After the approved email succeeds, the result is saved and the tenant is told a provider was contacted.",678,10.2,15)
end()

# 13 operations
workflow_page("Workflow 05 / Operations","Keep the queue visible",
 "Scheduled checks work from saved request and conversation state.","operations",(260,230,1700,950),[
 ("Trigger","Time-based schedules start separate summary, alert and sync lanes."),
 ("Steps","Read open requests, unanswered emergencies and unsynced conversations."),
 ("Decision","Aging marks an item overdue; only an unanswered emergency can re-alert."),
 ("Output","A daily summary, operator check or updated conversation view in Airtable.")
],"Actual n8n editor capture - every node visible in the full canvas",image_x=126,image_w=540)

detail_page("Workflow 05 / Detail A","Summary and alert lanes",
 "The scheduled checks read saved state and run independently of the intake flow.","operations",(270,230,1290,700),
 "Actual editor crop - digest, operator heartbeat and emergency re-alert",
 "One lane prepares a daily email summary; another checks whether the inbox has gone quiet. The emergency lane looks only for requests that still need a manager response.")

header("Workflow 05 / Detail B","Conversation sync",
       "The final lane moves saved conversation entries into the manager's Airtable view.")
screenshot("operations",(280,730,1010,970),y=315,max_h=160)
screenshot("operations",(930,730,1760,970),y=132,max_h=160)
text(42,121,"Actual editor crops - select, append and mark synced",9,color=GREEN)
box(42,52,708,55)
para(56,88,"The schedule selects unsynced messages, appends them to Airtable and records that the sync completed. This keeps the visible conversation tied to its saved request.",678,10.2,15)
end()

# 14 - live output: Requests
header("Demo output / Requests","A sortable manager view",
       "The saved request is mirrored into Airtable, where the manager can see its reference, status, priority and source.")
output_shot("airtable-requests.png",(52,48,1090,365),y=208)
text(42,193,"ACTUAL AIRTABLE GRID  /  SYNTHETIC DEMO REQUESTS",9,color=GREEN)
box(42,77,708,91)
text(56,143,"What the visible rows show",11,"Geist",GREEN)
para(56,123,"The same workspace contains requests that began in Telegram, email and the web form. The priority is saved with each reference, so the manager can scan the queue before opening a conversation.",675,10.5,16)
end()

# 15 - live output: Conversations
header("Demo output / Conversations","The follow-up stays attached",
       "A second Airtable view records the request reference, message direction and channel for tenant follow-up.")
output_shot("airtable-conversations.png",(52,48,1090,390),y=196)
text(42,181,"ACTUAL AIRTABLE GRID  /  CONTROLLED DEMO CONVERSATIONS",9,color=GREEN)
box(42,69,708,86)
text(56,132,"Why this matters",11,"Geist",GREEN)
para(56,112,"The visible entries include an inbound tenant message and outbound follow-up tied to the same request. Email onboarding and Telegram updates are recorded in the same conversation history.",675,10.5,16)
end()

# 16 - recorded proof, presented as demo evidence only
header("Recorded checks","Verified with controlled demo traffic",
       "These checks used synthetic maintenance scenarios and controlled accounts. They describe the demonstrated build, not a client outcome.")
output_shot("n8n-intake-execution.png",(350,190,1258,510),y=234)
text(42,219,"ACTUAL N8N EXECUTION  /  SUCCESSFUL INTAKE PATH",9,color=GREEN)
evidence=[
 "Six synthetic scenarios were each run five times from clean state: 30/30 expected priorities, with zero Telegram sends in fixture mode.",
 "A controlled form request completed the intake path and appeared in the Airtable Requests view as an urgent request.",
 "A live status question produced one factual reply without opening another ticket or invoking the manager decision flow."
]
y=181
for item in evidence:
    c.setFillColor(GREEN); c.circle(48,y+3,2.5,stroke=0,fill=1)
    y=para(62,y,item,670,10.1,14)-8
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
