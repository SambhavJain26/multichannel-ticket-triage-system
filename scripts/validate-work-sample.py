"""Public PDF privacy, geometry and flattened-image checks; visual QA is separate."""
from pathlib import Path
from io import BytesIO
import hashlib
import json
import re
from PIL import Image
from pypdf import PdfReader
import pdfplumber

ROOT=Path(__file__).resolve().parents[1]
PDF=ROOT/'output/pdf/maintenance-triage-automation-work-sample.pdf'
ASSETS=ROOT/'docs/work-sample-screenshots/v2'
reader=PdfReader(PDF)
review=json.loads((ASSETS/'review.json').read_text())
assert len(reader.pages)==review['pages']
assert hashlib.sha256(PDF.read_bytes()).hexdigest()==review['pdf_sha256'],'PDF differs from visually reviewed version'
patterns={
    'email':r'[\w.+-]+\s*@\s*[\w.-]+\.[A-Za-z]{2,}',
    'contact_or_external_url':r'https?\s*[:/]\s*/|www\.|mailto:|t\.me/|trycloudflare|linkedin|calendly',
    'private_identifier':r'\b(?:app|rec|tbl|viw)[A-Za-z0-9]{12,}\b|\b\d{10,15}\b|\bsk-[A-Za-z0-9_-]+',
    'internal_path':r'[A-Za-z]:[\\/]|AGENTS\.md|progress-notes|build-plan|\.json\b|\.py\b|Workflow\s*:',
}
def scan(s,label):
    for kind,pattern in patterns.items():
        assert not re.search(pattern,s,re.I),f'{label}: prohibited {kind}'

alltext='\n'.join(p.extract_text() for p in reader.pages)
scan(alltext,'PDF text'); scan(str(reader.metadata),'PDF metadata')
for i,p in enumerate(reader.pages,1):
    assert tuple(float(x) for x in p.mediabox)==(0.,0.,792.,612.)
    assert 'Maintenance Request Triage / Work Sample' in p.extract_text()
    assert f'{i} / {len(reader.pages)}' in p.extract_text()
    assert not p.get('/Annots'),f'Page {i}: annotations or links'
    for key in ['/AA','/PieceInfo']:
        assert key not in p,f'Page {i}: hidden or active content'
for key in ['/Names','/OpenAction','/AA','/AcroForm','/OCProperties']:
    assert key not in reader.trailer['/Root'],f'Unexpected catalog entry {key}'
assert not list(reader.attachments)

def pixel_hash(im): return hashlib.sha256(im.convert('RGB').tobytes()).hexdigest()
allowed={pixel_hash(Image.open(p)) for p in ASSETS.glob('*.png')}
image_count=0
for page in reader.pages:
    for obj in page.images:
        assert pixel_hash(Image.open(BytesIO(obj.data))) in allowed,'Embedded image differs from flattened public crop'
        image_count+=1
with pdfplumber.open(PDF) as doc:
    for n,p in enumerate(doc.pages,1):
        for ch in p.chars:
            assert ch['x0']>=41 and ch['x1']<=751 and ch['top']>=20 and ch['bottom']<=602,f'Text outside margins on page {n}'
            assert ch['size']>=8.9,f'Tiny authored text on page {n}'

ocr_path=ROOT/'tmp/work-sample-v2/image-ocr.json'
if ocr_path.exists():
    records=json.loads(ocr_path.read_text(encoding='utf-8-sig'))
    assert records and {r['image'] for r in records}=={p.name for p in ASSETS.glob('*.png')},'OCR coverage mismatch'
    manual=review
    unreadable=[r['image'] for r in records if not r.get('text','').strip()]
    assert set(unreadable)<=set(manual['reviewed_without_ocr']),'OCR-empty image requires recorded visual inspection'
    for r in records:
        scan(r['text'],r['image'])
    ocr_checked=sum(bool(r.get('text','').strip()) for r in records)
else: ocr_checked=0
result=dict(pages=len(reader.pages),embedded_images=image_count,ocr_images=ocr_checked,
            metadata=dict(reader.metadata),links=0,attachments=0,hidden_original_images=0,
            text_privacy='passed',image_integrity='passed',geometry='passed')
(ROOT/'tmp/work-sample-v2/validation.json').write_text(json.dumps(result,indent=2)+'\n')
print(f'PASS: {len(reader.pages)} pages; {image_count} flattened images; {ocr_checked} OCR image checks plus visual review; no links or attachments')
