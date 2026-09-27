"""Production solution brief, based on docs/production-maintenance-triage-blueprint.md.
Portfolio type and palette; illustrative examples, not claims of a live deployment.
"""
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
from fontTools.ttLib import TTFont as SourceFont
from fontTools.varLib.instancer import instantiateVariableFont

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'output/pdf/maintenance-triage-square-brief.pdf'
OUT.parent.mkdir(parents=True, exist_ok=True)
CACHE=ROOT/'tmp/pdfs/square-fonts'
CACHE.mkdir(parents=True,exist_ok=True)
for name,family,weight in [('Body','manrope',500),('Bold','manrope',700),('Display','geist',800)]:
    dest=CACHE/(name+'.ttf')
    font=SourceFont(ROOT/f'concept-brief/assets/fonts/{family}-variable.ttf')
    font=instantiateVariableFont(font,{'wght':weight},inplace=True)
    # Distinct embedded names prevent ReportLab from treating both weights as one face.
    for rec in font['name'].names:
        if rec.nameID in (1,4,6):rec.string=('Brief'+name).encode(rec.getEncoding())
    font.save(dest)
    pdfmetrics.registerFont(TTFont(name,str(dest)))
pdfmetrics.registerFontFamily('Body', normal='Body', bold='Bold')
W = H = 648
INK='#141210'; MUTED='#5A544B'; PAPER='#F4F1EA'; LINE='#E4DED4'
GREEN='#28634C'; SOFT='#EFF5F0'; ORANGE='#C2542D'; WHITE='#FFFFFF'
c=canvas.Canvas(str(OUT), pagesize=(W,H))
c.setTitle('Maintenance request coordination | Production solution brief')
c.setAuthor('Sambhav Jain')

def box(x,y,w,h,fill=WHITE,stroke=None,r=12):
    c.setLineWidth(.6)
    c.setFillColor(HexColor(fill)); c.setStrokeColor(HexColor(stroke or fill))
    c.roundRect(x,H-y-h,w,h,r,fill=1,stroke=bool(stroke))
def shell(x,y,w,h,fill=WHITE):
    box(x,y+2,w,h,'#EAE5DC',r=18)
    box(x,y,w,h,'#FAF8F3',LINE,18)
    box(x+5,y+5,w-10,h-10,fill,r=13)
def text(s,x,y,w,size=13,color=INK,bold=False,leading=None,font=None):
    p=Paragraph(s,ParagraphStyle('p',fontName=font or ('Bold' if bold else 'Body'),fontSize=size,leading=leading or size*1.3,textColor=HexColor(color)))
    _,h=p.wrap(w,1000); p.drawOn(c,x,H-y-h)
    assert y+h < 616, (s,y,h)
    return h
def line(x,y,x2,y2,color=LINE,width=1):
    c.setStrokeColor(HexColor(color));c.setLineWidth(width);c.line(x,H-y,x2,H-y2)
def arrow(x,y,x2,y2,color=GREEN,both=False):
    line(x,y,x2,y2,color,1.4)
    import math
    a=math.atan2(y2-y,x2-x)
    for d in [-.55,.55]:
        line(x2,y2,x2-6*math.cos(a+d),y2-6*math.sin(a+d),color,1.4)
    if both:
        for d in [-.55,.55]:line(x,y,x+6*math.cos(a+d),y+6*math.sin(a+d),color,1.4)
def label(s,x,y,w,color=GREEN):text(s.upper(),x,y,w,9,color,True,12)
def title(s,x,y,w,size=27,color=INK):return text(s,x,y,w,size,color,leading=size*1.08,font='Display')
def badge(s,x,y,w,color=GREEN,fill=SOFT):
    box(x,y,w,22,fill,r=11);text(s,x+10,y+4,w-18,9,color,True)
def icon(kind,x,y,color=GREEN):
    c.setStrokeColor(HexColor(color));c.setLineWidth(1.5)
    if kind=='person':
        c.circle(x+10,H-y-6,4,fill=0,stroke=1)
        c.roundRect(x+3,H-y-22,14,10,4,fill=0,stroke=1)
    elif kind=='db':
        c.ellipse(x,H-y-7,x+22,H-y,fill=0,stroke=1)
        line(x,y+3,x,y+21,color,1.5);line(x+22,y+3,x+22,y+21,color,1.5)
        c.arc(x,H-y-25,x+22,H-y-17,startAng=180,extent=180)
        c.arc(x,H-y-16,x+22,H-y-8,startAng=180,extent=180)
    elif kind=='check':
        c.circle(x+11,H-y-11,11,fill=0,stroke=1)
        line(x+5,y+11,x+9,y+15,color,1.5);line(x+9,y+15,x+17,y+7,color,1.5)
    else:
        c.roundRect(x,H-y-18,22,18,4,fill=0,stroke=1)
        line(x+5,y+18,x+5,y+23,color,1.5);line(x+5,y+23,x+11,y+18,color,1.5)
        line(x+5,y+6,x+17,y+6,color);line(x+5,y+11,x+13,y+11,color)
def page(n,section,title,sub):
    box(0,0,W,H,PAPER,r=0)
    text('Sambhav Jain',30,19,220,11,bold=True)
    text('AI automation for property management',30,35,280,8.5,MUTED)
    text('PREPARED FOR',437,19,181,8,MUTED)
    text('[Client Company]',437,33,181,10,bold=True)
    line(30,55,618,55)
    badge(f'0{n} / {section}',30,67,255,MUTED,WHITE)
    text(title,30,99,588,27,leading=29,font='Display')
    text(sub,30,162,588,11.5,MUTED)
    line(32,615,616,615)
    c.setFont('Body',8.5);c.setFillColor(HexColor(MUTED));c.drawString(32,16,'sambhavbuilds.com / Production solution brief')
    c.drawRightString(616,16,f'0{n} / 04')
def end():c.showPage()

# 1: Relevance and the division of work.
page(1,'What changes for your team','Maintenance requests, prepared.<br/><font color="'+ORANGE+'">Decisions stay with your team.</font>','A production system that gathers details, prepares the next action, and tracks each handoff.')
shell(30,202,588,105)
box(38,210,151,89,INK,r=11)
label('Research reviewed',51,222,127,'#CFC6BA')
text('[Company website]<br/>[Portfolio / markets]<br/>[Verified operating detail]',51,242,128,10.5,WHITE)
label('A note for [Decision Maker]',204,215,395,ORANGE)
text('Your [verified company detail] suggests a need to [specific operating goal]. I would connect [current intake] with [Client PMS] so [team] can review prepared requests instead of chasing the same details.',204,235,396,11.5)
label('What the system does',42,319,555)
features=[('message','Capture and connect','Receive portal, email, SMS, and phone transcripts. Keep originals and attachments; verify identity; link repeats and group shared incidents.'),('check','Sort, protect, and clarify','Use approved languages; read urgency, trade, access, and pets. Apply fixed rules. Acknowledge receipt and ask only for missing details.'),('person','Prepare and coordinate','Draft PMS notes and vendor instructions; check vendor eligibility; route manager and owner approvals; send only authorized actions.'),('db','Track and keep people informed','Answer status questions without new tickets. Track vendor replies, appointments, progress, and closure; surface delays and failures.')]
for i,(ic,head,copy) in enumerate(features):
    y=342+i*53
    icon(ic,40,y+3)
    text(head,77,y,528,12,bold=True)
    text(copy,77,y+20,528,10.5,MUTED)
shell(30,565,588,39,INK)
text('<b>What stays yours:</b> PMS, resident channels, vendors, and decision authority.',45,577,558,11,WHITE)
end()

# 2: Process rail and a distinct manager-facing decision package.
page(2,'How a request moves','From the first message<br/>to an approved action.','Illustrative production example: spreading water under a kitchen sink at 10:42 p.m.')
shell(30,200,588,61)
icon('message',45,220)
text('"Water is spreading under the kitchen sink. The tap is off but it is still flowing. My dog is here. You have permission to enter."',80,214,522,12)
shell(30,276,353,280)
line(54,306,54,526)
stages=[(290,'1','Match and preserve','Verify resident and unit; keep the original. Link replies; a vague opening gets a question, not a vendor task.'),(362,'2','Interpret and check safety','AI suggests urgency and trade.'),(435,'3','Ask, then reassess','"When did it start spreading?" Keep replies together. Do not re-ask known access or pet details.'),(500,'4','Route the right alert','Safety alerts do not wait. Routine work follows quiet-hour and task rules.')]
for y,num,head,copy in stages:
    box(42,y+2,24,24,PAPER,r=12);text(num,50,y+6,15,10,bold=True)
    text(head,77,y,285,12,bold=True)
    text(copy,77,y+21,285,11,MUTED)
    if num=='1':line(77,y+65,365,y+65)
    if num=='2':
        box(77,404,290,28,SOFT,r=8)
        text('<b>Fixed rules:</b> raise urgency; never lower it.',85,411,274,10,GREEN)
shell(397,276,221,280,INK)
label('Manager receives',412,292,191,'#EEAA8D')
title('One prepared<br/>decision',412,315,187,21,WHITE)
text('<b>Kitchen leak / [Unit]</b><br/>Spreading water; flow continues. Entry allowed; dog in unit.<br/><br/>Original, summary, rule reason, and vendor draft.<br/><br/>Vendors checked for trade, coverage, hours, and compliance.',412,366,189,11,'#F0EBE4')
text('Hold, edit, assign, select vendor, or seek owner approval.',412,514,189,10.5,'#EEAA8D',True)
arrow(384,490,396,490)
text('<b>After approval:</b> send once and update the PMS. Hold sends nothing. Confirm vendor contact only after success. Status replies use recorded facts, not invented arrival times.',30,571,588,11.5,GREEN)
end()

# 3: Actual business connections; AI never controls downstream channels directly.
page(3,'What connects to what','Your existing tools.<br/><font color="'+ORANGE+'">A connected production service.</font>','Proposed stack: n8n, PostgreSQL, and the OpenAI API. Exact routes follow your access and permissions.')
shell(30,199,588,47)
text('<b>Your portal, email, SMS, and phone-transcript service</b><br/>[Intake route: API / webhook / secure mailbox] - confirm per channel.',45,210,558,11)
arrow(207,248,207,264,both=True)
shell(30,268,366,117,SOFT)
label('Hosting: [client cloud / approved host]',46,280,332)
title('n8n + PostgreSQL',46,299,330,19)
text('Workflows, fixed rules, queues, and retries.<br/>Database: request state, audit, and send checks.<br/>PMS retains business records and final status.',46,328,332,11)
shell(424,268,194,117)
title('OpenAI API',440,282,163,18)
text('Approved context in;<br/>summary and drafts out.<br/>No action authority.',440,311,162,11)
arrow(397,310,423,310);arrow(423,350,397,350)
label('Connection routes / fill from prospect research',30,397,588,ORANGE)
routes=[('[Client PMS]','[API / partner access / export route]','Read units and open work; write notes and status. If writes are blocked, return a staff task or approved import.'),('[Manager Channel]','[App API + approval callback / secure review link]','Send the decision; verify the user and return the approval. [Owner approval route] handles spending exceptions.'),('[Vendor Channel]','[PMS vendor API / vendor portal / email service]','Send approved work; capture replies and delivery results. Publish events to [Reporting Tool / connection route].')]
for i,(head,route,copy) in enumerate(routes):
    y=417+i*63
    box(30,y,588,57,WHITE,r=11)
    text(head,44,y+11,135,11.5,bold=True)
    arrow(169,y+29,190,y+29,both=True)
    text(route,202,y+7,401,10.5,GREEN,True)
    text(copy,202,y+24,401,10.5,MUTED)
end()

# 4: Production lifecycle and service ownership, without demo framing.
page(4,'Daily operation and control','The process continues<br/>after the vendor is contacted.','Production scope includes progress tracking, failure handling, and a named person for exceptions.')
shell(30,201,588,77)
label('In your PMS / same work order',46,211,552)
for x,head,desc in [(46,'Vendor replies','Quote or acceptance'),(190,'Time confirmed','Then update resident'),(334,'Work progresses','Chase stalled work'),(478,'Staff verify','Then close the job')]:
    text(head,x,235,127,12,bold=True);text(desc,x,256,126,10.5,MUTED)
    if x<478:arrow(x+124,243,x+138,243)
label('Your team controls',30,294,278,ORANGE)
label('Daily checks and recovery',337,294,281)
controls=[('Human decisions','Staff decide vendor, spend, owner approval, emergency downgrade, appointment, credits, and closure.'),('Review, not guesswork','Legal or accommodation cases, bad files, unclear identity/language, or no vendor: staff review.'),('Access and privacy','Agree hosting, AI data use, and retention. Encrypt data; protect secrets; use role-based access and MFA.'),('Changes and ownership','Test staff-approved rule changes; no self-training. Agree support, deletion, service targets, and rollback.')]
for i,(head,body) in enumerate(controls):
    y=317+i*56
    text(head,30,y,283,11.5,bold=True)
    text(body,30,y+18,283,10.5,MUTED)
shell(337,312,281,230,INK)
ops=[('Follow up on stalled work','Recheck unanswered emergencies. Daily digests flag delays; age alone never makes an emergency.'),('Keep failed work visible','AI fails: keep the report for review. Send or PMS fails: retry, then assign staff. Do not claim success.'),('Prevent repeat or wrong actions','Reject duplicate or stale approvals. Flag PMS conflicts; never overwrite staff changes silently.'),('Check and recover the service','Monitor silent intake, test the full path, reconcile PMS data, and test encrypted backup restores.')]
for i,(head,body) in enumerate(ops):
    y=323+i*54
    text(head,351,y,253,11,WHITE,True)
    text(body,351,y+17,253,10,'#E1DBD2')
shell(30,554,588,49,INK)
title('Map this to your operation.',46,563,369,17,WHITE)
text('Sambhav Jain / sambhav@sambhavbuilds.com',46,586,368,9.5,'#D6CFC5')
box(442,562,159,33,ORANGE,r=16.5)
text('Discuss the fit',455,571,112,11,WHITE,True)
box(571,568,22,22,'#D87654',r=11);arrow(577,579,587,579,WHITE)
c.linkURL('https://cal.com/sambhav-builds/pm-automation-audit',(442,H-595,601,H-562),relative=0)
end()
c.save()
print(OUT)
