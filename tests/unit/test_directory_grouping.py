import pandas as pd
from busfactorpy.core.calculator import BusFactorCalculator


def sample_dir_data():
    """
    Cria um DataFrame com arquivos em diferentes níveis de diretório:
      - tests/test_a.py                  -> tests (nível 1)
      - tests/unit/test_b.py            -> tests/unit (nível 2)
      - src/app/main.py                 -> src/app (nível 2)
      - src/utils/helpers.py            -> src/utils (nível 2)
      - main.py                         -> raiz (.)
    """
    return pd.DataFrame(
        [
            {
                "file": "tests/test_a.py",
                "author": "A",
                "lines_added": 10,
                "lines_deleted": 0,
            },
            {
                "file": "tests/unit/test_b.py",
                "author": "A",
                "lines_added": 5,
                "lines_deleted": 0,
            },
            {
                "file": "tests/unit/test_b.py",
                "author": "B",
                "lines_added": 5,
                "lines_deleted": 0,
            },
            {
                "file": "src/app/main.py",
                "author": "A",
                "lines_added": 20,
                "lines_deleted": 0,
            },
            {
                "file": "src/utils/helpers.py",
                "author": "C",
                "lines_added": 30,
                "lines_deleted": 0,
            },
            {"file": "main.py", "author": "A", "lines_added": 1, "lines_deleted": 0},
        ]
    )


def test_group_by_directory_depth_1():
    """
    Depth=1 deve agrupar somente diretórios de primeiro nível (sem '.'),
    e consolidar subníveis dentro do nível 1 (ex.: tests/unit entra em 'tests').
    """
    df = sample_dir_data()
    calc = BusFactorCalculator(df, metric="churn", group_by="directory", depth=1)
    res = calc.calculate()

    # Espera-se apenas os diretórios de nível 1 presentes: 'tests' e 'src'
    dirs = sorted(res["file"].unique().tolist())
    assert dirs == ["src", "tests"]

    # 'tests' agrega contribuições de tests/ e tests/unit/
    tests_row = res[res["file"] == "tests"].iloc[0]
    assert tests_row["n_authors"] >= 2  # A e B contribuíram via tests/unit


def test_group_by_directory_depth_2():
    """
    Depth=2 deve retornar somente diretórios exatamente no nível 2:
    - 'tests/unit'
    - 'src/app'
    - 'src/utils'
    E não deve retornar 'tests' (nível 1) nem '.' (nível 0).
    """
    df = sample_dir_data()
    calc = BusFactorCalculator(df, metric="churn", group_by="directory", depth=2)
    res = calc.calculate()

    dirs = sorted(res["file"].unique().tolist())
    assert dirs == ["src/app", "src/utils", "tests/unit"]

    # Validar autores por diretório
    unit_row = res[res["file"] == "tests/unit"].iloc[0]
    assert unit_row["n_authors"] == 2  # A e B em tests/unit/test_b.py

    app_row = res[res["file"] == "src/app"].iloc[0]
    assert app_row["n_authors"] == 1  # só A

    utils_row = res[res["file"] == "src/utils"].iloc[0]
    assert utils_row["n_authors"] == 1  # só C

    # Em tests/unit a contribuição de A e B é 50/50 => Low (com threshold padrão 0.8)
    assert unit_row["risk_class"] in {"Low", "Medium", "High", "Critical"}
    # Checagem mais específica para a métrica churn: 5 e 5 => 0.5 => Low
    assert unit_row["risk_class"] == "Low"
