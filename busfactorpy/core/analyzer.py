class RiskAnalyzer:
    """
    Classifies files into risk levels based on Bus Factor metrics.
    """
    @staticmethod
    def classify_risk(n_authors: int, share: float, threshold: float = 0.8) -> str:
        """
        Applies risk classification rules based on a dynamic threshold.
        
        Args:
            n_authors: Number of contributors for the file.
            share: The calculated metric share (0.0 to 1.0).
            threshold: The value above which risk is considered High (default 0.8).
        
        Returns:
            Critical, High, Medium, or Low.
        """
        if n_authors == 1:
            return "Critical" # Bus Factor = 1
        
        # Define Medium threshold as a proportion of the High threshold
        # Example: If threshold is 0.8, medium is approx 0.6 to 0.8
        # If threshold is 0.5, medium is approx 0.375 to 0.5
        medium_threshold = round(threshold * 0.75, 4)
        
        if share >= threshold:
            return "High"
        elif medium_threshold <= share < threshold:
            return "Medium"
        else:
            return "Low"