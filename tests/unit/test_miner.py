import sys
import subprocess
import shutil
from pathlib import Path
import pytest

from busfactorpy.core.miner import GitMiner
from busfactorpy.core.ignore import BusFactorIgnore


def _git(cmd, cwd: Path):
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"Git command failed: {' '.join(cmd)}\nSTDERR:\n{result.stderr}"
        )
    return result.stdout.strip()


def normalize(path: str) -> str:
    return path.replace("\\", "/")


def create_repo_with_commits(tmp_path: Path):
    _git(["git", "init"], tmp_path)

    def commit_file(rel_path: str, content: str, name: str, email: str, msg: str):
        file_path = tmp_path / rel_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")
        _git(["git", "add", rel_path], tmp_path)
        _git(
            [
                "git",
                "-c",
                f"user.name={name}",
                "-c",
                f"user.email={email}",
                "commit",
                "-m",
                msg,
            ],
            tmp_path,
        )

    commit_file("src/a.py", "print('A1')\n", "AuthorA", "a@test.com", "Add a.py by A")
    commit_file(
        "src/a.py",
        "print('A2 changed by B')\n",
        "AuthorB",
        "b@test.com",
        "Modify a.py by B",
    )
    commit_file(
        "src/utils/b.py", "print('B util')\n", "AuthorB", "b@test.com", "Add b.py by B"
    )
    commit_file(
        "tests/unit/test_x.py",
        "print('test file')\n",
        "AuthorC",
        "c@test.com",
        "Add test_x.py by C",
    )
    commit_file(
        "src/ignored.py",
        "print('ignore')\n",
        "AuthorA",
        "a@test.com",
        "Add ignored.py by A",
    )


@pytest.fixture
def git_repo(tmp_path: Path):
    create_repo_with_commits(tmp_path)
    return tmp_path


def test_miner_basic(git_repo):
    ignorer = BusFactorIgnore(
        ignore_file_path=".busfactorignore", root_path=str(git_repo)
    )
    miner = GitMiner(str(git_repo), ignorer)
    df = miner.mine_commit_history()
    assert not df.empty

    files_norm = [normalize(f) for f in df["file"]]
    assert "src/a.py" in files_norm
    assert "src/utils/b.py" in files_norm

    authors_a = df[[normalize(f) == "src/a.py" for f in df["file"]]]["author"].unique()
    assert set(authors_a) == {"a@test.com", "b@test.com"}


def test_miner_scope_filters_only_prefix(git_repo):
    ignorer = BusFactorIgnore(
        ignore_file_path=".busfactorignore", root_path=str(git_repo)
    )
    miner = GitMiner(str(git_repo), ignorer, scope="src/utils")
    df = miner.mine_commit_history()

    files_norm = [normalize(f) for f in df["file"]]
    assert files_norm  # não vazio
    assert "src/utils/b.py" in files_norm
    assert "src/a.py" not in files_norm


def test_miner_scope_root_file_excluded(git_repo):
    ignorer = BusFactorIgnore(
        ignore_file_path=".busfactorignore", root_path=str(git_repo)
    )
    miner = GitMiner(str(git_repo), ignorer, scope="tests")
    df = miner.mine_commit_history()

    files_norm = [normalize(f) for f in df["file"]]
    assert "tests/unit/test_x.py" in files_norm
    assert "src/a.py" not in files_norm


def test_miner_scope_no_results(git_repo):
    ignorer = BusFactorIgnore(
        ignore_file_path=".busfactorignore", root_path=str(git_repo)
    )
    miner = GitMiner(str(git_repo), ignorer, scope="does/not/exist")
    df = miner.mine_commit_history()
    assert df.empty


def test_miner_scope_normalization(git_repo):
    ignorer = BusFactorIgnore(
        ignore_file_path=".busfactorignore", root_path=str(git_repo)
    )
    miner1 = GitMiner(str(git_repo), ignorer, scope="src/utils/")
    miner2 = GitMiner(str(git_repo), ignorer, scope="src\\utils")
    df1 = miner1.mine_commit_history()
    df2 = miner2.mine_commit_history()
    files1 = sorted(normalize(f) for f in df1["file"])
    files2 = sorted(normalize(f) for f in df2["file"])
    assert files1 == files2


def test_miner_ignore_file(git_repo):
    ignore_content = "src/ignored.py\ntests/\n"
    ignore_path = git_repo / ".busfactorignore"
    ignore_path.write_text(ignore_content, encoding="utf-8")

    ignorer = BusFactorIgnore(
        ignore_file_path=str(ignore_path), root_path=str(git_repo)
    )
    miner = GitMiner(str(git_repo), ignorer)
    df = miner.mine_commit_history()

    files_norm = [normalize(f) for f in df["file"]]
    assert "src/ignored.py" not in files_norm
    assert "tests/unit/test_x.py" not in files_norm
    assert "src/a.py" in files_norm


def test_miner_lines_added_deleted(git_repo):
    ignorer = BusFactorIgnore(
        ignore_file_path=".busfactorignore", root_path=str(git_repo)
    )
    miner = GitMiner(str(git_repo), ignorer)
    df = miner.mine_commit_history()

    a_rows = df[[normalize(f) == "src/a.py" for f in df["file"]]]
    # Deve ter pelo menos dois commits diferentes
    assert len(a_rows) >= 2
    assert (a_rows["lines_added"] >= 0).all()


@pytest.mark.skipif(
    sys.platform.startswith("win"),
    reason="Skip clone simulation on Windows (file locking)",
)
def test_miner_remote_clone_simulado(monkeypatch, git_repo, tmp_path):
    def fake_clone_from(url, to_path):
        # Simula clone: copia tudo
        for item in git_repo.iterdir():
            dest = Path(to_path) / item.name
            if item.is_dir():
                shutil.copytree(item, dest)
            else:
                shutil.copy2(item, dest)

    from git import Repo as GitRepo

    monkeypatch.setattr(GitRepo, "clone_from", fake_clone_from)

    ignorer = BusFactorIgnore(
        ignore_file_path=".busfactorignore", root_path=str(git_repo)
    )
    miner = GitMiner("http://fake.url/repo.git", ignorer)
    df = miner.mine_commit_history()

    files_norm = [normalize(f) for f in df["file"]]
    assert "src/a.py" in files_norm
