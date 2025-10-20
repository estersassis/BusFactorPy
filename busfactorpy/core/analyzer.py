class RiskAnalyzer:
    """
    Classifies files into risk levels based on Bus Factor metrics.
    """
    @staticmethod
    def classify_risk(n_authors: int, share: float) -> str:
        """
        Applies the documented risk classification rules:
        - Critical (Bus Factor = 1)
        - High (share >= 80%)
        - Medium (60% <= share < 80%)
        - Low (share < 60%)
        """
        if n_authors == 1:
            return "Critical" # Bus Factor = 1
        
        share_percent = share * 100
        
        if share_percent >= 80:
            return "High" # Main author contributes >= 80%
        elif 60 <= share_percent < 80:
            return "Medium" # Main author contributes 60–79%
        else:
            return "Low" # Distributed ownership (< 60%)