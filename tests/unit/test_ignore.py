import pytest
from pathlib import Path
from busfactorpy.core.ignore import BusFactorIgnore


@pytest.fixture
def create_ignore_file(tmp_path: Path):
    """
    Creates a temporary ignore file in the test directory
    and returns a configured instance of BusFactorIgnore.
    """
    def _creator(content: str, filename: str = ".busfactorignore"):
        file_path = tmp_path / filename
        file_path.write_text(content.strip() + "\n", encoding="utf-8")
        return BusFactorIgnore(
            ignore_file_path=str(file_path),
            root_path=str(tmp_path)
        )
    return _creator


def test_ignore_common_directories(create_ignore_file):
    """Tests the exclusion of common directories (vendor/, dist/, node_modules/)."""

    content = """
    vendor/
    dist/
    node_modules/
    """
    ignorer = create_ignore_file(content)

    assert ignorer.is_ignored("vendor/lib/file.py")
    assert ignorer.is_ignored("dist/main.js")
    assert ignorer.is_ignored("node_modules/library/index.js")
    assert not ignorer.is_ignored("src/vendor_utils.py")
    assert not ignorer.is_ignored("src/main.py")


def test_ignore_globstar_patterns(create_ignore_file):
    """Tests the globstar pattern (**/) for subdirectories."""

    content = """
    **/migrations/**
    """
    ignorer = create_ignore_file(content)

    assert ignorer.is_ignored("app/migrations/0001_initial.py")
    assert ignorer.is_ignored("project_root/db/migrations/0002.py")
    assert not ignorer.is_ignored("migrations_config.py")


def test_ignore_file_extension_patterns(create_ignore_file):
    """Tests exclusion by extension (*.cache, *.log)."""

    content = """
    *.cache
    *.log
    """

    ignorer = create_ignore_file(content)

    assert ignorer.is_ignored(".gitignore.cache")
    assert ignorer.is_ignored("output.log")
    assert not ignorer.is_ignored("cache.py")
    assert not ignorer.is_ignored("log_helper.py")


def test_ignore_specific_file_and_temp_patterns(create_ignore_file):
    """Tests exclusion of specific files and partial patterns."""

    content = """
    /README.md
    temp.*
    """

    ignorer = create_ignore_file(content)

    assert ignorer.is_ignored("README.md")
    assert not ignorer.is_ignored("src/README.md")
    assert ignorer.is_ignored("temp.json")
    assert ignorer.is_ignored("temp.py")


def test_ignore_comments_and_empty_lines(create_ignore_file):
    """Tests that comments (#) and empty lines are ignored."""

    content = """
    # Comment
    src/

    # another comment
    test_file.txt
    """

    ignorer = create_ignore_file(content, filename="custom.ignore")

    assert ignorer.is_ignored("src/code.py")
    assert ignorer.is_ignored("test_file.txt")


def test_non_existent_ignore_file(tmp_path: Path):
    """Tests behavior when the ignore file does not exist."""

    ignorer = BusFactorIgnore(
        ignore_file_path=str(tmp_path / "does_not_exist.ignore"),
        root_path=str(tmp_path)
    )

    assert not ignorer.is_ignored("anything/at/all.py")
    