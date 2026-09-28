"""Structural checks complement (do not replace) rendered visual inspection."""
from pathlib import Path
from pypdf import PdfReader
import pdfplumber

ROOT = Path(__file__).resolve().parents[2]
pdf = ROOT / 'output/pdf/maintenance-triage-square-brief.pdf'
reader = PdfReader(pdf)
assert len(reader.pages) == 4
expected = [
    ['Assumed current process', 'Focused follow-up questions', 'What this helps', 'Added'],
    ['Receive and connect', 'Fixed rules', 'Clarify and reassess', 'Prepare the work',
     'Obtain the human decision', 'Execute the approved action', 'Coordinate progress',
     'Verify and close', 'Do not wait', 'Owner approval', 'without a new request',
     'Who handles what', 'Workflow', 'Manager', 'Staff'],
    ['n8n', 'PostgreSQL', 'OpenAI API', 'Reporting tool', 'secure mailbox', 'partner',
     'secure review link', 'Added / proposed system', 'Routes to confirm with the client'],
    ['unanswered emergencies', 'age alone never', 'stale or duplicate', 'rollback', 'backup restores', 'Discuss the fit'],
]
used_fonts = set()
for i, page in enumerate(reader.pages):
    assert tuple(float(v) for v in page.mediabox) == (0, 0, 648, 648)
    content = ' '.join(page.extract_text().split())
    for term in expected[i]: assert term.lower() in content.lower(), (i+1, term)
    def check_font(txt, cm, tm, font, size):
        if not txt.strip(): return
        assert font is not None
        desc = font['/FontDescriptor'].get_object()
        assert '/FontFile2' in desc or '/FontFile3' in desc
        used_fonts.add(str(font['/BaseFont']))
    page.extract_text(visitor_text=check_font)
links = [a.get_object()['/A'].get('/URI') for p in reader.pages for a in p.get('/Annots', []) if '/A' in a.get_object()]
assert 'https://cal.com/sambhav-builds/pm-automation-audit' in links
with pdfplumber.open(pdf) as doc:
    for i,p in enumerate(doc.pages):
        for char in p.chars:
            assert 28 <= char['x0'] <= char['x1'] <= 620, (i+1, char)
            assert 12 <= char['top'] <= char['bottom'] <= 636, (i+1, char)
archive = ROOT / 'output/pdf/archive/square-20260928-redesign'
assert (archive/'maintenance-triage-square-brief-before.pdf').is_file()
assert (archive/'build-square-brief-before.py').is_file()
print('PASS: 4 square pages; all used fonts embedded; CTA; text bounds; capability terms; archive.')
print('Embedded faces:', ', '.join(sorted(used_fonts)))
