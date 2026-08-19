"""Interactive Model Alias Manager for Hermes Agent.

Provides an all-in-one dashboard to view, create, and delete model aliases
via the interactive terminal UI (using prompt_toolkit / questionary style choices).
"""

from __future__ import annotations

import os
from typing import Optional, List, Tuple
from prompt_toolkit.shortcuts import radiolist_dialog, input_dialog, message_dialog

from hermes_cli.config import load_config, load_config_readonly
from hermes_cli.model_switch import _load_direct_aliases, DirectAlias


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
    
    from hermes_cli.config import save_config
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
        from hermes_cli.config import save_config
        save_config(cfg)


def interactive_alias_dashboard(args=None) -> None:
    """All-in-one dashboard: [+ Create New Alias] and all existing model aliases."""
    import questionary
    from questionary import Choice
    from hermes_cli.main import select_provider_and_model

    while True:
        aliases = get_all_model_aliases()
        
        choices = [
            Choice(title="➕ [+ Create New Alias]", value="__CREATE__"),
            Choice(title="─────────────────────────────────────────────", value=None, disabled=True),
        ]
        
        if not aliases:
            choices.append(Choice(title="  (No model aliases defined yet)", value=None, disabled=True))
        else:
            for name, data in sorted(aliases.items()):
                prov_label = f" ({data['provider']})" if data.get('provider') else ""
                url_label = f" @ {data['base_url']}" if data.get('base_url') else ""
                title = f"• {name:<12} -> {data['model']}{prov_label}{url_label}"
                choices.append(Choice(title=title, value=name))
                
        choices.append(Choice(title="─────────────────────────────────────────────", value=None, disabled=True))
        choices.append(Choice(title="❌ Exit", value="__EXIT__"))

        selected = questionary.select(
            "⚡ Model Aliases Dashboard:",
            choices=choices,
            use_indicator=True,
        ).ask()

        if selected is None or selected == "__EXIT__":
            break

        if selected == "__CREATE__":
            # 1. Ask for alias name
            alias_name = questionary.text(
                "Enter alias name (e.g. 'mimo', 'flash', 'sonnet'):",
                validate=lambda text: True if text.strip() else "Alias name cannot be empty.",
            ).ask()

            if not alias_name or not alias_name.strip():
                continue

            alias_name = alias_name.strip().lower()

            print(f"\n👉 Pick provider and model for alias '{alias_name}' below:\n")
            
            # 2. Pick provider and model using existing hermes model picker logic
            try:
                # Capture current model/provider before selection
                cfg_before = load_config()
                select_provider_and_model(args=args)
                cfg_after = load_config()

                # Extract the newly picked model & provider
                model_cfg = cfg_after.get("model", {})
                new_model = model_cfg.get("default", "") if isinstance(model_cfg, dict) else str(model_cfg or "")
                new_prov = model_cfg.get("provider", "custom") if isinstance(model_cfg, dict) else "custom"
                new_base_url = model_cfg.get("base_url", "") if isinstance(model_cfg, dict) else ""

                # Revert model: default in config so we don't accidentally override the user's active session model
                # unless they intentionally set it
                cfg_after["model"] = cfg_before.get("model", {})
                from hermes_cli.config import save_config
                save_config(cfg_after)

                if new_model:
                    save_model_alias(alias_name, model=new_model, provider=new_prov, base_url=new_base_url)
                    print(f"\n✨ Successfully saved alias '{alias_name}' -> {new_model} ({new_prov})!\n")
            except Exception as e:
                print(f"\n❌ Failed to create alias: {e}\n")

        else:
            # Manage existing alias (Delete / View)
            action = questionary.select(
                f"Action for alias '{selected}':",
                choices=[
                    Choice(title="🗑️  Delete Alias", value="delete"),
                    Choice(title="← Back", value="back"),
                ],
            ).ask()

            if action == "delete":
                confirm = questionary.confirm(f"Are you sure you want to delete alias '{selected}'?").ask()
                if confirm:
                    delete_model_alias(selected)
                    print(f"✓ Deleted alias '{selected}'.")
