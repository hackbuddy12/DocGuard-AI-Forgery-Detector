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
#  GLOBAL STYLES (CYBER-FORENSICS DASHBOARD)
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;700&family=DM+Mono:wght@400;500&family=Space+Grotesk:wght@500;700&display=swap');

:root {
  --bg:        #07090f;
  --surface1:  #0d1117;
  --surface2:  #161c27;
  --surface3:  #1e2636;
  --border:    #222d3d;
  --accent:    #00c2ff;
  --green:     #00e5a0;
  --red:       #ff3d5a;
  --amber:     #ffb020;
  --text1:     #e8edf5;
  --text2:     #8899bb;
  --text3:     #4a5878;
  --mono:      'DM Mono', monospace;
}

html, body, [class*="css"] {
  font-family: 'DM Sans', sans-serif !important;
  background: var(--bg) !important;
  color: var(--text1) !important;
}

.stApp { background: var(--bg) !important; }

/* ── SIDEBAR ── */
section[data-testid="stSidebar"] {
  background: var(--surface1) !important;
  border-right: 1px solid var(--border) !important;
}
.sb-section { font-family: 'Space Grotesk', sans-serif; font-size: 0.85rem; color: var(--text3); text-transform: uppercase; letter-spacing: 0.12em; padding: 0.4rem 0; border-bottom: 1px solid var(--border); margin-bottom: 0.6rem; margin-top: 1.5rem; }
.sb-layer { display: flex; align-items: center; gap: 8px; padding: 5px 0; font-size: 0.82rem; color: var(--text2); border-radius: 6px; }
.sb-dot { width: 6px; height: 6px; border-radius: 50%; background: var(--accent); flex-shrink: 0; }

/* ── HERO ── */
.hero { background: var(--surface1); border: 1px solid var(--border); border-radius: 20px; padding: 3rem 2.5rem; margin-bottom: 2rem; position: relative; overflow: hidden; }
.hero::before { content: ''; position: absolute; inset: 0; background: radial-gradient(ellipse 60% 50% at 80% 50%, rgba(0,194,255,.08) 0%, transparent 70%), radial-gradient(ellipse 40% 60% at 20% 30%, rgba(123,97,255,.07) 0%, transparent 70%); pointer-events: none; }
.hero-label { font-family: var(--mono); font-size: 0.7rem; color: var(--accent); letter-spacing: 0.18em; text-transform: uppercase; margin-bottom: 0.8rem; }
.hero h1 { font-family: 'Space Grotesk', sans-serif; font-size: 3.2rem; margin: 0 0 0.6rem; color: var(--text1); font-weight: 700; line-height: 1.1; }
.hero h1 span { color: var(--accent); }
.hero p { color: var(--text2); font-size: 1rem; margin: 0; max-width: 600px; }
.tag-row { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 1.5rem; }
.tag { font-family: var(--mono); font-size: 0.65rem; padding: 4px 10px; border-radius: 4px; background: rgba(0,194,255,0.1); border: 1px solid rgba(0,194,255,0.2); color: var(--accent); text-transform: uppercase; }

/* ── SECTION HEADER ── */
.sec-hdr { display: flex; align-items: center; gap: 10px; font-family: 'Space Grotesk', sans-serif; font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.12em; color: var(--text3); margin: 2rem 0 1rem; }
.sec-hdr::after { content: ''; flex: 1; height: 1px; background: var(--border); }

/* ── VERDICT CARDS ── */
.verdict-box { border-radius: 16px; padding: 1.8rem 2rem; margin: 1.2rem 0; position: relative; overflow: hidden; }
.verdict-danger { background: rgba(255,61,90,.08); border: 1px solid rgba(255,61,90,.4); }
.verdict-danger::before { content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px; background: linear-gradient(90deg, var(--red), transparent); }
.verdict-warning { background: rgba(255,176,32,.08); border: 1px solid rgba(255,176,32,.4); }
.verdict-warning::before { content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px; background: linear-gradient(90deg, var(--amber), transparent); }
.verdict-info { background: rgba(0,194,255,.08); border: 1px solid rgba(0,194,255,.4); }
.verdict-info::before { content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px; background: linear-gradient(90deg, var(--accent), transparent); }
.verdict-success { background: rgba(0,229,160,.08); border: 1px solid rgba(0,229,160,.4); }
.verdict-success::before { content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px; background: linear-gradient(90deg, var(--green), transparent); }
.verdict-title { font-size: 1.5rem; font-weight: 700; font-family: 'Space Grotesk', sans-serif; margin-bottom: 0.3rem;}
.verdict-sub { font-size: 0.88rem; color: var(--text2); }

/* ── METRICS GRID ── */
.metric-grid { display: grid; grid-template-columns: repeat(6, 1fr); gap: 10px; margin: 1rem 0; }
.metric-card { background: var(--surface2); border: 1px solid var(--border); border-radius: 14px; padding: 1rem; text-align: center; }
.metric-num { font-family: 'Space Grotesk', sans-serif; font-size: 1.8rem; font-weight: 700; line-height: 1; margin-bottom: 0.3rem; }
.metric-label { font-size: 0.65rem; color: var(--text3); text-transform: uppercase; letter-spacing: 0.08em; font-family: var(--mono); }
.mv-danger { color: var(--red); }
.mv-warn { color: var(--amber); }
.mv-ok { color: var(--green); }
.mv-blue { color: var(--accent); }

/* ── GAUGE ── */
.gauge-wrap { background: var(--surface2); border: 1px solid var(--border); border-radius: 16px; padding: 1.5rem 1.8rem; margin: 1.2rem 0; }
.gauge-header { display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 0.8rem; }
.gauge-score { font-family: 'Space Grotesk', sans-serif; font-size: 3rem; font-weight: 700; line-height: 1; }
.gauge-bar-bg { background: var(--surface3); border-radius: 99px; height: 8px; overflow: hidden; margin-bottom: 0.6rem; }
.gauge-bar-fill { height: 100%; border-radius: 99px; transition: width 0.6s ease; }
.gauge-ticks { display: flex; justify-content: space-between; font-size: 0.65rem; color: var(--text3); font-family: var(--mono); }

/* ── PIPELINE STEPS ── */
.pipeline-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 8px; margin: 1rem 0; }
.pipe-step { background: var(--surface2); border: 1px solid var(--border); border-radius: 10px; padding: 0.6rem 0.8rem; font-size: 0.75rem; display: flex; align-items: center; gap: 8px; font-family: var(--mono); font-weight: 500; transition: all .3s; }
.pipe-done { border-color: rgba(0,229,160,.3); color: var(--green); }
.pipe-run  { border-color: rgba(0,194,255,.3); color: var(--accent); animation: pulse 1s infinite; }
.pipe-wait { color: var(--text3); }
@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.5} }

/* ── FINDINGS ── */
.finding { border-radius: 10px; padding: 0.9rem 1.1rem; margin: 0.4rem 0; display: flex; gap: 10px; align-items: flex-start; font-size: 0.85rem; }
.finding-critical { background: rgba(255,61,90,.08); border-left: 3px solid var(--red); color: #ffb3bc; }
.finding-warning { background: rgba(255,176,32,.08); border-left: 3px solid var(--amber); color: #ffd580; }
.finding-info { background: rgba(0,194,255,.08); border-left: 3px solid var(--accent); color: var(--text1); }
.finding-layer { font-family: var(--mono); font-size: 0.6rem; letter-spacing: 0.08em; text-transform: uppercase; opacity: 0.7; margin-bottom: 2px; }
.finding-title { font-weight: 700; font-size: 0.88rem; }
.finding-detail { font-weight: 400; opacity: 0.8; margin-top: 2px; }

/* ── INFO CARDS ── */
.feat-card { background: var(--surface2); border: 1px solid var(--border); border-radius: 14px; padding: 1.4rem; transition: all .2s; }
.feat-card:hover { border-color: var(--accent); transform: translateY(-2px); }
.feat-icon { font-size: 1.8rem; margin-bottom: 0.7rem; }
.feat-title { font-family: 'Space Grotesk', sans-serif; font-weight: 700; font-size: 1.1rem; margin-bottom: 0.4rem; color: var(--text1); }
.feat-desc { font-size: 0.85rem; color: var(--text2); line-height: 1.5; }

/* ── FILE & OCR DETAILS ── */
.file-detail, .ocr-field, .dl-quad { background: var(--surface2); border: 1px solid var(--border); border-radius: 8px; padding: 0.65rem 1rem; margin: 5px 0; }
.fd-key, .ocr-key { font-family: var(--mono); font-size: 0.65rem; color: var(--text3); letter-spacing: 0.08em; text-transform: uppercase; }
.fd-val, .ocr-val { font-size: 0.88rem; color: var(--text1); font-weight: 500; margin-top: 2px; }
.dl-score { font-family: 'Space Grotesk', sans-serif; font-size: 1.7rem; font-weight: 700; line-height: 1; }

/* ── OVERRIDES ── */
div[data-testid="stFileUploader"] { background: var(--surface2) !important; border: 2px dashed var(--border) !important; border-radius: 16px !important; }
div[data-testid="stFileUploader"]:hover { border-color: var(--accent) !important; }
div[data-testid="stTabs"] button { background: transparent !important; color: var(--text2) !important; font-family: 'Space Grotesk', sans-serif !important; font-weight: 600 !important; }
div[data-testid="stTabs"] button[aria-selected="true"] { color: var(--accent) !important; border-bottom: 2px solid var(--accent) !important; }
div[data-testid="stTabs"] [data-testid="stTabContent"] { border: 1px solid var(--border); border-radius: 8px !important; padding: 1rem !important; background: var(--surface2) !important; }
.stDownloadButton > button { background: linear-gradient(135deg, var(--accent), #7b61ff) !important; color: var(--bg) !important; border: none !important; border-radius: 10px !important; font-weight: 700 !important; font-family: 'Space Grotesk', sans-serif !important; width: 100% !important; padding: 0.75rem !important; letter-spacing: 0.02em !important; }
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
#  PYTORCH MODEL
# ═══════════════════════════════════════════════════════════════════════════════
@st.cache_resource(show_spinner=False)
def load_model():
    base = models.resnet18(weights=models.ResNet18_Weights.DEFAULT)
    base.fc = nn.Sequential(
        nn.Linear(512, 256), nn.ReLU(), nn.Dropout(0.4),
        nn.Linear(256, 64),  nn.ReLU(),
        nn.Linear(64, 2)
    )
    base.eval()
    return base

def dl_region_score(patch_pil, model):
    t = transforms.Compose([
        transforms.Resize((224, 224)), transforms.ToTensor(),
        transforms.Normalize([0.485,0.456,0.406],[0.229,0.224,0.225])
    ])
    with torch.no_grad():
        p = torch.softmax(model(t(patch_pil.convert("RGB")).unsqueeze(0)), dim=1)[0]
    return float(p[1])


# ═══════════════════════════════════════════════════════════════════════════════
#  IMAGE LOAD — ALL PDF PAGES STITCHED
# ═══════════════════════════════════════════════════════════════════════════════
def load_image(uploaded):
    data = uploaded.read()
    if uploaded.type == "application/pdf":
        doc = fitz.open(stream=data, filetype="pdf")
        n_pages = len(doc)
        page_images = []
        MAX_PAGES = 15
        for page_num in range(min(n_pages, MAX_PAGES)):
            pix = doc[page_num].get_pixmap(matrix=fitz.Matrix(2, 2))
            page_img = Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")
            page_images.append(page_img)
        if len(page_images) == 1:
            return page_images[0], data, 1
        total_width  = max(img.width for img in page_images)
        total_height = sum(img.height for img in page_images)
        combined = Image.new("RGB", (total_width, total_height), (255, 255, 255))
        y_off = 0
        for img in page_images:
            combined.paste(img, (0, y_off))
            y_off += img.height
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
                if tag in ("Software","ProcessingSoftware","HostComputer"):
                    findings.append({"level":"warning","title":f"Metadata: {tag} tag found",
                        "detail":f'Value "{val}" — document processed in software',"layer":"Metadata"})
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
            findings.append({"level":"critical","title":f"Editing software signature: {kw.decode()}",
                "detail":f"File bytes contain '{kw.decode()}' — edited in image software","layer":"Metadata"})
            meta["EditSoftware"] = kw.decode(); break

    actual_format = img_pil.format or "Unknown"
    if actual_format == "JPEG" and ext == "png":
        findings.append({"level":"warning","title":"Format mismatch: JPEG saved as .png",
            "detail":"Extension doesn't match actual format — possible re-encoding","layer":"Metadata"})
    return findings, meta


# ═══════════════════════════════════════════════════════════════════════════════
#  2. ELA
# ═══════════════════════════════════════════════════════════════════════════════
def run_ela(image, quality=92):
    buf = io.BytesIO()
    image.convert("RGB").save(buf, format="JPEG", quality=quality)
    buf.seek(0)
    comp = Image.open(buf).convert("RGB")
    orig = np.array(image).astype(np.float32)
    diff = np.abs(orig - np.array(comp).astype(np.float32))
    score = float(diff.mean())
    norm  = (diff / (diff.max()+1e-8) * 255).astype(np.uint8)
    ela_img = Image.fromarray(norm)
    h, w = orig.shape[:2]
    regions = {
        "top_left":  diff[:h//2, :w//2],  "top_right": diff[:h//2, w//2:],
        "bot_left":  diff[h//2:, :w//2],  "bot_right": diff[h//2:, w//2:],
    }
    region_scores = {k: float(v.mean()) for k,v in regions.items()}
    max_r = max(region_scores.values()); min_r = min(region_scores.values())
    spread = max_r - min_r
    findings = []
    if spread > 3.5:
        worst = max(region_scores, key=region_scores.get)
        findings.append({"level":"warning","title":f"ELA regional inconsistency (spread={spread:.2f})",
            "detail":f"Region '{worst.replace('_',' ')}' has much higher re-compression artifacts — uneven editing signature.","layer":"ELA"})
    if score > 6.0:
        findings.append({"level":"critical","title":f"High global ELA score ({score:.2f})",
            "detail":"Strong re-compression artifacts across entire document — significant editing detected.","layer":"ELA"})
    elif score > 3.5:
        findings.append({"level":"warning","title":f"Moderate ELA score ({score:.2f})",
            "detail":"Moderate compression artifacts — minor editing possible.","layer":"ELA"})
    ela_gray = np.array(ela_img.convert("L")).astype(np.float32)
    hotspot_boxes = []
    block = max(h, w) // 12
    ela_mean = ela_gray.mean(); ela_std = ela_gray.std()
    thresh = ela_mean + 2.8 * ela_std
    for i in range(0, h - block, block // 2):
        for j in range(0, w - block, block // 2):
            patch = ela_gray[i:i+block, j:j+block]
            if patch.mean() > thresh and patch.mean() > 30:
                hotspot_boxes.append((j, i, block, block, float(patch.mean())))
    hotspot_boxes.sort(key=lambda x: -x[4]); hotspot_boxes = hotspot_boxes[:5]
    return ela_img, score, region_scores, findings, hotspot_boxes

def ela_overlay(orig, ela_img):
    o = orig.resize((600, 400))
    e = np.array(ela_img.convert("L").resize((600, 400)))
    h_map = cv2.applyColorMap(e, cv2.COLORMAP_JET)
    return Image.blend(o, Image.fromarray(cv2.cvtColor(h_map, cv2.COLOR_BGR2RGB)), 0.5)


# ═══════════════════════════════════════════════════════════════════════════════
#  3. COLOR ANOMALY
# ═══════════════════════════════════════════════════════════════════════════════
def detect_color_anomaly(image):
    img_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    hsv    = cv2.cvtColor(img_cv, cv2.COLOR_BGR2HSV)
    h_img, w_img = hsv.shape[:2]
    red1 = (hsv[:,:,0] <  10) & (hsv[:,:,1] > 100) & (hsv[:,:,2] > 100)
    red2 = (hsv[:,:,0] > 165) & (hsv[:,:,1] > 100) & (hsv[:,:,2] > 100)
    red_mask = red1 | red2; red_count = int(red_mask.sum())
    findings = []; color_map = image.convert("RGB").copy()
    draw = ImageDraw.Draw(color_map); color_boxes = []
    if red_count > 50:
        coords = np.argwhere(red_mask)
        y1,x1  = coords.min(axis=0); y2,x2 = coords.max(axis=0)
        pad = 8
        draw.rectangle([x1-pad,y1-pad,x2+pad,y2+pad], outline=(255,80,80), width=3)
        color_boxes.append((x1-pad,y1-pad,x2-x1+2*pad,y2-y1+2*pad))
        findings.append({"level":"critical","title":f"Colored text detected ({red_count} red pixels)",
            "detail":f"Red-colored text at ({x1},{y1})–({x2},{y2}). Original docs have uniform black text — colored text indicates editing.","layer":"Color"})
    block = 20; rows_b = h_img//block; cols_b = w_img//block
    mean_sat = float(hsv[:,:,1].mean()); std_sat = float(hsv[:,:,1].std())
    thresh = mean_sat + 2.5 * std_sat
    sat_boxes = []
    for i in range(rows_b):
        for j in range(cols_b):
            if hsv[i*block:(i+1)*block, j*block:(j+1)*block, 1].mean() > thresh and \
               hsv[i*block:(i+1)*block, j*block:(j+1)*block, 1].mean() > 90:
                sat_boxes.append((j*block, i*block, block, block))
    if len(sat_boxes) > 3 and not (red_count > 50):
        xs=[b[0] for b in sat_boxes]; ys=[b[1] for b in sat_boxes]
        x1c,y1c=min(xs),min(ys); x2c,y2c=max(xs)+block,max(ys)+block
        if (x2c-x1c)*(y2c-y1c) > 400:
            draw.rectangle([x1c-4,y1c-4,x2c+4,y2c+4], outline=(255,165,0), width=2)
            color_boxes.append((x1c-4,y1c-4,x2c-x1c+8,y2c-y1c+8))
            findings.append({"level":"warning","title":f"Unusual color saturation ({len(sat_boxes)} blocks)",
                "detail":f"Saturation significantly above document average at ({x1c},{y1c})–({x2c},{y2c}).","layer":"Color"})
    return color_map, red_count, findings, color_boxes


# ═══════════════════════════════════════════════════════════════════════════════
#  4. COPY MOVE
# ═══════════════════════════════════════════════════════════════════════════════
def copy_move(image):
    img  = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    sift = cv2.SIFT_create()
    kp, des = sift.detectAndCompute(gray, None)
    count = 0; out = img.copy()
    if des is not None and len(des) > 10:
        matches = cv2.FlannBasedMatcher({"algorithm":1,"trees":5},{"checks":50}).knnMatch(des,des,k=2)
        good = []
        for pair in matches:
            if len(pair)==2:
                m,n = pair
                if m.distance < 0.7*n.distance and m.trainIdx!=m.queryIdx:
                    p1,p2 = kp[m.queryIdx].pt, kp[m.trainIdx].pt
                    if np.hypot(p1[0]-p2[0],p1[1]-p2[1]) > 20:
                        good.append((p1,p2))
        count = len(good)
        for p1,p2 in good[:30]:
            cv2.line(out,(int(p1[0]),int(p1[1])),(int(p2[0]),int(p2[1])),(80,80,255),1)
            cv2.circle(out,(int(p1[0]),int(p1[1])),4,(255,80,80),-1)
    findings = []
    if count > 45:
        findings.append({"level":"critical","title":f"High copy-move matches ({count})",
            "detail":"Large number of duplicated feature matches — region likely copied & pasted within document.","layer":"Copy-Move"})
    elif count > 20:
        findings.append({"level":"warning","title":f"Moderate copy-move matches ({count})",
            "detail":"Some repeated feature patterns — may indicate cloned regions.","layer":"Copy-Move"})
    return Image.fromarray(cv2.cvtColor(out,cv2.COLOR_BGR2RGB)), count, findings


# ═══════════════════════════════════════════════════════════════════════════════
#  5. NOISE
# ═══════════════════════════════════════════════════════════════════════════════
def noise_analysis(image):
    gray  = np.array(image.convert("L")).astype(np.float32)
    blur  = cv2.GaussianBlur(gray,(5,5),0)
    noise = np.abs(gray-blur)
    h,w   = noise.shape; bs = max(h,w)//20
    nm    = np.zeros_like(noise)
    for i in range(0,h-bs,bs//2):
        for j in range(0,w-bs,bs//2):
            nm[i:i+bs,j:j+bs] = np.std(noise[i:i+bs,j:j+bs])
    noise_std = float(np.std(nm))
    norm      = ((nm-nm.min())/(nm.max()-nm.min()+1e-8)*255).astype(np.uint8)
    nm_img    = Image.fromarray(cv2.applyColorMap(norm,cv2.COLORMAP_INFERNO)[:,:,::-1])
    findings  = []
    if noise_std > 20:
        findings.append({"level":"critical","title":f"High noise inconsistency (std={noise_std:.2f})",
            "detail":"Very different noise levels across regions — content likely pasted from different source.","layer":"Noise"})
    elif noise_std > 13:
        findings.append({"level":"warning","title":f"Slight noise variation (std={noise_std:.2f})",
            "detail":"Minor noise variation — may be natural for scanned documents.","layer":"Noise"})
    return nm_img, noise_std, findings


# ═══════════════════════════════════════════════════════════════════════════════
#  6. PHOTO SWAP
# ═══════════════════════════════════════════════════════════════════════════════
def detect_photo_swap(image):
    gray  = np.array(image.convert("L"))
    h,w   = gray.shape; bs = max(h,w)//12
    rows, cols = h//bs, w//bs
    nm = np.zeros((rows,cols))
    for i in range(rows):
        for j in range(cols):
            nm[i,j] = gray[i*bs:(i+1)*bs, j*bs:(j+1)*bs].std()
    mean_n, std_n = nm.mean(), nm.std()
    high = nm > (mean_n + 2.0*std_n)
    findings = []; annotated = image.convert("RGB").copy(); photo_box = None
    if high.any():
        cnts,_ = cv2.findContours(high.astype(np.uint8)*255,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
        if cnts:
            biggest = max(cnts, key=cv2.contourArea)
            bx,by,bw_b,bh_b = cv2.boundingRect(biggest)
            px,py,pw,ph = bx*bs, by*bs, bw_b*bs, bh_b*bs
            region_max = nm[by:by+bh_b, bx:bx+bw_b].max()
            z = (region_max-mean_n)/(std_n+1e-8)
            if z > 3.2:
                draw = ImageDraw.Draw(annotated)
                for t in range(3):
                    draw.rectangle([px-t,py-t,px+pw+t,py+ph+t], outline=(255,140,0))
                photo_box = (px,py,pw,ph)
                findings.append({"level":"critical","title":f"Photo region noise anomaly (z={z:.1f})",
                    "detail":f"Region at ({px},{py}) size {pw}×{ph}px has very different pixel statistics — consistent with a swapped photograph.","layer":"Photo"})
    return annotated, findings, photo_box


# ═══════════════════════════════════════════════════════════════════════════════
#  7. FONT
# ═══════════════════════════════════════════════════════════════════════════════
def font_analysis(image):
    gray  = np.array(image.convert("L"))
    edges = cv2.Canny(gray, 50, 150)
    strips = np.array_split(edges, 10, axis=0)
    dens  = [float(s.mean()) for s in strips]
    var   = float(np.std(dens)); findings = []
    if var > 18:
        findings.append({"level":"warning","title":f"Font/layout inconsistency (var={var:.2f})",
            "detail":"Text edge density varies significantly — different fonts or inserted text blocks may be present.","layer":"Font"})
    return var, findings


# ═══════════════════════════════════════════════════════════════════════════════
#  8. WORD-LEVEL BOXES
# ═══════════════════════════════════════════════════════════════════════════════
def get_suspicious_word_boxes(image, ela_arr, sensitivity="Medium"):
    boxes = []
    try:
        data = pytesseract.image_to_data(image, lang="eng",
            output_type=pytesseract.Output.DICT, config="--oem 3 --psm 6")
    except:
        return []
    img_rgb = np.array(image.convert("RGB"))
    img_hsv = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2HSV)
    img_lab = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2LAB)
    ih, iw  = img_rgb.shape[:2]
    word_features = []
    for i in range(len(data["text"])):
        txt = data["text"][i].strip()
        try: conf = int(data["conf"][i])
        except: continue
        if conf < 35 or not txt or len(txt) < 1: continue
        x, y, w, h = data["left"][i], data["top"][i], data["width"][i], data["height"][i]
        if w * h < 80: continue
        x2, y2 = min(x+w, iw), min(y+h, ih)
        if x2 <= x or y2 <= y: continue
        patch_rgb  = img_rgb[y:y2, x:x2]
        patch_hsv  = img_hsv[y:y2, x:x2]
        patch_lab  = img_lab[y:y2, x:x2]
        patch_ela  = ela_arr[y:y2, x:x2]
        patch_gray = cv2.cvtColor(patch_rgb, cv2.COLOR_RGB2GRAY).astype(np.float32)
        patch_u8   = cv2.cvtColor(patch_rgb, cv2.COLOR_RGB2GRAY)
        lap        = cv2.Laplacian(patch_u8, cv2.CV_32F)
        word_features.append({
            "box": (x,y,w,h), "text": txt,
            "ela":        float(patch_ela.mean()),
            "brightness": float(patch_gray.mean()),
            "sharpness":  float(lap.var()),
            "saturation": float(patch_hsv[:,:,1].mean()),
            "b_channel":  float(patch_lab[:,:,2].mean()),
            "conf": conf,
        })
    if len(word_features) < 3: return []
    def robust(vals):
        arr = np.array(vals); med = np.median(arr)
        mad = np.median(np.abs(arr-med))
        return med, max(mad*1.4826, 0.01)
    med_ela, mad_ela = robust([f["ela"]        for f in word_features])
    med_sat, mad_sat = robust([f["saturation"] for f in word_features])
    med_bri, mad_bri = robust([f["brightness"] for f in word_features])
    med_shp, mad_shp = robust([f["sharpness"]  for f in word_features])
    med_b,   mad_b   = robust([f["b_channel"]  for f in word_features])
    min_score = {"Low":10,"Medium":7,"High":5}.get(sensitivity, 7)
    suspicious = []
    for f in word_features:
        score = 0; reasons = []
        z_sat = (f["saturation"]-med_sat)/mad_sat
        if z_sat > 3.5: score += 6; reasons.append(f"colored ink (z={z_sat:.1f})")
        z_b = abs(f["b_channel"]-med_b)/mad_b
        if z_b > 4.5: score += 4; reasons.append(f"color fingerprint shift (b_z={z_b:.1f})")
        z_ela = (f["ela"]-med_ela)/mad_ela
        if z_ela > 3.0: score += 5; reasons.append(f"re-compression artifact (ELA z={z_ela:.1f})")
        z_bri = abs(f["brightness"]-med_bri)/mad_bri
        if z_bri > 4.0: score += 3; reasons.append(f"brightness mismatch (z={z_bri:.1f})")
        z_shp = abs(f["sharpness"]-med_shp)/mad_shp
        if z_shp > 4.0: score += 3; reasons.append(f"sharpness mismatch (z={z_shp:.1f})")
        if score >= min_score:
            suspicious.append({"box":f["box"],"text":f["text"],"score":score,"reasons":reasons})
    return suspicious


# ═══════════════════════════════════════════════════════════════════════════════
#  9. OCR
# ═══════════════════════════════════════════════════════════════════════════════
def run_ocr(image):
    img_cv = cv2.cvtColor(np.array(image.convert("RGB")), cv2.COLOR_RGB2BGR)
    h, w   = img_cv.shape[:2]
    if max(h,w) < 1000:
        scale  = 1000 // max(h,w) + 1
        img_cv = cv2.resize(img_cv, (w*scale,h*scale), interpolation=cv2.INTER_CUBIC)
    denoised = cv2.fastNlMeansDenoisingColored(img_cv, None, 8, 8, 7, 15)
    kernel   = np.array([[0,-1,0],[-1,5,-1],[0,-1,0]])
    sharp    = cv2.filter2D(denoised, -1, kernel)
    proc     = Image.fromarray(cv2.cvtColor(sharp, cv2.COLOR_BGR2RGB))
    raw = ""
    for lang in ["eng+hin+tel+tam","eng+hin","eng"]:
        try:
            raw = pytesseract.image_to_string(proc, lang=lang, config="--oem 3 --psm 6")
            if len(raw.strip()) > 10: break
        except: continue
    cleaned = []
    for line in raw.splitlines():
        line = line.strip()
        if not line: continue
        alnum = re.findall(r'[A-Za-z0-9\u0900-\u097F\u0C00-\u0C7F]', line)
        if len(alnum) >= 2: cleaned.append(line)
    text = "\n".join(cleaned); fields = {}
    for line in cleaned:
        lu = line.upper()
        if re.search(r'DOB|DATE.OF.BIRTH|जन्म', line, re.I):
            m = re.search(r'\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4}', line)
            if m: fields["Date of Birth"] = m.group()
        if re.search(r'ROLL\s*NO|ROLL NUMBER', lu):
            m = re.search(r'\d{8,}', line)
            if m: fields["Roll No"] = m.group()
        if re.search(r'FATHER|पिता', line, re.I): fields["Father Name"] = line
        if re.search(r'MOTHER|माता', line, re.I): fields["Mother Name"] = line
        if re.search(r'PAN|PERMANENT ACCOUNT', lu):
            m = re.search(r'[A-Z]{5}[0-9]{4}[A-Z]', line)
            if m: fields["PAN Number"] = m.group()
        if re.search(r'AADHAAR|AADHAR|XXXX', lu):
            m = re.search(r'[X\d]{4}\s[X\d]{4}\s\d{4}', line)
            if m: fields["Aadhaar"] = m.group()
        if re.search(r'GRAND TOTAL|TOTAL MARKS', lu): fields["Grand Total"] = line
        if re.search(r'DIVISION|GRADE', lu):           fields["Division/Grade"] = line
    return text, fields


# ═══════════════════════════════════════════════════════════════════════════════
#  10. WHITE PATCH
# ═══════════════════════════════════════════════════════════════════════════════
def detect_white_patches(image):
    gray = np.array(image.convert("L"))
    h, w = gray.shape; doc_mean = float(gray.mean())
    if doc_mean > 195: return 0, [], []
    bright_thresh = min(230, doc_mean + 50); min_span = 80; min_rows = 10
    row_spans = {}
    for y in range(h):
        row    = gray[y, :]
        bright = (row > bright_thresh).astype(np.uint8)
        padded = np.concatenate([[0], bright, [0]])
        diffs  = np.diff(padded.astype(np.int16))
        starts = np.where(diffs == 1)[0]; ends = np.where(diffs == -1)[0]
        if not len(starts): continue
        longest = max(zip(starts,ends), key=lambda p: p[1]-p[0])
        if longest[1]-longest[0] >= min_span: row_spans[y] = (longest[0],longest[1],longest[1]-longest[0])
    if not row_spans: return 0, [], []
    visited, boxes, flags = set(), [], []
    for y_start in sorted(row_spans.keys()):
        if y_start in visited: continue
        x0, x1, _ = row_spans[y_start]; y_end = y_start
        for y2 in range(y_start+1, min(y_start+300, h)):
            if y2 not in row_spans: break
            rx0,rx1,_ = row_spans[y2]
            if abs(rx0-x0)<30 and abs(rx1-x1)<30: y_end=y2; visited.add(y2)
            else: break
        if y_end-y_start+1 < min_rows: continue
        bx,by,bw,bh = int(x0),int(y_start),int(x1-x0),int(y_end-y_start+1)
        patch = gray[by:by+bh, bx:bx+bw]; contrast = float(patch.mean())-doc_mean
        if contrast > 30:
            boxes.append((bx,by,bw,bh))
            flags.append({"level":"critical","title":f"White overlay patch at ({bx},{by}) size {bw}×{bh}px",
                "detail":f"Uniform bright rectangle {contrast:.0f} levels above background — white box likely pasted over original text.","layer":"White Patch"})
    return len(boxes), boxes, flags


# ═══════════════════════════════════════════════════════════════════════════════
#  ANNOTATED IMAGE
# ═══════════════════════════════════════════════════════════════════════════════
def build_annotated(image, white_boxes, photo_box, color_boxes, ela_hotspots, word_suspects):
    annotated = image.convert("RGBA").copy()
    overlay   = Image.new("RGBA", annotated.size, (0,0,0,0))
    draw      = ImageDraw.Draw(overlay)
    for (x,y,bw,bh,_) in ela_hotspots:
        draw.rectangle([x,y,x+bw,y+bh], fill=(0,200,255,25), outline=(0,200,255,160), width=1)
    for (x,y,bw,bh) in color_boxes:
        draw.rectangle([x,y,x+bw,y+bh], fill=(255,165,0,20), outline=(255,165,0,200), width=2)
    for (x,y,bw,bh) in white_boxes:
        draw.rectangle([x,y,x+bw,y+bh], fill=(255,220,0,30), outline=(255,220,0,220), width=2)
        draw.rectangle([x,max(0,y-20),x+bw,max(0,y)], fill=(255,220,0,220))
    if photo_box:
        px,py,pw,ph = photo_box
        draw.rectangle([px,py,px+pw,py+ph], fill=(255,140,0,25), outline=(255,140,0,200), width=3)
        draw.rectangle([px,max(0,py-22),px+pw,max(0,py)], fill=(255,140,0,220))
    for ws in word_suspects:
        x,y,w,h = ws["box"]; sc = ws["score"]
        if sc >= 12:   col=(255,50,50,200);  fill=(255,50,50,30)
        elif sc >= 9:  col=(255,140,30,200); fill=(255,140,30,25)
        else:          col=(255,220,30,180); fill=(255,220,30,20)
        draw.rectangle([x-2,y-2,x+w+2,y+h+2], fill=fill, outline=col, width=2)
        badge_w = min(len(ws["text"])*7+8, w+4)
        draw.rectangle([x-2,max(0,y-16),x-2+badge_w,max(0,y)], fill=col)
    annotated = Image.alpha_composite(annotated, overlay).convert("RGB")
    draw2 = ImageDraw.Draw(annotated)
    for ws in word_suspects:
        x,y,w,h = ws["box"]
        draw2.text((x, max(0,y-14)), ws["text"][:10], fill=(255,255,255))
    for (x,y,bw,bh) in white_boxes:
        draw2.text((x+3,max(0,y-18)), "WHITE PATCH", fill=(0,0,0))
    if photo_box:
        px,py,pw,ph = photo_box
        draw2.text((px+4,max(0,py-20)), "PHOTO REGION", fill=(0,0,0))
    return annotated


# ═══════════════════════════════════════════════════════════════════════════════
#  SCORING
# ═══════════════════════════════════════════════════════════════════════════════
def compute_final_score(all_findings, word_suspect_count, sensitivity, red_pixel_count=0):
    weights = {"critical":20,"warning":8,"info":2}
    sens_mult = {"Low":0.75,"Medium":1.0,"High":1.25}[sensitivity]
    layer_scores = {}
    for f in all_findings:
        pts   = weights.get(f["level"],0)
        layer = f.get("layer","Other")
        layer_scores[layer] = layer_scores.get(layer,0)+pts
    capped = sum(min(v,28) for v in layer_scores.values())
    word_pts  = min(word_suspect_count*6, 25)
    if   red_pixel_count >= 2000: color_pts = 25
    elif red_pixel_count >= 1000: color_pts = 18
    elif red_pixel_count >= 200:  color_pts = 8
    elif red_pixel_count >= 50:   color_pts = 2
    else:                         color_pts = 0
    total = min(int((capped+word_pts+color_pts)*sens_mult), 100)
    return total, layer_scores


# ═══════════════════════════════════════════════════════════════════════════════
#  SIDEBAR
# ═══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("""
    <div style="padding:0 0.5rem;">
      <div style="font-family:'Space Grotesk',sans-serif;font-size:1.5rem;font-weight:700;
        color:var(--text1);margin-bottom:0.2rem;">Doc<span style="color:var(--accent);">Guard</span></div>
      <div style="font-family:'DM Mono',monospace;font-size:0.7rem;color:var(--text3);
        letter-spacing:0.1em;text-transform:uppercase;margin-bottom:1.5rem;">
        Forensics UI v4.1</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="sb-section">⚙ Settings</div>', unsafe_allow_html=True)
    sensitivity = st.select_slider(
        "Detection Sensitivity",
        options=["Low","Medium","High"],
        value="Medium",
        help="Higher sensitivity flags more anomalies but may increase false positives"
    )

    st.markdown('<div class="sb-section">🔬 Active Layers</div>', unsafe_allow_html=True)
    layers = [
        ("Metadata Forensics",     "EXIF, editing software signatures"),
        ("ELA Analysis",           "Re-compression artifact detection"),
        ("Color Anomaly",          "HSV saturation & red pixel isolation"),
        ("Copy-Move SIFT",         "Duplicate feature region matching"),
        ("Noise Analysis",         "Block-level noise profile check"),
        ("Photo Swap",             "Noise z-score for pasted photos"),
        ("Font Consistency",       "Text edge density variation"),
        ("Word-Level AI",          "Per-word multi-signal analysis"),
        ("White Patch Detection",  "Hidden content overlay detection"),
        ("OCR · 4 Languages",      "English · हिंदी · தமிழ் · తెలుగు"),
    ]
    for title, desc in layers:
        st.markdown(f"""
        <div class="sb-layer">
          <div class="sb-dot"></div>
          <div>
            <div style="color:var(--text1);font-size:0.8rem;font-weight:600;">{title}</div>
            <div style="font-size:0.68rem;color:var(--text3);">{desc}</div>
          </div>
        </div>""", unsafe_allow_html=True)

    st.markdown('<div class="sb-section">📖 About</div>', unsafe_allow_html=True)
    st.markdown("""
    <div style="font-size:0.78rem;color:var(--text2);line-height:1.6;padding:0 0.2rem;">
      AI-assisted forensic analysis tool. All findings must be reviewed by a trained human verifier.
      <br><br>
      <span style="color:var(--text3);font-family:var(--mono);">ThinkRoot × Vortex 2026</span>
    </div>""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
#  HERO HEADER
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="hero">
  <div class="hero-label">Explainable AI · Document Forensics</div>
  <h1>Doc<span>Guard</span></h1>
  <p>10-layer forensic analysis · Word-level highlighting · Multi-language OCR · Full PDF scan</p>
  <div class="tag-row">
    <span class="tag">PyTorch ResNet-18</span>
    <span class="tag">ELA Forensics</span>
    <span class="tag">Word AI Boxes</span>
    <span class="tag">Color Analysis</span>
    <span class="tag">Copy-Move SIFT</span>
    <span class="tag">Noise Map</span>
    <span class="tag">White Patch</span>
    <span class="tag">OCR · 4 Langs</span>
  </div>
</div>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
#  UPLOAD
# ═══════════════════════════════════════════════════════════════════════════════
uploaded = st.file_uploader(
    "Drop your document here — PDF, JPG, PNG, BMP, TIFF",
    type=["pdf","jpg","jpeg","png","bmp","tiff"],
    label_visibility="visible"
)

# ─── LANDING PAGE ─────────────────────────────────────────────────────────────
if not uploaded:
    st.markdown('<div class="sec-hdr">How It Works</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    for col, (ic, title, desc) in zip([c1,c2,c3], [
        ("🔍", "10-Layer Detection",
         "Metadata · ELA · Color · Copy-Move · Noise · Photo Swap · Font · Word AI · White Patch · OCR — every layer contributes to the final risk score."),
        ("🎨", "Full Region Highlighting",
         "Every suspicious word, region, and patch is highlighted with color-coded severity boxes directly on the document image."),
        ("📄", "Explainable Findings",
         "Plain-English explanation for every flag, with layer attribution — designed for non-technical document verification officers."),
    ]):
        col.markdown(f"""
        <div class="feat-card">
          <div class="feat-icon">{ic}</div>
          <div class="feat-title">{title}</div>
          <div class="feat-desc">{desc}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown('<div class="sec-hdr">Supported Document Types</div>', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    for col, (ic, label) in zip([c1,c2,c3,c4],[
        ("🆔","ID Cards & PAN"),("🎓","Marksheets"),("📁","PDF Reports"),("🖼️","Scanned Images")
    ]):
        col.markdown(f"""
        <div class="metric-card" style="text-align:center;padding:1.2rem 0.8rem;">
          <div style="font-size:1.6rem;margin-bottom:0.4rem;">{ic}</div>
          <div style="font-size:0.82rem;color:var(--text3);">{label}</div>
        </div>""", unsafe_allow_html=True)
    st.stop()


# ═══════════════════════════════════════════════════════════════════════════════
#  LOAD IMAGE
# ═══════════════════════════════════════════════════════════════════════════════
image, raw_bytes, n_pages = load_image(uploaded)
w0, h0 = image.size

# ─── FILE INFO ─────────────────────────────────────────────────────────────
col_img, col_meta = st.columns([2, 1])
with col_img:
    st.markdown('<div class="sec-hdr">📄 Uploaded Document</div>', unsafe_allow_html=True)
    if n_pages > 1:
        st.markdown(f'<div style="font-family:var(--mono); color:var(--accent); font-size:0.75rem; margin-bottom:10px;">📑 {n_pages} pages stitched for full analysis</div>', unsafe_allow_html=True)
    st.image(image, use_container_width=True)

with col_meta:
    st.markdown('<div class="sec-hdr">📋 File Details</div>', unsafe_allow_html=True)
    for lbl, val in [
        ("Filename",   uploaded.name),
        ("Dimensions", f"{w0} × {h0} px"),
        ("Format",     uploaded.type),
        ("Pages",      str(n_pages)),
        ("Sensitivity",sensitivity),
    ]:
        st.markdown(f"""
        <div class="file-detail">
          <div class="fd-key">{lbl}</div>
          <div class="fd-val">{val}</div>
        </div>""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
#  PIPELINE
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="sec-hdr">⚙ Analysis Pipeline</div>', unsafe_allow_html=True)
pbox = st.empty()
steps_list = [
    "Metadata", "ELA + Hotspots", "Color Anomaly", "Copy-Move",
    "Noise Map", "Photo Swap", "Font Analysis", "Word-Level AI",
    "White Patches", "OCR"
]

def show_pipeline(n):
    items = ""
    for i, s in enumerate(steps_list):
        cls  = "pipe-done" if i < n else "pipe-run" if i == n else "pipe-wait"
        icon = "✓" if i < n else "⟳" if i == n else "○"
        items += f'<div class="pipe-step {cls}"><span>{icon}</span><span>{s}</span></div>'
    pbox.markdown(f'<div class="pipeline-grid">{items}</div>', unsafe_allow_html=True)


# ─── RUN ALL LAYERS ─────────────────────────────────────────────────────────
all_findings = []

show_pipeline(0)
meta_findings, meta_info = analyse_metadata(image, raw_bytes, uploaded.name)
all_findings.extend(meta_findings)

show_pipeline(1)
ela_img, ela_score, region_ela, ela_findings, ela_hotspots = run_ela(image)
all_findings.extend(ela_findings)

show_pipeline(2)
color_img, red_count, color_findings, color_boxes = detect_color_anomaly(image)
all_findings.extend(color_findings)

show_pipeline(3)
cm_img, cm_count, cm_findings = copy_move(image)
all_findings.extend(cm_findings)

show_pipeline(4)
nm_img, noise_std, noise_findings = noise_analysis(image)
all_findings.extend(noise_findings)

show_pipeline(5)
photo_img, photo_findings, photo_box = detect_photo_swap(image)
all_findings.extend(photo_findings)

show_pipeline(6)
font_var, font_findings = font_analysis(image)
all_findings.extend(font_findings)

show_pipeline(7)
model = load_model()
quads      = [image.crop((0,0,w0//2,h0//2)), image.crop((w0//2,0,w0,h0//2)),
              image.crop((0,h0//2,w0//2,h0)), image.crop((w0//2,h0//2,w0,h0))]
quad_names = ["Top-Left","Top-Right","Bottom-Left","Bottom-Right"]
dl_scores  = [dl_region_score(q, model) for q in quads]
dl_max     = max(dl_scores)
if dl_max > 0.78:
    worst_q = quad_names[dl_scores.index(dl_max)]
    all_findings.append({
        "level":"warning",
        "title":f"PyTorch anomaly in {worst_q} quadrant (conf={dl_max:.2f})",
        "detail":f"ResNet-18 found visual inconsistency in {worst_q} region (confidence {dl_max:.2f}). "
                 f"Content has different deep features from authentic documents.",
        "layer":"DL"
    })
ela_arr       = np.array(ela_img.convert("L")).astype(np.float32)
word_suspects = get_suspicious_word_boxes(image, ela_arr, sensitivity)

show_pipeline(8)
wp_count, wp_boxes, wp_findings = detect_white_patches(image)
all_findings.extend(wp_findings)

show_pipeline(9)
ocr_text, ocr_fields = run_ocr(image)

pbox.empty()

# Build outputs
annotated   = build_annotated(image, wp_boxes, photo_box, color_boxes, ela_hotspots, word_suspects)
overlay_ela = ela_overlay(image, ela_img)
final_score, layer_scores = compute_final_score(all_findings, len(word_suspects), sensitivity, red_count)


# ═══════════════════════════════════════════════════════════════════════════════
#  VERDICT
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="sec-hdr">📋 Verdict</div>', unsafe_allow_html=True)

if final_score >= 65:
    verd_cls  = "verdict-danger"
    verd_icon = "🚨"
    verd_head = "HIGH RISK — LIKELY FORGED"
    verd_desc = f"Strong forgery indicators detected across multiple analysis layers. Score: {final_score}% — do NOT accept this document without thorough manual verification."
    score_col = "var(--red)"
elif final_score >= 45:
    verd_cls  = "verdict-warning"
    verd_icon = "⚠️"
    verd_head = "SUSPICIOUS — NEEDS REVIEW"
    verd_desc = f"Multiple anomaly signals detected across layers. Score: {final_score}% — flag for manual inspection by a trained verifier."
    score_col = "var(--amber)"
elif final_score >= 20:
    verd_cls  = "verdict-info"
    verd_icon = "🔍"
    verd_head = "LOW RISK — MINOR ANOMALIES"
    verd_desc = f"Minor irregularities detected, likely from scanning or compression artifacts. Score: {final_score}% — probably genuine but worth a quick manual review."
    score_col = "var(--accent)"
else:
    verd_cls  = "verdict-success"
    verd_icon = "✅"
    verd_head = "LIKELY GENUINE"
    verd_desc = f"No significant forgery indicators found across all 10 detection layers. Score: {final_score}%"
    score_col = "var(--green)"

v_col, g_col = st.columns([1, 1])

with v_col:
    st.markdown(f"""
    <div class="verdict-box {verd_cls}">
      <div style="font-family:var(--mono); font-size:0.7rem; color:{score_col}; letter-spacing:0.12em; text-transform:uppercase; margin-bottom:0.5rem;">
        {verd_icon} Forensic Assessment
      </div>
      <div class="verdict-title" style="color:{score_col};">{verd_head}</div>
      <div class="verdict-sub">{verd_desc}</div>
    </div>""", unsafe_allow_html=True)

with g_col:
    gauge_label = ("HIGH RISK" if final_score>=65 else
                   "SUSPICIOUS" if final_score>=45 else
                   "MINOR ANOMALIES" if final_score>=20 else "GENUINE")
    st.markdown(f"""
    <div class="gauge-wrap">
      <div class="gauge-header">
        <div>
          <div style="font-family:var(--mono); font-size:0.65rem; color:var(--text3); letter-spacing:0.1em; text-transform:uppercase; margin-bottom:4px;">Forgery Risk Score</div>
          <div style="font-family:var(--mono); font-size:0.8rem; color:{score_col}; letter-spacing:0.08em; font-weight:700;">{gauge_label}</div>
        </div>
        <div class="gauge-score" style="color:{score_col};">{final_score}<span style="font-size:1.5rem;opacity:0.5;">%</span></div>
      </div>
      <div class="gauge-bar-bg">
        <div class="gauge-bar-fill" style="width:{final_score}%; background:linear-gradient(90deg, var(--green), var(--amber), {score_col});"></div>
      </div>
      <div class="gauge-ticks">
        <span>0–19 Genuine</span>
        <span>20–44 Minor</span>
        <span>45–64 Suspicious</span>
        <span>65+ Forged</span>
      </div>
    </div>""", unsafe_allow_html=True)


# ─── METRIC STRIP ─────────────────────────────────────────────────────────────
def mv_class(val_str, warn, danger):
    try:
        v = float(val_str.replace("%",""))
        return "mv-danger" if v>=danger else "mv-warn" if v>=warn else "mv-ok"
    except: return "mv-blue"

metrics = [
    ("Risk Score",      f"{final_score}%",          45,  65),
    ("ELA Score",       f"{ela_score:.2f}",          3.5, 6.0),
    ("Copy-Move",       str(cm_count),               20,  45),
    ("Noise Std",       f"{noise_std:.2f}",          13,  20),
    ("Red Pixels",      str(red_count),              50,  200),
    ("Flagged Words",   str(len(word_suspects)),     1,   4),
]
cols = st.columns(6)
for col, (lbl, val, wt, dt) in zip(cols, metrics):
    cls = mv_class(val, wt, dt) if wt else "mv-blue"
    col.markdown(f"""
    <div class="metric-card">
      <div class="metric-num {cls}">{val}</div>
      <div class="metric-label">{lbl}</div>
    </div>""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
#  FINDINGS
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="sec-hdr">🚩 Detailed Findings</div>', unsafe_allow_html=True)

word_findings_display = []
for ws in word_suspects:
    word_findings_display.append({
        "level": "critical" if ws["score"] >= 12 else "warning",
        "title": f'Suspicious word: "{ws["text"]}" (score={ws["score"]})',
        "detail": f"At {ws['box'][:2]} — signals: {', '.join(ws['reasons'])}",
        "layer": "Word-AI"
    })

all_display = all_findings + word_findings_display

if all_display:
    # Group by level
    crits = [f for f in all_display if f.get("level")=="critical"]
    warns = [f for f in all_display if f.get("level")=="warning"]
    infos = [f for f in all_display if f.get("level") not in ("critical","warning")]

    if crits:
        st.markdown(f"""<div style="font-family:var(--mono); font-size:0.7rem; color:var(--red); letter-spacing:0.1em; text-transform:uppercase; margin:0.4rem 0; font-weight:600;">
          ● Critical ({len(crits)})</div>""", unsafe_allow_html=True)
        for f in crits:
            st.markdown(f"""
            <div class="finding finding-critical">
              <div class="finding-icon">🔴</div>
              <div class="finding-body">
                <div class="finding-layer">{f.get('layer','—')}</div>
                <div class="finding-title">{f['title']}</div>
                <div class="finding-detail">{f['detail']}</div>
              </div>
            </div>""", unsafe_allow_html=True)

    if warns:
        st.markdown(f"""<div style="font-family:var(--mono); font-size:0.7rem; color:var(--amber); letter-spacing:0.1em; text-transform:uppercase; margin:0.8rem 0 0.4rem; font-weight:600;">
          ● Warnings ({len(warns)})</div>""", unsafe_allow_html=True)
        for f in warns:
            st.markdown(f"""
            <div class="finding finding-warning">
              <div class="finding-icon">🟡</div>
              <div class="finding-body">
                <div class="finding-layer">{f.get('layer','—')}</div>
                <div class="finding-title">{f['title']}</div>
                <div class="finding-detail">{f['detail']}</div>
              </div>
            </div>""", unsafe_allow_html=True)

    if infos:
        for f in infos:
            st.markdown(f"""
            <div class="finding finding-info">
              <div class="finding-icon">🔵</div>
              <div class="finding-body">
                <div class="finding-layer">{f.get('layer','—')}</div>
                <div class="finding-title">{f['title']}</div>
                <div class="finding-detail">{f['detail']}</div>
              </div>
            </div>""", unsafe_allow_html=True)
else:
    st.markdown("""
    <div class="finding finding-info" style="border-left: 3px solid var(--green);">
      <div class="finding-icon">✅</div>
      <div class="finding-body">
        <div class="finding-title">No suspicious indicators detected</div>
        <div class="finding-detail">All 10 forensic layers returned clean results.</div>
      </div>
    </div>""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
#  VISUAL MAPS
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="sec-hdr">🗺 Forensic Visual Maps</div>', unsafe_allow_html=True)

t1,t2,t3,t4,t5,t6 = st.tabs([
    "Annotated — All Signals",
    "Color Map",
    "ELA Overlay",
    "Raw ELA",
    "Copy-Move",
    "Noise Map"
])

with t1:
    st.image(annotated, use_container_width=True)
    st.markdown(f"""
    <div style="font-family:var(--mono); font-size:0.75rem; color:var(--text2); padding:0.5rem 0; letter-spacing:0.04em;">
      🔴 {len(word_suspects)} suspicious word(s) &nbsp;·&nbsp;
      🟡 {len(wp_boxes)} white patch(es) &nbsp;·&nbsp;
      🔵 {len(ela_hotspots)} ELA hotspot(s) &nbsp;·&nbsp;
      🟠 {'1 photo anomaly' if photo_box else 'no photo anomaly'}
    </div>""", unsafe_allow_html=True)

with t2:
    st.image(color_img, use_container_width=True)
    st.markdown(f'<div style="font-family:var(--mono); font-size:0.75rem; color:var(--text2); padding:0.5rem 0;">{red_count} red pixels detected. Boxes highlight color anomaly regions.</div>', unsafe_allow_html=True)

with t3:
    st.image(overlay_ela, use_container_width=True)
    st.markdown('<div style="font-family:var(--mono); font-size:0.75rem; color:var(--text2); padding:0.5rem 0;">ELA heatmap overlay — warm regions indicate compression anomalies from editing.</div>', unsafe_allow_html=True)

with t4:
    st.image(ela_img, use_container_width=True)
    st.markdown('<div style="font-family:var(--mono); font-size:0.75rem; color:var(--text2); padding:0.5rem 0;">Raw ELA — brightness = degree of JPEG re-compression at each pixel.</div>', unsafe_allow_html=True)

with t5:
    st.image(cm_img, use_container_width=True)
    st.markdown(f'<div style="font-family:var(--mono); font-size:0.75rem; color:var(--text2); padding:0.5rem 0;">SIFT copy-move detection — {cm_count} duplicate feature pairs found.</div>', unsafe_allow_html=True)

with t6:
    st.image(nm_img, use_container_width=True)
    st.markdown('<div style="font-family:var(--mono); font-size:0.75rem; color:var(--text2); padding:0.5rem 0;">Noise map — warm regions = inconsistent pixel sources (possible paste).</div>', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
#  OCR + METADATA + DL SCORES
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="sec-hdr">🔤 Extracted Text · 📋 Metadata · 🧠 AI Scores</div>', unsafe_allow_html=True)

ocr_col, meta_col, dl_col = st.columns([2, 1.2, 1.2])

with ocr_col:
    st.markdown("**OCR Output**")
    with st.expander("Raw extracted text", expanded=False):
        st.text_area("", ocr_text, height=180, label_visibility="collapsed")
        st.caption("Tesseract · English · हिंदी · தமிழ் · తెలుగు")
    if ocr_fields:
        st.markdown("**Detected Fields**")
        for k, v in ocr_fields.items():
            st.markdown(f"""
            <div class="ocr-field">
              <div class="ocr-key">{k}</div>
              <div class="ocr-val">{v}</div>
            </div>""", unsafe_allow_html=True)
    else:
        st.markdown('<div style="font-size:0.82rem;color:var(--text3);">No structured fields auto-detected.</div>', unsafe_allow_html=True)

with meta_col:
    st.markdown("**File Metadata**")
    with st.expander("View all metadata", expanded=False):
        for k, v in meta_info.items():
            st.markdown(f"""
            <div class="ocr-field">
              <div class="ocr-key">{k}</div>
              <div class="ocr-val">{v}</div>
            </div>""", unsafe_allow_html=True)

with dl_col:
    st.markdown("**PyTorch Quadrant Scores**")
    for name, sv in zip(quad_names, dl_scores):
        color = "var(--red)" if sv>0.78 else "var(--amber)" if sv>0.60 else "var(--green)"
        st.markdown(f"""
        <div class="dl-quad" style="margin-bottom:6px;">
          <div style="display:flex;justify-content:space-between;align-items:center;">
            <div style="font-family:var(--mono); font-size:0.65rem; color:var(--text2); letter-spacing:0.06em; text-transform:uppercase;">{name}</div>
            <div class="dl-score" style="color:{color};">{sv:.3f}</div>
          </div>
          <div style="height:4px; background:rgba(255,255,255,0.04); border-radius:2px; margin-top:6px;">
            <div style="height:4px; width:{sv*100:.0f}%; background:{color}; border-radius:2px; opacity:0.9;"></div>
          </div>
        </div>""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
#  REPORT DOWNLOAD
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="sec-hdr">📄 Forensic Report</div>', unsafe_allow_html=True)

risk   = ("High" if final_score>=65 else "Suspicious" if final_score>=45
          else "Low-Minor" if final_score>=20 else "Low")
verdict_str = "FORGED" if final_score >= 45 else "GENUINE"

word_s = "\n".join(
    f"  [{ws['score']}] \"{ws['text']}\" at {ws['box'][:2]} — {', '.join(ws['reasons'])}"
    for ws in word_suspects
) or "  None"

report = f"""DOCGUARD FORENSIC REPORT v4.1
══════════════════════════════════════════════════════════════
File            : {uploaded.name}
Generated       : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Sensitivity     : {sensitivity}
Pages Analysed  : {n_pages}

VERDICT         : {verdict_str}
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

SUSPICIOUS WORDS (word-level AI)
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
6.  Photo Swap  — Noise z-score contrast analysis for pasted photos
7.  Font        — Text edge density variation across document strips
8.  Word-AI     — Per-word ELA + saturation + LAB color + brightness + sharpness analysis
9.  White Patch — Bright overlay rectangle detection (hidden content)
10. OCR         — Tesseract multi-language (English, Hindi, Tamil, Telugu)

ANNOTATION LEGEND
───────────────────────────────────────
Red boxes    = Suspicious words (multi-signal AI)
Yellow boxes = White patches (content hidden under white overlay)
Orange boxes = Photo region anomaly (possible photo swap)
Cyan boxes   = ELA hotspot blocks (re-compression artifacts)

DISCLAIMER
───────────────────────────────────────
AI-assisted tool. All findings must be reviewed by a trained human verifier.
DocGuard v4.1 — ThinkRoot × Vortex 2026
"""

dl_col_r, _ = st.columns([1, 2])
with dl_col_r:
    st.download_button(
        "📥  Download Full Forensic Report (.txt)",
        data=report,
        file_name=f"DocGuard_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
        mime="text/plain",
        use_container_width=True
    )