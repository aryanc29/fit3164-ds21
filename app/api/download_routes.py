from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional
import base64, tempfile, os, uuid

# Optional PDF support
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    from reportlab.lib.utils import ImageReader
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

router = APIRouter(prefix="/api/v1/export", tags=["export"])

# ---------- Request Models ----------
class ImageDownloadBody(BaseModel):
    data_url: str  # data:image/png;base64,xxxx
    filename: Optional[str] = "export.png"

class PdfDownloadBody(BaseModel):
    title: Optional[str] = "Weather Report"
    notes: Optional[str] = None
    images: List[str] = []
    filename: Optional[str] = "report.pdf"


# ---------- Helper ----------
def _save_data_url(data_url: str, filename: str):
    if not data_url.startswith("data:") or ";base64," not in data_url:
        raise HTTPException(status_code=400, detail="Invalid data URL")

    header, b64data = data_url.split(";base64,", 1)
    ext = header.split("/")[-1].split(";")[0]
    ext = ext if ext else "png"

    tmpfile = os.path.join(tempfile.gettempdir(), f"{uuid.uuid4().hex}.{ext}")
    with open(tmpfile, "wb") as f:
        f.write(base64.b64decode(b64data))
    return tmpfile


# ---------- Image Download ----------
@router.post("/image")
def export_image(body: ImageDownloadBody):
    fpath = _save_data_url(body.data_url, body.filename)
    return FileResponse(fpath, filename=body.filename)


# ---------- PDF Download ----------
@router.post("/pdf")
def export_pdf(body: PdfDownloadBody):
    if not REPORTLAB_AVAILABLE:
        raise HTTPException(status_code=500, detail="reportlab not installed")

    pdf_path = os.path.join(tempfile.gettempdir(), body.filename)
    c = canvas.Canvas(pdf_path, pagesize=A4)
    width, height = A4

    # Title
    c.setFont("Helvetica-Bold", 18)
    c.drawString(50, height - 60, body.title)

    # Optional notes
    y = height - 90
    if body.notes:
        c.setFont("Helvetica", 11)
        for line in body.notes.splitlines():
            c.drawString(50, y, line)
            y -= 16
        y -= 10

    # Add images
    for img_data in body.images:
        img_path = _save_data_url(img_data, "temp.png")
        img = ImageReader(img_path)
        iw, ih = img.getSize()
        scale = min((width - 100) / iw, (height * 0.5) / ih)
        w, h = iw * scale, ih * scale
        if y - h < 100:
            c.showPage()
            y = height - 80
        c.drawImage(img, 50, y - h, w, h)
        y -= (h + 20)
        os.remove(img_path)

    c.save()
    return FileResponse(pdf_path, filename=body.filename)
