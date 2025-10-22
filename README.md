# BusFactorPy

## Group Members

- Ester Sara Assis Silva
- Filipe Pirola Santos
- Matheus Grandinetti Barbosa Lima
- Vitor Costa

## System Explanation

The system is a **Python-based command-line tool** designed to measure the **Bus Factor** of a Git repository.  
It analyzes the commit history to identify files that are dominated by a small number of contributors, especially those maintained by a **single developer**.  

Such files represent a **knowledge concentration risk**: if the main contributor leaves the project, those parts of the code may become difficult or impossible to maintain.  

**How it works:**
1. **Extract commit history** from a Git repository (local path or GitHub URL).  
2. **Count unique contributors** per file and measure the proportion of changes made by the top contributor.  
3. **Classify risk levels**:  
   - **Critical** → Bus Factor = 1 (only one contributor).  
   - **High** → main author contributes ≥ 80% of changes.  
   - **Medium** → main author contributes 60–79%.  
   - **Low** → distributed ownership (< 60%).  
4. **Generate reports and visualizations** to highlight critical files.  

**Outputs:**
- CSV/JSON reports with metrics: `file, n_authors, main_author_share, risk_class`.  
- Bar charts of the top-N risky files.  
- CLI summary listing **critical and high-risk files**.

## Technologies

- **[PyDriller](https://github.com/ishepard/pydriller)** → mine Git history (commits, authors, files, churn).  
- **[GitPython](https://github.com/gitpython-developers/GitPython)** → Git repository operations (clone, checkout, branches).  
- **[Typer](https://github.com/fastapi/typer)** → build the command-line interface in Python.  
- **[Pandas](https://pandas.pydata.org/)** → data manipulation, aggregation, and CSV/JSON export.  
- **[Matplotlib](https://matplotlib.org/)** → visualizations (bar plots for author dominance).  
- **[Rich](https://github.com/Textualize/rich)** → improved CLI output with colors and tables.

## Installation

Prerequisites:
- Python 3.x
- Git

Option A — Install from repository (recommended):
```bash
# Clone the project
git clone https://github.com/estersassis/BusFactorPy.git
cd BusFactorPy

# (Optional) create virtual environment
python -m venv .venv
# Linux/macOS
source .venv/bin/activate
# Windows (PowerShell)
.venv\Scripts\Activate.ps1

# Installation (developer mode)
pip install -e .

# Alternative: install dependencies directly
pip install -r requirements.txt
```

Option B — Install directly via pip (from Git):
```bash
pip install "git+https://github.com/estersassis/BusFactorPy.git"
```

## Usage (CLI)

Display general help:
```bash
busfactorpy --help
```

Display version:
```bash
busfactorpy version
```

Analyze a local repository with terminal summary:
```bash
busfactorpy analyze . --format summary --top-n 10
```

Analyze a remote repository (GitHub URL) and export JSON:
```bash
busfactorpy analyze https://github.com/owner/repo -f json
```

Export CSV:
```bash
busfactorpy analyze . -f csv
```

Main parameters:
- `repository` (positional): local path or URL of the Git repository to analyze.
- `--format, -f`: `summary` (default), `csv` or `json`.
- `--top-n, -n`: number of riskiest files in the report/visualization (default: 10).

## Outputs and Generated Artifacts

- Reports:
  - `reports/busfactorpy_report.csv` (when `-f csv`)
  - `reports/busfactorpy_report.json` (when `-f json`)
- Visualization:
  - `charts/top_risky_files.png` (bar chart with Top N files by author dominance)
- Terminal summary when `--format summary`

## Local Development

Run from source code (without installing as package):
```bash
# In the project directory
python -m busfactorpy.cli analyze . --format summary -n 10
```

Update dependencies:
```bash
pip install -r requirements.txt
```