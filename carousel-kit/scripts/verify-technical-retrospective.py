"""Check the exported carousel against its Markdown copy; visual QA is separate."""
import re
from pathlib import Path
import pypdfium2 as pdfium

ROOT = Path(__file__).resolve().parents[2]
source = (ROOT / 'docs/build-2-content-strategy/technical-retrospective-carousel.md').read_text(encoding='utf-8')
fields = re.findall(r'### Slide (\d+)\n\n\*\*Title:\*\* ([^\n]+)\n\n\*\*Body:\*\* ([^\n]+)\n\n\*\*Footer:\*\* ([^\n]+)', source)
pdf_path = ROOT / 'carousel-kit/out/technical-retrospective-maintenance-triage.pdf'

assert len(fields) == 11, f"Expected 11 slides in markdown, found {len(fields)}"
pdf = pdfium.PdfDocument(pdf_path)
assert len(pdf) == len(fields) == 11, f"Expected 11 pages in PDF, found {len(pdf)}"

compact = lambda s: re.sub(r'[\s\u00b7\ufffd\'\"\u2018\u2019\u201c\u201d.,?!:;]+', '', s).lower()

for i, (number, title, body, footer) in enumerate(fields):
    page = pdf[i]
    w, h = page.get_size()
    assert abs(w - 810) < 2, f"Slide {number} width mismatch: {w}"
    assert abs(h - 1013) < 2, f"Slide {number} height mismatch: {h}"
    
    textpage = page.get_textpage()
    text = textpage.get_text_range()
    
    # Strip forbidden terms
    assert not re.search(r'(D:[/\\]|C:[/\\]|localhost|__AIRTABLE|Evidence mapping|Internal evidence)', text), f"Slide {number} has forbidden text leak"
    
    # Verify title, body, and footer content preservation
    for label, expected in [('title', title), ('body', body), ('footer', footer)]:
        for word in expected.split():
            cw = compact(word)
            if cw:
                assert cw in compact(text), f"Slide {number}: {label} word '{word}' ({cw}) not found in page text"

print(f"PASS: {len(fields)} pages verified; title, body, and footer wording preserved on every page; 810x1013 dimensions; no internal leaks; {pdf_path.stat().st_size:,} bytes.")
