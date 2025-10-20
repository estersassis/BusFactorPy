import pandas as pd
from .analyzer import RiskAnalyzer


class BusFactorCalculator:
    """
    Calculates Bus Factor metrics based on raw commit data (Pandas DataFrame).
    """
    def __init__(self, commit_data: pd.DataFrame):
        self.data = commit_data
    
    def _count_authors_per_file(self) -> pd.DataFrame:
        """
        Counts unique authors per file and calculates the share of changes 
        made by the top contributor (based on total lines changed/churn).
        """
        author_churn = self.data.groupby(['file', 'author']).agg(
            total_churn=('lines_added', lambda x: x.sum() + self.data.loc[x.index, 'lines_deleted'].sum())
        ).reset_index()

        file_metrics = author_churn.groupby('file').agg(
            n_authors=('author', 'nunique'),
            total_file_churn=('total_churn', 'sum'),
            main_author_churn=('total_churn', 'max')
        ).reset_index()

        file_metrics['main_author_share'] = (
            file_metrics['main_author_churn'] / file_metrics['total_file_churn']
        ).fillna(0)
        
        return file_metrics
    
    def calculate(self) -> pd.DataFrame:
        """
        Main method to compute Bus Factor metrics and apply risk analysis.
        """
        file_metrics = self._count_authors_per_file()
        
        file_metrics['risk_class'] = file_metrics.apply(
            lambda row: RiskAnalyzer.classify_risk(
                n_authors=row['n_authors'],
                share=row['main_author_share']
            ), axis=1
        )
        
        return file_metrics