"""Flatten public evidence crops. Raw captures remain in ignored local storage."""
from pathlib import Path
from PIL import Image, ImageDraw
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / 'tmp/work-sample-v2/raw'
OUT = ROOT / 'docs/work-sample-screenshots/v2'
OUT.mkdir(parents=True, exist_ok=True)
# Coordinates refer to the genuine capture, before cropping. Redactions replace
# pixels; neither a PDF overlay nor the uncropped source is embedded downstream.
SPECS = {
    'intake-full': ('intake-full.jpg', (125,375,1355,555), [(440,494,527,504),(743,450,837,460)]),
    'intake-normalize': ('intake-normalize.jpg', (565,290,1435,645), [(1235,536,1435,556)]),
    'intake-pairing': ('intake-pairing.jpg', (305,290,1200,660), [(750,438,950,460)]),
    'intake-complete': ('intake-complete.jpg', (190,415,1090,670), []),
    'intake-success': ('intake-execution.jpg', (370,90,518,137), []),
    'form-input': ('form-input.jpg', (399,18,859,458), []),
    'form-output': ('form-input-execution.jpg', (510,70,1395,390), [(612,235,765,258)]),
    'form-receipt': ('form-result.jpg', (415,22,866,129), []),
    'engine-full': ('engine-full.jpg', (135,354,1345,573), [(580,459,642,469),(1018,452,1090,466)]),
    'engine-classify': ('engine-classify.png', (460,290,1115,570), [(902,459,1115,481)]),
    'engine-safety': ('engine-safety.png', (635,390,1085,585), []),
    'engine-draft': ('engine-draft.png', (390,290,1260,472), [(825,440,1030,462)]),
    'engine-router': ('engine-routes.png', (880,375,1065,591), []),
    'engine-routes-upper': ('engine-routes.png', (1075,110,1308,451), []),
    'engine-routes-lower': ('engine-routes.png', (1075,490,1308,832), []),
    'engine-decision': ('engine-decision.jpg', (710,262,1237,654), []),
    'tenant-full': ('tenant-full.png', (135,245,1355,702), [(828,385,909,396),(828,606,909,617),(1263,345,1343,355),(1263,535,1343,544)]),
    'tenant-buffer': ('tenant-clarify.png', (330,325,1205,510), []),
    'tenant-clarify': ('tenant-clarify.png', (330,130,1200,316), [(545,290,748,309)]),
    'tenant-status': ('tenant-status.png', (330,290,1205,470), []),
    'tenant-handoff': ('tenant-handoff.png', (615,90,1260,285), [(1058,250,1260,275)]),
    'tenant-journey-start': ('tenant-clarification-evidence.jpg', (560,525,1250,814), []),
    'tenant-journey-ready': ('tenant-provider-update.jpg', (560,440,1250,814), []),
    'tenant-journey-status': ('tenant-status-evidence.jpg', (560,360,1250,814), []),
    'manager-full': ('manager-full.png', (125,175,1355,755), []),
    'manager-candidates': ('manager-candidates.png', (210,125,1060,380), []),
    'manager-approve': ('manager-approve.png', (350,175,1225,380), []),
    'manager-outcome': ('manager-outcome.png', (245,85,1340,465), []),
    'manager-approval-chat': ('manager-pending.jpg', (560,250,1045,810), []),
    'manager-sent': ('manager-result.jpg', (700,65,1245,167), []),
    'manager-repeat': ('manager-repeat-result.jpg', (790,65,1410,170), []),
    'vendor-email': ('vendor-email.jpg', (320,123,1195,452), [(495,179,650,201)]),
    'requests-classification': ('airtable-classification.jpg', (55,134,865,360), []),
    'requests-dispatch': ('airtable-dispatch-final.jpg', (55,134,847,359), []),
    'conversations-links': ('airtable-conversations-final.jpg', (55,135,680,519), []),
    'conversations-outcomes': ('airtable-conversations-final.jpg', (680,135,1220,519), []),
    'operations-full': ('operations-full.png', (275,160,1245,789), [(580,606,738,625)]),
    'operations-checks': ('operations-checks-clean.jpg', (80,165,1010,587), []),
    'operations-emergencies': ('operations-checks.png', (80,500,760,708), [(525,666,728,689)]),
    'operations-sync-select': ('operations-sync.png', (80,370,735,620), []),
    'operations-sync-complete': ('operations-sync.png', (740,370,1400,620), []),
    'operations-executed-select': ('operations-execution.jpg', (400,660,880,796), []),
    'operations-executed-complete': ('operations-execution.jpg', (905,660,1400,796), []),
    'operations-success': ('operations-execution.jpg', (370,90,511,137), []),
}

manifest = []
for name, (raw, crop, masks) in SPECS.items():
    im = Image.open(RAW / raw).convert('RGB')
    draw = ImageDraw.Draw(im)
    for rect in masks:
        draw.rectangle(rect, fill=im.getpixel((rect[0]-2,rect[1])))
    im = im.crop(crop)
    path = OUT / (name+'.png')
    im.save(path, format='PNG')
    manifest.append({'image':path.name, 'size':list(im.size),
                     'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                     'redactions':len(masks)})
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
print(f'Prepared {len(manifest)} flattened evidence images')
