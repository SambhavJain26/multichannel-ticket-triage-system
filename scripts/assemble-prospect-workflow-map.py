"""Assemble the four Figma PDF frame exports into the prospect deliverable.

Download frames in reading order to tmp/pdfs/figma-page-{1..4}.pdf first.
Temporary Figma asset URLs must never be committed.
"""
from pathlib import Path
from pypdf import PdfReader, PdfWriter

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output/pdf/maintenance-triage-workflow-map.pdf"
writer = PdfWriter()
for number in range(1, 5):
    reader = PdfReader(ROOT / f"tmp/pdfs/figma-page-{number}.pdf")
    assert len(reader.pages) == 1, f"Expected one Figma frame for page {number}"
    page = reader.pages[0]
    page.scale_to(841.8898, 595.2756)  # A4 landscape, about 11.7 x 8.3 inches.
    writer.add_page(page)
writer.add_metadata({
    "/Title": "Maintenance Triage - Workflow and Integration Map",
    "/Author": "Sambhav Jain | Sambhav Builds",
    "/Subject": "Proposed process, business outcomes, integrations and rollout",
})
OUTPUT.parent.mkdir(parents=True, exist_ok=True)
with OUTPUT.open("wb") as handle:
    writer.write(handle)

check = PdfReader(OUTPUT)
assert len(check.pages) == 4
texts = [page.extract_text() for page in check.pages]
for number, text in enumerate(texts, 1):
    assert len(text) > 700, f"Missing searchable text on page {number}"
required = [
    (0, "ILLUSTRATION ONLY"),
    (1, "HUMAN APPROVAL"),
    (1, "SEND FAILED?"),
    (2, "PostgreSQL"),
    (2, "IF PMS WRITE ACCESS IS LIMITED"),
    (3, "RUN IN SHADOW"),
    (3, "synthetic data"),
]
# Figma PDF glyph positioning may insert spaces within words during extraction.
# Normalize only for assertions; preserve the original exported text in the PDF.
for index, phrase in required:
    assert "".join(phrase.split()) in "".join(texts[index].split()), phrase
links = [
    str(annotation.get_object().get("/A", {}).get("/URI", ""))
    for page in check.pages
    for annotation in page.get("/Annots", [])
]
assert "https://cal.com/sambhav-builds/pm-automation-audit" in links
print(f"Verified {len(check.pages)} searchable A4 landscape pages and booking link: {OUTPUT}")
