from pathlib import Path
import pypdfium2 as pdfium
from PIL import Image

kit_out = Path("carousel-kit/out")
pages_dir = kit_out / "pages"
pages_dir.mkdir(parents=True, exist_ok=True)

pdf_path = kit_out / "technical-retrospective-maintenance-triage.pdf"
pdf = pdfium.PdfDocument(pdf_path)

images = []
for i, page in enumerate(pdf):
    # Render at 1.5x scale (1215x1520) for high visual fidelity
    img = page.render(scale=1.5).to_pil()
    img_path = pages_dir / f"slide-{i+1:02d}.png"
    img.save(img_path)
    images.append(img)
    print(f"Rendered slide {i+1:02d} -> {img_path}")

# Build a neat 3-column contact sheet
cols = 3
rows = (len(images) + cols - 1) // cols
w, h = images[0].size
thumb_w = 400
thumb_h = int(h * (thumb_w / w))

gap = 20
sheet_w = cols * thumb_w + (cols + 1) * gap
sheet_h = rows * thumb_h + (rows + 1) * gap

sheet = Image.new("RGB", (sheet_w, sheet_h), (90, 96, 104))

for idx, img in enumerate(images):
    c = idx % cols
    r = idx // cols
    x = gap + c * (thumb_w + gap)
    y = gap + r * (thumb_h + gap)
    thumb = img.resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
    sheet.paste(thumb, (x, y))

preview_path = kit_out / "technical-retrospective-maintenance-triage-preview.png"
sheet.save(preview_path)
print(f"Contact sheet saved -> {preview_path}")
