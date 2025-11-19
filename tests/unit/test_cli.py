import pandas as pd
from typer.testing import CliRunner
from busfactorpy.cli import app

runner = CliRunner()


def normalize(s: str) -> str:
    return s.replace("\\", "/")


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

    from busfactorpy.core import miner as miner_mod

    monkeypatch.setattr(
        miner_mod.GitMiner, "mine_commit_history", lambda self: fake_commit_df
    )

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

    result = runner.invoke(app, ["analyze", ".", "--format", "summary"])
    assert result.exit_code == 0
    out_norm = normalize(result.stdout)
    assert "Analysing repository:" in out_norm
    assert "Top 10 Arquivos" in out_norm
    # Caminho do gráfico normalizado
    assert "charts/top_risky_files.png" in out_norm


def test_cli_invalid_metric():
    result = runner.invoke(app, ["analyze", ".", "--metric", "inexistente"])
    assert result.exit_code != 0
    assert "Invalid metric" in result.stdout


def test_cli_invalid_threshold():
    result = runner.invoke(app, ["analyze", ".", "--threshold", "1.5"])
    assert result.exit_code != 0
    assert "Invalid threshold" in result.stdout
