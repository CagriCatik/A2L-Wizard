# A2L Wizard

A2L Wizard is a cross-platform GUI application for browsing, searching, and exporting parameters from `.a2l` (ASAP2/A2L) files. It provides an intuitive PySide6 interface with advanced filtering, search, and export capabilities.

---

## Features

### Interactive A2L Browser

- Load and parse `.a2l` files to display:
  - **Characteristics**
  - **Measurements**
  - **Measurement Arrays**
- Filter parameters by **type** and **module**.
- Live text search in parameter names and comments.
- Toggle column visibility via right-click on table headers.
- Export filtered data to `.xlsx` format.

---

## Project Layout

```plaintext
project_root/
├── data_utils.py       # A2L parsing and search logic
├── gui.py              # PySide6 GUI implementation
├── main.py             # Application entry point
├── requirements.txt    # Dependency list
├── static/
│   └── wizard.png      # Application icon
└── README.md
````

---

## Installation

### Prerequisites

- Python 3.10 or newer (tested with Python 3.11)
- Compatible with Windows, macOS, and Linux

### Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Usage

Start the application:

```bash
python main.py
```

### Main Functions

1. **Load .a2l File**
   Use *File → Load* or click **Load .a2l**.
2. **Filter Data**

   - Select **Type** from the dropdown.
   - Select **Module** from the dropdown.
   - Enter a **Search** term.
3. **Export Results**
   Click **Export Filtered** to save the currently visible table contents as an Excel file.

---

## Dependencies

`requirements.txt`:

```plaintext
pandas>=2.0.0
PySide6>=6.6.0
openpyxl>=3.1.0
```

---

## License

This project is licensed under the WTFPL
