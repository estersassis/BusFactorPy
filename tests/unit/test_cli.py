import pandas as pd
from typer.testing import CliRunner
from busfactorpy.cli import app

runner = CliRunner()


def test_cli_version():
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "BusFactorPy Versão:" in result.stdout


def test_cli_analyze_default(monkeypatch, tmp_path):
    # DataFrame sintético simulando saída do miner
    fake_commit_df = pd.DataFrame(
        [
            {
                "file": "src/a.py",
                "author": "a@test.com",
                "lines_added": 10,
                "lines_deleted": 0,
                "commit_hash": "h1",
            },
            {
                "file": "src/a.py",
                "author": "b@test.com",
                "lines_added": 5,
                "lines_deleted": 0,
                "commit_hash": "h2",
            },
        ]
    )

    # Monkeypatch do miner
    from busfactorpy.core import miner as miner_mod

    monkeypatch.setattr(
        miner_mod.GitMiner, "mine_commit_history", lambda self: fake_commit_df
    )

    # Monkeypatch do calculator
    fake_results = pd.DataFrame(
        [
            {
                "file": "src/a.py",
                "n_authors": 2,
                "main_author_share": 0.666,
                "risk_class": "Medium",
                "main_author": "a@test.com",
                "main_author_churn": 10,
                "total_file_churn": 15,
            }
        ]
    )

    from busfactorpy.core import calculator as calc_mod

    monkeypatch.setattr(
        calc_mod.BusFactorCalculator, "calculate", lambda self: fake_results
    )

    # Executa CLI
    result = runner.invoke(app, ["analyze", ".", "--format", "summary"])
    assert result.exit_code == 0
    assert "Analysing repository:" in result.stdout
    assert "Top 10 Arquivos" in result.stdout
    # Checa se gerou o gráfico (pela mensagem)
    assert "charts/top_risky_files.png" in result.stdout


def test_cli_invalid_metric(monkeypatch):
    result = runner.invoke(app, ["analyze", ".", "--metric", "inexistente"])
    assert result.exit_code != 0
    assert "Invalid metric" in result.stdout


def test_cli_invalid_threshold():
    result = runner.invoke(app, ["analyze", ".", "--threshold", "1.5"])
    assert result.exit_code != 0
    assert "Invalid threshold" in result.stdout


def test_cli_group_by_directory_depth(monkeypatch):
    # DataFrame com múltiplos diretórios para simular group-by
    fake_commit_df = pd.DataFrame(
        [
            {
                "file": "tests/unit/test_a.py",
                "author": "a@test.com",
                "lines_added": 10,
                "lines_deleted": 0,
                "commit_hash": "h1",
            },
            {
                "file": "tests/unit/test_a.py",
                "author": "b@test.com",
                "lines_added": 5,
                "lines_deleted": 0,
                "commit_hash": "h2",
            },
            {
                "file": "src/utils/x.py",
                "author": "c@test.com",
                "lines_added": 7,
                "lines_deleted": 0,
                "commit_hash": "h3",
            },
        ]
    )

    from busfactorpy.core import miner as miner_mod

    monkeypatch.setattr(
        miner_mod.GitMiner, "mine_commit_history", lambda self: fake_commit_df
    )

    # Simula resultado agregado (depth=2)
    fake_results = pd.DataFrame(
        [
            {
                "file": "tests/unit",
                "n_authors": 2,
                "main_author_share": 0.666,
                "risk_class": "Medium",
                "main_author": "a@test.com",
                "main_author_churn": 10,
                "total_file_churn": 15,
            },
            {
                "file": "src/utils",
                "n_authors": 1,
                "main_author_share": 1.0,
                "risk_class": "Critical",
                "main_author": "c@test.com",
                "main_author_churn": 7,
                "total_file_churn": 7,
            },
        ]
    )

    from busfactorpy.core import calculator as calc_mod

    monkeypatch.setattr(
        calc_mod.BusFactorCalculator, "calculate", lambda self: fake_results
    )

    result = runner.invoke(
        app,
        [
            "analyze",
            ".",
            "--group-by",
            "directory",
            "--depth",
            "2",
            "--format",
            "summary",
        ],
    )
    assert result.exit_code == 0
    assert "Grouping by: directory (depth=2)" in result.stdout
    # Verifica que diretórios agregados aparecem
    assert "tests/unit" in result.stdout
    assert "src/utils" in result.stdout
