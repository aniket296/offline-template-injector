# Offline Template & Variable Field Injector

<p align="center">
  <img src="https://img.shields.io/badge/Platform-Windows%2010%20%7C%2011-0078D6?style=for-the-badge&logo=windows&logoColor=white" alt="Platform Windows 10/11" />
  <img src="https://img.shields.io/badge/Python-3.11%2B-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.11+" />
  <img src="https://img.shields.io/badge/Privacy-100%25%20Offline--First-10B981?style=for-the-badge" alt="100% Offline-First" />
  <img src="https://img.shields.io/badge/Packaging-PyInstaller%20%26%20Inno%20Setup-4F46E5?style=for-the-badge" alt="PyInstaller & Inno Setup" />
  <img src="https://img.shields.io/badge/License-MIT-F59E0B?style=for-the-badge" alt="License MIT" />
</p>

> **A zero-cloud, high-speed Windows desktop application for educators, school administrators, and training coordinators to visually place variable fields onto PDF/Image templates, bind them to Excel (`.xlsx`) or CSV gradebooks, preview live student records on an interactive canvas, and batch-generate personalized PDFs locally.**

---

## Why This Exists (Real-World Impact)

Every academic term, teachers and school registrars spend days manually copying student names, roll numbers, grades, and verification IDs into report cards, merit certificates, and hall tickets—or worse, uploading confidential student spreadsheets to third-party cloud mail-merge tools that violate student data privacy policies.

**Offline Template & Variable Field Injector** eliminates manual data entry while keeping 100% of student records strictly on local school hardware:

- **Zero Cloud Exposure:** No internet connection, account login, or external API is ever used. Confidential student gradebooks never leave your machine.
- **No Broken Layouts on Long Names:** Built-in bounding-box font auto-shrink automatically scales down extra-long student names so they never overflow certificate borders.
- **Instant Classroom Printing:** Exports individual student PDFs with custom naming patterns (`101_Aarav_Sharma.pdf`) **and** a single multi-page `Master_Batch_Output.pdf` ready for one-click printing.
- **Standard, Open PDFs:** Generated PDFs are 100% standard, unencrypted documents compatible with every PDF viewer, printer, and school portal.

---

## Key Features

- **Interactive Drag-and-Drop Canvas Editor:** Load any `.pdf`, `.png`, or `.jpg` template, visually drag variable boxes across the page, resize via bottom-right corner handles, or nudge by `1pt` (`Arrow` keys) / `10pt` (`Shift+Arrow` keys) for pixel-perfect alignment.
- **Excel (`.xlsx`) Formula Evaluation & CSV Loader:** Reads calculated Excel formula results (`data_only=True`) and auto-detects CSV encodings (`UTF-8`, `UTF-8-SIG`, `CP1252`), cleanly formatting integer roll numbers without `.0` artifacts.
- **Bounding-Box Auto-Shrink Typography:** Uses exact PyMuPDF (`fitz.Font.text_length`) glyph metrics to iteratively shrink font sizes between `Max Size` and `Min Size` when a student's name exceeds the field width.
- **Dynamic Signature/Image & QR Code Overlays:** Stamp transparent PNG principal signatures, school seals, student photos, or dynamically generated high-contrast verification QR codes into any bounding box.
- **Live Record Stepper (`< Record 1 of N >`):** Flip through every row of your loaded spreadsheet directly on the canvas to visually inspect real student names, grades, and QR codes before running a batch.
- **Reusable `.otvi` Layout Presets:** Save your complete field layout, typography settings, and filename patterns to a `.otvi` JSON preset file for instant reuse next semester.
- **Multithreaded Dual Export Engine:** Powered by a responsive background worker pool that generates individual PDFs, a merged master PDF, or both simultaneously without freezing the Windows GUI.

---

## Visual Architecture & Directory Tree

```text
offline-template-injector/
├── .gitignore
├── .env.example
├── README.md
├── pyproject.toml
├── requirements.txt
├── run_local.bat                   # One-click local virtual-env bootstrapper & launcher
├── build_windows.spec              # PyInstaller single-file Windows executable spec
├── assets/
│   └── app_icon.ico                # Multi-resolution (16/32/48/256px) Indigo & Gold icon
├── installer/
│   └── setup.iss                   # Inno Setup 6 Windows installer script
├── scripts/
│   ├── generate_icon.py            # Programmatic Pillow icon generator
│   ├── build_exe.bat               # Runs pytest + icon gen + PyInstaller build
│   └── build_installer.bat         # Builds EXE + compiles Inno Setup installer (with fallback)
├── src/
│   ├── __init__.py
│   ├── main.py                     # High-DPI Windows entry point
│   ├── core/
│   │   ├── data_loader.py          # Excel (.xlsx) & CSV loader with formula & encoding support
│   │   ├── text_fitter.py          # PyMuPDF bounding-box auto-shrink font math & hex RGB parser
│   │   ├── qr_generator.py         # In-memory QR code PNG byte stream generator
│   │   ├── template_renderer.py    # Non-destructive PDF/Image stamping & PIL canvas previewer
│   │   ├── project_io.py           # .otvi JSON layout preset serializer & validator
│   │   └── batch_worker.py         # Thread-pool batch PDF & Master PDF merger with cancellation
│   ├── gui/
│   │   ├── app.py                  # Main controller wiring all panels & background worker polling
│   │   ├── styles.py               # Corporate Slate-Indigo ttk theme ("clam" + Segoe UI)
│   │   └── components/
│   │       ├── toolbar.py          # Grouped top action bar (Files, Insert Fields, Presets)
│   │       ├── canvas_editor.py    # Zoomable, scrollable drag-and-drop field placement canvas
│   │       ├── field_inspector.py  # Right-hand property editor (Binding, Typography, Geometry)
│   │       ├── record_stepper.py   # Live spreadsheet row navigation bar (< Record X of N >)
│   │       └── export_panel.py     # Output folder, clickable {Column} chips, & batch progress
│   ├── models/
│   │   ├── field_node.py           # FieldNode, FieldType (TEXT/IMAGE/QR), TextAlignment
│   │   ├── project_state.py        # TemplateProject, OutputSettings, ExportMode
│   │   └── batch_result.py         # RowTaskResult, RowStatus, BatchSummary
│   └── utils/
│       ├── config.py               # .env loader with safe typed defaults
│       ├── filename_parser.py      # Dynamic {Column} filename formatter & Windows path scrubber
│       └── logger.py               # Rotating file logger (~/.offline_template_injector/app.log)
└── tests/
    ├── conftest.py                 # Synthetic PDF, PNG, signature, XLSX, and CSV pytest fixtures
    ├── test_data_and_filenames.py  # Spreadsheet normalization & filename sanitization tests
    ├── test_text_fitter_and_qr.py  # Auto-shrink font math & QR byte generation tests
    └── test_renderer_and_preset.py # End-to-end PDF stamping, .otvi IO, & batch worker tests
```

---

## Quickstart Guide (4 Options)

### Option 1: Windows Installer (`OfflineTemplateInjector_Setup.exe`)
1. Download `OfflineTemplateInjector_Setup.exe` from the **Releases** page (or build it locally via Option 4).
2. Run the installer wizard to install **Offline Template & Variable Field Injector** into your Start Menu and Desktop.
3. Launch the app—no Python installation required.

### Option 2: One-Click Local Source Launcher (`run_local.bat`)
Double-click `run_local.bat` in the repository root, or run it from Command Prompt:
```bat
run_local.bat
```
> Automatically creates `.venv` if missing, installs `requirements.txt`, generates `assets\app_icon.ico`, and launches the desktop application.

### Option 3: Developer Terminal Setup (`venv` + `pip`)
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -e .[dev]
python scripts/generate_icon.py
python -m src.main
```

### Option 4: Rebuilding the Standalone `.exe` & Windows Installer
To compile the standalone single-file executable (`dist\OfflineTemplateInjector.exe`):
```bat
scripts\build_exe.bat
```
To compile both the standalone executable and the Windows Setup Installer (`dist_installer\OfflineTemplateInjector_Setup.exe`):
```bat
scripts\build_installer.bat
```

---

## Step-by-Step User Workflow

1. **Load Your Template:** Click **`Load Template (PDF/Image)`** in the top toolbar and choose your blank report card or certificate (`.pdf`, `.png`, or `.jpg`).
2. **Load Your Student Gradebook:** Click **`Load Data (.xlsx/.csv)`** and select your Excel or CSV file containing student columns (e.g., `Roll_No`, `Student_Name`, `Grade`, `Verification_ID`).
3. **Place & Bind Variable Fields:**
   - Click **`+ Add Text Field`**, **`+ Add Signature/Image Box`**, or **`+ Add QR Code Box`**.
   - Drag the box onto the desired line on the template canvas and resize using the bottom-right corner handle.
   - In the right-hand **Field Property Inspector**, select the matching **Spreadsheet Column Mapping**, choose your font family, color, alignment, and enable **`Auto-Shrink to Box`**.
4. **Preview Live Records & Save Preset:** Use the bottom **Live Record Stepper** (`|< First`, `< Prev Record`, `Next Record >`, `Last >|`) to flip through real students right on the canvas. Click **`Save Layout (.otvi)`** to save your layout for future batches.
5. **Configure Naming & Export Batch:**
   - In the **Batch Export & Output Settings** panel, click column tag chips (e.g., `{Index}`, `{Roll_No}`, `{Student_Name}`) to build your dynamic filename pattern.
   - Choose **`Both (Individual + Merged Master PDF)`** (or individual/merged only) and click **`Generate Batch PDFs`**.

---

## Tech Stack & Automated Testing

| Layer | Technology | Purpose |
| :--- | :--- | :--- |
| **Core PDF Engine** | `PyMuPDF` (`fitz` >= 1.24.0) | High-speed in-memory PDF cloning, glyph metrics, vector text/image stamping, & master PDF merging |
| **Spreadsheet Engine** | `openpyxl` (>= 3.1.2) & `csv` | Formula-evaluated `.xlsx` loading (`data_only=True`) & multi-encoding CSV parsing |
| **Imaging & QR** | `Pillow` (>= 10.0.0) & `qrcode` | Image-to-PDF conversion, transparent PNG signatures, QR generation, & programmatic `.ico` creation |
| **Desktop GUI** | `tkinter` / `ttk` (`clam`) | Native Windows High-DPI interface, interactive drag/resize canvas, & corporate Slate-Indigo theme |
| **Packaging** | `PyInstaller` & `Inno Setup 6` | Zero-dependency standalone `.exe` binary & Windows Setup installer wizard |

### Running the Automated Test Suite
```powershell
.\.venv\Scripts\pytest.exe -v
```
