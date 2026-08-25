"""Memory store JSON-RPC handlers for the desktop Settings Memory tab.

Reads and mutates the curated memory files (~/.hermes/memories/MEMORY.md
and USER.md) through tools.memory_tool.MemoryStore so the desktop inherits
the same file locking, external-drift detection, injection scanning, and
char-limit enforcement as agent-side writes.
"""

from .method_ctx import HandlerRegistry

_registry = HandlerRegistry()
method = _registry.method


@method("memory.list")
def _(rid, params: dict) -> dict:
    """Entries for both curated stores with per-store usage stats."""
    try:
        from tools.memory_tool import load_on_disk_store

        store = load_on_disk_store()
        result: dict = {"targets": {}}
        for target in ("memory", "user"):
            entries = list(store._entries_for(target))
            result["targets"][target] = {
                "entries": [
                    {"index": i, "preview": preview, "chars": len(entry)}
                    for i, entry in enumerate(entries)
                    # Preview keeps newlines flat for card rendering.
                    if (preview := entry.replace("\n", " ")) or True
                ],
                "chars_used": store._char_count(target),
                "char_limit": store._char_limit(target),
            }
        return _ok(rid, result)
    except Exception as e:
        return _err(rid, 5070, str(e))


@method("memory.write")
def _(rid, params: dict) -> dict:
    """Apply one add/replace/remove through the shared MemoryStore.

    Params:
        target: "memory" | "user"
        action: "add" | "replace" | "remove"
        content: new entry text (add / replace)
        old_text: unique substring locating the entry (replace / remove)
    """
    try:
        from tools.memory_tool import load_on_disk_store

        store = load_on_disk_store()
        target = str(params.get("target") or "").strip()
        action = str(params.get("action") or "").strip().lower()

        if target not in ("memory", "user"):
            return _err(rid, 4002, f"unknown memory target: {target}")
        if action not in ("add", "replace", "remove"):
            return _err(rid, 4002, f"unknown memory action: {action}")

        content = params.get("content")
        old_text = params.get("old_text")

        if action == "add":
            result = store.add(target, str(content or ""))
        elif action == "replace":
            result = store.replace(
                target, str(old_text or ""), str(content or "")
            )
        else:
            result = store.remove(target, str(old_text or ""))

        if not result.get("success"):
            return _err(rid, 4003, str(result.get("error") or "memory write failed"))

        entries = list(store._entries_for(target))
        return _ok(
            rid,
            {
                "message": result.get("message") or "ok",
                "chars_used": store._char_count(target),
                "char_limit": store._char_limit(target),
                "entry_count": len(entries),
            },
        )
    except Exception as e:
        return _err(rid, 5071, str(e))


def register(server) -> None:
    """Bind this module's handlers onto ``server``'s globals and registry."""
    _registry.install(server)
