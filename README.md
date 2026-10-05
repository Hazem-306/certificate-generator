# 🎓 Certificates Generator - Web Interface

A web application built for **Mawaheb Academy** to design, preview, and generate bulk PDF certificates from custom image templates and Excel spreadsheets.

---

## ✨ Features

- **Interactive Canvas Box Selector**: Visually select, drag, and resize text placement areas on your certificate template using an embedded interactive HTML5 canvas.
- **Multi-Field Support**: Configure multiple dynamic text fields (e.g., Student Name, Course Title, Date, Grade) with custom fonts, colors, font sizes, alignment, bold, and italic styles.
- **Excel Data Batch Import**: Upload Excel files (`.xlsx`) to map spreadsheet columns directly to dynamic certificate fields.
- **Real-Time Preview**: Live certificate rendering before starting bulk generation.
- **High Performance Batch Processing**:
  - **Single Combined PDF**: Rapidly merge hundreds/thousands of certificates into a single lightweight PDF document.
  - **ZIP Archive Export**: Package individual certificates into a downloadable ZIP archive.
  - Multi-threaded rendering using Python's `ThreadPoolExecutor`.

---

## 🛠️ Technology Stack

- **Frontend / UI**: [Streamlit](https://streamlit.io/) with custom HTML5/JS components
- **PDF Engine**: [ReportLab](https://www.reportlab.com/) & [pypdf](https://pypdf.readthedocs.io/)
- **Image Processing**: [Pillow (PIL)](https://python-pillow.org/)
- **Excel Parsing**: [openpyxl](https://openpyxl.readthedocs.io/)

---

## 📁 Project Structure

```
.
├── main.py              # Main Streamlit application UI & workflow
├── pdf_handler.py       # ReportLab PDF rendering & PDF merger engine
├── excel_parser.py      # Excel workbook loader & column extractor
├── engine.py           # Multi-threaded batch certificate generator
├── config.py           # Application configurations & styling constants
├── requirements.txt     # Python dependencies (excluding Streamlit)
└── box_canvas/          # Custom Streamlit HTML5 interactive box canvas
    └── index.html
```

---

## 🚀 Getting Started

### 1. Prerequisites
Ensure you have Python 3.8+ installed on your system.

### 2. Installation

Clone or open the repository directory, then install the dependencies:

```bash
# Install core dependencies
pip install -r requirements.txt

# Install Streamlit for the web application interface
pip install streamlit
```

### 3. Running the Application

Launch the Streamlit web server:

```bash
streamlit run main.py
```

After running the command, open your browser at `http://localhost:8501`.

---

## 📖 How to Use

1. **Upload Template**: Upload a high-resolution certificate template image (`.jpg`, `.png`).
2. **Import Excel Data**: Upload an `.xlsx` file containing recipient information.
3. **Configure Text Fields**:
   - Draw/adjust the text box directly on the interactive template canvas.
   - Assign each box to an Excel column.
   - Adjust styling parameters: Font Family (Arial, Calibri, Helvetica), Size, Color, Alignment, Bold, Italic.
4. **Preview & Generate**:
   - Click **Preview** to verify the alignment.
   - Choose output format (Combined PDF or ZIP of individual PDFs).
   - Click **Generate Certificates** to start batch processing.

---

## 📄 License

Internal tool developed for Mawaheb Academy.
