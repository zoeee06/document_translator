# 📘 Document Translator

This is a fully automated pipeline for translating scanned document images or PDFs, preserving their original layout. It leverages OCR (Optical Character Recognition), translation via OpenAI GPT-4, and intelligent rendering to produce high-quality translated documents.

---

## 📁 Project Structure

image-translator/
├── fonts/ # Custom fonts for rendering
├── input/ # Input files (images or PDFs)
├── layout/ # Layout information from OCR
├── layout_filled/ # Final layout with translated text
├── mask/ # Cut-out masks for rendering
├── ocr_cache/ # Intermediate OCR results (e.g., paragraphs_with_id.json)
├── output/ # Final translated images or PDFs
├── venv/ # (Ignored) Python virtual environment
├── .env # Stores your OpenAI API key (not committed)
├── .gitignore # Ensures sensitive files like service keys are excluded
├── service-key.json # [IGNORED] Google Vision API credentials (see below)
├── \*.py # Python scripts (translation, rendering, etc.)
├── README.md

---

## 🔑 Requirements

- Python 3.8+
- Google Cloud Vision API credentials
- OpenAI GPT-4 API key

---

## 🔐 Setup Credentials

### 1. OpenAI API Key

Create a `.env` file in the project root with:
OPENAI_API_KEY=your_openai_key_here

> This file is listed in `.gitignore` and **should not** be committed.

---

### 2. Google Vision API Credentials

You must obtain a `service_key.json` file from Google Cloud Console:

1. Enable **Google Cloud Vision API**.
2. Create a Service Account and download the `service_key.json`.
3. Save it under:
   image-translator/service-key.json

> ⚠️ This file is **ignored by Git** for security. Do not upload it to GitHub.

---

## 🧪 Installation

1. Create and activate a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
   pip install -r requirements.txt

🚀 Usage Steps
Step 1: Convert PDF to Images

```bash
python pdf_to_images.py the_path_to_your_file.pdf
```

Step 2: OCR + Paragraph ID Assignment

```bash
python save_ocr.py
```

Step 3: Translate Paragraphs via GPT-4

```bash
python translate_by_id.py
```

Step 4: Use Translated Paragraphs to generate final layout

```bash
 generate_final_layout.py
```

Step 5: Render into images

```bash
python render.py
```

Step 6: Convert Resulting PNGs to PDF

```bash
python pngs_to_pdf.py output
```
