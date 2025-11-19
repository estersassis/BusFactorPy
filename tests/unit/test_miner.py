import subprocess
from pathlib import Path
import pytest

from busfactorpy.core.miner import GitMiner
from busfactorpy.core.ignore import BusFactorIgnore


def _git(cmd, cwd: Path):
    """Helper para executar comandos git e falhar com mensagem clara."""
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"Git command failed: {' '.join(cmd)}\nSTDERR:\n{result.stderr}"
        )
    return result.stdout.strip()


def create_repo_with_commits(tmp_path: Path):
    """
    Cria um repositório git com alguns commits e autores distintos:
      - src/a.py (autor A, depois autor B)
      - src/utils/b.py (autor B)
      - tests/unit/test_x.py (autor C)
      - src/ignored.py (autor A) que será ignorado em alguns testes
    """
    _git(["git", "init"], tmp_path)

    def commit_file(
        rel_path: str, content: str, author_name: str, author_email: str, msg: str
    ):
        file_path = tmp_path / rel_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")
        _git(["git", "add", rel_path], tmp_path)
        _git(
            [
                "git",
                "-c",
                f"user.name={author_name}",
                "-c",
                f"user.email={author_email}",
                "commit",
                "-m",
                msg,
            ],
            tmp_path,
        )

    # Commit inicial a.py
    commit_file("src/a.py", "print('A1')\n", "AuthorA", "a@test.com", "Add a.py by A")
    # Modificação a.py por B (gera churn)
    commit_file(
        "src/a.py",
        "print('A2 changed by B')\n",
        "AuthorB",
        "b@test.com",
        "Modify a.py by B",
    )
    # Arquivo b.py por B
    commit_file(
        "src/utils/b.py", "print('B util')\n", "AuthorB", "b@test.com", "Add b.py by B"
    )
    # Arquivo de teste por C
    commit_file(
        "tests/unit/test_x.py",
        "print('test file')\n",
        "AuthorC",
        "c@test.com",
        "Add test_x.py by C",
    )
    # Arquivo que será ignorado depois
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
    assert set(
        ["file", "author", "lines_added", "lines_deleted", "commit_hash"]
    ).issubset(df.columns)

    # Deve capturar pelo menos src/a.py e src/utils/b.py
    assert "src/a.py" in df["file"].values
    assert "src/utils/b.py" in df["file"].values

    # Autores distintos para src/a.py (A e B)
    authors_a = df[df["file"] == "src/a.py"]["author"].unique()
    assert set(authors_a) == {"a@test.com", "b@test.com"}


def test_miner_scope_filters_only_prefix(git_repo):
    ignorer = BusFactorIgnore(
        ignore_file_path=".busfactorignore", root_path=str(git_repo)
    )
    # scope 'src/utils' deve incluir src/utils/b.py mas não src/a.py
    miner = GitMiner(str(git_repo), ignorer, scope="src/utils")
    df = miner.mine_commit_history()

    assert not df.empty
    assert all(f.startswith("src/utils") or f == "src/utils" for f in df["file"])
    assert "src/a.py" not in df["file"].values


def test_miner_scope_root_file_excluded(git_repo):
    ignorer = BusFactorIgnore(
        ignore_file_path=".busfactorignore", root_path=str(git_repo)
    )
    # scope 'tests' deve incluir test_x.py
    miner = GitMiner(str(git_repo), ignorer, scope="tests")
    df = miner.mine_commit_history()

    assert "tests/unit/test_x.py" in df["file"].values
    # Não deve incluir src/ arquivos
    assert "src/a.py" not in df["file"].values


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
    # Teste com barra final e backslash
    miner = GitMiner(str(git_repo), ignorer, scope="src/utils/")
    df1 = miner.mine_commit_history()
    miner2 = GitMiner(str(git_repo), ignorer, scope="src\\utils")
    df2 = miner2.mine_commit_history()
    # Ambos devem ser equivalentes
    assert df1.equals(df2)


def test_miner_ignore_file(git_repo, tmp_path):
    """
    Cria um .busfactorignore temporário que ignora 'src/ignored.py' e diretório tests/.
    """
    ignore_content = "src/ignored.py\ntests/\n"
    ignore_path = git_repo / ".busfactorignore"
    ignore_path.write_text(ignore_content, encoding="utf-8")

    ignorer = BusFactorIgnore(
        ignore_file_path=str(ignore_path), root_path=str(git_repo)
    )
    miner = GitMiner(str(git_repo), ignorer)
    df = miner.mine_commit_history()

    assert "src/ignored.py" not in df["file"].values
    # Arquivo de teste deve ter sido ignorado
    assert "tests/unit/test_x.py" not in df["file"].values
    # Ainda deve ter src/a.py
    assert "src/a.py" in df["file"].values


def test_miner_lines_added_deleted(git_repo):
    ignorer = BusFactorIgnore(
        ignore_file_path=".busfactorignore", root_path=str(git_repo)
    )
    miner = GitMiner(str(git_repo), ignorer)
    df = miner.mine_commit_history()

    # src/a.py teve duas versões (commit A e commit B)
    a_rows = df[df["file"] == "src/a.py"]
    # Deve haver pelo menos 2 registros (2 commits com modificações)
    assert len(a_rows) >= 2
    # Garantir que linhas adicionadas foram contabilizadas (>=1)
    assert (a_rows["lines_added"] >= 1).all()


def test_miner_remote_clone_simulado(monkeypatch, git_repo, tmp_path):
    """
    Simula clone remoto substituindo Repo.clone_from:
    - Cria uma cópia do diretório local em temp_dir
    - Ajusta repo_path para o temp_dir
    """

    def fake_clone_from(url, to_path):
        # Copia conteúdo do repo local para o diretório destino
        for item in git_repo.iterdir():
            dest = Path(to_path) / item.name
            if item.is_dir():
                shutil.copytree(item, dest)
            else:
                shutil.copy2(item, dest)

    import shutil
    from git import Repo as GitRepo

    monkeypatch.setattr(GitRepo, "clone_from", fake_clone_from)

    ignorer = BusFactorIgnore(
        ignore_file_path=".busfactorignore", root_path=str(git_repo)
    )

    # Usa uma URL fake começando com http para disparar _clone_repo
    miner = GitMiner("http://fake.url/repo.git", ignorer)
    df = miner.mine_commit_history()

    # Após mineração via clone simulado, deve existir dados
    assert not df.empty
    assert miner.is_cloned is False  # cleanup deve ter resetado
    assert miner.temp_dir is None

    # Verifica que clone realmente funcionou (a.py presente)
    assert "src/a.py" in df["file"].values
