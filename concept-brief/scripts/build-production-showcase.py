"""Render a separate prospect-facing production system showcase.

Examples are illustrative, not deployment evidence. No existing brief is modified.
"""
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'output/pdf/maintenance-triage-production-showcase.pdf'
W, H = 432, 720
M, CW = 28, 376
INK, MUTED, PAPER, WHITE = '#191C19', '#535A54', '#F8F7F2', '#FFFFFF'
GREEN, PALE, ORANGE, LINE = '#285F48', '#ECF3EE', '#B84924', '#D5D9D1'
for name, file in [('Body','arial.ttf'),('Bold','arialbd.ttf')]:
    pdfmetrics.registerFont(TTFont(name, 'C:/Windows/Fonts/'+file))
pdfmetrics.registerFontFamily('Body',normal='Body',bold='Bold')
c=canvas.Canvas(str(OUT),pagesize=(W,H))
c.setTitle('Maintenance coordination | Production system showcase')
c.setAuthor('Sambhav Jain')
TEXT_BOUNDS=[]

def rect(x,y,w,h,fill=WHITE,stroke=None,r=12):
    c.setLineWidth(.8)
    c.setFillColor(HexColor(fill)); c.setStrokeColor(HexColor(stroke or fill))
    c.roundRect(x,H-y-h,w,h,r,stroke=bool(stroke),fill=1)

def text(s,x,y,w,size=14,color=INK,bold=False,leading=None):
    q=Paragraph(s,ParagraphStyle('s',fontName='Bold' if bold else 'Body',fontSize=size,
        leading=leading or size*1.28,textColor=HexColor(color)))
    _,h=q.wrap(w,H)
    if y<684 and y+h>677: raise ValueError(f'Footer collision: {s[:50]} {y+h}')
    q.drawOn(c,x,H-y-h)
    TEXT_BOUNDS.append((c.getPageNumber(),x,y,w,h,s))
    return h

def line(x1,y1,x2,y2,color=LINE,width=.8):
    c.setStrokeColor(HexColor(color));c.setLineWidth(width)
    c.line(x1,H-y1,x2,H-y2)

def arrow(x,y1,y2,color=GREEN):
    line(x,y1,x,y2,color,1.3)
    line(x,y2,x-3,y2-4,color,1.3);line(x,y2,x+3,y2-4,color,1.3)

def icon(kind,x,y,color=GREEN):
    c.setStrokeColor(HexColor(color));c.setLineWidth(1.3)
    if kind=='person':
        c.circle(x+9,H-y-5,4,stroke=1,fill=0)
        c.roundRect(x+2,H-y-23,14,11,5,stroke=1,fill=0)
    elif kind=='message':
        c.roundRect(x,H-y-19,21,17,4,stroke=1,fill=0)
        line(x+5,y+19,x+3,y+24,color,1.3)
        line(x+5,y+7,x+16,y+7,color);line(x+5,y+12,x+13,y+12,color)
    elif kind=='record':
        c.roundRect(x+2,H-y-24,17,23,2,stroke=1,fill=0)
        for a in (7,12,17):line(x+6,y+a,x+15,y+a,color)
    else:
        c.circle(x+10,H-y-12,10,stroke=1,fill=0)
        line(x+5,y+12,x+9,y+16,color,1.5);line(x+9,y+16,x+16,y+8,color,1.5)

def page(n,kicker,title,sub=None):
    rect(0,0,W,H,PAPER,r=0)
    text('SAMBHAV JAIN',M,20,180,10,bold=True)
    text('MAINTENANCE COORDINATION',236,21,180,8.5,color=MUTED)
    line(M,43,W-M,43)
    text(kicker.upper(),M,61,CW,10,color=ORANGE,bold=True)
    th=text(title,M,84,CW,27,bold=True,leading=30)
    if sub:text(sub,M,96+th,CW,14,color=MUTED)
    line(M,686,W-M,686)
    text('sambhavbuilds.com',M,697,240,9,color=MUTED)
    text(f'{n} / 4',373,697,35,9,color=MUTED)

page(1,'01 / What changes','Maintenance requests,<br/>prepared for a decision.')
text('For [Client Company] / [Decision Maker]',M,159,CW,11,color=GREEN,bold=True)
text('When requests arrive in pieces, staff have to collect the story before they can act. This system gathers the details, asks follow-up questions, and prepares the next action in the tools your team uses.',M,192,CW,15,leading=20)
rect(M,290,CW,59,INK)
text('The change: less preparation by hand.<br/>Your team keeps the judgment.',43,302,346,14,color=WHITE,bold=True,leading=18)

rows=[
 ('message','From scattered messages','The system links reports and replies to one request, preserving the resident\'s original words.'),
 ('record','From chasing missing details','Approved follow-up questions collect what is missing. The manager receives the issue, access notes, history, and vendor options together.'),
 ('person','To a prepared human decision','Your manager reviews the urgency and chooses the action. Vendor contact, spending, and closure remain under your team\'s control.')]
y=363
for i,(kind,title,body) in enumerate(rows):
    icon(kind,38,y+3)
    text(title,77,y,327,16,bold=True)
    h=text(body,77,y+27,327,13.5,leading=17)
    if i<2:line(77,y+27+h+12,404,y+27+h+12)
    y+=100
text('Keep your channels, PM platform, and vendor relationships.',M,657,CW,11.5,color=GREEN,bold=True)
c.showPage()

page(2,'02 / Follow one request','The work between<br/>the message and the action.')
text('Illustrative production journey',M,157,CW,11,color=MUTED)
steps=[
 (185,'RESIDENT','Reports an active leak','"Water is spreading under my kitchen sink. It is still flowing. You can enter, but there is a dog."'),
 (279,'SYSTEM','Checks the issue and alerts','Links the resident, unit, and open work. AI reads the message; fixed safety rules apply. An urgent safety alert does not wait for a reply.'),
 (380,'SYSTEM + RESIDENT','Clarifies without starting over','"When did it start?" / "Ten minutes ago."<br/>The reply joins the same request. Known entry permission and pet details are not asked again.'),
 (481,'MANAGER','Reviews and approves','Reviews the prepared case and selects a vendor or holds the action. Any required owner approval comes before the send.'),
 (582,'SYSTEM','Sends, records, and updates','Sends the approved vendor request once. Records the send result, then updates the resident with confirmed status.')]
for i,(y,actor,title,body) in enumerate(steps,1):
    if i<5:arrow(42,y+28,steps[i][0]-7)
    rect(28,y,28,28,INK if i==4 else PALE,r=14)
    text(str(i),38,y+6,18,11,color=WHITE if i==4 else GREEN,bold=True)
    text(actor,72,y-1,332,9.5,color=ORANGE if i==4 else GREEN,bold=True)
    text(title,72,y+17,332,15.5,bold=True)
    text(body,72,y+43,332,13,leading=16)
c.showPage()

page(3,'03 / Tools and connections','Connected to your business.<br/>Controlled by your team.')
text('The production setup is configured around your PM platform, approved channels, and access.',M,158,CW,14,color=MUTED)
rect(M,213,CW,66,WHITE,LINE)
text('EXISTING SYSTEMS',42,224,346,9.5,color=MUTED,bold=True)
text('Resident channels + [Client PMS]',42,242,346,16,bold=True)
arrow(216,282,291)
text('Messages in; resident, unit, and work-order data read',M,298,CW,10.5,color=GREEN)
arrow(216,315,325)
rect(M,333,CW,166,PALE,LINE)
rect(M,333,CW,57,INK,r=12);rect(M,371,CW,19,INK,r=0)
text('n8n  /  workflow and fixed rules',42,345,346,16,color=WHITE,bold=True)
text('Connects the steps, questions, and approvals.',42,369,346,12,color=WHITE)
text('OpenAI API',43,408,155,15,color=GREEN,bold=True)
text('Receives message text; returns issue details and drafts.',43,433,153,12.5,leading=16)
line(216,407,216,482)
text('PostgreSQL',233,408,155,15,color=GREEN,bold=True)
text('Keeps request history, replies, decisions, and send records.',233,433,155,12.5,leading=16)
arrow(216,502,516)
text('DECISIONS AND CONFIRMED RESULTS',M,524,CW,10,color=GREEN,bold=True)
text('<b>Manager channel:</b> prepared case out; approval back.<br/><b>Vendor channel:</b> approved request and send result.<br/><b>PMS:</b> work-order notes and confirmed status.',M,545,CW,12.5,leading=19)
text('<b>Where it runs:</b> n8n and PostgreSQL on a client-owned cloud server; OpenAI is an external API service. PMS connections use the access your platform permits.',M,613,CW,12,leading=16)
c.showPage()

page(4,'04 / What your team gets','A complete handoff.<br/>A visible next action.')
text('Illustrative outputs from the same kitchen leak',M,158,CW,11,color=MUTED)
outputs=[
 (188,117,'person','MANAGER / READY TO REVIEW','Active kitchen leak; water still flowing.<br/>Entry permitted; dog in the unit.<br/>Original report, urgency reason, and eligible plumbing vendors in one view.'),
 (321,103,'message','VENDOR / AFTER APPROVAL','"Active kitchen leak at [Property / Unit]. Water is still flowing. Entry permitted; dog on site. Please confirm availability."'),
 (440,89,'record','TEAM / ONE SHARED RECORD','Manager approval recorded. Vendor request sent. Awaiting vendor response. Resident informed that a provider has been contacted.')]
for y,h,kind,label,body in outputs:
    rect(M,y,CW,h,WHITE,LINE)
    icon(kind,42,y+15)
    text(label,77,y+15,312,10,color=GREEN,bold=True)
    text(body,77,y+37,312,13,leading=17)
text('Less copying and chasing. Clearer decisions.<br/>The resident gets a factual update after contact,<br/>not an appointment promise before confirmation.',M,546,CW,13.5,leading=18)
rect(M,611,CW,65,INK)
text('See how this fits your maintenance process.',42,622,346,14,color=WHITE,bold=True)
text('Book a 15-minute walkthrough  >',42,647,346,13,color='#F0A47B',bold=True)
c.linkURL('https://cal.com/sambhav-builds/pm-automation-audit',(M,H-676,W-M,H-611),relative=0)
c.showPage()
c.save()
print(OUT)
