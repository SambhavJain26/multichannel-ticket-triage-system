"""Verify the HTML-exported PDF without modifying the earlier square brief."""
from pathlib import Path
from hashlib import sha256
from pypdf import PdfReader
import pdfplumber

ROOT = Path(__file__).resolve().parents[2]
PDF = ROOT / 'output/pdf/maintenance-triage-html-brief.pdf'
reader = PdfReader(PDF)
assert len(reader.pages) == 4
expected = [
    ['Assumed current process', 'Focused follow-up questions', 'What this helps', 'Reduced', 'Added'],
    ['Receive and connect', 'Fixed rules', 'Clarify and reassess', 'Prepare the work',
     'Obtain the human decision', 'Execute the approved action', 'Coordinate progress',
     'Verify and close', 'do not wait', 'Owner approval', 'without a new request',
     'Who handles what', 'Workflow', 'Manager', 'Staff'],
    ['n8n', 'PostgreSQL', 'OpenAI API', 'Reporting tool', 'secure mailbox', 'partner',
     'secure review link', 'Added / proposed system', 'Confirm the route'],
    ['unanswered emergencies', 'Age alone never', 'stale or duplicate', 'rollback', 'backup restores', 'Discuss the fit'],
]
fonts = set()
for i, page in enumerate(reader.pages):
    assert tuple(float(v) for v in page.mediabox) == (0, 0, 648, 648)
    content = ' '.join(page.extract_text().split())
    for term in expected[i]:
        assert term.lower() in content.lower(), (i+1, term)
    for font_ref in page['/Resources']['/Font'].values():
        font = font_ref.get_object()
        if font.get('/Subtype') == '/Type3':
            # Chromium embeds variable-font glyph programs as Type 3 CharProcs.
            assert font.get('/CharProcs') and font.get('/ToUnicode')
            assert all(proc.get_object().get_data() for proc in font['/CharProcs'].values())
            fonts.add(str(font['/FontDescriptor'].get_object()['/FontFamily']))
            continue
        for f in font.get('/DescendantFonts', [font]):
            f = f.get_object()
            descriptor = f['/FontDescriptor'].get_object()
            assert any(key in descriptor for key in ['/FontFile', '/FontFile2', '/FontFile3'])
            fonts.add(str(f['/BaseFont']))
links = [a.get_object()['/A'].get('/URI') for p in reader.pages for a in p.get('/Annots', []) if '/A' in a.get_object()]
assert 'https://cal.com/sambhav-builds/pm-automation-audit' in links
assert 'mailto:sambhav@sambhavbuilds.com' in links
with pdfplumber.open(PDF) as doc:
    for i, p in enumerate(doc.pages):
        for c in p.chars:
            assert 29 <= c['x0'] <= c['x1'] <= 619, (i+1, c)
            assert 12 <= c['top'] <= c['bottom'] <= 634, (i+1, c)
archive = ROOT / 'output/pdf/archive/square-20260928-html-rebuild'
old = ROOT / 'output/pdf/maintenance-triage-square-brief.pdf'
assert sha256(old.read_bytes()).digest() == sha256((archive/'maintenance-triage-square-brief-before.pdf').read_bytes()).digest()
assert (ROOT/'concept-brief/scripts/build-square-brief.py').read_bytes() == (archive/'build-square-brief-before.py').read_bytes()
print('PASS: four 648pt square pages; embedded fonts; links; text bounds; content; previous PDF and builder unchanged.')
print('Fonts:', ', '.join(sorted(fonts)))
