from pathlib import Path
import pathspec

class BusFactorIgnore:
    """
    Implements .gitignore compatible ignore functionality using pathspec.
    """
    def __init__(self, ignore_file_path: str = ".busfactorignore", root_path: str = "."):
        self.root_path = Path(root_path)
        self.spec = self._load_spec(ignore_file_path)

    def _load_spec(self, ignore_file_path: str):
        ignore_path = Path(ignore_file_path)

        if not ignore_path.exists():
            # If the ignore file does not exist, return an empty spec
            return pathspec.PathSpec.from_lines("gitwildmatch", [])

        with open(ignore_path, "r", encoding="utf-8") as f:
            patterns = f.read().splitlines()

        return pathspec.PathSpec.from_lines("gitwildmatch", patterns)

    def is_ignored(self, file_path: str) -> bool:
        """
        Applies the .gitignore logic.
        Assumes file_path is the path relative to the repository root,
        provided by GitMiner.
        """
        
        rel_path = Path(file_path).as_posix()
        return self.spec.match_file(rel_path)
        