"""Core AST Parser and Graph Extractor for Code-Maps."""

from __future__ import annotations

import ast
import hashlib
import json
import os
from pathlib import Path
from typing import Dict, Any, List, Tuple, Set


SUPPORTED_EXTENSIONS = {'.py', '.ts', '.tsx', '.js', '.jsx', '.go', '.rs', '.c', '.cpp', '.h', '.cs'}
IGNORED_DIRS = {
    '.git', 'node_modules', 'dist', 'build', '__pycache__', '.venv', 'venv',
    '.hermes-runtime', '.cargo', 'vendor', '.idea', '.vscode', '.ares', '.hermes',
    'tests', 'test', 'fixtures', 'snapshots'
}


def compute_file_hash(path: Path) -> str:
    """Compute sha256 checksum of a file."""
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except Exception:
        return ""


def scan_engine_files(root: Path) -> List[Path]:
    """Find all source code files, ignoring documentation, tests snapshots, and build artifacts."""
    found = []
    for dirpath, dirnames, filenames in os.walk(root):
        # In-place directory pruning to prevent descending into ignored folders
        dirnames[:] = [d for d in dirnames if d not in IGNORED_DIRS and not d.startswith('.')]
        for f in filenames:
            ext = os.path.splitext(f)[1].lower()
            if ext in SUPPORTED_EXTENSIONS:
                p = Path(dirpath) / f
                try:
                    rel_parts = set(p.relative_to(root).parts)
                    if not rel_parts.intersection(IGNORED_DIRS):
                        found.append(p)
                except ValueError:
                    pass
    return sorted(found)


def extract_python_ast(file_path: Path, root: Path) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Extract files, classes, functions, and import relations from Python AST."""
    rel_path = str(file_path.relative_to(root))
    nodes = []
    edges = []

    file_node_id = f"file:{rel_path}"
    nodes.append({
        "id": file_node_id,
        "name": file_path.name,
        "full_name": rel_path,
        "type": "file",
        "desc": f"Source Module: {rel_path}"
    })

    try:
        content = file_path.read_text(encoding='utf-8', errors='ignore')
        tree = ast.parse(content, filename=str(file_path))
    except Exception:
        return nodes, edges

    for stmt in tree.body:
        # Import statements -> edge to other files
        if isinstance(stmt, ast.Import):
            for alias in stmt.names:
                edges.append({"source": file_node_id, "target": f"import:{alias.name}", "label": "imports"})
        elif isinstance(stmt, ast.ImportFrom):
            mod = stmt.module or ""
            for alias in stmt.names:
                edges.append({"source": file_node_id, "target": f"import:{mod}.{alias.name}", "label": "imports"})
        elif isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
            fn_id = f"func:{rel_path}:{stmt.name}"
            nodes.append({
                "id": fn_id,
                "name": f"{stmt.name}()",
                "full_name": f"{rel_path}:{stmt.name}",
                "type": "func",
                "line": stmt.lineno,
                "desc": f"Function in {rel_path}"
            })
            edges.append({"source": file_node_id, "target": fn_id, "label": "defines"})
        elif isinstance(stmt, ast.ClassDef):
            cls_id = f"class:{rel_path}:{stmt.name}"
            nodes.append({
                "id": cls_id,
                "name": f"class {stmt.name}",
                "full_name": f"{rel_path}:{stmt.name}",
                "type": "class",
                "line": stmt.lineno,
                "desc": f"Class in {rel_path}"
            })
            edges.append({"source": file_node_id, "target": cls_id, "label": "defines"})
            for sub in stmt.body:
                if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    m_id = f"method:{rel_path}:{stmt.name}:{sub.name}"
                    nodes.append({
                        "id": m_id,
                        "name": f"{sub.name}()",
                        "full_name": f"{rel_path}:{stmt.name}.{sub.name}",
                        "type": "func",
                        "line": sub.lineno,
                        "desc": f"Method in {stmt.name}"
                    })
                    edges.append({"source": cls_id, "target": m_id, "label": "defines"})

    return nodes, edges


def build_code_map(root: Path) -> Dict[str, Any]:
    """Scan and build complete AST knowledge graph for the project."""
    files = scan_engine_files(root)
    all_nodes = []
    all_edges = []
    checksums = {}

    for f in files:
        checksums[str(f.relative_to(root))] = compute_file_hash(f)
        if f.suffix == '.py':
            ns, es = extract_python_ast(f, root)
            all_nodes.extend(ns)
            all_edges.extend(es)
        else:
            rel = str(f.relative_to(root))
            all_nodes.append({
                "id": f"file:{rel}",
                "name": f.name,
                "full_name": rel,
                "type": "file",
                "desc": f"Code Module: {rel}"
            })

    # Filter unresolved external imports to keep graph tight
    valid_ids = {n["id"] for n in all_nodes}
    filtered_edges = [e for e in all_edges if e["source"] in valid_ids and (e["target"] in valid_ids or e["label"] == "imports")]

    return {
        "nodes": all_nodes,
        "edges": filtered_edges,
        "checksums": checksums,
        "meta": {
            "total_files": len(files),
            "total_nodes": len(all_nodes),
            "total_edges": len(filtered_edges),
        }
    }
