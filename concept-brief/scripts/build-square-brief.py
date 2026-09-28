"""Four-page production brief. Authority: production-maintenance-triage-blueprint.md.
Coordinates are points measured from the top; labels and routes remain editable.
"""
from pathlib import Path
import math
import json
import re
from functools import lru_cache
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
from fontTools.ttLib import TTFont as SourceFont
from fontTools.varLib.instancer import instantiateVariableFont
from reportlab.graphics import renderPDF
from reportlab.graphics.shapes import Drawing, Group, Rect, Circle, Ellipse
from reportlab.graphics.svgpath import SvgPath

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'output/pdf/maintenance-triage-square-brief.pdf'
CACHE = ROOT / 'tmp/pdfs/square-fonts'
OUT.parent.mkdir(parents=True, exist_ok=True)
CACHE.mkdir(parents=True, exist_ok=True)
for name, family, weight in [('Body', 'manrope', 500), ('Bold', 'manrope', 700), ('Display', 'geist', 800)]:
    dest = CACHE / (name + '.ttf')
    font = instantiateVariableFont(SourceFont(ROOT / f'concept-brief/assets/fonts/{family}-variable.ttf'), {'wght': weight}, inplace=True)
    for rec in font['name'].names:
        if rec.nameID in (1, 4, 6):
            rec.string = ('Brief' + name).encode(rec.getEncoding())
    font.save(dest)
    pdfmetrics.registerFont(TTFont(name, str(dest)))
pdfmetrics.registerFontFamily('Body', normal='Body', bold='Bold')
W = H = 648
INK = '#141210'; MUTED = '#5A544B'; PAPER = '#F4F1EA'; LINE = '#DED8CF'
GREEN = '#28634C'; SOFT = '#EDF4EE'; ORANGE = '#C2542D'; WHITE = '#FFFFFF'
c = canvas.Canvas(str(OUT), pagesize=(W, H))
c.setTitle('Maintenance triage | Production solution brief')
c.setAuthor('Sambhav Jain')

def box(x, y, w, h, fill=WHITE, stroke=None, r=12):
    c.setLineWidth(.65)
    c.setFillColor(HexColor(fill)); c.setStrokeColor(HexColor(stroke or fill))
    c.roundRect(x, H-y-h, w, h, r, fill=1, stroke=bool(stroke))

def shell(x, y, w, h, fill=WHITE):
    box(x, y, w, h, '#FAF8F3', LINE, 16)
    box(x+5, y+5, w-10, h-10, fill, r=11)

def text(s, x, y, w, size=11, color=INK, bold=False, leading=None, font=None, maxh=None):
    p = Paragraph(s, ParagraphStyle('p', fontName=font or ('Bold' if bold else 'Body'), fontSize=size, leading=leading or size*1.24, textColor=HexColor(color)))
    _, h = p.wrap(w, 1000)
    assert y+h <= 608, (s, y, h)
    if maxh is not None: assert h <= maxh, (s, h, maxh)
    p.drawOn(c, x, H-y-h)
    return h

def line(x, y, x2, y2, color=LINE, width=1):
    c.setStrokeColor(HexColor(color)); c.setLineWidth(width)
    c.line(x, H-y, x2, H-y2)

def arrow(x, y, x2, y2, color=GREEN):
    line(x, y, x2, y2, color, 1.1)
    a = math.atan2(y2-y, x2-x)
    for d in [-.5, .5]: line(x2,y2,x2-5*math.cos(a+d),y2-5*math.sin(a+d),color,1.1)

def label(s,x,y,w,color=MUTED): text(s.upper(),x,y,w,8,color,True,10)
def heading(s,x,y,w,size=13,color=INK): return text(s,x,y,w,size,color,leading=size*1.12,font='Display')
def dot(n,x,y,fill=WHITE,color=INK):
    box(x,y,23,23,fill,LINE,11.5)
    c.setFillColor(HexColor(color)); c.setFont('Bold',10)
    c.drawCentredString(x+11.5,H-y-15,str(n))

@lru_cache(maxsize=None)
def icon_data(name):
    # Licensed paths copied from the portfolio's existing Lucide dependency.
    source = (ROOT / f'concept-brief/assets/icons/{name}.js').read_text(encoding='utf-8')
    raw = re.search(r'const __iconNode = (\[.*?\]);',source,re.S).group(1)
    return json.loads(re.sub(r'([,{]\s*)([A-Za-z]\w*):',r'\1"\2":',raw))

def icon(name,x,y,size=18,color=MUTED):
    group = Group()
    for kind, attrs in icon_data(name):
        a = {k:float(v) for k,v in attrs.items() if k not in ('key','d')}
        style = dict(fillColor=None,strokeColor=HexColor(color),strokeWidth=1.5,strokeLineCap=1,strokeLineJoin=1)
        if kind=='path': shape=SvgPath(attrs['d'],**style)
        elif kind=='rect': shape=Rect(a['x'],a['y'],a['width'],a['height'],rx=a.get('rx',0),ry=a.get('rx',0),**style)
        elif kind=='circle': shape=Circle(a['cx'],a['cy'],a['r'],**style)
        elif kind=='ellipse': shape=Ellipse(a['cx'],a['cy'],a['rx'],a['ry'],**style)
        else: raise ValueError(kind)
        group.add(shape)
    group.transform=(size/24,0,0,-size/24,0,size)
    drawing=Drawing(size,size); drawing.add(group)
    renderPDF.draw(drawing,c,x,H-y-size)

def icon_tile(name,x,y,color=MUTED,fill=PAPER):
    box(x,y,26,26,fill,r=13)
    icon(name,x+5,y+5,16,color)

def page(n,section,title,sub):
    box(0,0,W,H,PAPER,r=0)
    text('Sambhav Jain',30,17,230,10,bold=True)
    c.setFont('Bold',10); c.setFillColor(HexColor(INK))
    c.drawRightString(618,H-27,'[Client Company]')
    line(30,40,618,40)
    eyebrow = 'MAINTENANCE TRIAGE / '+section
    pill_width = pdfmetrics.stringWidth(eyebrow,'Bold',8)+20
    box(30,47,pill_width,18,'#FAF8F3',LINE,9)
    label(eyebrow,40,51,pill_width-20)
    heading(title,30,69,588,22)
    text(sub,30,100,588,11,MUTED,maxh=28)
    line(30,617,618,617)
    c.setFont('Body',8); c.setFillColor(HexColor(MUTED))
    c.drawString(30,16,'sambhavbuilds.com / Proposed production solution')
    c.drawRightString(618,16,f'{n:02d} / 04')

# PAGE 1: Comparison and relevance. Existing systems remain neutral.
page(1,'BUSINESS CHANGE','What changes in your <font color="'+ORANGE+'">maintenance process</font>','The same resident channels and PMS. Less manual preparation before your team decides.')
shell(30,126,588,91)
box(38,134,153,75,INK,r=11)
label('Research reviewed',50,145,129,'#D6CFC5')
text('[Website / source]<br/>[Portfolio / markets]<br/>[Verified operating detail]',50,162,130,10,WHITE,leading=12)
label('A note for [Decision Maker]',205,141,397,ORANGE)
text('At [Client Company], [verified detail] may make [operating goal] a priority. Connecting [intake] to [Client PMS] would give [team] the request details in one place before they decide.',205,159,396,11,maxh=55)
box(30,226,588,326,'#FAF8F3',LINE,14)
heading('Assumed current process',40,236,269,13)
heading('With the system',344,236,264,13,GREEN)
rows = [
 ('Resident channels','Portal, email, SMS, or phone reports.','Same channels, connected','Reports enter one controlled intake.'),
 ('Staff read and identify','Find the resident, unit, and open work.','Identity and request linked','Match units, duplicates, and related work.'),
 ('Staff chase missing details','Ask questions and piece replies together.','Focused follow-up questions','Ask for missing details; keep replies linked.'),
 ('Staff search and prepare','Look up policies, vendors, and job details.','Context and options prepared','Check policy and vendors; draft job notes.'),
 ('Staff decide and coordinate','Approve work, send it, and chase updates.','Staff decide; workflow tracks','Record confirmed sends and follow-ups.'),
]
for i,(lh,lb,rh,rb) in enumerate(rows):
    y=260+i*49
    box(38,y,276,43,WHITE,LINE,9)
    box(334,y,276,43,SOFT if i in (1,2,3) else WHITE,LINE,9)
    icon_tile(['mail','list-filter','message-circle-question-mark','database','user-round'][i],39,y+8)
    icon_tile(['mail','cpu','message-circle-question-mark','shield-check','circle-check'][i],343,y+8,GREEN if i in (1,2,3) else MUTED, '#E0ECE2' if i in (1,2,3) else PAPER)
    text(lh,73,y+6,230,11,bold=True)
    text(lb,73,y+23,230,10,MUTED,maxh=13)
    text(rh,377,y+6,230,11,GREEN if i in (1,2,3) else INK,True)
    text(rb,377,y+23,230,10,MUTED,maxh=13)
    if i<4:
        arrow(172,y+43,172,y+48,MUTED); arrow(476,y+43,476,y+48)
label('Stays',46,516,65)
text('Channels, PMS, people’s authority',100,514,230,10)
label('Reduced',344,516,65)
text('Reading, copying, and chasing',408,514,202,10)
label('Added',46,536,65,GREEN)
text('Connected intake, AI, fixed rules, request state, and follow-up checks',100,534,502,10)
line(30,563,618,563)
heading('What this helps your team do',30,573,258,13)
text('Less repeated prep and fewer duplicate actions.<br/>Faster decisions with clear ownership.',303,572,315,11,GREEN)
c.showPage()

# PAGE 2: All lifecycle stages; separate branch rail and explicit decision gate.
page(2,'END-TO-END WORKFLOW','From report to <font color="'+ORANGE+'">verified completion</font>','See what AI prepares, what the workflow handles, and where your team decides.')
box(30,132,409,474,WHITE,LINE,r=14)
line(52.5,152,52.5,574)
stages = [
 (142,46,'Receive and connect','Save report and files; match resident and unit. Link replies, duplicates, and incidents; acknowledge receipt.','WORKFLOW'),
 (196,65,'Interpret and check','AI suggests urgency and trade; flags access, pets, language.','AI'),
 (265,51,'Clarify and reassess','Ask approved follow-ups. Link and reassess each reply.','AI + WORKFLOW'),
 (320,49,'Prepare the work','Draft PMS and vendor notes; check trade, coverage, hours, and compliance.','AI + WORKFLOW'),
 (373,59,'Obtain the human decision','Manager reviews the source and reason; may hold, edit, change priority, assign, choose a vendor, or seek owner approval.','MANAGER'),
 (436,49,'Execute the approved action','After approval, update PMS and contact the vendor once. Tell the resident only after a successful send.','WORKFLOW'),
 (489,51,'Coordinate progress','Track vendor replies, quotes, confirmed times, and delays. Answer status without a new request.','WORKFLOW'),
 (544,49,'Verify and close','Staff verify and close in PMS; workflow sends the approved final update.','STAFF'),
]
for i,(y,h,head,body,owner) in enumerate(stages):
    if i==4: box(36,y-3,397,h+5,'#FCF0E9',r=9)
    dot(i+1,41,y+2,PAPER,ORANGE if i==4 else INK)
    heading(head,76,y,241,13,ORANGE if i==4 else INK)
    actor_color = ORANGE if owner in ('MANAGER','STAFF') else GREEN
    actor_fill = WHITE if owner in ('MANAGER','STAFF') else SOFT
    box(320,y+1,103,17,actor_fill,ORANGE if owner in ('MANAGER','STAFF') else None,r=8)
    label(owner,327,y+4,92,actor_color)
    text(body,76,y+18,347,11,maxh=14 if i==1 else 42)
    if i==1:
        box(76,y+36,346,26,SOFT,r=5)
        text('<b>Fixed rules:</b> only raise urgency; safety alerts do not wait.',83,y+42,333,10,GREEN,maxh=13)
    # The numbered rail groups the steps. Extra dividers consume the small
    # inter-step gaps and make otherwise separate text blocks feel crowded.
box(455,132,163,474,INK,r=14)
label('Who handles what',469,147,135,'#D6CFC5')
heading('AI',469,175,135,14,'#B8D8C5')
text('Reads reports, finds gaps, and drafts notes.',469,200,135,11,'#F0EBE4')
line(469,267,604,267,'#514B44')
heading('Workflow + rules',469,280,135,13,'#B8D8C5')
text('Links records, enforces policy, asks questions, checks vendors, and tracks sends.',469,305,135,11,'#F0EBE4')
line(469,391,604,391,'#514B44')
heading('Manager + staff',469,405,135,13,'#EEAA8D')
text('Manager approves work and vendor; staff handle exceptions and close.',469,430,135,11,'#F0EBE4')
line(469,520,604,520,'#514B44')
label('At any stage',469,533,135,'#D6CFC5')
text('Unclear, sensitive, or failed cases go to named staff.',469,551,135,10,'#F0EBE4')
c.showPage()

# PAGE 3: Three-zone architecture. Short links leave the central system legible.
page(3,'TOOLS & CONNECTIONS','How your <font color="'+ORANGE+'">systems connect</font>','Proposed stack and routes. Access depends on the client’s accounts and permissions.')
label('Existing channels',30,137,160)
label('Added / proposed system',211,137,200,GREEN)
label('Existing business tools',437,137,181)

def external_card(x,y,w,h,title,copy,ic):
    box(x,y,w,h,WHITE,LINE,10)
    icon_tile(ic,x+11,y+10)
    heading(title,x+45,y+13,w-55,11.5)
    text(copy,x+13,y+33,w-26,10,MUTED,maxh=h-38)

external_card(30,170,160,118,'Resident intake',
              'Portal, email, SMS, phone.<br/>Reports and replies in; questions and confirmed updates out.','mail')
label('Proposed / outside hosting',30,321,160,GREEN)
external_card(30,341,160,116,'OpenAI API',
              'Context in; interpretation and drafts back. No business actions. HTTPS API.','cpu')

# The enclosing surface is the client's approved hosting boundary.
shell(211,153,200,353,SOFT)
box(219,161,184,69,INK,r=10)
label('[Client AWS / approved cloud]',231,171,162,'#D6CFC5')
heading('n8n workflow',231,190,162,17,WHITE)
text('Links tools and runs the flow.',231,213,162,10,'#E9E3DB',maxh=13)
box(224,243,174,61,WHITE,'#BED1C1',9)
icon_tile('shield-check',235,255,GREEN,SOFT)
heading('Fixed rules',267,257,120,12)
text('Safety and approval limits.',235,282,151,10,maxh=13)
arrow(311,305,311,313)
box(224,314,174,60,WHITE,'#BED1C1',9)
icon_tile('message-circle-question-mark',235,326,GREEN,SOFT)
heading('Conversation state',267,328,120,11)
text('Replies, retries, delivery.',235,352,151,10,maxh=13)
arrow(311,376,311,396)
box(224,397,174,83,WHITE,'#BED1C1',9)
icon_tile('database',235,409,GREEN,SOFT)
heading('PostgreSQL',267,411,120,12)
text('Request state, history, audit, and duplicate checks.',235,439,151,10,maxh=26)
text('PMS remains the business record.',224,485,174,9,MUTED,maxh=12)

# Two resident/AI branches meet the n8n header. The cards describe direction.
line(202,207,202,400,GREEN,1.1)
line(202,207,211,207,GREEN,1.1)
for branch_y in (229,400):
    line(190,branch_y,202,branch_y,GREEN,1.1)
    c.setFillColor(HexColor(GREEN)); c.circle(202,H-branch_y,1.8,fill=1,stroke=0)

# One shared junction, with short branches, keeps the central service visually
# dominant. Directions are written in the endpoint copy.
line(411,207,423,207,GREEN,1.2)
line(423,200,423,476,GREEN,1.2)
business = [
 ('[Client PMS]','Reads resident, unit, and work; writes approved records.','database'),
 ('[Manager channel]','Decision request out; staff approval back.','user-round'),
 ('[Vendor channel]','Approved job out; reply and send result back.','send'),
 ('[Owner process]','Spend request out; owner decision back.','circle-check'),
 ('[Reporting tool]','Operational events out for portfolio view.','chart-no-axes-column'),
]
for i,(name,exchange,ic) in enumerate(business):
    y=169+i*69
    external_card(437,y,181,64,name,exchange,ic)
    line(423,y+31,437,y+31,GREEN,1.1)
    c.setFillColor(HexColor(GREEN)); c.circle(423,H-y-31,1.8,fill=1,stroke=0)

line(30,526,618,526)
label('Routes to confirm with the client',30,537,588,ORANGE)
routes = [
 ('Intake','[API / webhook / secure mailbox]'), ('PMS','[API / partner / import]'),
 ('Manager','[app / secure review link]'), ('Vendor','[PMS / portal / email]'),
 ('Owner','[existing approval]'), ('Reporting','[feed / export]'),
]
for i,(name,route) in enumerate(routes):
    x=30 if i%2==0 else 328; y=553+(i//2)*18
    text(f'<b>{name}:</b> {route}',x,y,280,10,maxh=13)
c.showPage()

# PAGE 4: Running the service, not repeating the lifecycle.
page(4,'OPERATIONS & OUTCOMES','How your team <font color="'+ORANGE+'">runs it each day</font>','Staff work in familiar tools. Each waiting item or failed action has an owner and a next step.')
shell(30,132,282,174)
heading('Daily operating view',46,147,250,14)
text('<b>Priority work.</b> Urgent and overdue items, owner/vendor delays, and unowned work.',46,172,250,11,maxh=41)
text('<b>Alerts.</b> Follow on-call and quiet-hour rules; check unanswered emergencies. Age alone never creates an emergency.',46,211,250,11,maxh=55)
text('<b>Daily summary.</b> Volume, response targets, waiting work, and exceptions.',46,265,250,11,maxh=28)
shell(328,132,290,174,INK)
heading('Human authority',344,147,255,14,'#EEAA8D')
text('Staff choose vendors and approve dispatch, spend, appointments, credits, emergency downgrades, and closure.',344,172,255,11,WHITE)
line(344,225,602,225,'#514B44')
heading('Sensitive-case review',344,239,255,13,WHITE)
text('Legal or accommodation issues go to staff. Verify identity before sharing records.',344,260,255,11,'#E9E3DB',maxh=28)

box(30,320,588,116,WHITE,LINE,12)
icon('shield-check',46,335,18,GREEN)
heading('Controls and recovery',72,337,529,14)
heading('Keep failures visible',46,363,263,11,GREEN)
text('Keep requests and safety checks if AI fails. Retry failed writes or sends; assign exceptions. Block stale or duplicate approvals.',46,381,263,10,maxh=42)
heading('Protect and maintain the service',337,363,264,11,GREEN)
text('Resolve data conflicts. Set roles/MFA, encryption, secrets, and retention. Monitor; test backup restores and rollback. Review changes; no self-training.',337,381,264,10,maxh=42)

heading('What this changes for the business',30,450,588,14)
text('Linked history reduces chasing; policy-led alerts limit interruptions. Confirmed updates and shared reporting make handoffs and portfolio work easier to track.',30,474,588,11,GREEN,maxh=28)

shell(30,514,588,92,INK)
heading('Discuss your maintenance workflow.',46,531,388,17,WHITE)
text('Review your tools, connections, and approval rules.',46,558,367,11,'#E9E3DB',maxh=14)
text('Sambhav Jain / sambhav@sambhavbuilds.com',46,584,371,10,'#D6CFC5')
box(451,542,150,38,ORANGE,r=19)
text('Discuss the fit',465,555,106,10,WHITE,True)
box(574,549,24,24,'#A63E1D',r=12); arrow(580,561,591,561,WHITE)
c.linkURL('https://cal.com/sambhav-builds/pm-automation-audit',(451,H-580,601,H-542),relative=0)
c.showPage()
c.save()
print(OUT)
