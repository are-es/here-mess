"""Code-Maps Hermes Tool Handler & Workspace Directory Search Resolver."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional

from plugins.codemaps.engine import build_code_map, compute_file_hash, scan_engine_files
from plugins.codemaps.visualizer import generate_map_html


def resolve_codemaps_dir(cwd: Path) -> Optional[Path]:
    """Search thoroughly for an existing codemaps folder across all root/subdirectories."""
    # 1. Direct candidate paths
    candidates = [
        cwd / "codemaps",
        cwd / "code-maps",
        cwd / ".hermes" / "codemaps",
        cwd / ".hermes" / "code-maps",
        cwd / ".ares" / "codemaps",
    ]
    for cand in candidates:
        if cand.is_dir() and (cand / "map.json").is_file():
            return cand

    # 2. Recursive search in subdirectories (e.g. .hermes/<feature>/codemaps)
    try:
        for p in cwd.glob("**/*"):
            if p.is_dir() and p.name in ("codemaps", "code-maps") and (p / "map.json").is_file():
                return p
    except Exception:
        pass

    return None


def load_plugin_yaml_config() -> Dict[str, Any]:
    """Load config section directly from plugins/codemaps/plugin.yaml."""
    try:
        import yaml
        plugin_yaml = Path(__file__).parent / "plugin.yaml"
        if plugin_yaml.is_file():
            data = yaml.safe_load(plugin_yaml.read_text(encoding='utf-8'))
            if isinstance(data, dict) and "config" in data and isinstance(data["config"], dict):
                return data["config"]
    except Exception:
        pass
    return {}


def get_target_codemaps_dir(cwd: Path, config: Optional[Dict[str, Any]] = None) -> Path:
    """Determine where to write new codemaps based on plugin.yaml config or defaults."""
    plugin_cfg = load_plugin_yaml_config()
    
    # 1. First priority: plugin.yaml config.output_folder
    custom_folder = plugin_cfg.get("output_folder")
    
    # 2. Second priority: passed config or global agent.folder
    if not custom_folder and config:
        agent_cfg = config.get("agent", {}) if isinstance(config, dict) else {}
        custom_folder = agent_cfg.get("folder") if isinstance(agent_cfg, dict) else None

    if custom_folder:
        clean_folder = str(custom_folder).strip().lstrip("/")
        return cwd / clean_folder / "codemaps"

    return cwd / "codemaps"


def handle_codemaps(args: Dict[str, Any], **kwargs) -> str:
    """Tool handler for AI Agent."""
    action = str(args.get("action", "scan")).strip().lower()
    cwd = Path(os.getcwd())

    existing_dir = resolve_codemaps_dir(cwd)

    if action == "scan":
        if existing_dir:
            try:
                map_data = json.loads((existing_dir / "map.json").read_text(encoding='utf-8'))
                nodes_cnt = len(map_data.get("nodes", []))
                edges_cnt = len(map_data.get("edges", []))
                mem_path = existing_dir / "memory.md"
                mem_note = f" (Memory available at {mem_path.name})" if mem_path.is_file() else ""
                return (
                    f"✓ Found existing code-map at: {existing_dir.relative_to(cwd)}\n"
                    f"Architecture: {nodes_cnt} symbols, {edges_cnt} relations{mem_note}.\n"
                    f"Do NOT rebuild map. Use action='query' or read map.json/memory.md to inspect."
                )
            except Exception:
                pass

        # Build fresh map
        target_dir = get_target_codemaps_dir(cwd)
        target_dir.mkdir(parents=True, exist_ok=True)
        
        map_data = build_code_map(cwd)
        (target_dir / "map.json").write_text(json.dumps(map_data, indent=2, ensure_ascii=False), encoding='utf-8')
        (target_dir / "checksums.json").write_text(json.dumps(map_data["checksums"], indent=2), encoding='utf-8')
        generate_map_html(map_data, target_dir / "map.html")
        
        mem_file = target_dir / "memory.md"
        if not mem_file.is_file():
            mem_file.write_text("# Project Architecture & Technical Memory\n\n- Initialized codebase architecture map.\n", encoding='utf-8')

        return (
            f"⚡ Successfully built fresh code-map at: {target_dir.relative_to(cwd)}\n"
            f"Mapped: {map_data['meta']['total_files']} files, {map_data['meta']['total_nodes']} nodes, {map_data['meta']['total_edges']} edges.\n"
            f"Visual Balloon HTML: {target_dir / 'map.html'}"
        )

    elif action == "update":
        target_dir = existing_dir or get_target_codemaps_dir(cwd)
        if not (target_dir / "checksums.json").is_file():
            return handle_codemaps({"action": "scan"})

        old_checksums = json.loads((target_dir / "checksums.json").read_text(encoding='utf-8'))
        current_files = scan_engine_files(cwd)
        
        changed = False
        new_checksums = {}
        for f in current_files:
            rel = str(f.relative_to(cwd))
            h = compute_file_hash(f)
            new_checksums[rel] = h
            if old_checksums.get(rel) != h:
                changed = True

        if not changed and len(old_checksums) == len(new_checksums):
            return "✓ Code-map is already up to date. Zero file changes detected (skipped rebuild in 0.01s)."

        # Re-build updated map
        map_data = build_code_map(cwd)
        (target_dir / "map.json").write_text(json.dumps(map_data, indent=2, ensure_ascii=False), encoding='utf-8')
        (target_dir / "checksums.json").write_text(json.dumps(new_checksums, indent=2), encoding='utf-8')
        generate_map_html(map_data, target_dir / "map.html")
        return f"⚡ Code-map updated successfully with latest codebase diff at: {target_dir.relative_to(cwd)}"

    elif action == "query":
        query_str = str(args.get("query", "")).strip().lower()
        if not existing_dir:
            return "No existing code-map found. Please run action='scan' first."
        
        map_data = json.loads((existing_dir / "map.json").read_text(encoding='utf-8'))
        matches = []
        for n in map_data.get("nodes", []):
            if query_str in n.get("name", "").lower() or query_str in n.get("full_name", "").lower():
                matches.append(n)

        if not matches:
            return f"No symbols matching '{query_str}' found in code-map."

        res = [f"Found {len(matches)} matches in architecture map:"]
        for m in matches[:10]:
            res.append(f"- [{m.get('type')}] {m.get('full_name', m.get('name'))} -> {m.get('desc', '')}")
        return "\n".join(res)

    elif action == "memory_save":
        note = str(args.get("note", "")).strip()
        if not note:
            return "Error: 'note' argument is required for memory_save."
        target_dir = existing_dir or get_target_codemaps_dir(cwd)
        target_dir.mkdir(parents=True, exist_ok=True)
        mem_file = target_dir / "memory.md"
        content = mem_file.read_text(encoding='utf-8') if mem_file.is_file() else "# Project Memory\n\n"
        content += f"- {note}\n"
        mem_file.write_text(content, encoding='utf-8')
        return f"✓ Saved architectural note to {mem_file.relative_to(cwd)}"

    return f"Unknown action: {action}. Supported: 'scan', 'update', 'query', 'memory_save'."
