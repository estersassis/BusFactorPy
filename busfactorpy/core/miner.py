import os
import shutil
import tempfile
import pandas as pd
from pydriller import Repository
from git import Repo, GitCommandError

class GitMiner:
    """
    Handles repository cloning and commit history extraction using PyDriller.
    """
    def __init__(self, path_to_repo: str):
        self.repo_path = path_to_repo
        self.temp_dir = None
        self.is_cloned = False
    
    def _clone_repo(self):
        """Clones a remote GitHub URL into a temporary directory."""
        if self.repo_path.startswith(("http", "git@")):
            self.temp_dir = tempfile.mkdtemp(prefix="busfactorpy_")
            try:
                Repo.clone_from(self.repo_path, self.temp_dir)
                self.repo_path = self.temp_dir
                self.is_cloned = True
                print(f"Cloned repository to: {self.repo_path}")
            except GitCommandError as e:
                self.cleanup()
                raise ConnectionError(f"Failed to clone repository: {e}")
    
    def _extract_data(self) -> pd.DataFrame:
        """Iterates commits and extracts file changes and authors."""
        data = []
        for commit in Repository(self.repo_path).traverse_commits():
            for modification in commit.modified_files:
                data.append({
                    'file': modification.new_path if modification.new_path else modification.old_path,
                    'author': commit.author.email,
                    'lines_added': modification.added_lines,
                    'lines_deleted': modification.deleted_lines,
                    'commit_hash': commit.hash
                })
        
        return pd.DataFrame(data).dropna(subset=['file'])
    
    def mine_commit_history(self) -> pd.DataFrame:
        """The main method to run cloning and extraction."""
        if not os.path.exists(self.repo_path):
            self._clone_repo()

        df = self._extract_data()

        self.cleanup()
        
        return df

    def cleanup(self):
        """Removes the temporary cloned repository directory."""
        if self.is_cloned and self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
            self.is_cloned = False
            self.temp_dir = None