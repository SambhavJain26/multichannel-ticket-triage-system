"""Four-page production brief. Authority: production-maintenance-triage-blueprint.md.
Coordinates are points measured from the top; labels and routes remain editable.
"""
from pathlib import Path
import math
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
    box(x,y,23,23,fill,LINE,11.5); text(str(n),x+6,y+5,16,10,color,True)

def page(n,section,title,sub):
    box(0,0,W,H,PAPER,r=0)
    text('Sambhav Jain',30,17,230,10,bold=True)
    text('[Client Company]',433,17,185,10,bold=True)
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
shell(30,128,588,87)
box(38,136,153,71,INK,r=11)
label('Research reviewed',50,147,129,'#D6CFC5')
text('[Website / source]<br/>[Portfolio / markets]<br/>[Verified operating detail]',50,164,130,10,WHITE)
label('A note for [Decision Maker]',205,141,397,ORANGE)
text('Your [verified company detail] makes [operating goal] relevant. Connecting [intake] to [Client PMS] would help [team] spend less time gathering details and more time making informed decisions.',205,158,396,11,maxh=55)
heading('Assumed current process',40,228,269,13)
heading('With the system',344,228,264,13,GREEN)
rows = [
 ('Resident channels','Portal, email, SMS, or phone reports.','Same channels, connected','Approved intake brings reports together.'),
 ('Staff read and identify','Find the resident, unit, and open work.','Identity and request linked','Match unit, replies, duplicates, and incidents.'),
 ('Staff chase missing details','Ask questions and piece replies together.','Focused follow-up questions','Ask what is missing; keep replies together.'),
 ('Staff search and prepare','Look up policies, vendors, and job details.','Context and options prepared','Check policy and vendors; draft instructions.'),
 ('Staff decide and coordinate','Approve work, send it, and chase updates.','Staff approve; actions tracked','Record confirmed sends and follow-ups.'),
]
for i,(lh,lb,rh,rb) in enumerate(rows):
    y=251+i*53
    box(30,y,284,43,WHITE,LINE,9)
    box(334,y,284,43,SOFT if i in (1,2,3) else WHITE,LINE,9)
    if i in (1,2,3): line(336,y+10,336,y+33,GREEN,2)
    text(f'{i+1:02d}',40,y+8,22,9,MUTED,True)
    text(lh,65,y+6,239,11,bold=True)
    text(lb,65,y+23,239,10,MUTED,maxh=13)
    text(rh,346,y+6,262,11,GREEN if i in (1,2,3) else INK,True)
    text(rb,346,y+23,262,10,MUTED,maxh=13)
    if i<4:
        arrow(172,y+44,172,y+51,MUTED); arrow(476,y+44,476,y+51)
label('Stays',30,521,65)
text('Channels, PMS, people’s authority',84,519,234,10)
label('Reduced',334,521,65)
text('Reading, copying, and chasing',398,519,220,10)
label('Added',30,541,65,GREEN)
text('Connectors, workflow, AI, fixed rules, database, and follow-up checks',84,539,534,10)
line(30,563,618,563)
heading('What this helps your team do',30,573,258,13)
text('Repeat less preparation. Decide sooner.<br/>Avoid duplicate actions. See who owns each step.',303,572,315,11,GREEN)
c.showPage()

# PAGE 2: All lifecycle stages; separate branch rail and explicit decision gate.
page(2,'END-TO-END WORKFLOW','From report to <font color="'+ORANGE+'">verified completion</font>','One connected process, with questions, approvals, progress, and closure kept on the same record.')
box(30,132,409,468,WHITE,r=14)
line(52,152,52,574)
stages = [
 (140,52,'Receive and connect','Keep the report and attachments; acknowledge receipt. Verify identity; link replies, duplicates, and incidents.'),
 (196,65,'Interpret and check','<b>AI:</b> urgency, trade, language, access, and pets.'),
 (265,51,'Clarify and reassess','Ask approved questions for missing symptoms or details. Keep known facts; reassess replies and worsening issues.'),
 (320,49,'Prepare the work','Draft PMS notes and vendor instructions. Check trade, coverage, hours, and compliance.'),
 (373,59,'Obtain the human decision','Review the original, context, and rule reason. Hold, edit, reclassify, assign, choose a vendor, or seek owner approval.'),
 (436,49,'Execute the approved action','Claim once; update the PMS and contact the vendor. Tell the resident only what the send result confirms.'),
 (489,51,'Coordinate progress','Track acceptance, quotes, confirmed times, and delays. Answer status questions without opening new requests.'),
 (544,49,'Verify and close','Staff review completion evidence and close the PMS work order. Send the approved final update.'),
]
for i,(y,h,head,body) in enumerate(stages):
    if i==4: box(36,y-3,397,h+5,'#FCF0E9',r=9)
    dot(i+1,41,y+2,PAPER,ORANGE if i==4 else INK)
    heading(head,76,y,350,13,ORANGE if i==4 else INK)
    text(body,76,y+18,348,11,maxh=42)
    if i==1:
        box(76,y+36,346,26,SOFT,r=5)
        text('<b>Fixed rules:</b> apply policy; only raise urgency.',83,y+42,333,10,GREEN,maxh=13)
    if i<7 and i!=4: line(76,y+h,426,y+h)
box(455,132,163,468,INK,r=14)
label('Routes that matter',469,144,135,'#D6CFC5')
heading('Safety first',469,167,135,13,'#EEAA8D')
text('Alert the on-call role under policy. Do not wait for clarification.',469,191,135,11,'#F0EBE4')
line(449,219,449,176,ORANGE); arrow(449,176,458,176,ORANGE)
line(439,219,449,219,ORANGE)
heading('Clarification loop',469,263,135,13,'#B8D8C5')
text('Reply received → reassess at step 2. No symptom yet? Ask before preparing vendor work.',469,287,135,10,'#F0EBE4')
line(439,293,451,293,GREEN); line(451,293,451,240,GREEN); arrow(451,240,439,240)
heading('Owner approval',469,366,135,13,'#EEAA8D')
text('Spend approval returns to step 5. Vendor contact waits for approval.',469,390,135,10,'#F0EBE4')
arrow(439,383,457,383,ORANGE); line(457,383,457,426,ORANGE); arrow(457,426,439,426,ORANGE)
line(469,452,604,452,'#514B44')
heading('Human ownership',469,465,135,13,WHITE)
arrow(439,475,457,475,MUTED)
text('Unclear, sensitive, unreadable, or failed cases go to named staff. Use approved languages; identity or vendor gaps do not become guesses.',469,489,135,10,'#F0EBE4')
c.showPage()

# PAGE 3: A spoke map with numbered, directional exchanges and matching route key.
page(3,'TOOLS & CONNECTIONS','How your <font color="'+ORANGE+'">systems connect</font>','Proposed stack and routes. Access depends on the client’s accounts and permissions.')
def node(x,y,w,h,name,copy,fill=WHITE):
    box(x,y,w,h,fill,LINE,10)
    heading(name,x+10,y+9,w-20,13)
    text(copy,x+10,y+28,w-20,10,MUTED,maxh=h-33)

node(30,132,180,67,'Resident channels','Portal / email / SMS / phone transcripts')
node(436,132,182,67,'OpenAI API','HTTPS API: interpretation and drafts. No action authority.')
shell(242,218,164,171,SOFT)
box(247,223,154,49,INK,r=11)
box(247,251,154,21,INK,r=0)
label('Approved / client cloud',253,230,142,'#D6CFC5')
heading('n8n workflow',253,249,141,15,WHITE)
text('Connectors • fixed rules<br/>Queue and retries',253,284,141,10)
line(253,318,394,318,'#BED1C1')
heading('PostgreSQL',253,329,141,13)
text('Processing state,<br/>audit and send checks',253,350,141,10)
node(30,256,163,74,'[Client PMS]','Business record: residents, units, open work, final status')
node(455,256,163,74,'[Manager channel]','Decisions and verified staff approvals')
node(30,377,180,64,'[Vendor channel]','Approved jobs, replies, and delivery results')
node(438,377,180,64,'[Owner process]','Spending approval and recorded decisions')
# Intake has distinct incoming report and outgoing resident communication paths.
line(210,152,294,152,GREEN); arrow(294,152,294,218)
text('1 · reports',232,134,110,10,GREEN)
line(274,218,274,181,GREEN); arrow(274,181,210,181)
text('questions<br/>+ updates',218,186,53,10,GREEN)
# AI has no connection to any business endpoint.
line(374,218,374,151,GREEN); arrow(374,151,436,151)
text('context',379,135,58,10,GREEN)
line(436,181,393,181,GREEN); arrow(393,181,393,218)
text('drafts',402,194,46,10,GREEN)
arrow(193,279,242,279); text('2 · data',196,263,48,10,GREEN)
arrow(242,314,193,314); text('updates',196,299,46,10,GREEN)
arrow(406,279,455,279); text('3 · ask',412,263,42,10,GREEN)
arrow(455,314,406,314); text('approve',408,299,46,10,GREEN)
line(258,389,258,400,GREEN); arrow(258,400,210,400)
text('4 · job',218,381,48,10,GREEN)
line(210,426,281,426,GREEN); arrow(281,426,281,389)
text('reply',236,429,44,10,GREEN)
line(390,389,390,400,GREEN); arrow(390,400,438,400)
text('5 · ask',391,381,45,10,GREEN)
line(438,426,368,426,GREEN); arrow(368,426,368,389)
text('decision',380,429,55,10,GREEN)
arrow(324,389,324,445)
box(245,446,159,28,WHITE,LINE,8)
text('6 · [Reporting tool]',258,452,140,11,bold=True)
text('events',330,427,44,10,GREEN)
label('Connection methods / confirm for each prospect',30,483,588,ORANGE)
routes=[
 ('1','[API / webhook / secure mailbox]'),
 ('2','[API / partner / export-import route]'),
 ('3','[App integration / secure review link]'),
 ('4','[PMS vendor route / portal / email service]'),
 ('5','[Existing owner approval process]'),
 ('6','[Reporting connection]'),
]
for i,(num,route) in enumerate(routes):
    x=30 if i<3 else 334; y=501+(i%3)*20
    text(num,x,y,18,10,GREEN,True); text(route,x+19,y,265,10)
line(30,563,618,563)
text('<b>Confirm:</b> [Products], [permissions], [hosting / AI data policy]. If PMS writes are blocked, use [staff task / approved import]. Manager approvals must be authenticated; every route returns confirmed state where supported.',30,574,588,10,MUTED,maxh=30)
c.showPage()

# PAGE 4: Running the service, not repeating the lifecycle.
page(4,'OPERATIONS & OUTCOMES','How your team <font color="'+ORANGE+'">runs it each day</font>','Staff work in familiar tools. Each waiting item or failed action has an owner and a next step.')
heading('Daily operating view',30,137,275,14)
ops=[
 ('Start with priority, not inbox order','See urgent work, overdue items, owner approvals, vendor delays, and unowned exceptions.'),
 ('Alert according to company policy','Check unanswered emergencies. Apply on-call and quiet-hour rules; age alone never creates an emergency.'),
 ('Keep the portfolio visible','Daily summaries and existing reports show volume, waiting work, response targets, and exceptions.'),
]
for i,(head,body) in enumerate(ops):
    y=166+i*78
    heading(head,30,y,278,13)
    text(body,30,y+25,278,11,maxh=42)
    if i<2: line(30,y+73,307,y+73)
shell(328,132,290,272,INK)
label('Authority stays with people',344,146,257,'#EEAA8D')
text('Staff control vendor selection, dispatch, spend, emergency downgrades, appointments, credits, and closure.',344,167,255,11,WHITE)
line(344,218,602,218,'#514B44')
heading('Review the cases that need judgment',344,232,255,13,WHITE)
text('Legal or accommodation cases need trained staff. Unverified identity: reveal no records; route to staff.',344,267,255,11,'#E9E3DB')
heading('Keep every action accountable',344,322,255,13,WHITE)
text('Reject stale or duplicate approvals. Preserve the actor, decision, and send result. Resident updates follow confirmed facts.',344,345,255,11,'#E9E3DB')
heading('Recovery is part of the build',30,418,588,14)
text('<b>Visible failures.</b> AI failure keeps the report and safety checks. PMS or send failures retry, then go to staff. Data conflicts trigger review, not a silent overwrite.',30,442,282,11,maxh=69)
text('<b>Service controls.</b> Roles, MFA, encryption, secrets, and retention. Monitor intake and the full path; test backup restores, rule changes, and rollback. No self-training.',335,442,283,11,maxh=69)
line(30,513,618,513)
text('<b>Questions + linked history</b> → less chasing.<br/><b>Policy-led alerts</b> → fewer needless interruptions.',30,524,285,10,GREEN)
text('<b>Tracked sends + facts</b> → clearer handoffs and updates.<br/><b>Shared event history</b> → better portfolio visibility.',334,524,284,10,GREEN)
shell(30,563,588,43,INK)
heading('Discuss your tools and workflow.',44,573,386,15,WHITE)
text('Sambhav Jain / sambhav@sambhavbuilds.com',44,591,371,8.5,'#D6CFC5')
box(451,570,154,29,ORANGE,r=14.5)
text('Discuss the fit',465,578,112,10,WHITE,True)
box(578,575,19,19,'#A63E1D',r=9.5); arrow(583,584,592,584,WHITE)
c.linkURL('https://cal.com/sambhav-builds/pm-automation-audit',(451,H-599,605,H-570),relative=0)
c.showPage()
c.save()
print(OUT)
