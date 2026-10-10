"""Build the public case study from flattened genuine application evidence."""
from pathlib import Path
from io import BytesIO
import json
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader
from pypdf import PdfReader, PdfWriter
ROOT=Path(__file__).resolve().parents[1]
ASSETS=ROOT/'docs/work-sample-screenshots/v2'
OUT=ROOT/'output/pdf/maintenance-triage-automation-work-sample.pdf'
OUT.parent.mkdir(parents=True,exist_ok=True)
W,H=792,612
INK,GREEN,MUTED,PALE,LINE=map(HexColor,['#172334','#006249','#526173','#e9f3ee','#b8cec3'])
for name,file in [('Geist','geist-variable.ttf'),('Manrope','manrope-variable.ttf')]:
    pdfmetrics.registerFont(TTFont(name,str(ROOT/'concept-brief/assets/fonts'/file)))
c=canvas.Canvas(str(OUT),pagesize=(W,H),pageCompression=1)
titles=[]; uses=[]
def text(x,y,s,size=11.5,font='Manrope',color=INK):
    c.setFillColor(color); c.setFont(font,size); c.drawString(x,y,s)
def wrap(s,width,size=11.5):
    rows=[]; row=''
    for word in s.split():
        cand=(row+' '+word).strip()
        if row and pdfmetrics.stringWidth(cand,'Manrope',size)>width:
            rows.append(row); row=word
        else: row=cand
    if row: rows.append(row)
    return rows
def para(x,y,s,width=708,size=11.5,leading=17,color=INK):
    for row in wrap(s,width,size):
        if y<49: raise ValueError('Text crosses footer: '+row)
        text(x,y,row,size,color=color); y-=leading
    return y
def header(kicker,title,sub=''):
    c.setStrokeColor(GREEN); c.setLineWidth(3); c.line(42,582,74,582)
    text(42,557,kicker.upper(),9.5,color=GREEN); text(42,524,title,25,'Geist')
    if pdfmetrics.stringWidth(title,'Geist',25)>708: raise ValueError(title)
    if sub: para(42,500,sub,708,11.5,17)
    titles.append(title)
def shot(name,top=460,width=708,height=330,x=None):
    im=Image.open(ASSETS/(name+'.png')).convert('RGB')
    scale=min(width/im.width,height/im.height,1.0); w,h=im.width*scale,im.height*scale
    if x is None: x=42+(708-w)/2
    y=top-h
    if y<49 or top>477: raise ValueError('Image bounds: '+name)
    c.setStrokeColor(LINE); c.setLineWidth(.6); c.rect(x-.5,y-.5,w+1,h+1,stroke=1,fill=0)
    c.drawImage(ImageReader(im),x,y,width=w,height=h)
    uses.append(dict(page=len(titles),image=name+'.png',width_pt=w,height_pt=h,scale=scale))
    return y
def caption(y,s,x=42,width=708): return para(x,y,s,width,10.8,15,GREEN)
def panel(x,top,w,title,body,h=106):
    c.setFillColor(PALE); c.roundRect(x,top-h,w,h,7,stroke=0,fill=1)
    text(x+15,top-25,title,13,'Geist',GREEN); para(x+15,top-47,body,w-30,11.5,17)
def end(): c.showPage()
def full(kicker,title,summary,image,items,photo_height=245):
    header(kicker,title,summary); y=shot(image,460,height=photo_height)
    caption(y-15,'Actual n8n canvas: every node visible. Readable sections follow.')
    y=min(y-48,315)
    for label,body in items:
        text(42,y,label,11.5,'Geist',GREEN); y=para(151,y,body,599,11.5,16)-12
    end()
def detail(kicker,title,summary,image,body,photo_height=290):
    header(kicker,title,summary); y=shot(image,450,height=photo_height)
    caption(y-16,'Actual editor capture: enlarged at native resolution.')
    para(42,y-51,body,708,11.5,17); end()

header('Automation case study','Maintenance request triage','From a tenant message to a reviewed request, approved vendor contact and a visible record of the outcome.')
panel(42,452,344,'The problem','Maintenance messages arrive across channels with missing detail. Managers need a clear priority, the right trade and a reliable next step.',122)
panel(406,452,344,'What I built','Five connected n8n workflows collect, clarify and organize requests, then put vendor contact behind a manager approval.',122)
y=shot('requests-classification',303,height=198)
caption(y-17,'Actual Airtable workspace with synthetic maintenance records.')
para(42,67,'The following pages show the build and a connected execution, rather than client performance claims.',708,11,16); end()

header('Architecture','Five workflows, shared state','n8n coordinates the work. Postgres retains ticket and conversation state; Airtable provides the manager view.')
rows=[('01','Tenant Intake','Email or form -> normalized request -> shared triage engine.'),('02','Triage Engine','Issue -> priority, trade and missing details -> saved ticket and eligible draft.'),('03','Tenant Telegram','Conversation -> clarification or factual status -> the same request.'),('04','Manager Desk','Vendor roster -> approval button -> email, tenant update and recorded result.'),('05','Operations','Scheduled checks -> emergency review and conversation sync to Airtable.')]
y=446
for n,title,body in rows:
    text(42,y,n,13,'Geist',GREEN); text(85,y,title,13,'Geist'); para(260,y,body,490,11,16)
    c.setStrokeColor(LINE); c.setLineWidth(.6); c.line(42,y-26,750,y-26); y-=53
text(42,158,'Demonstration scope',13,'Geist',GREEN)
para(42,134,'Demo Tenant, Maple Court, Unit 2B and the vendor names are synthetic. These captures use live OpenAI, Telegram, Airtable and Gmail through controlled demo accounts. The form was submitted in test mode. Vendor email went to a controlled demo mailbox, not a real contractor.',708,11.5,17)
para(42,64,'The visible fixture branch supplies mock classifications for rehearsal; the shown ticket journey used the live model.',708,10.8,15); end()

full('Workflow 01 / Tenant Intake','Two entrances, one request','Email and the web form feed the same engine, preserving the source message and tenant context.','intake-full',[
('Trigger','An IMAP maintenance email or a form submission.'),('Incoming data','Issue text, property, unit, reply channel and entry permission when supplied.'),('Key steps','Normalize intake; call the engine; reselect its saved ticket; create a pairing token.'),('Output','A manager handoff when reviewable, a pairing email when eligible and a form receipt.'),('Approval','Vendor sending is handled later by the Manager Desk approval route.')])
detail('Workflow 01 / Normalization','Preserve the source before triage','Both entrances become one request shape with a stable source identifier.','intake-normalize','The shared context retains the tenant message and its origin while the engine runs. Intake then reads the durable result before continuing. This avoids depending on a sub-workflow returning an item on every branch.')
detail('Workflow 01 / Handoff','Connect the tenant and manager','The saved request controls two paths: manager review and tenant onboarding.','intake-pairing','A one-time token connects an email or form request to its Telegram conversation. Reviewable requests also enter the Manager Desk. The onboarding gate prevents an ineligible or repeated pairing email.')
detail('Workflow 01 / Completion','Record delivery, then finish','The onboarding message is recorded before the form displays its receipt.','intake-complete','SMTP sends the Telegram onboarding email to the controlled demo mailbox. The delivery result is attached to the saved request history. A form submission then receives a completion screen; vendor dispatch remains a separate approval action.',240)
header('Workflow 01 / Demonstration input','A concrete form request','The second demonstration uses the same synthetic tenant and property as the Telegram journey.')
y=shot('form-input',450,width=350,height=340,x=42); caption(y-16,'Actual form: tenant, unit and property.',42,350)
text(430,431,'The submitted issue',14,'Geist',GREEN)
para(430,405,'The bathroom exhaust fan stopped spinning yesterday. There is no smoke, burning smell or sparking. No pets are present.',300,12,19)
text(430,293,'Included context',13,'Geist',GREEN); para(430,269,'Demo Tenant / Maple Court, Unit 2B / Entry permission: Yes',300,11.5,18)
para(430,193,'The next page shows the actual submitted payload and completion screen. Contact fields are removed or flattened out of the public captures.',300,11.5,18); end()
header('Workflow 01 / Executed result','The form became MR-0009','The real submission completed the intake path and created a ROUTINE / APPLIANCE request.')
y=shot('form-output',460,height=260); caption(y-16,'Actual Form Trigger output. Contact value redacted; test mode is visible.')
shot('intake-success',166,width=160,height=50,x=42)
para(42,97,'Saved result: MR-0009. Its vendor status remains AWAITING_VENDOR; no vendor email was sent for this request.',265,11.5,17)
shot('form-receipt',166,width=420,height=105,x=330); caption(57,'Actual receipt after completion.',330,420); end()

full('Workflow 02 / Triage Engine','Interpret, check and persist','The engine is called by intake or tenant conversation flows once there is a concrete maintenance issue.','engine-full',[
('Incoming data','Normalized message, source identifier, trusted tenant context and test-mode flag.'),('Decisions','Check prior processing; classify the issue; apply fixed safety and trade boundaries.'),('State','Postgres retains the ticket, classification reason, events and an eligible vendor draft.'),('Output','A saved result routed as emergency, needs review, urgent or routine.'),('Approval','The engine recommends and drafts. The manager chooses whether to contact a vendor.')])
detail('Workflow 02 / Classification','A structured reading of the issue','The live model identifies request type, summary, priority, trade, access notes and missing information.','engine-classify','The workflow calls gpt-5.6-luna through OpenAI and requires a structured response. A separate test-mode route can use mock classifications for fixtures; it was not used for MR-0007 or MR-0009.',275)
detail('Workflow 02 / Safety checks','Check the result before drafting','Fixed rules check safety and maintenance semantics before the ticket event is persisted.','engine-safety','The saved priority reflects both the structured model response and explicit safety and trade boundaries. Human-only or review-only requests skip automatic drafting; the engine does not use a draft as permission to send.',195)
detail('Workflow 02 / Draft eligibility','Prepare a note without sending it','Only an eligible saved maintenance request receives an automatic vendor draft.','engine-draft','The workflow filters eligible tickets, builds the draft request, calls OpenAI and attaches the returned note. The note is saved for manager review. Preparing it does not dispatch a vendor or promise an appointment.',182)
header('Workflow 02 / Output decisions','Four explicit priority routes','The saved result exits through a named priority branch. Downstream workflows use that state to decide the next step.')
y=shot('engine-router',420,width=185,height=216,x=42); caption(y-16,'Priority router.',42,185)
y=shot('engine-routes-upper',460,width=233,height=341,x=264); caption(y-16,'Emergency / review outputs.',264,233)
y=shot('engine-routes-lower',460,width=233,height=342,x=517); caption(y-16,'Urgent / routine outputs.',517,233); end()
header('Workflow 02 / Actual model result','MR-0007: a contained faucet leak','This is the recorded live execution after the tenant supplied entry permission and pet information.')
y=shot('engine-decision',460,width=510,height=380,x=42); caption(y-16,'Actual checked classification from n8n.',42,520)
text(580,435,'Saved interpretation',13,'Geist',GREEN); para(580,409,'URGENT / PLUMBING',170,12,19)
para(580,345,'The reason distinguishes persistent contained water from active flooding. The access note allows entry and confirms no pets.',170,11.5,18)
para(580,206,'Postgres verification found no remaining missing-information fields. Manager review followed only after this clarification.',170,11.5,18); end()

full('Workflow 03 / Tenant Telegram','Keep the request conversational','A tenant message or pairing link starts this workflow. Saved conversation state determines the appropriate path.','tenant-full',[
('Incoming data','Telegram text, chat context and a configured synthetic tenant profile.'),('Decisions','Recognize pairing, welcome, new issue, preliminary conversation, clarification or status.'),('Data movement','Concrete issues call the shared engine; replies merge into the existing request.'),('Output','A targeted question, factual progress reply or complete request for manager review.')],240)
header('Workflow 03 / Clarification','Ask for the detail that matters','A vague opening stays in conversation state. A concrete request with missing information stays in clarification.')
y=shot('tenant-buffer',460,height=150); caption(y-16,'Pre-triage buffer: store the opening and ask for a maintenance symptom.')
para(42,270,'Once a ticket exists, the answer is re-triaged and merged into its original reference. The manager is notified only when the request is complete or explicitly needs review.',708,11.5,17)
y=shot('tenant-clarify',212,height=135); caption(y-16,'Actual clarification route: re-triage and merge into the original request.'); end()
header('Workflow 03 / Status and handoff','Separate progress from new work','Status reads existing tickets. A new issue or clarified request reaches the manager only through an explicit eligibility decision.')
y=shot('tenant-status',460,height=146); caption(y-16,'Status route: build a factual reply, send it and record delivery.')
y=shot('tenant-handoff',272,height=190); caption(y-16,'Manager handoff: decide eligibility before calling the Manager Desk.'); end()
header('Workflow 03 / Connected demonstration','From a vague opening to MR-0007','These are consecutive messages in the active tenant conversation. The synthetic profile supplies Maple Court, Unit 2B.')
y=shot('tenant-journey-start',450,width=690,height=289); caption(y-16,'Actual Telegram conversation pane. Other chats and contacts are excluded.')
para(42,108,'The bathroom opening created no ticket, Airtable record or manager alert. The concrete dripping-faucet message then created MR-0007 and prompted for entry permission. The tenant also supplied timing and pet information in the answer.',708,11.5,17); end()
header('Workflow 03 / Clarification outcome','One reply unlocked manager review','The tenant confirms when the issue started, allows entry and reports no pets. The same MR-0007 reference continues.')
y=shot('tenant-journey-ready',460,width=650,height=320); caption(y-16,'Actual conversation: clarification answer, review notice and provider-contacted update.')
para(42,99,'The provider-contacted message appears only after the later approval and successful vendor send. It does not claim a booked visit or a completed repair.',708,11.5,17); end()
header('Workflow 03 / Status outcome','A factual answer without a new ticket','The tenant asks when the repair will happen. The workflow responds from open-request state rather than running triage again.')
y=shot('tenant-journey-status',460,width=570,height=365,x=42); caption(y-16,'Actual conversation with surrounding messages.',42,575)
para(635,420,'MR-0007 and a preserved open demonstration request, MR-0001, are summarized together.',115,11.5,17)
para(635,277,'No arrival time was invented. The database ticket count stayed unchanged, and neither the engine nor manager flow was invoked.',115,11.5,17); end()

full('Workflow 04 / Manager Desk','Make the vendor decision explicit','Reviewable requests enter the upper lane. Telegram approval callbacks enter the lower lane.','manager-full',[
('Incoming data','Saved ticket, property, trade, access notes, draft and manager action.'),('Key steps','Read the vendor roster; save matching candidates; show choices; mirror the request.'),('Approval','Select a matched vendor or Hold. Review-only requests expose no vendor-send action.'),('Output','One approved email, saved send state, a tenant update and an Airtable change.')],250)
detail('Workflow 04 / Vendor matching','Present relevant vendor choices','The Airtable roster supplies candidates that serve the request property and trade.','manager-candidates','The workflow saves candidates in Postgres before preparing the manager message. It reattaches the request context after the database lookup, so the alert and approval keyboard retain the correct ticket and vendor choices.',245)
detail('Workflow 04 / Approval gate','Claim one send before using SMTP','A Telegram button supplies the chosen vendor. The stored ticket must permit that action before any email is sent.','manager-approve','Postgres claims the send atomically. The email route runs only when the claim permits it, preventing a repeated tap from dispatching the same request again. A Hold or already-handled outcome exits before SMTP.',215)
detail('Workflow 04 / After sending','Update the tenant and the workspace','A successful email is finalized in durable state before the downstream updates run.','manager-outcome','The tenant is told a maintenance provider was contacted. The update delivery is recorded, and Airtable receives the selected vendor and send status. The flow records vendor contact; it does not imply a confirmed appointment.',260)
header('Workflow 04 / Actual approval','The prepared request and the action','MR-0007 reaches the manager only after the tenant supplies the missing access detail.')
shot('manager-approval-chat',460,width=345,height=395,x=405)
text(42,430,'What the manager can review',14,'Geist',GREEN)
para(42,404,'The message includes the reference, urgency, trade, unit, issue summary, access permission and vendor email draft.',315,12,19)
text(42,290,'Demonstrated approval',13,'Geist',GREEN)
para(42,265,'For this controlled demonstration, the operator clicked Send to Maple Plumbing. This exercises the same approval button a property manager would use.',315,11.5,18)
para(42,162,'The vendor name is synthetic. Sending used the configured demo mailbox, so the sample shows real delivery without contacting a real contractor.',315,11.5,18)
caption(74,'Actual manager conversation pane.',42,315); end()
header('Workflow 04 / Observable output','The approved email was delivered','Postgres finalized the send as SENT. The received subject and body match the faucet request and access details.')
y=shot('manager-sent',477,width=545,height=102); caption(y-16,'Actual n8n finalization result: sent.')
y=shot('vendor-email',343,height=285); caption(y-16,'Actual Gmail delivery to the controlled demo account. Contact address and sidebars excluded.'); end()
header('Workflow 04 / Controlled alternate branch','Repeated approval stopped safely','The same MR-0007 vendor button was pressed again after the successful send.')
y=shot('manager-repeat',442,width=620,height=105); caption(y-16,'Actual n8n claim output: already_handled.')
panel(42,280,344,'What executed','Callback normalization and the Postgres claim ran. The send decision rejected another dispatch.',118)
panel(406,280,344,'What changed','No additional SMTP send ran. The durable record still contained one successful vendor-send attempt.',118)
para(42,110,'Both repeated callback executions stopped before SMTP. This evidence pairs the execution decision with the unchanged business state, rather than relying on a green status alone.',708,11.5,17); end()
header('Workflow 04 / Verified workspace','Sent and awaiting approval are distinct','The visible references, priorities, sources and linked conversation records were checked against Postgres before capture.')
y=shot('requests-dispatch',437,height=225); caption(y-16,'Actual Airtable Requests grid with synthetic records.')
panel(42,187,344,'MR-0007 / faucet leak','URGENT request; vendor status SENT; selected vendor Maple Plumbing.',106)
panel(406,187,344,'MR-0009 / exhaust fan','ROUTINE request; AWAITING_VENDOR. No selected vendor or vendor email yet.',106); end()

header('Workflow 05 / Operations','Four separate scheduled lanes','Schedules read saved state. Conversation sync keeps the manager view aligned with the tenant interaction.')
y=shot('operations-full',460,width=560,height=360,x=42); caption(y-16,'Actual full canvas: all four lanes and every node.',42,570)
para(630,430,'Daily notification / Operator heartbeat / Emergency re-alert / Conversation sync',120,12,19)
para(630,268,'Each lane has its own trigger and state lookup. Only the emergency lane can invoke manager escalation.',120,11.5,18); end()
detail('Workflow 05 / Configuration gates','Notifications follow configuration','The daily email and operator Telegram heartbeat load their configuration before preparing any message.','operations-checks','Both notification features were disabled during this demonstration. The configured daily email is a short reminder to review open requests in Airtable; this sample does not present an unexecuted digest as a delivered output.',290)
detail('Workflow 05 / Emergency review','Age alone does not create an emergency','The scheduled query selects unanswered emergency requests before re-entering manager review.','operations-emergencies','Only open EMERGENCY requests awaiting vendor handling and older than 15 minutes enter this lane. It calls the Manager Desk for review. MR-0007 remained URGENT and was excluded; the query does not turn request age into an emergency priority.',218)
detail('Workflow 05 / Sync input','Select unsynced conversation entries','The five-minute schedule reads messages retained in Postgres and prepares linked Airtable records.','operations-sync-select','Each append includes a synthetic conversation label, request reference, direction, channel, intent and delivery state. The same request stays traceable across clarification, vendor updates and status replies.',250)
detail('Workflow 05 / Sync completion','Append first, then mark completion','The external append result is preserved before Postgres records the message as synced.','operations-sync-complete','Airtable receives the conversation entry and its request link. The workflow then marks that durable entry as synced. This separates an unsynced message from a completed mirror operation and prevents normal repeated appends.',250)
header('Workflow 05 / Actual execution','Status messages reached Airtable','The scheduled run selected and synced two entries from the MR-0007 status exchange.')
shot('operations-success',460,width=145,height=47,x=42)
para(225,444,'Actual run: two selected messages, successful Airtable appends, and completed Postgres sync marks.',525,11.5,17)
y=shot('operations-executed-select',382,width=480,height=136); caption(y-16,'Executed selection and preparation: two items.')
y=shot('operations-executed-complete',211,width=495,height=136); caption(y-16,'Executed append and sync mark: two items.'); end()
header('Workflow 05 / Linked records','Every conversation keeps its request','The actual Airtable conversation view retains reference and direction without exposing message bodies or contact fields.')
y=shot('conversations-links',456,width=560,height=340,x=42); caption(y-16,'Actual linked conversation records.',42,560)
para(635,428,'MR-0007 has its request message, clarification answer, provider update and status exchange under the same reference.',115,11.5,17)
para(635,271,'MR-0009 retains its email pairing entry. These visible links were checked against the durable records.',115,11.5,17); end()
header('Workflow 05 / Recorded outcomes','Intent and delivery remain visible','This is the adjacent portion of the same conversation grid, in the same row order as the preceding page.')
y=shot('conversations-outcomes',456,width=515,height=360,x=42); caption(y-16,'Actual channel, intent and delivery-state columns.',42,530)
text(605,425,'MR-0007 journey',13,'Geist',GREEN)
para(605,398,'Inbound request / Clarification answer / Sent provider update / Recorded status question / Sent status response',145,11.5,18)
para(605,219,'The recorded states correspond to the actual Telegram conversation shown earlier.',145,11.5,18); end()
header('Verified demonstration','Evidence beyond the canvas','Fresh synthetic executions on 10 October 2026 were checked against actual messages, durable records and Airtable output.')
checks=[('Vague bathroom opening','Clarification prompt; no ticket, manager alert or Airtable request.'),('Concrete faucet symptom','MR-0007 created; entry-permission question sent before manager review.'),('Clarification answer','Original MR-0007 updated; missing information cleared; manager draft shown.'),('Form fan request','MR-0009 saved as ROUTINE / APPLIANCE; intake receipt displayed.'),('Approved vendor contact','One delivered demo email; SENT state; tenant and Airtable updated.'),('Repeated vendor button','already_handled; no second SMTP send; one successful send attempt retained.'),('Tenant status question','Consolidated factual reply; unchanged ticket count; no re-triage or manager call.'),('Scheduled conversation sync','Two status entries appended and marked synced; matching Airtable rows visible.')]
y=444
for case,result in checks:
    text(42,y,case,11.5,'Geist',GREEN); para(253,y,result,497,11.2,16)
    c.setStrokeColor(LINE); c.setLineWidth(.6); c.line(42,y-29,750,y-29); y-=44
para(42,65,'These are demonstrated behaviors with synthetic data and controlled services, not measurements of client savings or production performance.',708,10.8,15); end()
c.save()
reader=PdfReader(OUT); writer=PdfWriter()
for i,page in enumerate(reader.pages,1):
    buf=BytesIO(); fc=canvas.Canvas(buf,pagesize=(W,H)); fc.setStrokeColor(LINE); fc.setLineWidth(.8); fc.line(42,39,750,39)
    fc.setFillColor(MUTED); fc.setFont('Manrope',9); fc.drawString(42,22,'Maintenance Request Triage / Work Sample'); fc.drawRightString(750,22,f'{i} / {len(reader.pages)}')
    fc.save(); buf.seek(0); page.merge_page(PdfReader(buf).pages[0]); writer.add_page(page)
writer.add_metadata({'/Title':'Maintenance Request Triage - Work Sample','/Author':'Automation Work Sample','/Subject':'Verified synthetic maintenance automation demonstration','/Creator':'Work Sample Builder','/Producer':'Work Sample Builder'})
with OUT.open('wb') as f: writer.write(f)
(ROOT/'tmp/work-sample-v2/page-manifest.json').write_text(json.dumps({'titles':titles,'images':uses},indent=2)+'\n',encoding='utf-8')
print(f'{len(reader.pages)} pages: {OUT}')
