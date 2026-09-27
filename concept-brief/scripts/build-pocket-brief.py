"""Build the independent four-page, phone-first maintenance brief."""
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'output/pdf/maintenance-triage-pocket-guide.pdf'
pdfmetrics.registerFont(TTFont('Body', 'C:/Windows/Fonts/arial.ttf'))
pdfmetrics.registerFont(TTFont('Bold', 'C:/Windows/Fonts/arialbd.ttf'))
pdfmetrics.registerFontFamily('Body', normal='Body', bold='Bold')
W, H = 396, 612
INK, MUTED, PAPER = '#191C19', '#555B55', '#FAF9F5'
GREEN, PALE, ORANGE, LINE = '#286349', '#EDF4EF', '#B34822', '#D7DBD3'
c = canvas.Canvas(str(OUT), pagesize=(W, H))
c.setTitle('Maintenance requests | A practical system guide')
c.setAuthor('Sambhav Jain')

def box(x, y, w, h, fill=PAPER, stroke=None, r=12):
    c.setFillColor(HexColor(fill))
    c.setStrokeColor(HexColor(stroke or fill))
    c.roundRect(x, H-y-h, w, h, r, fill=1, stroke=bool(stroke))

def p(text, x, y, w, size=13, color=INK, bold=False, leading=None):
    style = ParagraphStyle('text', fontName='Bold' if bold else 'Body', fontSize=size,
                           leading=leading or size*1.28, textColor=HexColor(color))
    q = Paragraph(text, style)
    _, h = q.wrap(w, H)
    if y < 578 and y+h > 574:
        raise ValueError(f'Content overlaps footer: {text[:60]} at {y+h}')
    q.drawOn(c, x, H-y-h)
    return h

def rule(y, x=26, end=370):
    c.setStrokeColor(HexColor(LINE)); c.setLineWidth(.7)
    c.line(x,H-y,end,H-y)

def arrow(x, y1, y2, color=GREEN):
    c.setStrokeColor(HexColor(color)); c.setLineWidth(1.3)
    c.line(x,H-y1,x,H-y2)
    c.line(x,H-y2,x-3,H-y2+4); c.line(x,H-y2,x+3,H-y2+4)

def page(n, section, title, subtitle=None):
    box(0,0,W,H,PAPER,r=0)
    p('SAMBHAV JAIN',26,20,185,9,bold=True)
    p('SYSTEM GUIDE / '+str(n).zfill(2),264,20,110,9,color=MUTED)
    rule(42)
    p(section.upper(),26,57,344,10,color=ORANGE,bold=True)
    h=p(title,26,79,344,26,bold=True,leading=28)
    if subtitle: p(subtitle,26,89+h,344,13,color=MUTED)
    rule(578)
    p('sambhavbuilds.com',26,585,220,9,color=MUTED)
    p(f'{n} / 4',340,585,40,9,color=MUTED)

# Page 1: output first, not a cover or a feature inventory.
page(1,'Maintenance request triage','What your manager\nreceives'.replace('\n','<br/>'))
p('For [Client Company] / [Decision Maker]',26,147,344,11,color=GREEN,bold=True)
p('A request with the key details gathered, missing information followed up, and the next action ready for a person to review.',26,177,344,15,leading=20)
box(26,253,344,213,'#FFFFFF',LINE)
box(26,253,344,34,INK,r=10)
box(26,273,344,14,INK,r=0)
p('ILLUSTRATIVE MANAGER VIEW',40,264,316,10,color='#FFFFFF',bold=True)
p('Kitchen sink leak',42,302,312,19,bold=True)
p('<b>Reported:</b> Water is still flowing and spreading.',42,333,310)
p('<b>Access:</b> Entry permitted. Dog in the unit.',42,380,310)
rule(423,42,354)
p('Review urgency  /  Hold  /  Select vendor',42,437,310,11,color=GREEN,bold=True)
p('Less time rebuilding the story.<br/>A clearer handoff to the manager.',26,485,344,16,bold=True,leading=21)
p('Your team still controls vendor contact, spending, appointments, and closure.',26,537,344,12,color=MUTED)
c.showPage()

# Page 2: one coherent, fictional case; vertical actor/action sequence.
page(2,'One request, end to end','From report<br/>to approved action')
p('Illustrative case - not a customer result.',26,145,344,11,color=MUTED)
steps = [
 ('RESIDENT','Reports the leak','"Water is spreading under my kitchen sink. It is still flowing. You can enter, but there is a dog."'),
 ('SYSTEM + RESIDENT','Asks only what is missing','"When did it start?"<br/>"About ten minutes ago." The reply stays with this request.'),
 ('SYSTEM','Prepares the manager view','Links the unit and history; checks safety; gathers eligible vendor options. Known access and pet details are kept.'),
 ('MANAGER','Decides what happens next','Reviews the original message and urgency reason, then holds, changes, or approves vendor contact.'),
 ('SYSTEM','Sends and records the result','Contacts the selected vendor once. Updates the resident only after the send succeeds - no invented arrival time.')]
ys=[178,253,328,403,478]
for i,((actor,title,body),y) in enumerate(zip(steps,ys),1):
    if i<5: arrow(39,y+25,ys[i]-5)
    box(26,y,26,26,INK if i==4 else PALE,r=13)
    p(str(i),34,y+5,18,11,color='#FFFFFF' if i==4 else GREEN,bold=True)
    p(actor,64,y-1,306,9,color=ORANGE if i==4 else GREEN,bold=True)
    p(title,64,y+13,306,14,bold=True)
    p(body,64,y+34,306,11.7,leading=14)
p('Safety alerts must not wait for clarification. Sensitive or unclear cases go to a person.',26,549,344,10,color=MUTED,leading=12)
c.showPage()

# Page 3: diagram names software and separates existing, proposed, external.
page(3,'Software and connections','What I would add')
p('Proposed client setup. Connections depend on your software access and permissions.',26,121,344,13,color=MUTED)
box(26,174,344,55,'#FFFFFF',LINE)
p('YOUR EXISTING TOOLS',40,184,316,9,color=MUTED,bold=True)
p('Resident channel + [Client PMS]',40,201,316,14,bold=True)
arrow(198,231,237)
p('Messages + allowed resident / work-order data',26,240,344,10,color=GREEN)
arrow(198,254,262)
box(26,267,344,69,INK)
p('n8n WORKFLOWS',40,278,316,14,color='#FFFFFF',bold=True)
p('Route questions, checks, approvals, and sends.',40,301,316,13,color='#FFFFFF')
arrow(110,338,362); arrow(286,338,362)
box(26,368,165,89,PALE,LINE)
box(205,368,165,89,PALE,LINE)
p('OpenAI API',38,379,141,14,color=GREEN,bold=True)
p('Receives message text; returns issue details and drafts.',38,405,141,12,leading=15)
p('PostgreSQL',217,379,141,14,color=GREEN,bold=True)
p('Stores request history, replies, approvals, and send state.',217,405,141,12,leading=15)
p('<b>Back through n8n:</b> manager decisions, approved vendor messages, and allowed PMS updates.',26,470,344,12,leading=15)
p('Fixed safety rules are separate from AI. People approve vendor contact.',26,508,344,12,bold=True,leading=15)
p('<b>Hosting:</b> n8n + PostgreSQL on a client-owned server. OpenAI runs as an external API service.',26,545,344,11,leading=14)
c.showPage()

# Page 4: practical fit, clear ownership, honest demo status, quiet invitation.
page(4,'Fit with your business','Agree the connections.<br/>Keep the decisions.')
items=[
 ('01','Start with your intake','Choose the existing mailbox or resident channel. Confirm identity checks and the data it can share.'),
 ('02','Connect the review and work record','Route prepared requests to your manager channel. Write approved results to the PMS where access allows; otherwise use a staff-reviewed task.'),
 ('03','Set the rules with your team','You choose questions, vendor eligibility, approval limits, and access. I configure the connections; we agree hosting, backups, and support.')]
y=151
for num,title,body in items:
    p(num,26,y,30,12,color=ORANGE,bold=True)
    p(title,66,y,304,14,bold=True)
    h=p(body,66,y+24,304,12.5,leading=16)
    y += 24+h+20
rule(y-5)
p('<b>Current build:</b> a local demo using Gmail, Telegram, and Airtable with n8n, PostgreSQL, and OpenAI. PMS integration and production deployment are still to be built for the client.',26,y+8,344,11.5,color=MUTED,leading=15)
box(26,480,344,85,INK)
p('See one request in the demo.',40,491,316,17,color='#FFFFFF',bold=True)
p('Then discuss your intake and PM platform.',40,516,316,12,color='#FFFFFF')
p('Book a short walkthrough  >',40,542,300,12,color='#EEA176',bold=True)
c.linkURL('https://cal.com/sambhav-builds/pm-automation-audit',(26,H-565,370,H-480),relative=0)
c.showPage()
c.save()
print(OUT)
