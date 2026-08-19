"""Interactive Model Alias Manager for Hermes Agent.

Provides an all-in-one dashboard to view, create, and delete model aliases
via the native curses/prompt_toolkit UI (zero external dependencies).
"""

from __future__ import annotations

import os
from typing import Optional, List, Dict, Any

from hermes_cli.config import load_config, load_config_readonly, save_config
from hermes_cli.curses_ui import curses_radiolist


def get_all_model_aliases() -> dict[str, dict[str, str]]:
    """Load model aliases from config."""
    cfg = load_config_readonly()
    aliases = {}
    
    # 1. model_aliases section
    user_aliases = cfg.get("model_aliases")
    if isinstance(user_aliases, dict):
        for name, entry in user_aliases.items():
            if isinstance(entry, dict):
                aliases[name.strip().lower()] = {
                    "model": entry.get("model", ""),
                    "provider": entry.get("provider", "custom"),
                    "base_url": entry.get("base_url", ""),
                }
            elif isinstance(entry, str):
                aliases[name.strip().lower()] = {
                    "model": entry.strip(),
                    "provider": "custom",
                    "base_url": "",
                }

    # 2. model.aliases section
    model_section = cfg.get("model", {})
    if isinstance(model_section, dict):
        simple_aliases = model_section.get("aliases")
        if isinstance(simple_aliases, dict):
            for name, val in simple_aliases.items():
                if name.strip().lower() not in aliases and isinstance(val, str):
                    aliases[name.strip().lower()] = {
                        "model": val.strip(),
                        "provider": model_section.get("provider", "custom"),
                        "base_url": "",
                    }
    return aliases


def save_model_alias(name: str, model: str, provider: str = "custom", base_url: str = "") -> None:
    """Save a model alias into ~/.hermes/config.yaml under model_aliases."""
    cfg = load_config()
    if "model_aliases" not in cfg or not isinstance(cfg["model_aliases"], dict):
        cfg["model_aliases"] = {}
    
    cfg["model_aliases"][name.strip().lower()] = {
        "model": model.strip(),
        "provider": provider.strip() if provider else "custom",
        "base_url": base_url.strip() if base_url else "",
    }
    save_config(cfg)


def delete_model_alias(name: str) -> None:
    """Delete an alias from ~/.hermes/config.yaml."""
    cfg = load_config()
    name_clean = name.strip().lower()
    modified = False
    
    if isinstance(cfg.get("model_aliases"), dict) and name_clean in cfg["model_aliases"]:
        del cfg["model_aliases"][name_clean]
        modified = True
        
    model_sec = cfg.get("model")
    if isinstance(model_sec, dict) and isinstance(model_sec.get("aliases"), dict):
        if name_clean in model_sec["aliases"]:
            del model_sec["aliases"][name_clean]
            modified = True
            
    if modified:
        save_config(cfg)


def interactive_alias_dashboard(args=None) -> None:
    """All-in-one dashboard: [+ Create New Alias] and all existing model aliases."""
    from hermes_cli.main import select_provider_and_model

    while True:
        aliases = get_all_model_aliases()
        
        items = ["➕ [+ Create New Alias]"]
        alias_keys = [None]  # Index 0 is Create
        
        if aliases:
            for name, data in sorted(aliases.items()):
                prov_label = f" ({data['provider']})" if data.get('provider') else ""
                url_label = f" @ {data['base_url']}" if data.get('base_url') else ""
                items.append(f"• {name:<12} -> {data['model']}{prov_label}{url_label}")
                alias_keys.append(name)
        else:
            items.append("  (No aliases yet — press ➕ to create one)")
            alias_keys.append(None)
            
        items.append("❌ Exit")
        alias_keys.append("__EXIT__")

        sel_idx = curses_radiolist(
            title="⚡ Model Aliases Dashboard (Enter: Select | ESC/q: Exit)",
            items=items,
            selected=0,
            cancel_returns=len(items) - 1,
        )

        chosen_key = alias_keys[sel_idx]

        if chosen_key == "__EXIT__" or sel_idx == len(items) - 1:
            break

        if chosen_key is None and sel_idx == 0:
            # 1. Ask for alias name via clean terminal input
            print("\n" + "=" * 50)
            try:
                alias_name = input("Enter new alias name (e.g. 'mimo', 'flash', 'sonnet') [or Enter to cancel]: ").strip()
            except (EOFError, KeyboardInterrupt):
                alias_name = ""

            if not alias_name:
                continue

            alias_name = alias_name.lower()
            print(f"\n👉 Pick provider and model for alias '{alias_name}' below...\n")
            
            # 2. Pick provider and model using existing hermes model picker logic
            try:
                cfg_before = load_config()
                select_provider_and_model(args=args)
                cfg_after = load_config()

                # Extract the newly picked model & provider
                model_cfg = cfg_after.get("model", {})
                new_model = model_cfg.get("default", "") if isinstance(model_cfg, dict) else str(model_cfg or "")
                new_prov = model_cfg.get("provider", "custom") if isinstance(model_cfg, dict) else "custom"
                new_base_url = model_cfg.get("base_url", "") if isinstance(model_cfg, dict) else ""

                # Revert model default in config so we don't accidentally override the active session model
                cfg_after["model"] = cfg_before.get("model", {})
                save_config(cfg_after)

                if new_model:
                    save_model_alias(alias_name, model=new_model, provider=new_prov, base_url=new_base_url)
                    print(f"\n✨ Successfully saved alias '{alias_name}' -> {new_model} ({new_prov})!\n")
            except Exception as e:
                print(f"\n❌ Failed to create alias: {e}\n")

        elif chosen_key is not None:
            # Manage existing alias (Delete / Back)
            action_items = [f"🗑️  Delete Alias '{chosen_key}'", "← Back"]
            act_idx = curses_radiolist(
                title=f"Manage Alias: {chosen_key}",
                items=action_items,
                selected=0,
                cancel_returns=1,
            )
            if act_idx == 0:
                delete_model_alias(chosen_key)
                print(f"✓ Deleted alias '{chosen_key}'.")
