// Public prose comes from Markdown; diagram labels explain the same build.
const fs = require('fs'), path = require('path');
const root = path.resolve(__dirname, '../..'), kit = path.join(root, 'carousel-kit');
const source = fs.readFileSync(path.join(root, 'docs/build-2-content-strategy/technical-retrospective-carousel.md'), 'utf8').replaceAll('\r\n', '\n');
const esc = s => s.replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;');
const paths = {
  circle: '<svg viewBox="0 0 300 100" preserveAspectRatio="none"><path d="M23,52 C20,20 88,6 160,7 C238,8 286,25 283,53 C280,81 210,95 138,94 C66,93 20,79 17,49 C15,32 32,19 58,11"/><path d="M43,13 C115,1 215,11 269,31 C293,40 296,59 273,73" opacity=".65"/></svg>',
  under: '<svg viewBox="0 0 300 20" preserveAspectRatio="none"><path d="M4,12 C62,3 148,4 214,9 C250,12 274,12 296,7"/><path d="M12,18 C72,10 150,11 222,15" opacity=".55"/></svg>',
  strike: '<svg viewBox="0 0 300 12" preserveAspectRatio="none"><path d="M2,7 C74,3 168,10 298,4"/></svg>',
};

function a(text, type, color = 'blue') {
  const s = esc(text);
  if (type === 'hl') return `<span class="hl${color === 'blue' ? ' hl--blue' : ''}">${s}</span>`;
  if (type === 'sel') return `<span class="sel${color === 'gold' ? ' sel--gold' : ''}">${s}<i></i><i></i><i></i><i></i></span>`;
  return `<span class="pen pen--${type} pen--${color}">${s}${paths[type]}</span>`;
}

const chain = (nodes) => `<div class="v-chain v-chain--${nodes.length}">${nodes.map((n, i) => `${i ? '<div class="v-arrow">→</div>' : ''}<div class="v-node">${n}</div>`).join('')}</div>`;
const lane = (label, content) => `<div class="v-lane"><div class="v-label">${label}</div>${content}</div>`;
const table = (headers, rows, cls = '') => `<table class="v-table ${cls}"><thead><tr>${headers.map(x => `<th>${x}</th>`).join('')}</tr></thead><tbody>${rows.map(row => `<tr>${row.map(x => `<td>${x}</td>`).join('')}</tr>`).join('')}</tbody></table>`;
const steps = (rows) => `<ol class="v-steps">${rows.map((r, i) => `<li><b>${String(i + 1).padStart(2, '0')}</b><h3>${r[0]}</h3><p>${r[1]}</p></li>`).join('')}</ol>`;

const diagrams = {
  2: steps([
    ['Squeaky hinge', 'Marked urgent by the tenant, but needs a routine handyman.'],
    [a('Hidden gas leak', 'hl', 'gold'), 'Polite and understated note, but needs an immediate contractor.']
  ]),
  3: lane('Before manager review', chain(['Incoming request', 'Clarify details', a('Assess urgency', 'hl', 'gold')])) +
     lane('After manager review', chain(['Manager decides', 'Vendor notified', 'Tenant updated'])) +
     '<div class="v-rail">Advisory only: the workflow never dispatches a vendor without human approval.</div>',
  4: `<div class="v-columns"><div class="v-column"><h3>AI assists</h3><p>Extract symptoms</p><p>Identify trade</p><p>Draft dispatch</p></div><div class="v-column"><h3>Manager decides</h3><p>Verify diagnosis</p><p>Select contractor</p><p>${a('Approve each dispatch', 'sel', 'blue')}</p></div></div>`,
  5: steps([
    ['Hazard detection', 'Gas odors, spreading water, or sparking electrical signals.'],
    [a('Forced escalation', 'hl', 'blue'), 'Safety rules immediately override priority to emergency.'],
    ['No down-ranking', 'Software is never permitted to dismiss a danger signal.']
  ]),
  6: lane('The gap', chain(['Vendor dispatch', 'Shared inbox', a('Duplicate ticket', 'strike', 'gold')])) +
     `<p class="v-gap">${a('Outbound dispatch re-entered intake', 'under', 'gold')}</p>` +
     lane('The fix', chain(['Vendor dispatch', a('System tag', 'sel', 'blue'), 'Filtered out'])) +
     '<p class="v-quiet">Intake triggers ignore all outgoing system emails.</p>',
  7: lane('The bug', chain(['"Any update?"', 'Triage engine', a('New ticket opened', 'strike', 'blue')])) +
     lane('The fix', chain(['"Any update?"', 'Check open repairs', a('Factual status reply', 'hl', 'gold')])) +
     '<p class="v-quiet">Status queries are answered directly without disturbing the manager.</p>',
  8: table(
    ['What comes in', 'What happens'],
    [
      ['Disability accommodation', 'Direct human review'],
      ['Legal or lease question', a('Route to staff', 'hl', 'gold')],
      ['Unclear symptom', 'Ask tenant clarification'],
      ['AI timeout or failure', a('Flag for attention', 'under', 'blue')]
    ],
    'v-results'
  ),
  9: `<div class="v-route"><p>The rambling message</p><p class="v-route-arrow">↓</p><p>The hidden ${a('hazard', 'circle', 'gold')}</p><p class="v-route-arrow">↓</p><p>The ${a('second click', 'under', 'blue')}</p><p class="v-route-arrow">↓</p><p>The email feedback loop</p></div>`,
  10: table(
    ['I checked', 'Recorded behavior'],
    [
      ['Understated gas odor', a('Escalated to emergency', 'hl', 'gold')],
      ['Squeaky door marked urgent', 'Kept as routine'],
      ['Approve tapped twice', a('No second email sent', 'under', 'blue')],
      ['Follow-up status query', a('Answered without a ticket', 'hl', 'blue')]
    ],
    'v-results'
  ),
  11: steps([
    ['Structured photo collection', 'Ask tenants for photos before dispatching expensive trades.'],
    ['Contractor ETA tracking', 'Track vendor confirmations and arrival windows automatically.'],
    [a('Property system sync', 'hl', 'gold'), 'Sync work order status and invoices directly with accounting.']
  ]),
};

const titleMarks = {
  1: [],
  2: ['themselves', 'under', 'blue'],
  4: ['authorizes', 'hl', 'gold'],
  5: ['down-rank', 'under', 'gold'],
  6: ['itself', 'circle', 'gold'],
  7: ['new repair', 'hl', 'blue'],
  8: ['person', 'sel', 'blue'],
  9: ['build', 'hl', 'gold'],
  11: ['next', 'circle', 'blue']
};

const slides = [...source.matchAll(/### Slide (\d+)\n\n\*\*Title:\*\* ([^\n]+)\n\n\*\*Body:\*\* ([^\n]+)\n\n\*\*Footer:\*\* ([^\n]+)/g)];
if (slides.length !== 11) throw Error(`Expected eleven slide fields, found ${slides.length}`);

const shells = slides.map(m => {
  const n = +m[1], title = m[2], body = m[3], footer = m[4];
  let h = esc(title);
  if (titleMarks[n]?.length) {
    const [word, type, color] = titleMarks[n];
    if (!h.includes(word)) throw Error(`Missing title mark for word "${word}" in slide ${n}`);
    h = h.replace(word, a(word, type, color));
  }
  let content;
  if (n === 1) {
    h = 'Maintenance<br>triage that<br>puts safety<br><span class="pay pen pen--under pen--gold">first' + paths.under + '</span>';
    content = `<h1 class="display v-cover">${h}</h1><p class="tech-copy">${esc(body)}</p>`;
  } else {
    const heading = `<h2 class="tech-title">${h}</h2>`,
          copy = `<p class="tech-copy">${esc(body)}</p>`,
          visual = `<div class="v-visual">${diagrams[n]}</div>`;
    content = heading + visual + copy;
  }
  return `<section class="slide technical technical--visual${n === 9 ? ' slide--invert' : ''}" data-slide="${n}"><div class="eyebrow"><span>BUILD NOTES · MAINTENANCE TRIAGE</span></div><div class="body">${content}</div><div class="footer"><span>${esc(footer)}</span><b>${String(n).padStart(2, '0')}</b></div></section>`;
});

const snapScript = `<script>
(function () {
  var UNIT = 24, PHASE = 71.5;
  document.querySelectorAll('.slide').forEach(function (slide) {
    var body = slide.querySelector('.body');
    if (!body) { return; }
    var host = body.querySelector('.display, .lead, .head, .group, .lead-in, .claim, .fig, .close-lead, .pay, .checks li');
    if (!host) { host = body.firstElementChild; }
    if (!host) { return; }
    var probe = document.createElement('span');
    probe.style.cssText = 'display:inline-block;width:0;height:0;overflow:hidden';
    host.insertBefore(probe, host.firstChild);
    var baseline = probe.getBoundingClientRect().bottom - slide.getBoundingClientRect().top;
    probe.remove();
    var delta = Math.round((baseline - PHASE) / UNIT) * UNIT + PHASE - baseline;
    body.style.transform = 'translateY(' + delta.toFixed(2) + 'px)';
  });
})();
</script>`;

const html = `<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Maintenance triage that puts safety first</title><link rel="preconnect" href="https://api.fontshare.com"><link rel="preconnect" href="https://cdn.fontshare.com" crossorigin><link href="https://api.fontshare.com/v2/css?f[]=switzer@400,500,600,700,800,900&display=swap" rel="stylesheet"><link href="https://api.fontshare.com/v2/css?f[]=zodiak@700,701,800,801&display=swap" rel="stylesheet"><link href="carousel-template.css" rel="stylesheet"></head><body>${shells.join('\n')}${snapScript}</body></html>`;

const out = path.join(kit, 'technical-retrospective-maintenance-triage.html');
fs.writeFileSync(out, html);
console.log('Generated:', out);
