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

## Instalação

Pré-requisitos:
- Python 3.x
- Git

Opção A — Instalar a partir do repositório (recomendado):
```bash
# Clonar o projeto
git clone https://github.com/estersassis/BusFactorPy.git
cd BusFactorPy

# (Opcional) criar ambiente virtual
python -m venv .venv
# Linux/macOS
source .venv/bin/activate
# Windows (PowerShell)
.venv\Scripts\Activate.ps1

# Instalação (modo desenvolvedor)
pip install -e .

# Alternativa: instalar dependências diretamente
pip install -r requirements.txt
```

Opção B — Instalar direto via pip (a partir do Git):
```bash
pip install "git+https://github.com/estersassis/BusFactorPy.git"
```

## Execução (CLI)

Exibir ajuda geral:
```bash
busfactorpy --help
```

Exibir versão:
```bash
busfactorpy version
```

Analisar um repositório local com resumo no terminal:
```bash
busfactorpy analyze . --format summary --top-n 10
```

Analisar um repositório remoto (GitHub URL) e exportar JSON:
```bash
busfactorpy analyze https://github.com/owner/repo -f json
```

Exportar CSV:
```bash
busfactorpy analyze . -f csv
```

Parâmetros principais:
- `repository` (posicional): caminho local ou URL do repositório Git a analisar.
- `--format, -f`: `summary` (padrão), `csv` ou `json`.
- `--top-n, -n`: quantidade de arquivos mais arriscados no relatório/visualização (padrão: 10).

## Saídas e artefatos gerados

- Relatórios:
  - `reports/busfactorpy_report.csv` (quando `-f csv`)
  - `reports/busfactorpy_report.json` (quando `-f json`)
- Visualização:
  - `charts/top_risky_files.png` (gráfico de barras com os Top N arquivos por dominância do autor)
- Resumo no terminal quando `--format summary`

## Desenvolvimento local

Rodar a partir do código (sem instalar como pacote):
```bash
# No diretório do projeto
python -m busfactorpy.cli analyze . --format summary -n 10
```

Atualizar dependências:
```bash
pip install -r requirements.txt
```