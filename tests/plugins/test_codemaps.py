import json
from pathlib import Path
import pytest
from plugins.codemaps.engine import build_code_map, compute_file_hash, scan_engine_files
from plugins.codemaps.tools import resolve_codemaps_dir, get_target_codemaps_dir, handle_codemaps


def test_code_maps_scan_and_resolve(tmp_path):
    # 1. Create a dummy codebase in tmp_path
    (tmp_path / "src").mkdir()
    py_file = tmp_path / "src" / "app.py"
    py_file.write_text("def my_app():\n    pass\n")

    # 2. Build map via handle_codemaps
    monkeypatch_cwd = tmp_path
    import os
    orig_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        res = handle_codemaps({"action": "scan"})
        assert "Successfully built fresh code-map" in res

        # Verify discovery
        found_dir = resolve_codemaps_dir(tmp_path)
        assert found_dir is not None
        assert (found_dir / "map.json").is_file()
        assert (found_dir / "map.html").is_file()

        # 3. Test query action
        q_res = handle_codemaps({"action": "query", "query": "my_app"})
        assert "my_app" in q_res

        # 4. Test memory_save action (writes to root .ares/memory.md)
        m_res = handle_codemaps({"action": "memory_save", "note": "Use port 8080"})
        assert "Saved architectural note" in m_res
        assert "Use port 8080" in (tmp_path / ".ares" / "memory.md").read_text()

        # 5. Test update action with no changes
        u_res = handle_codemaps({"action": "update"})
        assert "Code-map is already up to date" in u_res

    finally:
        os.chdir(orig_cwd)


def test_custom_agent_folder_config(tmp_path):
    cfg = {"agent": {"folder": ".ares"}}
    target = get_target_codemaps_dir(tmp_path, config=cfg)
    assert target == tmp_path / ".ares" / "codemaps"
