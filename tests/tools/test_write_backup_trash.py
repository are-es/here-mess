"""Pre-write backup of existing workspace files into ``<workspace>/.trash/``.

Every overwrite of an existing file inside the ARES workspace copies the
current bytes to ``<workspace>/.trash/<same relative path>/<stem>-<timestamp><ext>``
BEFORE the new content lands, so an over-aggressive edit can always be
reverted -- to the latest version or to any earlier one, since each write
gets its own timestamped copy.

These run against a REAL LocalEnvironment (actual shell commands / actual
files under tmp_path), matching tests/tools/test_write_file_syntax_gate.py.
"""

import re
from pathlib import Path

import pytest

from tools.environments.local import LocalEnvironment
from tools.file_operations import ShellFileOperations


TS = r"\d{8}T\d{6}\.\d{6}"


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


def _backup_names(root: Path, rel_dir: str) -> list[str]:
    d = root / ".trash" / rel_dir
    return sorted(p.name for p in d.iterdir()) if d.is_dir() else []


class TestWorkspaceBackup:
    def test_overwrite_mirrors_original_path_into_trash(self, ops, workspace: Path):
        target = workspace / "paap" / "src" / "file.py"
        target.write_text("original\n")

        res = ops.write_file(str(target), "replaced\n")

        assert res.error is None, res.error
        assert target.read_text() == "replaced\n"
        names = _backup_names(workspace, "paap/src")
        assert len(names) == 1, names
        assert re.fullmatch(rf"file-{TS}\.py", names[0]), names[0]
        backup = workspace / ".trash" / "paap" / "src" / names[0]
        assert backup.read_text() == "original\n"

    def test_each_overwrite_keeps_its_own_version(self, ops, workspace: Path):
        target = workspace / "paap" / "src" / "file.py"
        target.write_text("v1\n")

        ops.write_file(str(target), "v2\n")
        ops.write_file(str(target), "v3\n")

        backups = workspace / ".trash" / "paap" / "src"
        assert sorted(p.read_text() for p in backups.iterdir()) == ["v1\n", "v2\n"]

    def test_new_file_is_not_backed_up(self, ops, workspace: Path):
        target = workspace / "paap" / "src" / "fresh.py"

        res = ops.write_file(str(target), "new\n")

        assert res.error is None, res.error
        assert not (workspace / ".trash").exists()

    def test_file_outside_workspace_is_not_backed_up(self, ops, workspace: Path, tmp_path: Path):
        outside = tmp_path / "outside.txt"
        outside.write_text("old\n")

        res = ops.write_file(str(outside), "new\n")

        assert res.error is None, res.error
        assert outside.read_text() == "new\n"
        assert not (workspace / ".trash").exists()

    def test_file_already_in_trash_is_not_backed_up_again(self, ops, workspace: Path):
        target = workspace / ".trash" / "paap" / "old.py"
        target.parent.mkdir(parents=True)
        target.write_text("archived\n")

        res = ops.write_file(str(target), "touched\n")

        assert res.error is None, res.error
        assert target.read_text() == "touched\n"
        assert list(target.parent.iterdir()) == [target], "no nested backup-of-a-backup"

    def test_patch_replace_backs_up_before_editing(self, ops, workspace: Path):
        target = workspace / "paap" / "src" / "mod.py"
        target.write_text("value = 1\n")

        res = ops.patch_replace(str(target), "value = 1", "value = 2")

        assert res.error is None, res.error
        assert target.read_text() == "value = 2\n"
        names = _backup_names(workspace, "paap/src")
        assert len(names) == 1, names
        backup = workspace / ".trash" / "paap" / "src" / names[0]
        assert backup.read_text() == "value = 1\n"

    def test_backup_failure_blocks_the_write(self, ops, workspace: Path):
        # ``.trash`` occupied by a regular file -> creating the mirror dir fails.
        (workspace / ".trash").write_text("not a directory\n")
        target = workspace / "paap" / "src" / "file.py"
        target.write_text("original\n")

        res = ops.write_file(str(target), "replaced\n")

        assert res.error is not None
        assert "back up" in res.error.lower()
        assert target.read_text() == "original\n", "original must survive a failed backup"
