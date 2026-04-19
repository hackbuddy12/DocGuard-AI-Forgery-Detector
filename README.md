# DocGuard: AI Document Forensics 🔍

**Built for the ThinkRoot x Vortex Hackathon 2026**

* 🌐 **ThinkRoot Documentation Website:** [Insert your thinkroot.dev link here]
* 🎥 **Demo Video:** [Insert your YouTube/Drive link here]

## 📌 Overview
DocGuard is a multi-layer cyber-forensic analysis tool designed to verify document authenticity and detect digital tampering. It processes PDFs and images (ID cards, marksheets, reports) through 10 distinct analytical layers to flag forged content at the pixel, region, and metadata levels.

## ⚙️ System Architecture & Tech Stack
Our approach combines traditional image processing with deep learning models to provide explainable AI findings.

* **Frontend:** Streamlit (Python) for a responsive, intelligence-style dashboard.
* **Deep Learning:** PyTorch & torchvision (ResNet-18) for quadrant-based visual anomaly scoring.
* **Computer Vision:** OpenCV & scikit-image for Error Level Analysis (ELA), Copy-Move SIFT detection, and HSV color anomaly isolation.
* **OCR:** PyTesseract for multi-language text extraction (English, Hindi, Tamil, Telugu) and field mapping.
* **Document Parsing:** PyMuPDF (fitz) for PDF page stitching and rasterization.

## 🔬 The 10-Layer Detection Pipeline
1. **Metadata Forensics:** Extracts EXIF data and scans raw bytes for editing software signatures (e.g., Photoshop, Canva).
2. **ELA Analysis:** Detects JPEG re-compression artifacts to find newly pasted elements.
3. **Color Anomaly:** Isolates unnatural HSV saturation and flags red-pixel tampering.
4. **Copy-Move SIFT:** Matches duplicate feature regions to detect cloning within the document.
5. **Noise Analysis:** Checks block-level noise profiles for inconsistencies.
6. **Photo Swap Detection:** Calculates noise z-scores to find replaced ID photographs.
7. **Font Consistency:** Analyzes text edge density variation across document strips.
8. **Word-Level AI:** Evaluates per-word bounding boxes against multiple signals (ELA, LAB color, sharpness) to flag specific tampered words.
9. **White Patch Detection:** Identifies bright overlay rectangles hiding original content.
10. **4-Language OCR:** Extracts critical fields (DOB, Roll No, PAN, Aadhaar).

## 🚀 Setup Instructions

Follow these steps to run the application locally:

**1. Clone the repository**
```bash
git clone [https://github.com/your-username/DocGuard-AI-Document-Forensics.git](https://github.com/your-username/DocGuard-AI-Document-Forensics.git)
cd DocGuard-AI-Document-Forensics

2. Install dependencies
Make sure you have Python 3.9+ installed.
pip install -r requirements.txt

3. Install Tesseract-OCR (Prerequisite)
You must have Tesseract installed on your system.

Windows: Download the installer from the official UB-Mannheim repository. Ensure the path C:\Program Files\Tesseract-OCR\tesseract.exe exists.

Mac: brew install tesseract

Linux: sudo apt-get install tesseract-ocr

🚀 STEP 6 — Add requirements.txt (Already good)

Your file :contentReference[oaicite:2]{index=2} is fine. Just rename correctly.

4. Run the Application
streamlit run app.py
