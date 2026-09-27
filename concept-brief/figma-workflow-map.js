// Editable Figma Design authoring source. Execute with the Figma use_figma tool.
// Four landscape pages, with live text and auto-layout content.
const ids = [];
const C = {paper:'#F4F1EA',white:'#FFFFFF',ink:'#202923',muted:'#586159',line:'#D6DBD4',forest:'#285747',pale:'#E5EDE6',amber:'#905C1E',sand:'#F4E8D4',red:'#A43C32',rose:'#F8E7E2',brand:'#C2542D'};
const rgb=h=>({r:parseInt(h.slice(1,3),16)/255,g:parseInt(h.slice(3,5),16)/255,b:parseInt(h.slice(5,7),16)/255});
const paint=h=>[{type:'SOLID',color:rgb(h)}];
await Promise.all([figma.loadFontAsync({family:'Geist',style:'Regular'}),figma.loadFontAsync({family:'Geist',style:'SemiBold'}),figma.loadFontAsync({family:'Manrope',style:'Regular'})]);
function track(n){ids.push(n.id);return n;}
function box(parent,name,x,y,w,h,fill=C.white,stroke=null){const n=track(figma.createAutoLayout('VERTICAL'));n.name=name;n.resize(w,h);n.primaryAxisSizingMode='FIXED';n.counterAxisSizingMode='FIXED';n.itemSpacing=7;n.paddingTop=n.paddingBottom=16;n.paddingLeft=n.paddingRight=18;n.fills=paint(fill);n.cornerRadius=10;if(stroke){n.strokes=paint(stroke);n.strokeWeight=1;}parent.appendChild(n);n.x=x;n.y=y;return n;}
function txt(parent,s,size=18,color=C.ink,bold=false,w=null){const n=track(figma.createText());n.fontName={family:bold?'Geist':'Manrope',style:bold?'SemiBold':'Regular'};n.fontSize=size;n.lineHeight={unit:'PERCENT',value:132};n.fills=paint(color);n.characters=s;n.textAutoResize='HEIGHT';parent.appendChild(n);n.resize(w||parent.width-parent.paddingLeft-parent.paddingRight,Math.max(1,n.height));return n;}
function label(parent,s,color=C.forest){return txt(parent,s,12,color,true);}
function loose(parent,name,x,y,w,s,size=18,color=C.ink,bold=false){const b=box(parent,name,x,y,w,10,C.paper);b.fills=[];b.paddingLeft=b.paddingRight=b.paddingTop=b.paddingBottom=0;b.primaryAxisSizingMode='AUTO';txt(b,s,size,color,bold,w);return b;}
function line(parent,x1,y1,x2,y2,color=C.line,dashed=false,arrow=false){const n=track(figma.createVector());parent.appendChild(n);n.name=arrow?'Flow arrow':'Divider / data connection';n.vectorPaths=[{windingRule:'NONZERO',data:`M ${x1} ${y1} L ${x2} ${y2}`}];n.strokes=paint(color);n.strokeWeight=1.6;n.fills=[];if(dashed)n.dashPattern=[5,5];if(arrow){const dx=x2-x1,dy=y2-y1,a=Math.atan2(dy,dx),l=6;const v=track(figma.createVector());parent.appendChild(v);v.name='Arrowhead';v.vectorPaths=[{windingRule:'NONZERO',data:`M ${x2-l*Math.cos(a-.5)} ${y2-l*Math.sin(a-.5)} L ${x2} ${y2} L ${x2-l*Math.cos(a+.5)} ${y2-l*Math.sin(a+.5)}`}];v.strokes=paint(color);v.strokeWeight=1.6;v.fills=[];}return n;}
function page(i,title,sub){let right=0;for(const c of figma.currentPage.children)right=Math.max(right,c.x+c.width);const p=track(figma.createFrame());p.name=`0${i} / ${title}`;p.resize(1120,792);p.fills=paint(C.paper);figma.currentPage.appendChild(p);p.x=right+100;p.y=100;p.placeholder=true;loose(p,'Brand',44,28,460,'SAMBHAV JAIN  /  MAINTENANCE OPERATIONS',12,C.muted,true);loose(p,'Document type',758,28,318,'PROPOSED PRODUCTION WORKFLOW',12,C.muted,true);line(p,44,56,1076,56);loose(p,'Title',44,81,1032,title,38,C.ink,true);loose(p,'Subtitle',44,141,1032,sub,18,C.muted);line(p,44,744,1076,744);loose(p,'Footer',44,758,910,'Sambhav Builds  |  Process & integration brief  |  September 2026',12,C.muted);loose(p,'Page number',1027,757,49,`${i} / 4`,12,C.muted,true);return p;}
function card(p,name,x,y,w,h,kicker,title,body,fill=C.white,color=C.forest){const b=box(p,name,x,y,w,h,fill);if(kicker)label(b,kicker,color);txt(b,title,22,C.ink,true);if(body)txt(b,body,17,C.muted);return b;}

// PAGE 1: Business result and honest, prospect-specific measurement.
const p1=page(1,'A clearer path from report to repair.','Maintenance requests arrive ready for a human decision, with every handoff recorded.');
const intro=box(p1,'Core promise',44,192,1032,112,C.forest);intro.paddingLeft=intro.paddingRight=24;
txt(intro,'Your team decides. The system prepares.',30,C.white,true);
txt(intro,'Read incoming reports, collect missing details, surface risk and prepare the next action inside the tools your business already uses.',19,'#E2ECE5');
const a=card(p1,'Before',44,328,316,118,'TODAY','Messages to work through','Read, look up, rekey and chase details.',C.white,C.muted);
const b=card(p1,'Preparation',402,328,316,118,'AUTOMATED PREPARATION','One prepared request','Summary, priority, context and vendor options.',C.pale);
const c=card(p1,'Decision',760,328,316,118,'HUMAN CONTROL','An informed next action','Review, hold, approve or assign manually.',C.sand,C.amber);
line(p1,367,387,393,387,C.forest,false,true);line(p1,725,387,751,387,C.forest,false,true);
const outcomes=[['Less intake admin','Reduce repetitive reading, copying and first-response preparation.'],['Earlier risk awareness','Route safety signals to the on-call role under your policy.'],['Fewer loose ends','Keep an owner, next action and visible waiting state on each request.'],['Clearer resident updates','Report confirmed progress and keep follow-ups on the same request.']];
outcomes.forEach((o,i)=>{const q=box(p1,o[0],44+i*264,470,240,129,C.paper);q.paddingLeft=q.paddingRight=0;q.paddingTop=0;txt(q,o[0],22,C.ink,true);txt(q,o[1],17,C.muted);});
const calc=box(p1,'Illustrative capacity calculation',44,622,1032,96,C.white);calc.layoutMode='HORIZONTAL';calc.itemSpacing=24;
const num=box(calc,'Illustrative hours',0,0,212,62,C.white);num.paddingTop=num.paddingBottom=num.paddingLeft=num.paddingRight=0;txt(num,'50 hours / month',25,C.forest,true);label(num,'ILLUSTRATION ONLY',C.muted);
const math=box(calc,'Assumptions',0,0,754,64,C.white);math.paddingTop=math.paddingBottom=math.paddingLeft=math.paddingRight=0;txt(math,'1,000 requests × 3 minutes of intake work saved ÷ 60 = 50 hours.',18,C.ink,true);txt(math,'Use your own volume and measured pilot savings. This is capacity arithmetic, not a client result or a guarantee of faster repairs.',16,C.muted);
p1.placeholder=false;

// PAGE 2: Main path, decisions, clarification loop and exceptions.
const p2=page(2,'Follow one maintenance request.','Proposed production flow. Connected channels and permitted actions are agreed during setup.');
const steps=[
 ['01  RECEIVE & CONNECT','Preserve the report; verify resident and unit. Link duplicates and replies to the existing request.',C.white],
 ['02  INTERPRET & APPLY POLICY','AI suggests summary, trade and urgency. Separate fixed rules enforce safety and review boundaries.',C.pale],
 ['03  COMPLETE THE REQUEST','Ask approved questions for missing details. Reassess replies; prepare notes and eligible vendor options.',C.pale],
 ['04  HUMAN APPROVAL','Manager reviews, edits, holds or selects a vendor. Obtain owner approval when authority requires it.',C.sand],
 ['05  CONTACT & CONFIRM','Claim the approved action once. Send through the vendor channel; record the confirmed send result.',C.pale],
 ['06  TRACK, VERIFY & CLOSE','Record vendor responses and confirmed appointments. Staff verify completion and close in the PMS.',C.white]
];
steps.forEach((s,i)=>{const y=190+i*88;const q=box(p2,s[0],44,y,580,76,s[2]);q.paddingTop=q.paddingBottom=10;q.itemSpacing=4;label(q,s[0],i===3?C.amber:C.forest);txt(q,s[1],16,C.ink);if(i<5)line(p2,334,y+77,334,y+86,C.forest,false,true);});
const notes=[
 ['FOLLOW-UP OR STATUS?','Use the existing record. Answer with known facts; no duplicate ticket or invented ETA.',C.white,C.muted],
 ['SAFETY OR SENSITIVE CASE?','Safety: alert the on-call role without waiting for details. Sensitive or unusable output: trained staff review.',C.rose,C.red],
 ['DETAILS STILL MISSING?','Ask resident → attach reply → reassess step 02. Hold vendor approval until ready or handled by a person.',C.sand,C.amber],
 ['HOLD / NO VENDOR / OWNER PENDING','Keep a visible task with the coordinator or property manager. No unapproved vendor contact.',C.sand,C.amber],
 ['SEND FAILED?','Retry under policy; coordinator owns the exception. Tell the resident “contacted” only after send succeeds.',C.rose,C.red],
 ['MONITOR UNTIL RESOLVED','Track owner, vendor and resident delays. Age flags overdue work; it never creates an emergency by itself.',C.white,C.muted]
];
notes.forEach((n,i)=>{const y=190+i*88;line(p2,625,y+38,652,y+38,n[3],i===0,false);const q=box(p2,n[0],662,y,414,76,n[2]);q.paddingTop=q.paddingBottom=9;q.itemSpacing=3;label(q,n[0],n[3]);txt(q,n[1],15,C.ink);});
p2.placeholder=false;

// PAGE 3: Real systems, interfaces, data direction and source of truth.
const p3=page(3,'How it connects to your business.','Your property management system (PMS) stays the business record. Connections depend on available access.');
loose(p3,'Column 1 label',44,190,286,'YOUR EXISTING CHANNELS',12,C.muted,true);
loose(p3,'Column 2 label',417,190,286,'ADDED AUTOMATION SERVICE',12,C.forest,true);
loose(p3,'Column 3 label',790,190,286,'YOUR EXISTING WORKSPACE',12,C.muted,true);
card(p3,'Intake channels',44,221,286,151,'INBOUND','Portal · email · text','Approved events or mailbox access carry reports and replies. Voice enters as a transcript from your call provider.');
card(p3,'People channels',44,421,286,166,'TWO-WAY MESSAGING','Residents & vendors','Existing email, text or vendor portal carries approved messages, replies and delivery results.');
const engine=box(p3,'Added automation',417,221,286,366,C.forest);label(engine,'CLIENT-OWNED DEPLOYMENT','#CCDCD0');txt(engine,'n8n',30,C.white,true);txt(engine,'Routes events, applies policy and coordinates approvals.',17,'#E2ECE5');txt(engine,'OpenAI API',23,C.white,true);txt(engine,'Interprets the request and prepares drafts. Fixed safety rules run separately.',17,'#E2ECE5');txt(engine,'PostgreSQL',23,C.white,true);txt(engine,'Stores processing history, conversation state, approvals and retry records.',17,'#E2ECE5');
card(p3,'PMS integration',790,221,286,173,'READ + WRITE WHERE PERMITTED','Your PMS','Read resident, unit and vendor context. Write approved work orders, notes and confirmed status. Preserve staff edits.');
card(p3,'Approval channel',790,421,286,166,'HUMAN DECISIONS','Manager & owner tools','Use an approved mobile, Teams, Slack or PMS channel. Route vendor choices and spend approvals to authorized people.');
line(p3,336,282,408,282,C.forest,false,true);loose(p3,'Inbound connector label',341,295,67,'events /\nmail',12,C.muted);
line(p3,408,493,336,493,C.forest,false,true);loose(p3,'Message connector label',338,504,75,'messages\n+ receipts',12,C.muted);
line(p3,711,282,781,282,C.forest,true,true);line(p3,781,294,711,294,C.forest,true,true);loose(p3,'PMS connector label',718,305,66,'API /\nsync',12,C.muted);
line(p3,711,483,781,483,C.amber,false,true);line(p3,781,495,711,495,C.amber,false,true);loose(p3,'Approval connector label',713,506,72,'review /\ndecision',12,C.muted);
const fallback=box(p3,'Limited access alternative',44,610,659,111,C.white);label(fallback,'IF PMS WRITE ACCESS IS LIMITED',C.muted);txt(fallback,'Start with a roster sync and prepared tasks or emails. Staff create the work order; add controlled write-back only after access is confirmed.',17,C.ink);
const infra=box(p3,'Production controls',727,610,349,111,C.pale);label(infra,'BEHIND THE SERVICE');txt(infra,'Queue + retries · monitoring · encrypted backups · access controls · agreed retention.',16,C.ink);txt(infra,'Solid: action flow  /  Dashed: data sync',12,C.muted);
p3.placeholder=false;

// PAGE 4: Practical integration responsibilities, rollout gates and proof limits.
const p4=page(4,'Start small. Expand on evidence.','A staged implementation keeps your current process available while the new workflow earns trust.');
const phases=[
 ['1  MAP & CONFIGURE','Confirm tools, permissions, resident identity, vendor coverage, spending limits and on-call rules.'],
 ['2  RUN IN SHADOW','Read a copy of requests. Compare recommendations with staff decisions; send no resident or vendor messages.'],
 ['3  ASSIST INTAKE','Enable approved receipt and clarification messages. Prepare records; staff retain control of material actions.'],
 ['4  ENABLE APPROVALS','Pilot selected properties and trades. Test duplicate clicks, failed sends, owner approval and manual recovery.'],
 ['5  EXPAND & HAND OVER','Roll out only after agreed gates pass. Train staff, document support ownership and rehearse rollback.']
];
phases.forEach((s,i)=>{const q=box(p4,s[0],44,192+i*82,604,72,i===1?C.pale:C.white);q.paddingTop=q.paddingBottom=9;q.itemSpacing=3;label(q,s[0]);txt(q,s[1],16,C.ink);if(i<4)line(p4,346,265+i*82,346,272+i*82,C.forest,false,true);});
const provide=box(p4,'Client responsibilities',674,192,402,115,C.sand);label(provide,'YOUR TEAM PROVIDES',C.amber);txt(provide,'A process owner, approved system access, tenant/vendor rosters, response rules and reviewers for pilot decisions.',17,C.ink);
const deliver=box(p4,'Implementation responsibilities',674,323,402,115,C.pale);label(deliver,'IMPLEMENTATION DELIVERS');txt(deliver,'Configured connectors and workflows, safety tests, monitoring, recovery runbooks, staff training and handover.',17,C.ink);
const gates=box(p4,'Pilot success measures',674,454,402,139,C.white);label(gates,'AGREE THE LAUNCH GATES');txt(gates,'Measure intake minutes, decision time, missed and unnecessary escalations, repeat contacts and exception age.',17,C.ink);txt(gates,'Pause expansion if safety or recovery checks fail.',15,C.amber,true);
const proof=box(p4,'Scope and evidence',44,616,604,105,C.paper);proof.paddingLeft=proof.paddingRight=0;proof.paddingTop=0;label(proof,'DEMO TODAY → CLIENT PRODUCTION',C.muted);txt(proof,'The demo shows email/form/Telegram triage, Airtable visibility and human-approved vendor email on synthetic data. PMS integration, verified identity and production controls require implementation. Broader safety testing remains a launch gate.',15,C.muted);
const cta=box(p4,'Contact and next step',674,616,402,105,C.forest);label(cta,'NEXT STEP','#D6E5DA');const link=txt(cta,'Map this to your actual tools →',22,C.white,true);link.hyperlink={type:'URL',value:'https://cal.com/sambhav-builds/pm-automation-audit'};txt(cta,'sambhav@sambhavbuilds.com',16,'#E2ECE5');
p4.placeholder=false;
const roots=[p1,p2,p3,p4];
// Final copy-fit adjustments, kept here so fresh-file generation matches the export.
const replacements=new Map([
 ['Read incoming reports, collect missing details, surface risk and prepare the next action inside the tools your business already uses.','Collect missing details, surface risk and prepare the next action in the tools your business already uses.'],
 ['Messages to work through','A raw inbox'],
 ['Clearer resident updates','Resident updates'],
 ['Use your own volume and measured pilot savings. This is capacity arithmetic, not a client result or a guarantee of faster repairs.','Replace these assumptions with your measured pilot results. Capacity saved does not guarantee faster repairs.'],
 ['Approved events or mailbox access carry reports and replies. Voice enters as a transcript from your call provider.','Reports and replies enter through approved events or mailbox access. Calls enter as provider transcripts.'],
 ['Queue + retries · monitoring · encrypted backups · access controls · agreed retention.','Retries, monitoring, backups, access control and retention.'],
 ['Solid: action flow  /  Dashed: data sync','Solid: actions / Dashed: data sync'],
 ['Roll out only after agreed gates pass. Train staff, document support ownership and rehearse rollback.','Expand after agreed gates pass. Train staff and document support. Disable forwarding or subscriptions to return to the existing process.'],
 ['AI suggests summary, trade and urgency. Separate fixed rules enforce safety and review boundaries.','AI suggests summary, trade and urgency. Fixed safety rules may raise urgency, never lower it; sensitive cases go to staff.']
]);
for(const p of roots)for(const n of p.findAllWithCriteria({types:['TEXT']}))if(replacements.has(n.characters))n.characters=replacements.get(n.characters);
for(const n of p1.children){if(['Before','Preparation','Decision'].includes(n.name))n.resize(316,134);}
math.resize(754,76);math.itemSpacing=4;
p3.children.find(n=>n.name==='Intake channels').resize(286,173);
for(const n of p4.children.filter(n=>n.type==='FRAME'&&/^[1-5]  /.test(n.name))){const t=n.children.filter(c=>c.type==='TEXT')[1];t.fontSize=15;t.lineHeight={unit:'PERCENT',value:125};}
line(p3,336,482,408,482,C.forest,false,true);
const overflow=[];
for(const p of roots){for(const n of p.findAllWithCriteria({types:['TEXT']})){const a=n.absoluteBoundingBox,b=n.parent.absoluteBoundingBox;if(a&&b&&(a.y+a.height>b.y+b.height+1||a.x+a.width>b.x+b.width+1))overflow.push({id:n.id,text:n.characters,parent:n.parent.id});}}
return {createdNodeIds:ids,frames:roots.map(p=>({id:p.id,name:p.name,width:p.width,height:p.height})),textOverflow:overflow};
