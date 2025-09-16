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
