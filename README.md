# A2L-Wizard

<p align="center">
  <img src="./static/wizard.png" alt="A2L Wizard screenshot" width="300" />
</p>

<div align="center">
A2L Wizard is a cross-platform GUI application for browsing, searching, and exporting parameters from `.a2l` files. 
</div>

<p align="center">
It provides an intuitive user interface with mediocre filtering, search, and export capabilities.
</p>


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

<p align="center">
  <img src="./static/image.png" alt="A2L Wizard screenshot" width="1200" />
</p>

## A2L Wizard Data Flow and Architecture

- **A2L Wizard** is a desktop application for loading, browsing, filtering, and exporting data from `.a2l` files.
- It features a GUI for interactive parameter search, a data parsing layer that processes A2L file structures into structured data, and export capabilities to Excel.
- The diagram below illustrates the high-level architecture, showing how user actions flow through the GUI, data processing logic, and file operations.


```mermaid
graph LR

%% Style definitions
classDef user fill:#f4e1d2,stroke:#c97c5d,stroke-width:2px,color:#000,font-weight:bold
classDef entry fill:#dbeafe,stroke:#3b82f6,stroke-width:2px,color:#000
classDef gui fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#000
classDef data fill:#fef9c3,stroke:#eab308,stroke-width:2px,color:#000
classDef file fill:#fde68a,stroke:#d97706,stroke-width:2px,color:#000
classDef df fill:#f0abfc,stroke:#a21caf,stroke-width:2px,color:#000

%% ========= Top-level =========
U[User]:::user -->|Launch| MAIN[main.py<br/>Entry point]:::entry
MAIN --> APP[A2LSearchWindow<br/>gui.py]:::gui

%% ========= GUI Layer =========
subgraph GUI [A2L Wizard GUI]
  APP --> ICON[static/wizard.png<br/>Window Icon]:::gui
  APP --> MENUS[MenuBar and Actions]:::gui
  APP --> CTRL[Controls<br/>Type Module Search]:::gui
  APP --> TREE[Results Table]:::gui
  APP --> STATUS[Status Bar]:::gui
  APP --> EXPORT[Export Filtered<br/>to Excel]:::gui
end

%% ========= Data Layer =========
subgraph Data_Layer [A2L Parsing and Search data_utils.py]
  LOAD[load_data path]:::data
  PARSE[parse_a2l_file filepath]:::data
  C1[parse_characteristic]:::data
  M1[parse_measurement]:::data
  MA1[parse_measurement_array]:::data
  CLEAN[clean_text]:::data
  SEARCH[search_parameters data query]:::data
  DICT[param_dict<br/>key value store]:::data
end

APP -->|Load A2L| LOAD
LOAD --> PARSE
PARSE --> C1
PARSE --> M1
PARSE --> MA1
C1 --> DICT
M1 --> DICT
MA1 --> DICT
CLEAN -.-> C1
CLEAN -.-> M1
CLEAN -.-> MA1
APP -->|Filter and Search| SEARCH
SEARCH -->|results| TREE
DICT -->|source for filters| SEARCH

%% ========= Filesystem IO =========
subgraph Filesystem
  A2LFILE[A2L file]:::file
  XLSX[XLSX file]:::file
end

U -->|Select file| A2LFILE
APP -->|read| A2LFILE
EXPORT -->|write| XLSX

%% ========= Dataframes =========
subgraph Dataframes
  PD[pandas DataFrame]:::df
  OXL[openpyxl Excel engine]:::df
end

APP -->|build DataFrame| PD
PD -->|uses engine| OXL
```

## Project Layout

```plaintext
A2L-Wizard/
├── data_utils.py       # A2L parsing and search logic
├── gui.py              # PySide6 GUI implementation
├── main.py             # Application entry point
├── requirements.txt    # Dependency list
├── static/
│   └── wizard.png      
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

