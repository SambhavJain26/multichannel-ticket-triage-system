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
text('Your [verified company detail] makes [operating goal] relevant. Connecting [intake] to [Client PMS] would help [team] spend less time gathering details and more time making informed decisions.',205,159,396,11,maxh=55)
box(30,226,588,326,'#FAF8F3',LINE,14)
heading('Assumed current process',40,236,269,13)
heading('With the system',344,236,264,13,GREEN)
rows = [
 ('Resident channels','Portal, email, SMS, or phone reports.','Same channels, connected','Reports enter one controlled intake.'),
 ('Staff read and identify','Find the resident, unit, and open work.','Identity and request linked','Match units, duplicates, and related work.'),
 ('Staff chase missing details','Ask questions and piece replies together.','Focused follow-up questions','Ask for missing details; keep replies linked.'),
 ('Staff search and prepare','Look up policies, vendors, and job details.','Context and options prepared','Check policy and vendors; draft job notes.'),
 ('Staff decide and coordinate','Approve work, send it, and chase updates.','Staff approve; actions tracked','Record confirmed sends and follow-ups.'),
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
text('Connectors, workflow, AI, fixed rules, database, and follow-up checks',100,534,502,10)
line(30,563,618,563)
heading('What this helps your team do',30,573,258,13)
text('Repeat less preparation. Decide sooner.<br/>Avoid duplicate actions. See who owns each step.',303,572,315,11,GREEN)
c.showPage()

# PAGE 2: All lifecycle stages; separate branch rail and explicit decision gate.
page(2,'END-TO-END WORKFLOW','From report to <font color="'+ORANGE+'">verified completion</font>','One connected process, with questions, approvals, progress, and closure kept on the same record.')
box(30,132,409,474,WHITE,LINE,r=14)
line(52.5,152,52.5,574)
stages = [
 (142,46,'Receive and connect','Keep reports and attachments; acknowledge receipt. Verify identity; link replies, duplicates, and incidents.'),
 (196,65,'Interpret and check','<b>AI:</b> urgency, trade, language, access, and pets.'),
 (265,51,'Clarify and reassess','Ask for missing symptoms or details with approved questions. Keep known facts; reassess replies and worsening issues.'),
 (320,49,'Prepare the work','Draft PMS notes and vendor instructions. Check trade, coverage, hours, and compliance.'),
 (373,59,'Obtain the human decision','Review the original, context, and rule reason. Hold, edit, reclassify, assign, choose a vendor, or seek owner approval.'),
 (436,49,'Execute the approved action','Claim once; update the PMS and contact the vendor. Tell the resident only what the send result confirms.'),
 (489,51,'Coordinate progress','Track acceptance, quotes, confirmed times, and delays. Answer status questions without opening new requests.'),
 (544,49,'Verify and close','Staff review completion evidence and close the PMS work order. Send the approved final update.'),
]
for i,(y,h,head,body) in enumerate(stages):
    if i==4: box(36,y-3,397,h+5,'#FCF0E9',r=9)
    dot(i+1,41,y+2,PAPER,ORANGE if i==4 else INK)
    heading(head,76,y,347,13,ORANGE if i==4 else INK)
    text(body,76,y+18,347,11,maxh=42)
    if i==1:
        box(76,y+36,346,26,SOFT,r=5)
        text('<b>Fixed rules:</b> apply policy; only raise urgency.',83,y+42,333,10,GREEN,maxh=13)
    # The numbered rail groups the steps. Extra dividers consume the small
    # inter-step gaps and make otherwise separate text blocks feel crowded.
box(455,132,163,474,INK,r=14)
label('Routes that matter',469,144,135,'#D6CFC5')
heading('Safety first',469,167,135,13,'#EEAA8D')
text('Alert the on-call role under policy. Do not wait for clarification.',469,191,135,11,'#F0EBE4')
line(449,219,449,176,ORANGE); arrow(449,176,458,176,ORANGE)
line(439,219,449,219,ORANGE)
heading('Clarification loop',469,263,135,13,'#B8D8C5')
text('Replies return to step 2. No symptom yet? Ask before preparing vendor work.',469,287,135,11,'#F0EBE4')
line(439,293,451,293,GREEN); line(451,293,451,240,GREEN); arrow(451,240,439,240)
heading('Owner approval',469,366,135,13,'#EEAA8D')
text('Spend approval returns to step 5. Vendor contact waits.',469,390,135,11,'#F0EBE4')
arrow(439,383,457,383,ORANGE); line(457,383,457,426,ORANGE); arrow(457,426,439,426,ORANGE)
line(469,452,604,452,'#514B44')
label('At any stage',469,465,135,'#D6CFC5')
heading('Human ownership',469,484,135,13,WHITE)
text('Named staff review unclear, sensitive, unreadable, or failed cases, including identity or vendor gaps. Use approved languages.',469,508,135,10,'#F0EBE4')
c.showPage()

# PAGE 3: Readable connection rows; all external actions pass through n8n.
page(3,'TOOLS & CONNECTIONS','How your <font color="'+ORANGE+'">systems connect</font>','Proposed stack and routes. Access depends on the client’s accounts and permissions.')
def node(x,y,w,h,name,copy,fill=WHITE,ic='mail'):
    box(x,y,w,h,fill,LINE,10)
    icon(ic,x+11,y+10,17)
    heading(name,x+36,y+11,w-46,11.5)
    text(copy,x+12,y+34,w-24,10,MUTED,maxh=h-39)

shell(30,132,186,416,SOFT)
box(38,140,170,75,INK,r=10)
label('Added / approved hosting',50,151,147,'#D6CFC5')
heading('n8n workflow',50,171,147,16,WHITE)
text('All connections run here.',50,195,147,10,'#E9E3DB')
icon('shield-check',50,231,18,GREEN)
heading('Rules and delivery',50,258,148,13)
text('Fixed safety policy,<br/>approved questions,<br/>queue and retries.',50,280,148,11)
arrow(111,328,111,350); arrow(131,350,131,328)
box(44,357,158,91,WHITE,'#BED1C1',9)
icon('database',55,369,18,GREEN)
heading('PostgreSQL',80,371,115,13)
text('Processing state,<br/>conversation history,<br/>audit and send checks.',55,394,135,10)
line(50,465,196,465,'#BED1C1')
text('Client-owned or approved cloud.<br/><br/>PMS remains the business record.',50,478,147,10,MUTED)

# A generous 144-point routing corridor keeps labels separate from endpoints.
connections = [
 ('Resident channels','Portal / email / SMS / phone','[API / webhook / secure mailbox]','reports + replies','questions + updates','mail'),
 ('OpenAI API','Interpretation and drafts only','HTTPS API; outside client hosting','context to AI','structured result','cpu'),
 ('[Client PMS]','Resident / unit / open-work records','[API / partner / export-import route]','lookup + updates','records + result','database'),
 ('[Manager channel]','Human review and authenticated approval','[App integration / secure review link]','decision request','staff approval','user-round'),
 ('[Vendor channel]','Approved job and delivery tracking','[PMS route / portal / email service]','approved job','reply + send result','send'),
 ('[Owner process]','Spending authority stays with the owner','[Existing owner approval process]','spend request','owner decision','circle-check'),
 ('[Reporting tool]','Portfolio status and exception reporting','[Reporting connection]','operational events',None,'chart-no-axes-column'),
]
for i,(name,role,method,outgoing,incoming,ic) in enumerate(connections):
    y=132+i*60
    box(370,y,248,54,WHITE,LINE,9)
    icon(ic,381,y+9,16)
    heading(name,404,y+9,203,12)
    text(role,382,y+25,224,10,MUTED,maxh=13)
    text(method,382,y+39,224,10,MUTED,maxh=13)
    # Incoming resident reports reverse the usual request/response direction.
    if i==0: arrow(370,y+22,216,y+22)
    else: arrow(216,y+22,370,y+22)
    text(outgoing,225,y+7,140,10,GREEN,maxh=13)
    if incoming:
        if i==0: arrow(216,y+48,370,y+48)
        else: arrow(370,y+48,216,y+48)
        text(incoming,225,y+33,140,10,GREEN,maxh=13)

line(30,560,618,560)
label('Confirm before connecting',30,572,186,ORANGE)
text('[Products / permissions / hosting / AI data policy]. If PMS writes are blocked: [staff task / approved import]. Confirm reply and delivery support for each route.',230,571,388,10,MUTED,maxh=38)
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
text('Staff control vendor selection, dispatch, spend, emergency downgrades, appointments, credits, and closure.',344,172,255,11,WHITE)
line(344,225,602,225,'#514B44')
heading('Sensitive-case review',344,239,255,13,WHITE)
text('Staff review legal and accommodation cases. Verify identity before revealing any records.',344,260,255,11,'#E9E3DB',maxh=28)

box(30,320,588,116,WHITE,LINE,12)
icon('shield-check',46,335,18,GREEN)
heading('Controls and recovery',72,337,529,14)
heading('Keep failures visible',46,363,263,11,GREEN)
text('Keep reports and safety checks if AI fails. Retry failed writes or sends; route exceptions to staff. Reject stale or duplicate approvals.',46,381,263,10,maxh=42)
heading('Protect and maintain the service',337,363,264,11,GREEN)
text('Review data conflicts. Set access, MFA, encryption, secrets, and retention. Monitor; test backup restores, changes, and rollback. No self-training.',337,381,264,10,maxh=42)

heading('What this changes for the business',30,450,588,14)
text('Linked history means less chasing. Policy-led alerts limit interruptions. Logged decisions, confirmed resident updates, and shared reporting support reliable handoffs and portfolio visibility.',30,474,588,11,GREEN,maxh=28)

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
