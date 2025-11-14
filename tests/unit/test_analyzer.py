import pytest
from busfactorpy.core.analyzer import RiskAnalyzer


class TestRiskAnalyzer:
    """Test cases for the RiskAnalyzer class."""
    
    def test_classify_risk_critical(self):
        """Test that files with only one author are classified as Critical."""
        result = RiskAnalyzer.classify_risk(n_authors=1, share=1.0)
        assert result == "Critical"
        
        # Even if share is lower, single author should still be Critical
        result = RiskAnalyzer.classify_risk(n_authors=1, share=0.5)
        assert result == "Critical"
    
    def test_classify_risk_high(self):
        """Test that files with >= 80% share are classified as High."""
        result = RiskAnalyzer.classify_risk(n_authors=2, share=0.80)
        assert result == "High"
        
        result = RiskAnalyzer.classify_risk(n_authors=3, share=0.95)
        assert result == "High"
    
    def test_classify_risk_medium(self):
        """Test that files with 60-79% share are classified as Medium."""
        result = RiskAnalyzer.classify_risk(n_authors=2, share=0.60)
        assert result == "Medium"
        
        result = RiskAnalyzer.classify_risk(n_authors=3, share=0.75)
        assert result == "Medium"
        
        # Test boundary: 79.9% should still be Medium
        result = RiskAnalyzer.classify_risk(n_authors=2, share=0.799)
        assert result == "Medium"
    
    def test_classify_risk_low(self):
        """Test that files with < 60% share are classified as Low."""
        result = RiskAnalyzer.classify_risk(n_authors=3, share=0.50)
        assert result == "Low"
        
        result = RiskAnalyzer.classify_risk(n_authors=5, share=0.30)
        assert result == "Low"
        
        # Test boundary: 59.9% should be Low
        result = RiskAnalyzer.classify_risk(n_authors=2, share=0.599)
        assert result == "Low"
    
    def test_classify_risk_edge_cases(self):
        """Test edge cases for risk classification."""
        # Test with 0 share
        result = RiskAnalyzer.classify_risk(n_authors=2, share=0.0)
        assert result == "Low"
        
        # Test with exactly 60% and 80% boundaries
        result = RiskAnalyzer.classify_risk(n_authors=2, share=0.60)
        assert result == "Medium"
        
        result = RiskAnalyzer.classify_risk(n_authors=2, share=0.80)
        assert result == "High"
