import pandas as pd
from typer.testing import CliRunner
from busfactorpy.cli import app
import re
from datetime import datetime
from unittest.mock import patch, MagicMock
from busfactorpy.core.trend import TrendAnalyzer

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


def test_cli_invalid_since_date():
    result = runner.invoke(app, ["analyze", ".", "--trend", "--since", "data-errada"])
    assert result.exit_code != 0
    assert "Invalid date format" in result.stdout


def test_cli_invalid_until_date():
    result = runner.invoke(app, ["analyze", ".", "--trend", "--until", "2023/13/01"])
    assert result.exit_code != 0
    assert "Invalid date format" in result.stdout


def test_cli_trend_default(monkeypatch):
    
    fake_commit_df = pd.DataFrame([
        {
            "file": "a.py",
            "author": "dev@test.com",
            "date": pd.Timestamp("2024-01-01", tz="UTC"),
            "commit_hash": "h1",
            "lines_added": 10, "lines_deleted": 0
        }
    ])
    from busfactorpy.core import miner as miner_mod
    monkeypatch.setattr(miner_mod.GitMiner, "mine_commit_history", lambda self: fake_commit_df)

    with patch("busfactorpy.cli.TrendAnalyzer") as MockTrend:
        fake_trend_df = pd.DataFrame({
            "date": [datetime(2024, 1, 1)],
            "risky_percentage": [50.0],
            "total_files": [1]
        })
        MockTrend.return_value.analyze.return_value = fake_trend_df

        result = runner.invoke(app, [
            "analyze", ".", 
            "--trend", 
            "--since", "2024-01-01", 
            "--window", "60", 
            "--step", "15"
        ])

        assert result.exit_code == 0
        assert "Running Trend Analysis" in result.stdout
        
        MockTrend.assert_called_once()
        
        MockTrend.return_value.analyze.assert_called_once()
        
        call_kwargs = MockTrend.return_value.analyze.call_args[1]
        
        assert isinstance(call_kwargs['start_date'], datetime)
        assert call_kwargs['start_date'].year == 2024
        assert call_kwargs['window_days'] == 60
        assert call_kwargs['step_days'] == 15