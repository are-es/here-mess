"""Pre-write backup of existing files into the trash root.

Every overwrite of an existing file inside a project root copies the current
bytes to ``<trash root>/<project-name>/<relative path>/<stem>-<timestamp><ext>``
BEFORE the new content lands, so an over-aggressive edit can always be
reverted -- to the latest version or to any earlier one, since each write
gets its own timestamped copy.

The trash root is ``<hermes home>/.trash`` by default (keeping backups out of
project trees and out of ``git status``) and is overridable via the
``files.trash_path`` config key.

These run against a REAL LocalEnvironment (actual shell commands / actual
files under tmp_path), matching tests/tools/test_write_file_syntax_gate.py.
"""

import re
from pathlib import Path

import pytest

from tools import file_operations
from tools.environments.local import LocalEnvironment
from tools.file_operations import ShellFileOperations


TS = r"\d{8}T\d{6}\.\d{6}"


@pytest.fixture
def trash_root(tmp_path: Path, monkeypatch):
    """Stand in for ``<hermes home>/.trash`` without touching the real home."""
    root = tmp_path / "hermes-home" / ".trash"
    monkeypatch.setattr(file_operations, "_trash_root", lambda: str(root))
    return root


@pytest.fixture
def workspace(tmp_path: Path, monkeypatch):
    root = tmp_path / "ares-workspace"
    (root / "paap" / "src").mkdir(parents=True)
    monkeypatch.setenv("ARES_WORKSPACE_ROOT", str(root))
    return root


@pytest.fixture
def ops(workspace: Path):
    env = LocalEnvironment(cwd=str(workspace))
    return ShellFileOperations(env, cwd=str(workspace))


def _backup_names(trash_root: Path, project: str, rel_dir: str) -> list[str]:
    d = trash_root / project / rel_dir
    return sorted(p.name for p in d.iterdir()) if d.is_dir() else []


class TestBackupIntoTrashRoot:
    def test_overwrite_mirrors_original_path_into_trash(
        self, ops, workspace: Path, trash_root: Path
    ):
        target = workspace / "paap" / "src" / "file.py"
        target.write_text("original\n")

        res = ops.write_file(str(target), "replaced\n")

        assert res.error is None, res.error
        assert target.read_text() == "replaced\n"
        assert not (workspace / ".trash").exists(), "project tree stays clean"
        names = _backup_names(trash_root, workspace.name, "paap/src")
        assert len(names) == 1, names
        assert re.fullmatch(rf"file-{TS}\.py", names[0]), names[0]
        backup = trash_root / workspace.name / "paap" / "src" / names[0]
        assert backup.read_text() == "original\n"

    def test_each_overwrite_keeps_its_own_version(
        self, ops, workspace: Path, trash_root: Path
    ):
        target = workspace / "paap" / "src" / "file.py"
        target.write_text("v1\n")

        ops.write_file(str(target), "v2\n")
        ops.write_file(str(target), "v3\n")

        backups = trash_root / workspace.name / "paap" / "src"
        assert sorted(p.read_text() for p in backups.iterdir()) == ["v1\n", "v2\n"]

    def test_new_file_is_not_backed_up(self, ops, workspace: Path, trash_root: Path):
        target = workspace / "paap" / "src" / "fresh.py"

        res = ops.write_file(str(target), "new\n")

        assert res.error is None, res.error
        assert not trash_root.exists()

    def test_file_outside_any_project_root_is_not_backed_up(
        self, ops, workspace: Path, tmp_path: Path, trash_root: Path
    ):
        outside = tmp_path / "outside.txt"
        outside.write_text("old\n")

        res = ops.write_file(str(outside), "new\n")

        assert res.error is None, res.error
        assert outside.read_text() == "new\n"
        assert not trash_root.exists()

    def test_file_already_in_trash_is_not_backed_up_again(
        self, ops, workspace: Path, trash_root: Path
    ):
        archived = trash_root / workspace.name / "paap" / "old.py"
        archived.parent.mkdir(parents=True)
        archived.write_text("archived\n")

        res = ops.write_file(str(archived), "touched\n")

        assert res.error is None, res.error
        assert archived.read_text() == "touched\n"
        assert list(archived.parent.iterdir()) == [archived], "no backup-of-a-backup"

    def test_patch_replace_backs_up_before_editing(
        self, ops, workspace: Path, trash_root: Path
    ):
        target = workspace / "paap" / "src" / "mod.py"
        target.write_text("value = 1\n")

        res = ops.patch_replace(str(target), "value = 1", "value = 2")

        assert res.error is None, res.error
        assert target.read_text() == "value = 2\n"
        names = _backup_names(trash_root, workspace.name, "paap/src")
        assert len(names) == 1, names
        backup = trash_root / workspace.name / "paap" / "src" / names[0]
        assert backup.read_text() == "value = 1\n"

    def test_backup_failure_blocks_the_write(
        self, ops, workspace: Path, trash_root: Path
    ):
        # Trash root occupied by a regular file -> creating the mirror dir fails.
        trash_root.parent.mkdir(parents=True, exist_ok=True)
        trash_root.write_text("not a directory\n")
        target = workspace / "paap" / "src" / "file.py"
        target.write_text("original\n")

        res = ops.write_file(str(target), "replaced\n")

        assert res.error is not None
        assert "back up" in res.error.lower()
        assert target.read_text() == "original\n", "original must survive a failed backup"

    def test_two_projects_do_not_collide(
        self, workspace: Path, tmp_path: Path, trash_root: Path
    ):
        # A second project root with the SAME relative path inside it.
        other = tmp_path / "other-project"
        (other / ".git").mkdir(parents=True)
        (other / "paap" / "src").mkdir(parents=True)
        for root, text in ((workspace, "from-workspace\n"), (other, "from-other\n")):
            target = root / "paap" / "src" / "file.py"
            target.write_text(text)
            env = LocalEnvironment(cwd=str(root))
            ShellFileOperations(env, cwd=str(root)).write_file(str(target), "replaced\n")

        ws_mirror = trash_root / workspace.name / "paap" / "src"
        other_mirror = trash_root / other.name / "paap" / "src"
        assert [p.read_text() for p in ws_mirror.iterdir()] == ["from-workspace\n"]
        assert [p.read_text() for p in other_mirror.iterdir()] == ["from-other\n"]


class TestTrashRootResolution:
    """``_trash_root`` prefers ``files.trash_path``, else ``<hermes home>/.trash``."""

    def test_defaults_to_hermes_home_trash(self, tmp_path: Path, monkeypatch):
        monkeypatch.setattr(
            file_operations, "_load_trash_path_config", lambda: ""
        )
        monkeypatch.setenv("HERMES_HOME", str(tmp_path / "home"))

        assert file_operations._trash_root() == str(tmp_path / "home" / ".trash")

    def test_configured_path_wins(self, tmp_path: Path, monkeypatch):
        monkeypatch.setattr(
            file_operations,
            "_load_trash_path_config",
            lambda: str(tmp_path / "elsewhere"),
        )
        monkeypatch.setenv("HERMES_HOME", str(tmp_path / "home"))

        assert file_operations._trash_root() == str(tmp_path / "elsewhere")

    def test_configured_path_expands_user(self, monkeypatch):
        monkeypatch.setattr(
            file_operations, "_load_trash_path_config", lambda: "~/custom-trash"
        )

        assert file_operations._trash_root() == str(Path.home() / "custom-trash")
