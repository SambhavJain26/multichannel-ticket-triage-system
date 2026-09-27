"""Four-page square solution brief. Synthetic examples; no client data."""
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'output/pdf/maintenance-triage-square-brief.pdf'
OUT.parent.mkdir(parents=True, exist_ok=True)
for name, file in [('Body','arial.ttf'), ('Bold','arialbd.ttf')]:
    pdfmetrics.registerFont(TTFont(name, 'C:/Windows/Fonts/' + file))
pdfmetrics.registerFontFamily('Body', normal='Body', bold='Bold')
W = H = 648
INK='#191B18'; MUTED='#585F58'; PAPER='#F7F5EF'; LINE='#D5D9D0'
GREEN='#28634C'; SOFT='#EAF2EB'; ORANGE='#C7512A'; WHITE='#FFFFFF'
c=canvas.Canvas(str(OUT), pagesize=(W,H))
c.setTitle('Maintenance request triage | A solution brief')
c.setAuthor('Sambhav Jain')

def box(x,y,w,h,fill=WHITE,stroke=None,r=12):
    c.setFillColor(HexColor(fill)); c.setStrokeColor(HexColor(stroke or fill))
    c.roundRect(x,H-y-h,w,h,r,fill=1,stroke=bool(stroke))
def text(s,x,y,w,size=13,color=INK,bold=False,leading=None):
    p=Paragraph(s,ParagraphStyle('p',fontName='Bold' if bold else 'Body',fontSize=size,leading=leading or size*1.3,textColor=HexColor(color)))
    _,h=p.wrap(w,1000); p.drawOn(c,x,H-y-h)
    assert y+h < 616, (s,y,h)
    return h
def line(x,y,x2,y2,color=LINE,width=1):
    c.setStrokeColor(HexColor(color));c.setLineWidth(width);c.line(x,H-y,x2,H-y2)
def arrow(x,y,x2,y2,color=GREEN):
    line(x,y,x2,y2,color,1.4)
    import math
    a=math.atan2(y2-y,x2-x)
    for d in [-.55,.55]:
        line(x2,y2,x2-6*math.cos(a+d),y2-6*math.sin(a+d),color,1.4)
def label(s,x,y,w,color=GREEN):text(s.upper(),x,y,w,9.5,color,True,12)
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
    text('Sambhav Jain',32,22,180,11,bold=True)
    text('FOR [CLIENT COMPANY]',365,23,250,9,MUTED)
    line(32,48,616,48)
    label(f'0{n} / {section}',32,64,580)
    text(title,32,86,584,29,bold=True,leading=32)
    text(sub,32,157,580,13,MUTED)
    line(32,615,616,615)
    c.setFont('Body',9);c.setFillColor(HexColor(MUTED));c.drawString(32,16,'sambhavbuilds.com')
    c.drawRightString(616,16,f'0{n} / 04')
def end():c.showPage()

# 1: Business relevance, then a visible change in responsibility.
page(1,'The operational change','Less preparation work.\n<br/>Better-informed decisions.','Maintenance request triage and coordination for your existing operation.')
box(32,199,584,107,WHITE,LINE)
box(40,207,151,91,INK,r=9)
label('Prepared for',53,219,125,'#D6D9D0')
text('[Decision Maker]',53,239,125,13,WHITE,True)
text('[Client Company]',53,263,125,11,'#D6D9D0')
label('A note for your team',207,213,390,ORANGE)
text('After reviewing [verified company detail], I see a possible fit around [specific intake bottleneck]. This system would help [team or role] spend less time chasing details and more time deciding the next action.',207,232,392,12)
label('Today / staff assemble the context',32,325,280,MUTED)
label('With the system / staff decide',340,325,276)
steps=[('Read each message','Capture and link the request'),('Chase the missing details','Ask focused follow-up questions'),('Search records and vendors','Prepare context and vendor options')]
for i,(a,b) in enumerate(steps):
    y=348+i*53
    box(32,y,264,42,WHITE,LINE,9);text(a,46,y+12,239,12,bold=True)
    arrow(307,y+21,329,y+21)
    box(340,y,276,42,SOFT,r=9);text(b,354,y+12,248,12,GREEN,True)
    if i<2:
        arrow(164,y+43,164,y+51,MUTED);arrow(478,y+43,478,y+51)
line(32,519,616,519)
icon('person',34,534,MUTED)
text('What stays yours',68,532,200,13,bold=True)
text('Resident channels, the PMS, vendor relationships, and staff approval.',68,552,536,13,MUTED)
text('Intended result: less repeat handling, clearer urgency, and a prepared next step.',32,586,584,12,GREEN,True)
end()

# 2: Dialogue and a real-looking, explicitly illustrative decision preview.
page(2,'One request, end to end','From a resident message\n<br/>to a manager decision.','Illustrative example: a kitchen leak. Known access and pet details stay with the request.')
line(48,226,48,552,GREEN,1.5)
for y,num in [(216,'1'),(305,'2'),(421,'3'),(551,'4')]:
    box(34,y,28,28,PAPER,GREEN,14);text(num,43,y+5,20,12,GREEN,True)
label('Resident reports',78,208,200)
box(78,228,538,62,WHITE,LINE,10)
text('"Water is spreading under the kitchen sink. It is still flowing with the tap off. My dog is here. You have permission to enter."',92,240,510,13)
label('System checks and clarifies',78,307,500)
text('Links the unit and flags spreading water under your safety rules. Alerts the on-call team without waiting for a reply.',78,328,528,12)
box(78,368,538,37,SOFT,r=9)
text('If onset is missing: "When did the water start spreading?"',92,379,510,12,GREEN,True)
label('Manager reviews / illustrative preview',78,422,500,ORANGE)
box(78,442,538,96,INK,r=12)
text('Kitchen leak  |  [Property / Unit]',93,454,508,15,WHITE,True)
text('Escalation: spreading water; flow continues.<br/>Access allowed. Dog in unit. Plumbing vendor options ready.',93,479,500,12,'#E0E4DB')
text('Review original message   /   Hold   /   Select vendor',93,516,500,11,'#F2B69A',True)
text('Approved action is sent and recorded.',78,550,530,14,bold=True)
text('The resident is told a provider was contacted only after the send succeeds. No invented arrival time.',78,574,530,12,MUTED)
end()

# 3: Named software with explicit read, send, and approval routes.
page(3,'The proposed build','Connected to your tools.\n<br/>Run in an approved environment.','Existing tools stay neutral. Green shows the software and connections I would add.')
box(32,207,584,56,WHITE,LINE)
icon('message',47,223,MUTED)
text('Your resident channels',82,217,500,14,bold=True)
text('[Portal]  /  [Maintenance Email]  /  [SMS Provider]',82,240,500,12,MUTED)
arrow(324,264,324,297)
text('API, webhook, or mailbox access',339,274,264,10,MUTED)
box(32,301,365,144,SOFT,GREEN)
label('Added / client cloud or approved host',47,313,336)
text('n8n workflows',47,335,320,18,GREEN,True)
text('Capture messages, apply fixed safety rules, ask questions, and route approved actions.',47,364,330,13)
icon('db',47,411)
text('PostgreSQL: request state and history',80,414,300,12,GREEN,True)
box(429,301,187,144,WHITE,LINE)
label('External AI service',441,313,164)
text('OpenAI API',441,336,164,17,bold=True)
text('Reads allowed message data and returns a summary.',441,365,161,12)
text('No direct vendor contact.',441,413,161,11,GREEN,True)
arrow(398,352,429,352);arrow(429,390,398,390)
line(210,446,210,467,GREEN,1.4)
line(117,467,523,467,GREEN,1.4)
arrow(117,467,117,485);arrow(324,467,324,485);arrow(523,467,523,485)
for x,w,title,desc in [(32,177,'[Client PMS]','Read unit context; write approved updates.'),(225,177,'[Manager Channel]','Send review request; receive approval.'),(418,198,'[Vendor Channel]','Send only after staff approval.')]:
    box(x,489,w,73,WHITE,LINE,10)
    text(title,x+12,501,w-24,13,bold=True);text(desc,x+12,526,w-24,11,MUTED)
text('Connection routes depend on your PMS access. If writes are limited, prepare a task for staff instead. Hosting, credentials, and AI data use are agreed with you.',32,578,584,12,MUTED)
end()

# 4: Evidence boundaries, buyer controls, and a restrained working-call CTA.
page(4,'Capability and control','A working demo.\n<br/>A client-specific implementation.','The core flow is built. Your PMS connection and production setup are separate work.')
label('Implemented in the local demo',32,207,584)
demo=[('message','Follow-up conversations','Missing details stay linked to the same request.'),('person','Manager-approved vendor email','Vendor options are shown; Hold sends nothing.'),('check','Duplicate-send protection','A repeated approval cannot claim a second send.')]
for i,(ic,title,desc) in enumerate(demo):
    y=233+i*57
    icon(ic,34,y+2)
    text(title,72,y,544,14,bold=True)
    text(desc,72,y+23,544,12,MUTED)
    if i<2:line(72,y+48,616,y+48)
text('Demo tools: n8n, PostgreSQL, OpenAI, Airtable, Telegram, and email. These demo channels do not need to become your business tools.',32,410,584,12,MUTED)
box(32,455,584,65,SOFT,r=10)
text('Your team keeps the decision.',46,468,550,14,GREEN,True)
text('Spend, vendor choice, sensitive cases, appointments, and closure stay with staff. Failed sends remain visible; they do not become success updates.',46,489,550,11)
box(32,535,584,66,INK,r=12)
text('Would this fit your maintenance process?',47,545,365,16,WHITE,True)
text('Bring your PMS and current intake setup.\n<br/>Sambhav Jain  |  sambhav@sambhavbuilds.com',47,569,355,10.5,'#D6D9D0')
box(435,551,165,34,ORANGE,r=8)
text('Discuss your setup',450,560,147,12,WHITE,True)
c.linkURL('https://cal.com/sambhav-builds/pm-automation-audit',(435,H-585,600,H-551),relative=0)
end()
c.save()
print(OUT)
