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
label('Today / repeated staff work',42,325,265,MUTED)
label('Added / system preparation',343,325,260)
items=[('Read and match messages','Link resident, unit, and open work','message'),('Ask for missing information','Ask only what is still missing','message'),('Look up policy and vendors','Prepare eligible options and notes','db')]
for i,(a,b,ic) in enumerate(items):
    y=349+i*57
    box(30,y,275,44,WHITE,r=11);icon(ic,42,y+12,MUTED);text(a,72,y+12,221,11.5,bold=True)
    arrow(313,y+22,333,y+22)
    box(343,y,275,44,SOFT,r=11);text(b,356,y+12,248,11.5,GREEN,True)
    if i<2:arrow(168,y+45,168,y+54,MUTED);arrow(480,y+45,480,y+54)
shell(30,524,588,79,INK)
label('What stays',45,537,95,'#EEAA8D')
text('Your PMS, resident channels, vendor relationships, and approval authority.',145,535,455,12,WHITE,True)
text('Less chasing. Clearer priorities. A visible owner and next action.',45,575,551,12,'#DDD7CE')
end()

# 2: Process rail and a distinct manager-facing decision package.
page(2,'How a request moves','From the first message<br/>to an approved action.','Illustrative production example: spreading water under a kitchen sink at 10:42 p.m.')
shell(30,200,588,61)
icon('message',45,220)
text('"Water is spreading under the kitchen sink. The tap is off but it is still flowing. My dog is here. You have permission to enter."',80,214,522,12)
shell(30,276,353,280)
line(54,306,54,526)
stages=[(291,'1','Match the request','Verify resident and unit; keep the original message. Link repeats and replies.'),(357,'2','Interpret and check safety','AI suggests urgency and trade.'),(438,'3','Ask only what is missing','Approved follow-up: "When did the water start spreading?" Reassess the reply.'),(512,'4','Prepare the human decision','Safety alerts do not wait for clarification.')]
for y,num,head,copy in stages:
    box(42,y+2,24,24,PAPER,r=12);text(num,50,y+6,15,10,bold=True)
    text(head,77,y,285,12,bold=True)
    text(copy,77,y+21,285,11,MUTED)
    if num=='1':line(77,y+57,365,y+57)
    if num=='2':
        box(77,399,290,28,SOFT,r=8)
        text('<b>Fixed rules:</b> raise urgency; never lower it.',85,406,274,10,GREEN)
shell(397,276,221,280,INK)
label('Manager receives',412,292,191,'#EEAA8D')
title('One prepared<br/>decision',412,315,187,21,WHITE)
text('<b>Kitchen leak</b><br/>[Property / Unit]<br/><br/>Spreading water; flow continues.<br/>Entry allowed. Dog in unit.<br/><br/>Original message, policy reason, vendor choices, and owner-approval need.',412,371,189,11.3,'#F0EBE4')
badge('Review / hold / approve',412,520,190,WHITE,'#39352F')
arrow(384,490,396,490)
text('<b>After approval:</b> claim the action once, update the PMS, and contact the vendor. Tell the resident only what the sending service confirms.',30,575,588,12,GREEN)
end()

# 3: Actual business connections; AI never controls downstream channels directly.
page(3,'What connects to what','Your existing tools.<br/><font color="'+ORANGE+'">A connected production service.</font>','Proposed stack: n8n, PostgreSQL, and the OpenAI API. Exact routes follow your access and permissions.')
shell(30,205,588,51)
icon('message',44,219,MUTED)
text('Existing portal / email / SMS / phone transcripts',77,215,524,12,bold=True)
text('Resident messages in; approved questions and confirmed updates back.',77,235,524,10.5,MUTED)
arrow(206,257,206,289,both=True)
text('API, webhook, or mailbox',224,264,255,10,MUTED)
shell(30,294,366,159,SOFT)
label('Client-owned or approved cloud',46,308,332)
title('n8n workflows',46,329,330,21)
text('Verify context; apply fixed rules; ask questions; route approvals; coordinate sends.',46,359,331,12)
line(46,401,380,401,'#C9DCCF')
icon('db',46,414)
text('<b>PostgreSQL</b> stores state, audit history, queued work, and duplicate-action checks.',79,408,300,11)
shell(424,294,194,159)
label('External service',440,308,162)
title('OpenAI API',440,333,162,19)
text('Receives limited, approved context. Returns the issue summary and draft wording.',440,363,160,11.5)
text('No approval authority.',440,426,160,10.5,GREEN,True)
arrow(397,355,423,355);arrow(423,401,397,401)
line(206,454,206,473,GREEN,1.1);line(120,473,528,473,GREEN,1.1)
for x,w,head,desc in [(30,180,'[Client PMS]','Resident and unit lookup; work orders and final status.'),(234,180,'[Manager Channel]','Decision request out; authorized approval back.'),(438,180,'[Vendor Channel]','Approved job out; replies and delivery status back.')]:
    arrow(x+w/2,473,x+w/2,490,both=True)
    box(x,493,w,70,WHITE,r=12)
    text(head,x+12,503,w-24,12,bold=True);text(desc,x+12,525,w-24,10.5,MUTED)
text('<b>PMS stays the business record.</b> If write access is limited, return prepared tasks for staff. Connect owner approvals and reporting to the tools already in use.',30,578,588,11.5,MUTED)
end()

# 4: Production lifecycle and service ownership, without demo framing.
page(4,'Daily operation and control','The process continues<br/>after the vendor is contacted.','Production scope includes progress tracking, failure handling, and a named person for exceptions.')
shell(30,204,588,92)
label('In your PMS / same work order',46,217,552)
for x,head,desc in [(46,'Vendor replies','Quote or acceptance'),(190,'Time confirmed','Then update resident'),(334,'Work progresses','Chase stalled work'),(478,'Staff verify','Then close the job')]:
    text(head,x,243,127,12,bold=True);text(desc,x,265,126,10.5,MUTED)
    if x<478:arrow(x+124,251,x+138,251)
label('Your team controls',30,316,278,ORANGE)
label('The service keeps work visible',337,316,281)
controls=[('person','Approvals','Vendor choice, spend, owner approval, sensitive cases, and closure.'),('db','Access and data','Approved data fields, role-based access, retention, and protected credentials.'),('check','Policy and ownership','Your on-call rules and vendor criteria. A named operator owns service health.')]
for i,(ic,head,body) in enumerate(controls):
    y=340+i*59
    icon(ic,31,y+2,ORANGE);text(head,65,y,246,12,bold=True);text(body,65,y+20,246,10.5,MUTED)
    if i<2:line(65,y+53,309,y+53)
shell(337,337,281,179,INK)
text('<b>Failed connection</b><br/>Queue and retry. If it still fails, assign it to a person.<br/><br/><b>Conflicting or unclear data</b><br/>Flag for review; never overwrite silently.<br/><br/><b>Service health</b><br/>Monitor intake, reconcile PMS updates, and test encrypted backup recovery.',352,352,251,11,'#F0EBE4')
shell(30,538,588,65,INK)
title('Map this to your operation.',46,550,368,18,WHITE)
text('Your channels, PMS access, approval rules, and hosting.<br/>Sambhav Jain / sambhav@sambhavbuilds.com',46,573,368,9.5,'#D6CFC5')
box(442,552,159,37,ORANGE,r=18.5)
text('Discuss the fit',455,562,112,11,WHITE,True)
box(571,560,22,22,'#D87654',r=11);arrow(577,571,587,571,WHITE)
c.linkURL('https://cal.com/sambhav-builds/pm-automation-audit',(442,H-589,601,H-552),relative=0)
end()
c.save()
print(OUT)
