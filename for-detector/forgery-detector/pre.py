import streamlit as st
import cv2
import numpy as np
from PIL import Image, ImageDraw
import pytesseract
import io, re
import fitz
import torch
import torch.nn as nn
import torchvision.transforms as transforms
import torchvision.models as models
from datetime import datetime

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

st.set_page_config(
    page_title="DocGuard — Document Forensics",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ═══════════════════════════════════════════════════════════════════════════════
#  STYLES  —  Modern Clean SaaS / Intelligence Dashboard
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500&family=Poppins:wght@500;600;700&display=swap');

:root {
  --bg:          #0b0f19;
  --surface:     #111827;
  --card:        #1f2937;
  --card2:       #374151;
  --border:      #374151;
  --border-hi:   #4b5563;
  --primary:     #3b82f6;
  --primary-dim: rgba(59, 130, 246, 0.15);
  --primary-hover:#2563eb;
  --red:         #ef4444;
  --orange:      #f97316;
  --yellow:      #eab308;
  --green:       #10b981;
  --muted:       #9ca3af;
  --text:        #f3f4f6;
  --mono:        'JetBrains Mono', monospace;
  --display:     'Poppins', sans-serif;
  --body:        'Inter', sans-serif;
  --radius:      10px;
}

html, body, [class*="css"] {
  font-family: var(--body) !important;
  color: var(--text) !important;
  background: var(--bg) !important;
}
.stApp { background: var(--bg) !important; }

/* ── SIDEBAR ── */
section[data-testid="stSidebar"] {
  background: var(--surface) !important;
  border-right: 1px solid var(--border) !important;
}
section[data-testid="stSidebar"] > div { padding-top: 0 !important; }

/* ── HERO ── */
.hero {
  background: linear-gradient(135deg, var(--surface) 0%, #151e32 100%);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 2.5rem 3rem 2.5rem;
  margin-bottom: 2rem;
  position: relative; overflow: hidden;
  box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3);
}
.hero::before {
  content: '';
  position: absolute; top: -50%; right: -10%;
  width: 400px; height: 200%;
  background: radial-gradient(circle, rgba(59,130,246,0.1) 0%, transparent 70%);
  pointer-events: none;
  transform: rotate(15deg);
}
.hero-kicker {
  font-family: var(--mono);
  font-size: 0.7rem; letter-spacing: 0.15em; text-transform: uppercase;
  color: var(--primary); margin-bottom: 0.8rem;
  display: flex; align-items: center; gap: 8px; font-weight: 500;
}
.hero-kicker::before { content: '●'; color: var(--primary); font-size: 0.5rem; }
.hero-title {
  font-family: var(--display);
  font-size: 4rem; line-height: 1.1; letter-spacing: -0.02em;
  color: #ffffff; margin: 0 0 1rem; font-weight: 700;
}
.hero-title span { color: var(--primary); }
.hero-sub {
  font-size: 1rem; font-weight: 400;
  color: var(--muted); max-width: 600px;
  line-height: 1.6; margin-bottom: 1.8rem;
}
.tag-strip { display: flex; flex-wrap: wrap; gap: 8px; }
.tag {
  font-family: var(--mono);
  font-size: 0.65rem; font-weight: 500;
  padding: 4px 12px; border-radius: 9999px;
  background: var(--primary-dim);
  border: 1px solid rgba(59, 130, 246, 0.3);
  color: #93c5fd;
}

/* ── SECTION HEADER ── */
.shdr {
  font-family: var(--display);
  font-size: 1.25rem; font-weight: 600; letter-spacing: -0.01em;
  color: #ffffff; margin: 2rem 0 1rem;
  display: flex; align-items: center; gap: 10px;
}
.shdr::before { 
  content: ''; display: block; 
  width: 4px; height: 1.1rem; 
  background: var(--primary); border-radius: 2px; 
}

/* ── CARD ── */
.g-card {
  background: var(--card); border: 1px solid var(--border);
  border-radius: var(--radius); padding: 1.5rem; margin-bottom: 0.8rem;
  box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.g-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 15px -3px rgba(0,0,0,0.15);
}

/* ── VERDICT ── */
.verd { border-radius: var(--radius); padding: 1.8rem 2rem; margin-bottom: 0.8rem; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); }
.verd-forged     { background:rgba(239,68,68,0.05);  border:1px solid rgba(239,68,68,0.2);  border-top:4px solid var(--red); }
.verd-suspicious { background:rgba(249,115,22,0.05); border:1px solid rgba(249,115,22,0.2); border-top:4px solid var(--orange); }
.verd-minor      { background:rgba(234,179,8,0.05);  border:1px solid rgba(234,179,8,0.2);  border-top:4px solid var(--yellow); }
.verd-genuine    { background:rgba(16,185,129,0.05); border:1px solid rgba(16,185,129,0.2); border-top:4px solid var(--green); }
.verd-eyebrow {
  font-family: var(--mono); font-size:0.7rem; font-weight: 500;
  letter-spacing:0.1em; text-transform:uppercase;
  margin-bottom:0.8rem;
}
.verd-head {
  font-family: var(--display); font-weight: 600;
  font-size: 1.8rem; letter-spacing: -0.01em;
  margin-bottom: 0.5rem; line-height: 1.2;
}
.verd-body { font-size:0.95rem; font-weight:400; color: var(--text); opacity:0.9; line-height:1.5; }

/* ── GAUGE ── */
.gauge {
  background: var(--card); border: 1px solid var(--border);
  border-radius: var(--radius); padding: 1.5rem 2rem;
  box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
}
.gauge-top {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 1.2rem;
}
.gauge-num {
  font-family: var(--display); font-weight: 700;
  font-size: 4rem; line-height: 1; letter-spacing: -0.02em;
}
.gauge-pct {
  font-family: var(--display); font-size: 1.8rem; font-weight: 500;
  color: var(--muted); vertical-align: text-top; margin-left: 2px;
}
.gauge-label {
  font-family: var(--display); font-size: 1.1rem; font-weight: 600;
  margin-top: 4px;
}
.gauge-bar-bg {
  height: 8px; border-radius: 4px;
  background: var(--surface); overflow: hidden; margin-bottom: 0.8rem;
  box-shadow: inset 0 1px 3px rgba(0,0,0,0.2);
}
.gauge-bar { height: 100%; border-radius: 4px; transition: width 1s ease-out; }
.gauge-ticks {
  display: flex; justify-content: space-between;
  font-family: var(--mono); font-size: 0.65rem; font-weight: 500;
}

/* ── METRICS ── */
.metrics-row {
  display: grid; grid-template-columns: repeat(6,1fr);
  gap: 12px; margin: 1rem 0;
}
.metric {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 8px; padding: 1rem 0.8rem; text-align: center;
  box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
}
.metric-v {
  font-family: var(--display); font-weight: 600;
  font-size: 1.6rem; line-height: 1; margin-bottom: 6px;
}
.metric-l {
  font-family: var(--body); font-size: 0.7rem; font-weight: 500;
  color: var(--muted);
}
.mv-ok     { color: var(--green); }
.mv-warn   { color: var(--yellow); }
.mv-danger { color: var(--red); }
.mv-blue   { color: var(--primary); }
.mv-amber  { color: var(--orange); }

/* ── FINDINGS ── */
.finding {
  display: flex; gap: 12px; align-items: flex-start;
  border-radius: 8px; padding: 1rem 1.2rem; margin: 8px 0; font-size: 0.9rem;
  background: var(--card); border: 1px solid var(--border);
}
.fc { border-left: 4px solid var(--red); }
.fw { border-left: 4px solid var(--orange); }
.fi { border-left: 4px solid var(--primary); }
.f-layer {
  font-family: var(--mono); font-size: 0.65rem; font-weight: 500;
  color: var(--muted); text-transform: uppercase; margin-bottom: 4px;
}
.f-title { font-weight: 600; font-size: 0.95rem; color: #ffffff; }
.f-detail { font-weight: 400; font-size: 0.85rem; color: var(--text); opacity: 0.85; margin-top: 4px; line-height: 1.5; }

/* ── PIPELINE ── */
.pipe {
  display: grid; grid-template-columns: repeat(5,1fr);
  gap: 8px; margin: 1rem 0 2rem;
}
.pstep {
  font-family: var(--body); font-size: 0.75rem; font-weight: 500;
  padding: 8px 12px; border-radius: 6px;
  display: flex; align-items: center; gap: 8px;
  background: var(--surface); border: 1px solid var(--border);
}
.ps-done { border-color:rgba(16,185,129,0.3); background:rgba(16,185,129,0.05); color:var(--green); }
.ps-run  { border-color:rgba(59,130,246,0.3); background:rgba(59,130,246,0.05); color:var(--primary);
           animation: pulse 1.5s cubic-bezier(0.4, 0, 0.6, 1) infinite; }
.ps-wait { color: var(--muted); }
@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.5} }

/* ── LEGEND ── */
.legend {
  display: flex; flex-wrap: wrap; gap: 16px;
  font-family: var(--body); font-size: 0.75rem; font-weight: 500;
  color: var(--muted); margin: 0.5rem 0 1.5rem;
}
.l-item { display: flex; align-items: center; gap: 6px; }
.l-dot  { width:10px; height:10px; border-radius:50%; flex-shrink:0; }

/* ── IMG FRAME ── */
.img-frame {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: var(--radius); padding: 12px; margin-bottom: 12px;
  box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
}

/* ── FIELDS ── */
.field {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 6px; padding: 0.75rem 1rem; margin: 6px 0;
}
.field-k {
  font-family: var(--body); font-size: 0.7rem; font-weight: 500;
  color: var(--muted); text-transform: uppercase; margin-bottom: 2px;
}
.field-v { font-family: var(--mono); font-size: 0.85rem; color: #ffffff; }

/* ── DL SCORES ── */
.dl-row {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 6px; padding: 0.8rem 1rem; margin: 6px 0;
  display: flex; align-items: center; justify-content: space-between;
}
.dl-name { font-family: var(--body); font-size: 0.75rem; font-weight: 500; color: var(--muted); }
.dl-val  { font-family: var(--display); font-size: 1.3rem; font-weight: 600; }
.dl-bar-bg { height: 4px; background: var(--card2); border-radius: 2px; margin-top: 6px; }
.dl-bar    { height: 4px; border-radius: 2px; }

/* ── FILE DETAIL ── */
.file-detail {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 6px; padding: 0.75rem 1rem; margin: 6px 0;
  display: flex; justify-content: space-between; align-items: center;
}
.fd-k { font-family: var(--body); font-size: 0.75rem; font-weight: 500; color: var(--muted); }
.fd-v { font-family: var(--mono); font-size: 0.8rem; color: #ffffff; font-weight: 500; }

/* ── FEAT CARDS ── */
.feat {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: var(--radius); padding: 1.8rem 1.5rem;
  transition: transform 0.2s, box-shadow 0.2s;
  height: 100%;
}
.feat:hover { transform: translateY(-4px); box-shadow: 0 10px 15px -3px rgba(0,0,0,0.2); }
.feat-ic { font-size: 2rem; margin-bottom: 1rem; }
.feat-t {
  font-family: var(--display); font-size: 1.2rem; font-weight: 600;
  color: #ffffff; margin-bottom: 0.5rem; line-height: 1.3;
}
.feat-d { font-size: 0.9rem; color: var(--muted); line-height: 1.6; }

/* ── PAGE BADGE ── */
.pbadge {
  display: inline-flex; align-items: center; gap: 8px;
  background: var(--primary-dim); border: 1px solid rgba(59,130,246,0.2);
  border-radius: 999px; padding: 6px 14px;
  font-family: var(--body); font-size: 0.75rem; font-weight: 500;
  color: #60a5fa; margin-bottom: 12px;
}

/* ── TABS ── */
div[data-testid="stTabs"] button {
  font-family: var(--body) !important;
  font-size: 0.85rem !important; font-weight: 500 !important;
  background: transparent !important; color: var(--muted) !important;
  border: none !important; border-bottom: 2px solid transparent !important;
  padding: 0.5rem 1rem !important;
}
div[data-testid="stTabs"] button[aria-selected="true"] {
  color: var(--primary) !important;
  border-bottom: 2px solid var(--primary) !important;
}
div[data-testid="stTabs"] [data-testid="stTabContent"] {
  background: var(--surface) !important; 
  border: 1px solid var(--border) !important;
  border-radius: var(--radius) !important;
  padding: 1.5rem !important;
  margin-top: 0.5rem;
}

/* ── UPLOAD ── */
[data-testid="stFileUploader"] {
  background: var(--surface) !important;
  border: 2px dashed var(--border-hi) !important;
  border-radius: var(--radius) !important;
  padding: 1rem !important;
  transition: border-color 0.2s;
}
[data-testid="stFileUploader"]:hover { border-color: var(--primary) !important; }

/* ── DOWNLOAD ── */
.stDownloadButton > button {
  background: linear-gradient(to right, var(--primary), var(--primary-hover)) !important;
  color: #ffffff !important;
  border: none !important; border-radius: 8px !important;
  font-family: var(--body) !important;
  font-size: 0.9rem !important; font-weight: 600 !important;
  width: 100% !important; padding: 0.8rem !important;
  box-shadow: 0 4px 6px -1px rgba(59, 130, 246, 0.3) !important;
  transition: transform 0.1s, box-shadow 0.1s !important;
}
.stDownloadButton > button:hover { 
  transform: translateY(-1px) !important; 
  box-shadow: 0 6px 8px -1px rgba(59, 130, 246, 0.4) !important; 
}

/* ── SIDEBAR ── */
.sb-title {
  font-family: var(--display); font-size: 1.8rem; font-weight: 700;
  color: var(--primary); padding: 1.5rem 1rem 0.2rem;
}
.sb-ver {
  font-family: var(--mono); font-size: 0.65rem; font-weight: 500;
  color: var(--muted); text-transform: uppercase;
  padding: 0 1rem 1.5rem;
}
.sb-sec {
  font-family: var(--display); font-size: 0.85rem; font-weight: 600;
  color: #ffffff; text-transform: uppercase; letter-spacing: 0.05em;
  padding: 0.8rem 1rem 0.4rem; margin-top: 0.5rem;
  border-bottom: 1px solid var(--border);
}
.sb-row {
  display: flex; align-items: flex-start; gap: 10px;
  padding: 0.6rem 1rem; font-size: 0.85rem;
}
.sb-bullet {
  width: 6px; height: 6px; border-radius: 50%;
  background: var(--primary); flex-shrink: 0; margin-top: 6px;
}
.sb-main { color: #e5e7eb; font-weight: 500; font-size: 0.85rem; }
.sb-sub  { color: var(--muted); font-size: 0.7rem; font-family: var(--body); margin-top: 2px; }

/* ── SCROLLBAR ── */
::-webkit-scrollbar { width: 8px; height: 8px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--border-hi); border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: var(--muted); }

footer, #MainMenu { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
#  IMAGE RESIZE HELPER — caps display width, analysis uses full-res
# ═══════════════════════════════════════════════════════════════════════════════
def resize_display(img: Image.Image, max_w: int = 860) -> Image.Image:
    w, h = img.size
    if w <= max_w:
        return img
    return img.resize((max_w, int(h * max_w / w)), Image.LANCZOS)


# ═══════════════════════════════════════════════════════════════════════════════
#  PYTORCH MODEL
# ═══════════════════════════════════════════════════════════════════════════════
@st.cache_resource(show_spinner=False)
def load_model():
    base = models.resnet18(weights=models.ResNet18_Weights.DEFAULT)
    base.fc = nn.Sequential(
        nn.Linear(512, 256), nn.ReLU(), nn.Dropout(0.4),
        nn.Linear(256, 64),  nn.ReLU(), nn.Linear(64, 2)
    )
    base.eval()
    return base

def dl_region_score(patch_pil, model):
    t = transforms.Compose([
        transforms.Resize((224, 224)), transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ])
    with torch.no_grad():
        p = torch.softmax(model(t(patch_pil.convert("RGB")).unsqueeze(0)), dim=1)[0]
    return float(p[1])


# ═══════════════════════════════════════════════════════════════════════════════
#  LOAD IMAGE — all PDF pages stitched vertically
# ═══════════════════════════════════════════════════════════════════════════════
def load_image(uploaded):
    data = uploaded.read()
    if uploaded.type == "application/pdf":
        doc = fitz.open(stream=data, filetype="pdf")
        n_pages = len(doc)
        pages = []
        for i in range(min(n_pages, 15)):
            pix = doc[i].get_pixmap(matrix=fitz.Matrix(2, 2))
            pages.append(Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB"))
        if len(pages) == 1:
            return pages[0], data, 1
        tw = max(p.width  for p in pages)
        th = sum(p.height for p in pages)
        combined = Image.new("RGB", (tw, th), (255, 255, 255))
        y = 0
        for p in pages:
            combined.paste(p, (0, y)); y += p.height
        return combined, data, n_pages
    return Image.open(io.BytesIO(data)).convert("RGB"), data, 1


# ═══════════════════════════════════════════════════════════════════════════════
#  1. METADATA
# ═══════════════════════════════════════════════════════════════════════════════
def analyse_metadata(img_pil, raw_bytes, filename):
    findings, meta = [], {}
    ext = filename.rsplit(".", 1)[-1].lower()
    try:
        from PIL.ExifTags import TAGS
        exif_raw = img_pil._getexif()
        if exif_raw:
            for tag_id, val in exif_raw.items():
                tag = TAGS.get(tag_id, str(tag_id))
                meta[tag] = str(val)[:80]
                if tag in ("Software", "ProcessingSoftware", "HostComputer"):
                    findings.append({"level": "warning",
                        "title": f"Metadata: {tag} tag found",
                        "detail": f'Value "{val}" — document processed in software', "layer": "Metadata"})
        else:
            meta["EXIF"] = "None (normal for scanned/govt documents)"
    except:
        meta["EXIF"] = "Not readable"
    info = getattr(img_pil, "info", {})
    for k, v in info.items():
        if k == "icc_profile": meta["ICC_Profile"] = f"{len(v)} bytes"
        elif k not in ("exif",): meta[str(k)] = str(v)[:60]
    edit_kw = [b"Photoshop", b"GIMP", b"Paint.NET", b"Canva",
               b"Snapseed", b"Adobe", b"Lightroom", b"Inkscape"]
    for kw in edit_kw:
        if kw.lower() in raw_bytes.lower():
            findings.append({"level": "critical",
                "title": f"Editing software signature: {kw.decode()}",
                "detail": f"File bytes contain '{kw.decode()}' — edited in image software", "layer": "Metadata"})
            meta["EditSoftware"] = kw.decode(); break
    if (img_pil.format or "Unknown") == "JPEG" and ext == "png":
        findings.append({"level": "warning", "title": "Format mismatch: JPEG saved as .png",
            "detail": "Extension doesn't match actual format — possible re-encoding", "layer": "Metadata"})
    return findings, meta


# ═══════════════════════════════════════════════════════════════════════════════
#  2. ELA
# ═══════════════════════════════════════════════════════════════════════════════
def run_ela(image, quality=92):
    buf = io.BytesIO()
    image.convert("RGB").save(buf, format="JPEG", quality=quality); buf.seek(0)
    comp  = Image.open(buf).convert("RGB")
    orig  = np.array(image).astype(np.float32)
    diff  = np.abs(orig - np.array(comp).astype(np.float32))
    score = float(diff.mean())
    ela_img = Image.fromarray((diff / (diff.max() + 1e-8) * 255).astype(np.uint8))
    h, w = orig.shape[:2]
    regions = {
        "top_left":  diff[:h//2, :w//2],  "top_right": diff[:h//2, w//2:],
        "bot_left":  diff[h//2:, :w//2],  "bot_right": diff[h//2:, w//2:],
    }
    rs = {k: float(v.mean()) for k, v in regions.items()}
    spread = max(rs.values()) - min(rs.values())
    findings = []
    if spread > 3.5:
        worst = max(rs, key=rs.get)
        findings.append({"level": "warning",
            "title": f"ELA regional inconsistency (spread={spread:.2f})",
            "detail": f"Region '{worst.replace('_',' ')}' shows much higher re-compression artifacts.", "layer": "ELA"})
    if score > 6.0:
        findings.append({"level": "critical", "title": f"High global ELA score ({score:.2f})",
            "detail": "Strong re-compression artifacts across entire document — significant editing detected.", "layer": "ELA"})
    elif score > 3.5:
        findings.append({"level": "warning", "title": f"Moderate ELA score ({score:.2f})",
            "detail": "Moderate compression artifacts — minor editing possible.", "layer": "ELA"})
    ela_gray = np.array(ela_img.convert("L")).astype(np.float32)
    hotspot_boxes = []
    block = max(h, w) // 12
    thresh = ela_gray.mean() + 2.8 * ela_gray.std()
    for i in range(0, h - block, block // 2):
        for j in range(0, w - block, block // 2):
            patch = ela_gray[i:i+block, j:j+block]
            if patch.mean() > thresh and patch.mean() > 30:
                hotspot_boxes.append((j, i, block, block, float(patch.mean())))
    hotspot_boxes.sort(key=lambda x: -x[4]); hotspot_boxes = hotspot_boxes[:5]
    return ela_img, score, rs, findings, hotspot_boxes

def ela_overlay(orig, ela_img):
    dw = min(orig.width, 900)
    dh = int(orig.height * dw / orig.width)
    o  = orig.resize((dw, dh), Image.LANCZOS)
    e  = np.array(ela_img.convert("L").resize((dw, dh), Image.LANCZOS))
    hm = cv2.applyColorMap(e, cv2.COLORMAP_JET)
    return Image.blend(o, Image.fromarray(cv2.cvtColor(hm, cv2.COLOR_BGR2RGB)), 0.5)


# ═══════════════════════════════════════════════════════════════════════════════
#  3. COLOR ANOMALY
# ═══════════════════════════════════════════════════════════════════════════════
def detect_color_anomaly(image):
    img_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    hsv    = cv2.cvtColor(img_cv, cv2.COLOR_BGR2HSV)
    hi, wi = hsv.shape[:2]
    r1 = (hsv[:,:,0] <  10) & (hsv[:,:,1] > 100) & (hsv[:,:,2] > 100)
    r2 = (hsv[:,:,0] > 165) & (hsv[:,:,1] > 100) & (hsv[:,:,2] > 100)
    red_mask = r1 | r2; red_count = int(red_mask.sum())
    findings = []; color_map = image.convert("RGB").copy()
    draw = ImageDraw.Draw(color_map); color_boxes = []
    if red_count > 50:
        c = np.argwhere(red_mask); y1,x1 = c.min(axis=0); y2,x2 = c.max(axis=0); p=8
        draw.rectangle([x1-p,y1-p,x2+p,y2+p], outline=(239,68,68), width=3)
        color_boxes.append((x1-p,y1-p,x2-x1+2*p,y2-y1+2*p))
        findings.append({"level":"critical","title":f"Colored text detected ({red_count} red pixels)",
            "detail":f"Red-colored text at ({x1},{y1})–({x2},{y2}). Original docs have uniform black text.","layer":"Color"})
    block=20; mean_s=float(hsv[:,:,1].mean()); std_s=float(hsv[:,:,1].std())
    thresh=mean_s+2.5*std_s; sat_boxes=[]
    for i in range(hi//block):
        for j in range(wi//block):
            if hsv[i*block:(i+1)*block,j*block:(j+1)*block,1].mean()>thresh and \
               hsv[i*block:(i+1)*block,j*block:(j+1)*block,1].mean()>90:
                sat_boxes.append((j*block,i*block,block,block))
    if len(sat_boxes)>3 and not(red_count>50):
        xs=[b[0] for b in sat_boxes]; ys=[b[1] for b in sat_boxes]
        x1c,y1c=min(xs),min(ys); x2c,y2c=max(xs)+block,max(ys)+block
        if (x2c-x1c)*(y2c-y1c)>400:
            draw.rectangle([x1c-4,y1c-4,x2c+4,y2c+4],outline=(249,115,22),width=2)
            color_boxes.append((x1c-4,y1c-4,x2c-x1c+8,y2c-y1c+8))
            findings.append({"level":"warning","title":f"Unusual saturation ({len(sat_boxes)} blocks)",
                "detail":f"Saturation above document average at ({x1c},{y1c})–({x2c},{y2c}).","layer":"Color"})
    return color_map, red_count, findings, color_boxes


# ═══════════════════════════════════════════════════════════════════════════════
#  4. COPY-MOVE
# ═══════════════════════════════════════════════════════════════════════════════
def copy_move(image):
    img  = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    sift = cv2.SIFT_create(); kp, des = sift.detectAndCompute(gray, None)
    count=0; out=img.copy()
    if des is not None and len(des)>10:
        matches=cv2.FlannBasedMatcher({"algorithm":1,"trees":5},{"checks":50}).knnMatch(des,des,k=2)
        good=[]
        for pair in matches:
            if len(pair)==2:
                m,n=pair
                if m.distance<0.7*n.distance and m.trainIdx!=m.queryIdx:
                    p1,p2=kp[m.queryIdx].pt,kp[m.trainIdx].pt
                    if np.hypot(p1[0]-p2[0],p1[1]-p2[1])>20: good.append((p1,p2))
        count=len(good)
        for p1,p2 in good[:30]:
            cv2.line(out,(int(p1[0]),int(p1[1])),(int(p2[0]),int(p2[1])),(80,80,255),1)
            cv2.circle(out,(int(p1[0]),int(p1[1])),4,(255,80,80),-1)
    findings=[]
    if count>45:
        findings.append({"level":"critical","title":f"High copy-move matches ({count})",
            "detail":"Large number of duplicate feature matches — region likely cloned within document.","layer":"Copy-Move"})
    elif count>20:
        findings.append({"level":"warning","title":f"Moderate copy-move matches ({count})",
            "detail":"Some repeated feature patterns — may indicate cloned regions.","layer":"Copy-Move"})
    return Image.fromarray(cv2.cvtColor(out,cv2.COLOR_BGR2RGB)), count, findings


# ═══════════════════════════════════════════════════════════════════════════════
#  5. NOISE
# ═══════════════════════════════════════════════════════════════════════════════
def noise_analysis(image):
    gray=np.array(image.convert("L")).astype(np.float32)
    blur=cv2.GaussianBlur(gray,(5,5),0); noise=np.abs(gray-blur)
    h,w=noise.shape; bs=max(h,w)//20; nm=np.zeros_like(noise)
    for i in range(0,h-bs,bs//2):
        for j in range(0,w-bs,bs//2):
            nm[i:i+bs,j:j+bs]=np.std(noise[i:i+bs,j:j+bs])
    noise_std=float(np.std(nm))
    norm=((nm-nm.min())/(nm.max()-nm.min()+1e-8)*255).astype(np.uint8)
    nm_img=Image.fromarray(cv2.applyColorMap(norm,cv2.COLORMAP_INFERNO)[:,:,::-1])
    findings=[]
    if noise_std>20:
        findings.append({"level":"critical","title":f"High noise inconsistency (std={noise_std:.2f})",
            "detail":"Very different noise levels across regions — content likely pasted from different source.","layer":"Noise"})
    elif noise_std>13:
        findings.append({"level":"warning","title":f"Slight noise variation (std={noise_std:.2f})",
            "detail":"Minor noise variation — may be natural for scanned documents.","layer":"Noise"})
    return nm_img, noise_std, findings


# ═══════════════════════════════════════════════════════════════════════════════
#  6. PHOTO SWAP
# ═══════════════════════════════════════════════════════════════════════════════
def detect_photo_swap(image):
    gray=np.array(image.convert("L")); h,w=gray.shape
    bs=max(h,w)//12; rows,cols=h//bs,w//bs
    nm=np.zeros((rows,cols))
    for i in range(rows):
        for j in range(cols):
            nm[i,j]=gray[i*bs:(i+1)*bs,j*bs:(j+1)*bs].std()
    mean_n,std_n=nm.mean(),nm.std()
    high=nm>(mean_n+2.0*std_n)
    findings=[]; annotated=image.convert("RGB").copy(); photo_box=None
    if high.any():
        cnts,_=cv2.findContours(high.astype(np.uint8)*255,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
        if cnts:
            biggest=max(cnts,key=cv2.contourArea)
            bx,by,bw_b,bh_b=cv2.boundingRect(biggest)
            px,py,pw,ph=bx*bs,by*bs,bw_b*bs,bh_b*bs
            z=(nm[by:by+bh_b,bx:bx+bw_b].max()-mean_n)/(std_n+1e-8)
            if z>3.2:
                draw=ImageDraw.Draw(annotated)
                for t in range(3): draw.rectangle([px-t,py-t,px+pw+t,py+ph+t],outline=(249,115,22))
                photo_box=(px,py,pw,ph)
                findings.append({"level":"critical","title":f"Photo region noise anomaly (z={z:.1f})",
                    "detail":f"Region at ({px},{py}) size {pw}×{ph}px — consistent with a swapped photograph.","layer":"Photo"})
    return annotated, findings, photo_box


# ═══════════════════════════════════════════════════════════════════════════════
#  7. FONT
# ═══════════════════════════════════════════════════════════════════════════════
def font_analysis(image):
    gray=np.array(image.convert("L"))
    edges=cv2.Canny(gray,50,150)
    dens=[float(s.mean()) for s in np.array_split(edges,10,axis=0)]
    var=float(np.std(dens)); findings=[]
    if var>18:
        findings.append({"level":"warning","title":f"Font/layout inconsistency (var={var:.2f})",
            "detail":"Text edge density varies significantly — different fonts or inserted text blocks may be present.","layer":"Font"})
    return var, findings


# ═══════════════════════════════════════════════════════════════════════════════
#  8. WORD-LEVEL BOXES
# ═══════════════════════════════════════════════════════════════════════════════
def get_suspicious_word_boxes(image, ela_arr, sensitivity="Medium"):
    try:
        data=pytesseract.image_to_data(image,lang="eng",
            output_type=pytesseract.Output.DICT,config="--oem 3 --psm 6")
    except: return []
    img_rgb=np.array(image.convert("RGB"))
    img_hsv=cv2.cvtColor(img_rgb,cv2.COLOR_RGB2HSV)
    img_lab=cv2.cvtColor(img_rgb,cv2.COLOR_RGB2LAB)
    ih,iw=img_rgb.shape[:2]; wf=[]
    for i in range(len(data["text"])):
        txt=data["text"][i].strip()
        try: conf=int(data["conf"][i])
        except: continue
        if conf<35 or not txt: continue
        x,y,w,h=data["left"][i],data["top"][i],data["width"][i],data["height"][i]
        if w*h<80: continue
        x2,y2=min(x+w,iw),min(y+h,ih)
        if x2<=x or y2<=y: continue
        pr=img_rgb[y:y2,x:x2]; ph=img_hsv[y:y2,x:x2]
        pl=img_lab[y:y2,x:x2]; pe=ela_arr[y:y2,x:x2]
        pg=cv2.cvtColor(pr,cv2.COLOR_RGB2GRAY).astype(np.float32)
        lap=cv2.Laplacian(cv2.cvtColor(pr,cv2.COLOR_RGB2GRAY),cv2.CV_32F)
        wf.append({"box":(x,y,w,h),"text":txt,
            "ela":float(pe.mean()),"brightness":float(pg.mean()),
            "sharpness":float(lap.var()),"saturation":float(ph[:,:,1].mean()),
            "b_channel":float(pl[:,:,2].mean()),"conf":conf})
    if len(wf)<3: return []
    def robust(vals):
        a=np.array(vals); m=np.median(a)
        return m, max(np.median(np.abs(a-m))*1.4826, 0.01)
    me,mae=robust([f["ela"]        for f in wf])
    ms,mas=robust([f["saturation"] for f in wf])
    mb,mab=robust([f["brightness"] for f in wf])
    mh,mah=robust([f["sharpness"]  for f in wf])
    mc,mac=robust([f["b_channel"]  for f in wf])
    min_s={"Low":10,"Medium":7,"High":5}.get(sensitivity,7); out=[]
    for f in wf:
        sc=0; rs=[]
        zs=(f["saturation"]-ms)/mas
        if zs>3.5: sc+=6; rs.append(f"colored ink (z={zs:.1f})")
        zc=abs(f["b_channel"]-mc)/mac
        if zc>4.5: sc+=4; rs.append(f"color fingerprint shift (b_z={zc:.1f})")
        ze=(f["ela"]-me)/mae
        if ze>3.0: sc+=5; rs.append(f"re-compression (ELA z={ze:.1f})")
        zb=abs(f["brightness"]-mb)/mab
        if zb>4.0: sc+=3; rs.append(f"brightness mismatch (z={zb:.1f})")
        zh=abs(f["sharpness"]-mh)/mah
        if zh>4.0: sc+=3; rs.append(f"sharpness mismatch (z={zh:.1f})")
        if sc>=min_s: out.append({"box":f["box"],"text":f["text"],"score":sc,"reasons":rs})
    return out


# ═══════════════════════════════════════════════════════════════════════════════
#  9. OCR
# ═══════════════════════════════════════════════════════════════════════════════
def run_ocr(image):
    img_cv=cv2.cvtColor(np.array(image.convert("RGB")),cv2.COLOR_RGB2BGR)
    h,w=img_cv.shape[:2]
    if max(h,w)<1000:
        sc=1000//max(h,w)+1
        img_cv=cv2.resize(img_cv,(w*sc,h*sc),interpolation=cv2.INTER_CUBIC)
    sharp=cv2.filter2D(cv2.fastNlMeansDenoisingColored(img_cv,None,8,8,7,15),
                       -1,np.array([[0,-1,0],[-1,5,-1],[0,-1,0]]))
    proc=Image.fromarray(cv2.cvtColor(sharp,cv2.COLOR_BGR2RGB))
    raw=""
    for lang in ["eng+hin+tel+tam","eng+hin","eng"]:
        try:
            raw=pytesseract.image_to_string(proc,lang=lang,config="--oem 3 --psm 6")
            if len(raw.strip())>10: break
        except: continue
    cleaned=[l.strip() for l in raw.splitlines()
             if len(re.findall(r'[A-Za-z0-9\u0900-\u097F\u0C00-\u0C7F]',l.strip()))>=2]
    text="\n".join(cleaned); fields={}
    for line in cleaned:
        lu=line.upper()
        if re.search(r'DOB|DATE.OF.BIRTH|जन्म',line,re.I):
            m=re.search(r'\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4}',line)
            if m: fields["Date of Birth"]=m.group()
        if re.search(r'ROLL\s*NO|ROLL NUMBER',lu):
            m=re.search(r'\d{8,}',line)
            if m: fields["Roll No"]=m.group()
        if re.search(r'FATHER|पिता',line,re.I): fields["Father Name"]=line
        if re.search(r'MOTHER|माता',line,re.I): fields["Mother Name"]=line
        if re.search(r'PAN|PERMANENT ACCOUNT',lu):
            m=re.search(r'[A-Z]{5}[0-9]{4}[A-Z]',line)
            if m: fields["PAN Number"]=m.group()
        if re.search(r'AADHAAR|AADHAR|XXXX',lu):
            m=re.search(r'[X\d]{4}\s[X\d]{4}\s\d{4}',line)
            if m: fields["Aadhaar"]=m.group()
        if re.search(r'GRAND TOTAL|TOTAL MARKS',lu): fields["Grand Total"]=line
        if re.search(r'DIVISION|GRADE',lu): fields["Division/Grade"]=line
    return text, fields


# ═══════════════════════════════════════════════════════════════════════════════
#  10. WHITE PATCH
# ═══════════════════════════════════════════════════════════════════════════════
def detect_white_patches(image):
    gray=np.array(image.convert("L")); h,w=gray.shape
    doc_mean=float(gray.mean())
    if doc_mean>195: return 0,[],[]
    bt=min(230,doc_mean+50); row_spans={}
    for y in range(h):
        row=gray[y,:]; bright=(row>bt).astype(np.uint8)
        padded=np.concatenate([[0],bright,[0]]); diffs=np.diff(padded.astype(np.int16))
        starts=np.where(diffs==1)[0]; ends=np.where(diffs==-1)[0]
        if not len(starts): continue
        longest=max(zip(starts,ends),key=lambda p:p[1]-p[0])
        if longest[1]-longest[0]>=80: row_spans[y]=(longest[0],longest[1],longest[1]-longest[0])
    if not row_spans: return 0,[],[]
    visited,boxes,flags=[],[],[]
    for ys in sorted(row_spans.keys()):
        if ys in visited: continue
        x0,x1,_=row_spans[ys]; ye=ys
        for y2 in range(ys+1,min(ys+300,h)):
            if y2 not in row_spans: break
            rx0,rx1,_=row_spans[y2]
            if abs(rx0-x0)<30 and abs(rx1-x1)<30: ye=y2; visited.append(y2)
            else: break
        if ye-ys+1<10: continue
        bx,by,bw,bh=int(x0),int(ys),int(x1-x0),int(ye-ys+1)
        contrast=float(gray[by:by+bh,bx:bx+bw].mean())-doc_mean
        if contrast>30:
            boxes.append((bx,by,bw,bh))
            flags.append({"level":"critical","title":f"White overlay patch at ({bx},{by}) size {bw}×{bh}px",
                "detail":f"Uniform bright rectangle {contrast:.0f} levels above background — white box likely pasted over original text.","layer":"White Patch"})
    return len(boxes),boxes,flags


# ═══════════════════════════════════════════════════════════════════════════════
#  ANNOTATED IMAGE
# ═══════════════════════════════════════════════════════════════════════════════
def build_annotated(image, white_boxes, photo_box, color_boxes, ela_hotspots, word_suspects):
    ann=image.convert("RGBA").copy(); ov=Image.new("RGBA",ann.size,(0,0,0,0))
    dr=ImageDraw.Draw(ov)
    for (x,y,bw,bh,_) in ela_hotspots:
        dr.rectangle([x,y,x+bw,y+bh],fill=(0,200,255,25),outline=(0,200,255,160),width=1)
    for (x,y,bw,bh) in color_boxes:
        dr.rectangle([x,y,x+bw,y+bh],fill=(255,165,0,20),outline=(255,165,0,200),width=2)
    for (x,y,bw,bh) in white_boxes:
        dr.rectangle([x,y,x+bw,y+bh],fill=(255,220,0,30),outline=(255,220,0,220),width=2)
        dr.rectangle([x,max(0,y-20),x+bw,max(0,y)],fill=(255,220,0,220))
    if photo_box:
        px,py,pw,ph=photo_box
        dr.rectangle([px,py,px+pw,py+ph],fill=(255,140,0,25),outline=(255,140,0,200),width=3)
        dr.rectangle([px,max(0,py-22),px+pw,max(0,py)],fill=(255,140,0,220))
    for ws in word_suspects:
        x,y,w,h=ws["box"]; sc=ws["score"]
        col=(239,68,68,200) if sc>=12 else (249,115,22,200) if sc>=9 else (234,179,8,180)
        fill=(239,68,68,30) if sc>=12 else (249,115,22,25) if sc>=9 else (234,179,8,20)
        dr.rectangle([x-2,y-2,x+w+2,y+h+2],fill=fill,outline=col,width=2)
        dr.rectangle([x-2,max(0,y-16),x-2+min(len(ws["text"])*7+8,w+4),max(0,y)],fill=col)
    ann=Image.alpha_composite(ann,ov).convert("RGB")
    dr2=ImageDraw.Draw(ann)
    for ws in word_suspects:
        x,y,_,_=ws["box"]; dr2.text((x,max(0,y-14)),ws["text"][:10],fill=(255,255,255))
    for (x,y,bw,bh) in white_boxes: dr2.text((x+3,max(0,y-18)),"WHITE PATCH",fill=(0,0,0))
    if photo_box:
        px,py,pw,ph=photo_box; dr2.text((px+4,max(0,py-20)),"PHOTO REGION",fill=(0,0,0))
    return ann


# ═══════════════════════════════════════════════════════════════════════════════
#  SCORING
# ═══════════════════════════════════════════════════════════════════════════════
def compute_final_score(all_findings, word_suspect_count, sensitivity, red_pixel_count=0):
    weights={"critical":20,"warning":8,"info":2}
    mult={"Low":0.75,"Medium":1.0,"High":1.25}[sensitivity]
    ls={}
    for f in all_findings:
        layer=f.get("layer","Other")
        ls[layer]=ls.get(layer,0)+weights.get(f["level"],0)
    capped=sum(min(v,28) for v in ls.values())
    word_pts=min(word_suspect_count*6,25)
    color_pts=(25 if red_pixel_count>=2000 else 18 if red_pixel_count>=1000
               else 8 if red_pixel_count>=200 else 2 if red_pixel_count>=50 else 0)
    return min(int((capped+word_pts+color_pts)*mult),100), ls


# ═══════════════════════════════════════════════════════════════════════════════
#  SIDEBAR
# ═══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown('<div class="sb-title">DocGuard</div>', unsafe_allow_html=True)
    st.markdown('<div class="sb-ver">Document Forensics · v4.2</div>', unsafe_allow_html=True)

    st.markdown('<div class="sb-sec">⚙ Configuration</div>', unsafe_allow_html=True)
    sensitivity = st.select_slider(
        "Detection Sensitivity", options=["Low","Medium","High"], value="Medium",
        help="Higher sensitivity catches more anomalies but may increase false positives"
    )

    st.markdown('<div class="sb-sec">🔬 Active Layers</div>', unsafe_allow_html=True)
    for title, sub in [
        ("Metadata Forensics",  "EXIF · software signatures"),
        ("ELA Analysis",        "Re-compression artifacts"),
        ("Color Anomaly",       "HSV saturation · red pixels"),
        ("Copy-Move SIFT",      "Duplicate region matching"),
        ("Noise Analysis",      "Block-level profile check"),
        ("Photo Swap",          "Noise z-score analysis"),
        ("Font Consistency",    "Edge density variation"),
        ("Word-Level AI",       "Per-word multi-signal"),
        ("White Patch Detect",  "Hidden content overlay"),
        ("OCR · 4 Languages",   "EN · हिंदी · தமிழ் · తెలుగు"),
    ]:
        st.markdown(f"""
        <div class="sb-row">
          <div class="sb-bullet"></div>
          <div>
            <div class="sb-main">{title}</div>
            <div class="sb-sub">{sub}</div>
          </div>
        </div>""", unsafe_allow_html=True)

    st.markdown('<div class="sb-sec">ℹ About</div>', unsafe_allow_html=True)
    st.markdown("""
    <div style="padding:0.6rem 1rem;font-size:0.75rem;font-weight:400;
      color:#9ca3af;line-height:1.6;font-family:'Inter',sans-serif;">
      AI-assisted intelligence tool. All results require final review by a trained analyst.
      <br><br>ThinkRoot × Vortex 2026
    </div>""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
#  HERO
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="hero">
  <div class="hero-kicker">Explainable AI · Document Forensics · 10-Layer Analysis</div>
  <div class="hero-title">Doc<span>Guard</span></div>
  <div class="hero-sub">
    Multi-layer forensic analysis for document authenticity verification.
    Detects tampering at pixel, region, word and metadata levels across
    all pages of PDFs and images.
  </div>
  <div class="tag-strip">
    <span class="tag">PyTorch ResNet-18</span>
    <span class="tag">ELA Forensics</span>
    <span class="tag">Word AI Boxes</span>
    <span class="tag">Color Analysis</span>
    <span class="tag">Copy-Move SIFT</span>
    <span class="tag">Metadata</span>
    <span class="tag">Noise Map</span>
    <span class="tag">White Patch</span>
    <span class="tag">Full PDF Scan</span>
    <span class="tag">4-Language OCR</span>
  </div>
</div>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
#  UPLOAD
# ═══════════════════════════════════════════════════════════════════════════════
uploaded = st.file_uploader(
    "Upload document — PDF (all pages scanned), JPG, PNG, BMP, TIFF",
    type=["pdf","jpg","jpeg","png","bmp","tiff"],
    label_visibility="visible"
)

if not uploaded:
    st.markdown('<div class="shdr">Capabilities</div>', unsafe_allow_html=True)
    c1,c2,c3 = st.columns(3)
    for col,(ic,t,d) in zip([c1,c2,c3],[
        ("🔍","10-Layer Detection",
         "Metadata · ELA · Color · Copy-Move · Noise · Photo Swap · Font · Word AI · White Patch · OCR. Every layer contributes a weighted score."),
        ("🎨","Full Region Highlighting",
         "Suspicious words, ELA hotspots, white patches, and photo anomalies are all highlighted on the document with color-coded severity."),
        ("📄","Explainable Findings",
         "Every flag has a plain-English explanation with layer attribution, designed for non-technical document verification officers."),
    ]):
        col.markdown(f"""
        <div class="feat">
          <div class="feat-ic">{ic}</div>
          <div class="feat-t">{t}</div>
          <div class="feat-d">{d}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown('<div class="shdr">Supported Documents</div>', unsafe_allow_html=True)
    c1,c2,c3,c4 = st.columns(4)
    for col,(ic,lbl) in zip([c1,c2,c3,c4],[
        ("🆔","Aadhaar / PAN"),("🎓","Mark Sheets"),("📁","PDF Reports"),("🖼️","Scanned Images")
    ]):
        col.markdown(f"""
        <div class="g-card" style="text-align:center;padding:1.5rem 1rem;">
          <div style="font-size:1.8rem;margin-bottom:0.8rem;">{ic}</div>
          <div style="font-size:0.85rem;color:var(--text);font-family:'Inter',sans-serif;
            font-weight:600;text-transform:uppercase;letter-spacing:0.05em;">{lbl}</div>
        </div>""", unsafe_allow_html=True)
    st.stop()


# ═══════════════════════════════════════════════════════════════════════════════
#  LOAD
# ═══════════════════════════════════════════════════════════════════════════════
image, raw_bytes, n_pages = load_image(uploaded)
w0, h0 = image.size

col_img, col_meta = st.columns([2, 1])
with col_img:
    st.markdown('<div class="shdr">Uploaded Document</div>', unsafe_allow_html=True)
    if n_pages > 1:
        st.markdown(f'<div class="pbadge">📑 {n_pages} pages — stitched for full analysis</div>',
                    unsafe_allow_html=True)
    st.markdown('<div class="img-frame">', unsafe_allow_html=True)
    st.image(resize_display(image, 860), use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

with col_meta:
    st.markdown('<div class="shdr">File Details</div>', unsafe_allow_html=True)
    for lbl, val in [
        ("Filename",   uploaded.name),
        ("Dimensions", f"{w0} × {h0} px"),
        ("Format",     uploaded.type),
        ("Pages",      str(n_pages)),
        ("Sensitivity",sensitivity),
    ]:
        st.markdown(f"""
        <div class="file-detail">
          <div class="fd-k">{lbl}</div>
          <div class="fd-v">{val}</div>
        </div>""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
#  PIPELINE
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="shdr">Analysis Pipeline</div>', unsafe_allow_html=True)
pbox = st.empty()
STEPS = ["Metadata","ELA + Hotspots","Color Anomaly","Copy-Move",
         "Noise Map","Photo Swap","Font Analysis","Word-Level AI","White Patches","OCR"]

def show_pipe(n):
    items="".join(
        f'<div class="pstep {"ps-done" if i<n else "ps-run" if i==n else "ps-wait"}">'
        f'<span style="font-size:1.1em;">{"✓" if i<n else "⟳" if i==n else "·"}</span><span>{s}</span></div>'
        for i,s in enumerate(STEPS)
    )
    pbox.markdown(f'<div class="pipe">{items}</div>', unsafe_allow_html=True)


# ─── RUN ──────────────────────────────────────────────────────────────────────
all_findings = []

show_pipe(0)
meta_findings, meta_info = analyse_metadata(image, raw_bytes, uploaded.name)
all_findings.extend(meta_findings)

show_pipe(1)
ela_img, ela_score, region_ela, ela_findings, ela_hotspots = run_ela(image)
all_findings.extend(ela_findings)

show_pipe(2)
color_img, red_count, color_findings, color_boxes = detect_color_anomaly(image)
all_findings.extend(color_findings)

show_pipe(3)
cm_img, cm_count, cm_findings = copy_move(image)
all_findings.extend(cm_findings)

show_pipe(4)
nm_img, noise_std, noise_findings = noise_analysis(image)
all_findings.extend(noise_findings)

show_pipe(5)
photo_img, photo_findings, photo_box = detect_photo_swap(image)
all_findings.extend(photo_findings)

show_pipe(6)
font_var, font_findings = font_analysis(image)
all_findings.extend(font_findings)

show_pipe(7)
model = load_model()
quads      = [image.crop((0,0,w0//2,h0//2)), image.crop((w0//2,0,w0,h0//2)),
              image.crop((0,h0//2,w0//2,h0)), image.crop((w0//2,h0//2,w0,h0))]
quad_names = ["Top-Left","Top-Right","Bottom-Left","Bottom-Right"]
dl_scores  = [dl_region_score(q, model) for q in quads]
if max(dl_scores) > 0.78:
    wq = quad_names[dl_scores.index(max(dl_scores))]
    all_findings.append({"level":"warning",
        "title":f"PyTorch anomaly in {wq} quadrant (conf={max(dl_scores):.2f})",
        "detail":f"ResNet-18 found visual inconsistency in {wq}. Content has different deep features from authentic documents.","layer":"DL"})
ela_arr       = np.array(ela_img.convert("L")).astype(np.float32)
word_suspects = get_suspicious_word_boxes(image, ela_arr, sensitivity)

show_pipe(8)
wp_count, wp_boxes, wp_findings = detect_white_patches(image)
all_findings.extend(wp_findings)

show_pipe(9)
ocr_text, ocr_fields = run_ocr(image)
pbox.empty()

annotated   = build_annotated(image, wp_boxes, photo_box, color_boxes, ela_hotspots, word_suspects)
overlay_ela = ela_overlay(image, ela_img)
final_score, layer_scores = compute_final_score(all_findings, len(word_suspects), sensitivity, red_count)


# ═══════════════════════════════════════════════════════════════════════════════
#  VERDICT
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="shdr">Verdict</div>', unsafe_allow_html=True)

if   final_score>=65: vc,vi,vh,vd,sc="verd-forged",    "🚨","HIGH RISK — LIKELY FORGED",    f"Strong forgery indicators across multiple layers. Score: {final_score}% — do NOT accept without thorough manual verification.","#ef4444"
elif final_score>=45: vc,vi,vh,vd,sc="verd-suspicious","⚠", "SUSPICIOUS — NEEDS REVIEW",    f"Multiple anomaly signals detected. Score: {final_score}% — flag for manual inspection.","#f97316"
elif final_score>=20: vc,vi,vh,vd,sc="verd-minor",     "🔍","LOW RISK — MINOR ANOMALIES",   f"Minor irregularities, likely scanning/compression artifacts. Score: {final_score}% — probably genuine.","#eab308"
else:                 vc,vi,vh,vd,sc="verd-genuine",   "✓", "LIKELY GENUINE",               f"No significant forgery indicators found across all 10 layers. Score: {final_score}%","#10b981"

gauge_label=("HIGH RISK" if final_score>=65 else "SUSPICIOUS" if final_score>=45
             else "MINOR ANOMALIES" if final_score>=20 else "GENUINE")

vcol, gcol = st.columns(2)
with vcol:
    st.markdown(f"""
    <div class="verd {vc}">
      <div class="verd-eyebrow" style="color:{sc};">{vi} Forensic Assessment</div>
      <div class="verd-head" style="color:{sc};">{vh}</div>
      <div class="verd-body">{vd}</div>
    </div>""", unsafe_allow_html=True)

with gcol:
    st.markdown(f"""
    <div class="gauge">
      <div class="gauge-top">
        <div>
          <div style="font-family:'Inter',sans-serif;font-weight:500;font-size:0.75rem;
            color:var(--muted);text-transform:uppercase;letter-spacing:0.05em;margin-bottom:4px;">
            Forgery Risk Score
          </div>
          <div class="gauge-label" style="color:{sc};">{gauge_label}</div>
        </div>
        <div class="gauge-num" style="color:{sc};">{final_score}<span class="gauge-pct">%</span></div>
      </div>
      <div class="gauge-bar-bg">
        <div class="gauge-bar" style="width:{final_score}%;
          background:linear-gradient(90deg,#10b981,#eab308,{sc});"></div>
      </div>
      <div class="gauge-ticks">
        <span style="color:#10b981;">0–19 Genuine</span>
        <span style="color:#eab308;">20–44 Minor</span>
        <span style="color:#f97316;">45–64 Suspicious</span>
        <span style="color:#ef4444;">65+ Forged</span>
      </div>
    </div>""", unsafe_allow_html=True)

# ── METRICS ───────────────────────────────────────────────────────────────────
def mvc(v,w,d):
    try:
        n=float(v.replace("%",""))
        return "mv-danger" if n>=d else "mv-warn" if n>=w else "mv-ok"
    except: return "mv-amber"

metrics=[
    ("Risk Score",    f"{final_score}%",      45,  65),
    ("ELA Score",     f"{ela_score:.2f}",      3.5, 6.0),
    ("Copy-Move",     str(cm_count),           20,  45),
    ("Noise Std",     f"{noise_std:.2f}",      13,  20),
    ("Red Pixels",    str(red_count),          50,  200),
    ("Flagged Words", str(len(word_suspects)), 1,   4),
]
cols=st.columns(6)
for col,(lbl,val,wt,dt) in zip(cols,metrics):
    cls=mvc(val,wt,dt) if wt else "mv-amber"
    col.markdown(f"""
    <div class="metric">
      <div class="metric-v {cls}">{val}</div>
      <div class="metric-l">{lbl}</div>
    </div>""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
#  FINDINGS
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="shdr">Detailed Findings</div>', unsafe_allow_html=True)

word_display=[{"level":"critical" if ws["score"]>=12 else "warning",
    "title":f'Suspicious word: "{ws["text"]}" (score={ws["score"]})',
    "detail":f"At {ws['box'][:2]} — signals: {', '.join(ws['reasons'])}",
    "layer":"Word-AI"} for ws in word_suspects]
all_display=all_findings+word_display

if all_display:
    crits=[f for f in all_display if f.get("level")=="critical"]
    warns=[f for f in all_display if f.get("level")=="warning"]
    infos=[f for f in all_display if f.get("level") not in ("critical","warning")]

    def render_f(items, cls, icon):
        for f in items:
            st.markdown(f"""
            <div class="finding {cls}">
              <div style="font-size:1.1rem;flex-shrink:0;margin-top:2px;">{icon}</div>
              <div>
                <div class="f-layer">{f.get('layer','—')}</div>
                <div class="f-title">{f['title']}</div>
                <div class="f-detail">{f['detail']}</div>
              </div>
            </div>""", unsafe_allow_html=True)

    if crits:
        st.markdown(f"""<div style="font-family:'Inter',sans-serif;font-weight:600;font-size:0.75rem;
          color:#ef4444;letter-spacing:0.1em;text-transform:uppercase;margin:0.8rem 0 0.4rem;">
          Critical — {len(crits)} finding(s)</div>""", unsafe_allow_html=True)
        render_f(crits,"fc","🔴")
    if warns:
        st.markdown(f"""<div style="font-family:'Inter',sans-serif;font-weight:600;font-size:0.75rem;
          color:#f97316;letter-spacing:0.1em;text-transform:uppercase;margin:1.2rem 0 0.4rem;">
          Warnings — {len(warns)} finding(s)</div>""", unsafe_allow_html=True)
        render_f(warns,"fw","🟠")
    if infos:
        render_f(infos,"fi","🔵")
else:
    st.markdown("""
    <div class="finding fi" style="border-left-color:var(--green);">
      <div style="font-size:1.2rem;flex-shrink:0;color:var(--green);">✓</div>
      <div>
        <div class="f-title">No suspicious indicators detected</div>
        <div class="f-detail">All 10 forensic layers returned clean results.</div>
      </div>
    </div>""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
#  VISUAL MAPS — all output images capped at 860px width
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="shdr">Forensic Visual Maps</div>', unsafe_allow_html=True)

st.markdown("""
<div class="legend">
  <div class="l-item"><div class="l-dot" style="background:#ef4444;"></div>Red — Suspicious word</div>
  <div class="l-item"><div class="l-dot" style="background:#eab308;"></div>Yellow — White patch</div>
  <div class="l-item"><div class="l-dot" style="background:#f97316;"></div>Orange — Photo anomaly</div>
  <div class="l-item"><div class="l-dot" style="background:#06b6d4;"></div>Cyan — ELA hotspot</div>
  <div class="l-item"><div class="l-dot" style="background:#3b82f6;"></div>Blue — Color anomaly</div>
</div>""", unsafe_allow_html=True)

CAP = "font-family:'Inter',sans-serif;font-size:0.8rem;color:var(--muted);padding:0.6rem 0;"

t1,t2,t3,t4,t5,t6 = st.tabs([
    "All Signals","Color Map","ELA Overlay","Raw ELA","Copy-Move","Noise Map"
])
with t1:
    st.image(resize_display(annotated, 860), use_container_width=False)
    st.markdown(f'<div style="{CAP}">🔴 {len(word_suspects)} word(s) · 🟡 {len(wp_boxes)} white patch(es) · 🔵 {len(ela_hotspots)} ELA hotspot(s) · 🟠 {"1 photo anomaly" if photo_box else "no photo anomaly"}</div>', unsafe_allow_html=True)
with t2:
    st.image(resize_display(color_img, 860), use_container_width=False)
    st.markdown(f'<div style="{CAP}">{red_count} red pixels detected.</div>', unsafe_allow_html=True)
with t3:
    st.image(resize_display(overlay_ela, 860), use_container_width=False)
    st.markdown(f'<div style="{CAP}">ELA heatmap overlay — warm regions indicate compression anomalies from editing.</div>', unsafe_allow_html=True)
with t4:
    st.image(resize_display(ela_img, 860), use_container_width=False)
    st.markdown(f'<div style="{CAP}">Raw ELA — brightness = JPEG re-compression degree at each pixel.</div>', unsafe_allow_html=True)
with t5:
    st.image(resize_display(cm_img, 860), use_container_width=False)
    st.markdown(f'<div style="{CAP}">SIFT copy-move — {cm_count} duplicate feature pairs found.</div>', unsafe_allow_html=True)
with t6:
    st.image(resize_display(nm_img, 860), use_container_width=False)
    st.markdown(f'<div style="{CAP}">Noise map — warm regions = inconsistent pixel sources.</div>', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
#  OCR · METADATA · DL SCORES
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="shdr">OCR · Metadata · AI Scores</div>', unsafe_allow_html=True)
oc, mc, dc = st.columns([2, 1.2, 1.2])

with oc:
    st.markdown("""<div style="font-family:'Inter',sans-serif;font-weight:600;font-size:0.75rem;
      color:#60a5fa;letter-spacing:0.1em;text-transform:uppercase;margin-bottom:0.6rem;">
      OCR Output</div>""", unsafe_allow_html=True)
    with st.expander("Raw extracted text", expanded=False):
        st.text_area("", ocr_text, height=180, label_visibility="collapsed")
        st.caption("Tesseract · English · हिंदी · தமிழ் · తెలుగు")
    if ocr_fields:
        st.markdown("""<div style="font-family:'Inter',sans-serif;font-weight:600;font-size:0.75rem;
          color:#60a5fa;letter-spacing:0.1em;text-transform:uppercase;margin:1rem 0 0.6rem;">
          Detected Fields</div>""", unsafe_allow_html=True)
        for k, v in ocr_fields.items():
            st.markdown(f"""
            <div class="field">
              <div class="field-k">{k}</div>
              <div class="field-v">{v}</div>
            </div>""", unsafe_allow_html=True)
    else:
        st.markdown('<div style="font-size:0.85rem;color:var(--muted);font-family:\'Inter\',sans-serif;">No structured fields auto-detected.</div>', unsafe_allow_html=True)

with mc:
    st.markdown("""<div style="font-family:'Inter',sans-serif;font-weight:600;font-size:0.75rem;
      color:#60a5fa;letter-spacing:0.1em;text-transform:uppercase;margin-bottom:0.6rem;">
      File Metadata</div>""", unsafe_allow_html=True)
    with st.expander("View all metadata", expanded=False):
        for k, v in meta_info.items():
            st.markdown(f"""
            <div class="field">
              <div class="field-k">{k}</div>
              <div class="field-v">{v}</div>
            </div>""", unsafe_allow_html=True)

with dc:
    st.markdown("""<div style="font-family:'Inter',sans-serif;font-weight:600;font-size:0.75rem;
      color:#60a5fa;letter-spacing:0.1em;text-transform:uppercase;margin-bottom:0.6rem;">
      PyTorch Quadrant Scores</div>""", unsafe_allow_html=True)
    for name, sv in zip(quad_names, dl_scores):
        color="#ef4444" if sv>0.78 else "#f97316" if sv>0.60 else "#10b981"
        st.markdown(f"""
        <div class="dl-row">
          <div style="flex:1;">
            <div class="dl-name">{name}</div>
            <div class="dl-bar-bg">
              <div class="dl-bar" style="width:{sv*100:.0f}%;background:{color};"></div>
            </div>
          </div>
          <div class="dl-val" style="color:{color};margin-left:16px;">{sv:.3f}</div>
        </div>""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
#  REPORT DOWNLOAD
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="shdr">Forensic Report</div>', unsafe_allow_html=True)

risk    = "High" if final_score>=65 else "Suspicious" if final_score>=45 else "Low-Minor" if final_score>=20 else "Low"
verdict = "FORGED" if final_score >= 45 else "GENUINE"
word_s  = "\n".join(f"  [{ws['score']}] \"{ws['text']}\" at {ws['box'][:2]} — {', '.join(ws['reasons'])}"
                    for ws in word_suspects) or "  None"

report = f"""DOCGUARD FORENSIC REPORT v4.2
══════════════════════════════════════════════════════════════
File            : {uploaded.name}
Generated       : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Sensitivity     : {sensitivity}
Pages Analysed  : {n_pages}

VERDICT         : {verdict}
SCORE           : {final_score}%
RISK LEVEL      : {risk} Risk

KEY METRICS
───────────────────────────────────────
ELA Score (global)       : {ela_score:.4f}
ELA per region           : {region_ela}
ELA Hotspot Blocks       : {len(ela_hotspots)}
Copy-Move Matches        : {cm_count}
Noise Std Dev            : {noise_std:.4f}
Font Variation           : {font_var:.4f}
Red Pixels (color edit)  : {red_count}
White Patches            : {wp_count}
Suspicious Words         : {len(word_suspects)}
PyTorch DL Scores        : {dict(zip(quad_names, [f"{s:.3f}" for s in dl_scores]))}

SUSPICIOUS WORDS
───────────────────────────────────────
{word_s}

METADATA
───────────────────────────────────────
{chr(10).join(f"  {k}: {v}" for k,v in meta_info.items())}

ALL FINDINGS ({len(all_findings)} total)
───────────────────────────────────────
{chr(10).join(f"[{f.get('level','?').upper()}] [{f.get('layer','?')}] {f['title']}{chr(10)}   → {f['detail']}{chr(10)}" for f in all_findings) or "None detected."}

METHODOLOGY
───────────────────────────────────────
1.  Metadata    — EXIF, editing software signatures in raw bytes
2.  ELA         — JPEG re-compression artifact detection (global + per-region + hotspot)
3.  Color       — HSV saturation outlier + red pixel isolation with bounding boxes
4.  Copy-Move   — SIFT keypoint duplicate region matching
5.  Noise       — Block-level noise profile inconsistency
6.  Photo Swap  — Noise z-score contrast for pasted photos
7.  Font        — Text edge density variation across document strips
8.  Word-AI     — Per-word ELA + saturation + LAB color + brightness + sharpness
9.  White Patch — Bright overlay rectangle detection (hidden content)
10. OCR         — Tesseract multi-language (English, Hindi, Tamil, Telugu)

DISCLAIMER
───────────────────────────────────────
AI-assisted tool. All findings require review by a trained human verifier.
DocGuard v4.2 — ThinkRoot × Vortex 2026
"""

btn_col, _ = st.columns([1, 2])
with btn_col:
    st.download_button(
        "📥  Download Forensic Report (.txt)",
        data=report,
        file_name=f"DocGuard_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
        mime="text/plain",
        use_container_width=True
    )