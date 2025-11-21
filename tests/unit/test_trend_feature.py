import pytest
import pandas as pd
from datetime import datetime
from unittest.mock import MagicMock, patch
from typer.testing import CliRunner
from busfactorpy.cli import app
from busfactorpy.core.trend import TrendAnalyzer

runner = CliRunner()

@pytest.fixture
def mock_commit_data():
    """Cria um DataFrame falso simulando um histórico de commits."""
    dates = [
        datetime(2023, 1, 1),
        datetime(2023, 2, 1),
        datetime(2023, 3, 1),
        datetime(2023, 4, 1),
    ]
    data = []
    for i, d in enumerate(dates):
        data.append({
            'hash': f'hash_{i}',
            'msg': 'fix',
            'author_name': 'Dev A',
            'author_email': 'a@example.com',
            'date': pd.Timestamp(d), 
            'files': ['file1.py']
        })
    return pd.DataFrame(data)

def test_trend_analyzer_logic(mock_commit_data):
    with patch('busfactorpy.core.trend.BusFactorCalculator') as MockCalc:
        mock_result = pd.DataFrame({
            'Bus Factor': [1, 5], 
            'File': ['a.py', 'b.py'],
            'risk_class': ['Critical', 'Low']
        })
        MockCalc.return_value.calculate.return_value = mock_result

        analyzer = TrendAnalyzer(mock_commit_data, {})
        
        df_trend = analyzer.analyze(
            start_date=datetime(2023, 2, 1),
            end_date=datetime(2023, 4, 1),
            window_days=30,
            step_days=30
        )
        
        assert not df_trend.empty
        assert len(df_trend) >= 2 
        assert 'risky_percentage' in df_trend.columns

def test_trend_analyzer_missing_bus_factor_column(mock_commit_data):
    with patch('busfactorpy.core.trend.BusFactorCalculator') as MockCalc:
        mock_result = pd.DataFrame({
            'File': ['a.py'],
            'risk_class': ['Critical']
        })
        MockCalc.return_value.calculate.return_value = mock_result
        
        analyzer = TrendAnalyzer(mock_commit_data, {})
        df_trend = analyzer.analyze(
            start_date=datetime(2023, 2, 1),
            end_date=datetime(2023, 2, 28),
            window_days=30,
            step_days=30
        )
        
        assert df_trend.iloc[0]['risky_files'] == 1

def test_cli_trend_command_integration():
    with patch('busfactorpy.cli.GitMiner') as MockMiner, \
         patch('busfactorpy.cli.TrendAnalyzer') as MockTrend, \
         patch('busfactorpy.cli.BusFactorVisualizer') as MockViz:
        
        fake_commits = pd.DataFrame({
            'date': [pd.Timestamp('2023-01-01', tz='UTC')],
            'hash': ['abc'],
            'author_name': ['Dev']
        })
        MockMiner.return_value.mine_commit_history.return_value = fake_commits
        
        fake_trend_result = pd.DataFrame({
            'date': [datetime(2023, 1, 1)],
            'risky_percentage': [50.0]
        })
        MockTrend.return_value.analyze.return_value = fake_trend_result

        result = runner.invoke(app, ["analyze", ".", "--trend", "--window", "60", "--step", "30"])
        
        assert result.exit_code == 0
        assert "Running Trend Analysis" in result.stdout
        MockViz.return_value.plot_trend.assert_called_once()