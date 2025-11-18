import pytest
import pandas as pd
import numpy as np
from busfactorpy.core.calculator import BusFactorCalculator

@pytest.fixture
def sample_commit_data():
    """
    Creates a DataFrame simulating a commit history with specific scenarios:
    
    1. 'mono_author.py': Only Author A (Critical Risk).
    2. 'high_churn_low_commits.py': 
       - Author A: 1000 lines, 1 commit.
       - Author B: 10 lines, 10 commits.
       -> Useful to test the difference between 'churn' and 'commit-number'.
    3. 'distributed.py':
       - Author A: 50 lines.
       - Author B: 50 lines.
       -> Perfect distribution (High Entropy, Low HHI).
    """
    data = [
        # File 1: Monopoly (Author A)
        {'file': 'mono_author.py', 'author': 'a@test.com', 'lines_added': 100, 'lines_deleted': 0, 'commit_hash': 'h1'},
        
        # File 2: Conflict (A has Churn, B has Frequency)
        {'file': 'conflict.py', 'author': 'a@test.com', 'lines_added': 1000, 'lines_deleted': 0, 'commit_hash': 'h2'},
        # Author B makes 10 small commits
        {'file': 'conflict.py', 'author': 'b@test.com', 'lines_added': 1, 'lines_deleted': 0, 'commit_hash': 'h3'},
        {'file': 'conflict.py', 'author': 'b@test.com', 'lines_added': 1, 'lines_deleted': 0, 'commit_hash': 'h4'},
        {'file': 'conflict.py', 'author': 'b@test.com', 'lines_added': 1, 'lines_deleted': 0, 'commit_hash': 'h5'},
        {'file': 'conflict.py', 'author': 'b@test.com', 'lines_added': 1, 'lines_deleted': 0, 'commit_hash': 'h6'},
        {'file': 'conflict.py', 'author': 'b@test.com', 'lines_added': 1, 'lines_deleted': 0, 'commit_hash': 'h7'},
        
        # File 3: Distributed (50/50 Churn)
        {'file': 'dist.py', 'author': 'a@test.com', 'lines_added': 50, 'lines_deleted': 0, 'commit_hash': 'h8'},
        {'file': 'dist.py', 'author': 'b@test.com', 'lines_added': 50, 'lines_deleted': 0, 'commit_hash': 'h9'},
    ]
    return pd.DataFrame(data)

def test_invalid_metric_raises_error(sample_commit_data):
    """Tests if an invalid metric raises a ValueError."""
    with pytest.raises(ValueError, match="Invalid metric"):
        BusFactorCalculator(sample_commit_data, metric="magic-metric")

def test_valid_metrics_init(sample_commit_data):
    """Tests initialization with all valid metrics."""
    for m in ["churn", "entropy", "hhi", "ownership", "commit-number"]:
        calc = BusFactorCalculator(sample_commit_data, metric=m)
        assert calc.metric == m

def test_metric_churn_logic(sample_commit_data):
    """
    In 'conflict.py':
    Author A: 1000 lines
    Author B: 5 lines (5 commits of 1 line each)
    Total: 1005
    Main Author by CHURN must be A.
    """
    calc = BusFactorCalculator(sample_commit_data, metric="churn")
    df = calc.calculate()
    
    row = df[df['file'] == 'conflict.py'].iloc[0]
    assert row['main_author'] == 'a@test.com'
    assert row['main_author_churn'] == 1000
    # Share approx 0.99
    assert row['main_author_share'] > 0.99 
    assert row['risk_class'] == "High"

def test_metric_commit_number_logic(sample_commit_data):
    """
    In 'conflict.py':
    Author A: 1 commit
    Author B: 5 commits
    Main Author by COMMIT-NUMBER must be B.
    """
    calc = BusFactorCalculator(sample_commit_data, metric="commit-number")
    df = calc.calculate()
    
    row = df[df['file'] == 'conflict.py'].iloc[0]
    assert row['main_author'] == 'b@test.com' # B wins here
    assert row['main_author_share'] == 5 / 6 # 5 out of 6 total commits
    assert row['risk_class'] == "High"

def test_metric_hhi_logic(sample_commit_data):
    """
    In 'dist.py':
    A: 50 lines, B: 50 lines.
    Share A = 0.5, Share B = 0.5.
    HHI = 0.5^2 + 0.5^2 = 0.25 + 0.25 = 0.5.
    """
    calc = BusFactorCalculator(sample_commit_data, metric="hhi")
    df = calc.calculate()
    
    row = df[df['file'] == 'dist.py'].iloc[0]
    # HHI must be exactly 0.5
    assert pytest.approx(row['main_author_share'], 0.01) == 0.5
    # HHI 0.5 is low risk (if default threshold is 0.8) -> Low
    assert row['risk_class'] == "Low"

def test_metric_entropy_logic(sample_commit_data):
    """
    In 'dist.py' (2 authors, 50/50):
    Shannon Entropy = 1 bit.
    Max Entropy = log2(2) = 1.
    Normalized Risk = 1 - (1/1) = 0.0.
    """
    calc = BusFactorCalculator(sample_commit_data, metric="entropy")
    df = calc.calculate()
    
    row = df[df['file'] == 'dist.py'].iloc[0]
    assert pytest.approx(row['main_author_share'], 0.01) == 0.0
    assert row['risk_class'] == "Low"

def test_single_author_is_critical_always(sample_commit_data):
    """
    In 'mono_author.py', only 1 author.
    Must always be 'Critical', regardless of metric.
    """
    for m in ["churn", "hhi", "entropy"]:
        calc = BusFactorCalculator(sample_commit_data, metric=m)
        df = calc.calculate()
        row = df[df['file'] == 'mono_author.py'].iloc[0]
        assert row['risk_class'] == "Critical"

def test_custom_threshold_changes_risk(sample_commit_data):
    """
    Scenario: Author A has ~66% share.
    
    Default Threshold (0.8):
       High >= 0.8
       Medium >= 0.6 (0.8 * 0.75)
       -> 0.66 falls into MEDIUM.
       
    Strict Threshold (0.6):
       High >= 0.6
       -> 0.66 falls into HIGH.
    """
    # Create custom data for this test
    data = pd.DataFrame([
        {'file': 't.py', 'author': 'A', 'lines_added': 66, 'lines_deleted': 0},
        {'file': 't.py', 'author': 'B', 'lines_added': 34, 'lines_deleted': 0},
    ])
    
    # 1. Test with default (0.8)
    calc_default = BusFactorCalculator(data, metric="churn", threshold=0.8)
    res_default = calc_default.calculate().iloc[0]
    assert res_default['risk_class'] == "Medium" # 0.66 is between 0.6 and 0.8
    
    # 2. Test with low/strict threshold (0.6)
    calc_strict = BusFactorCalculator(data, metric="churn", threshold=0.6)
    res_strict = calc_strict.calculate().iloc[0]
    assert res_strict['risk_class'] == "High" # 0.66 >= 0.6