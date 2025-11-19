import pandas as pd
import numpy as np
from .analyzer import RiskAnalyzer


class BusFactorCalculator:
    """
    Calculates Bus Factor metrics based on raw commit data (Pandas DataFrame).
    """

    def __init__(
            self, 
            commit_data: pd.DataFrame, 
            metric: str = "churn", 
            threshold: float = 0.8,
            group_by: str = "file",
            depth: int = 1
        ):
        self.metric = metric.lower()
        self.threshold = threshold
        self.valid_metrics = {"churn", "entropy", "hhi", "ownership", "commit-number"}

        if self.metric not in self.valid_metrics:
            raise ValueError(
                f"Invalid metric '{metric}'. "
                f"Valid metrics: {', '.join(self.valid_metrics)}"
            )
    
        group_by = (group_by or "file").lower()
        if group_by not in {"file", "directory"}:
            raise ValueError("group_by must be 'file' or 'directory'.")

        if group_by == "directory":
            if depth < 1:
                raise ValueError("depth must be >= 1 when grouping by directory.")
            self.data = self._apply_directory_grouping(commit_data, depth)
        else:
            self.data = commit_data
    
    def _dir_key_and_depth(self, path: str, depth: int) -> tuple[str, int]:
        """
        Convert a file path to a directory key with the given depth and return its depth.
        Depth is the number of path segments in the directory key.
        Examples:
          - 'src/app/main.py' with depth=1 -> ('src', 1)
          - 'src/app/main.py' with depth=2 -> ('src/app', 2)
          - 'main.py' (repo root) -> ('.', 0)
        """
        if not isinstance(path, str):
            return ".", 0
        norm = path.replace("\\", "/").strip("/")
        if not norm:
            return ".", 0
        parts = norm.split("/")
        if len(parts) <= 1:
            # file directly at repo root
            return ".", 0
        dirs = parts[:-1]
        key = "/".join(dirs[:depth]).strip("/")
        if not key:
            return ".", 0
        return key, len(key.split("/"))

    def _apply_directory_grouping(self, df: pd.DataFrame, depth: int) -> pd.DataFrame:
        """
        Build directory key and filter rows to keep ONLY entries whose directory key
        has exactly the requested depth.
        """
        tmp = df.copy()
        keys_and_depths = tmp["file"].apply(lambda p: self._dir_key_and_depth(p, depth))
        tmp["__dir_key__"] = keys_and_depths.apply(lambda t: t[0])
        tmp["__dir_depth__"] = keys_and_depths.apply(lambda t: t[1])

        # Keep ONLY the exact depth (exclude shallower groups like '.' or 'tests' when depth=2)
        tmp = tmp[tmp["__dir_depth__"] == depth]

        # Replace file by the directory key to reuse metric pipelines
        tmp["file"] = tmp["__dir_key__"]
        tmp = tmp.drop(columns=["__dir_key__", "__dir_depth__"])
        return tmp

    # =============================================================
    # BASE EXTRACTION: author × file × churn
    # =============================================================
    def _aggregate_author_churn(self) -> pd.DataFrame:
        """
        Returns a table: file | author | total_churn
        """
        author_churn = self.data.groupby(['file', 'author']).agg(
            total_churn=('lines_added',
                lambda x: x.sum() + self.data.loc[x.index, 'lines_deleted'].sum())
        ).reset_index()

        return author_churn

    # =============================================================
    # METRIC IMPLEMENTATIONS
    # =============================================================

    def _metric_churn(self, author_churn: pd.DataFrame) -> pd.DataFrame:
        """
        Counts unique authors per file and calculates the share of changes 
        made by the top contributor (based on total lines changed/churn).
        """
        # Identify main contributor (highest churn)
        idx_max = author_churn.loc[
            author_churn.groupby('file')['total_churn'].idxmax()
        ]

        main_author_data = idx_max[['file', 'author', 'total_churn']].rename(
            columns={'author': 'main_author', 'total_churn': 'main_author_churn'}
        )

        # Aggregate file-level churn and authors
        file_metrics = author_churn.groupby('file').agg(
            n_authors=('author', 'nunique'),
            total_file_churn=('total_churn', 'sum')
        ).reset_index()

        file_metrics = file_metrics.merge(main_author_data, on='file', how='left')

        file_metrics['main_author_share'] = (
            file_metrics['main_author_churn'] / file_metrics['total_file_churn']
        ).fillna(0)

        return file_metrics

    def _metric_entropy(self, author_churn: pd.DataFrame) -> pd.DataFrame:
        """
        Shannon entropy of contributions per file.
        """
        def shannon_entropy(group):
            churn = group['total_churn'].values
            p = churn / churn.sum()
            return -np.sum(p * np.log2(p))

        entropy_df = author_churn.groupby('file')[['author', 'total_churn']].apply(
            lambda g: pd.Series({
                "entropy": shannon_entropy(g),
                "n_authors": g['author'].nunique(),
                "total_file_churn": g['total_churn'].sum()
            })
        ).reset_index()

        # Normalize entropy so it can be used as a share-like metric (High value = High Risk)
        # Normal entropy: High value = Distributed (Low Risk).
        # We invert it: 1 - (H / H_max), where H_max = log2(n_authors)
        # If n_authors=1, entropy is 0, share is 1.0
        
        def normalize_entropy_risk(row):
            if row['n_authors'] <= 1:
                return 1.0
            max_entropy = np.log2(row['n_authors'])
            if max_entropy == 0:
                return 1.0
            return 1 - (row['entropy'] / max_entropy)

        entropy_df['main_author_share'] = entropy_df.apply(normalize_entropy_risk, axis=1)
        
        entropy_df['main_author'] = None
        entropy_df['main_author_churn'] = None

        return entropy_df

    def _metric_hhi(self, author_churn: pd.DataFrame) -> pd.DataFrame:
        """
        Herfindahl-Hirschman Index (HHI).
        """
        def compute_hhi(group):
            churn = group['total_churn'].values
            p = churn / churn.sum()
            return np.sum(p**2)

        hhi_df = author_churn.groupby('file')[['author', 'total_churn']].apply(
            lambda g: pd.Series({
                "hhi": compute_hhi(g),
                "n_authors": g['author'].nunique(),
                "total_file_churn": g['total_churn'].sum()
            })
        ).reset_index()

        # HHI ranges from 1/N to 1. 1 means monopoly (High Risk).
        hhi_df['main_author_share'] = hhi_df['hhi']

        hhi_df['main_author'] = None
        hhi_df['main_author_churn'] = None

        return hhi_df

    def _metric_commit_count(self) -> pd.DataFrame:
        """
        Calculates share based on pure number of commits (frequency), 
        ignoring lines changed.
        """
        # Count commits per file per author
        # Note: We use self.data directly here, not author_churn
        commits_df = self.data.groupby(['file', 'author']).size().reset_index(name='commits')

        idx_max = commits_df.loc[
            commits_df.groupby('file')['commits'].idxmax()
        ]

        main_author_data = idx_max[['file', 'author', 'commits']].rename(
            columns={'author': 'main_author', 'commits': 'main_author_commits'}
        )

        file_metrics = commits_df.groupby('file').agg(
            n_authors=('author', 'nunique'),
            total_commits=('commits', 'sum')
        ).reset_index()

        file_metrics = file_metrics.merge(main_author_data, on='file', how='left')

        file_metrics['main_author_share'] = (
            file_metrics['main_author_commits'] / file_metrics['total_commits']
        ).fillna(0)
        
        file_metrics['total_file_churn'] = None 
        file_metrics['main_author_churn'] = None

        return file_metrics

    def calculate(self) -> pd.DataFrame:
        
        # Aggregation based on churn (lines) is needed for churn, entropy, hhi
        # Commit count logic uses raw data directly
        
        if self.metric == "churn":
            result = self._metric_churn(self._aggregate_author_churn())

        elif self.metric == "entropy":
            result = self._metric_entropy(self._aggregate_author_churn())

        elif self.metric == "hhi":
            result = self._metric_hhi(self._aggregate_author_churn())

        elif self.metric == "ownership":
             # Mapping ownership to commit count as per typical implementation, 
             # or could remain alias for churn depending on definition. 
             # Given previous file, it was commit-based.
            result = self._metric_commit_count()

        elif self.metric == "commit-number":
            result = self._metric_commit_count()

        # Add risk classification with dynamic threshold
        result['risk_class'] = result.apply(
            lambda row: RiskAnalyzer.classify_risk(
                n_authors=row['n_authors'],
                share=row['main_author_share'],
                threshold=self.threshold
            ), axis=1
        )

        return result