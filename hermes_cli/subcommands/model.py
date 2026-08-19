"""``hermes model`` subcommand parser.

Extracted verbatim from ``hermes_cli/main.py:main()`` (god-file Phase 2).
Handler injected to avoid importing ``main``.
"""

from __future__ import annotations

from typing import Callable


def build_model_parser(subparsers, *, cmd_model: Callable) -> None:
    """Attach the ``model`` subcommand to ``subparsers``."""
    # =========================================================================
    # model command
    # =========================================================================
    model_parser = subparsers.add_parser(
        "model",
        help="Select default model and provider",
        description="Interactively select your inference provider and default model",
    )
    model_parser.add_argument(
        "--refresh",
        action="store_true",
        help="Wipe the model picker disk cache and re-fetch every provider's live /v1/models list.",
    )
    model_parser.add_argument(
        "--portal-url",
        help="Portal base URL for Nous login (default: production portal)",
    )
    model_parser.add_argument(
        "--inference-url",
        help="Inference API base URL for Nous login (default: production inference API)",
    )
    model_parser.add_argument(
        "--client-id",
        default=None,
        help="OAuth client id to use for Nous login (default: hermes-cli)",
    )
    model_parser.add_argument(
        "--scope", default=None, help="OAuth scope to request for Nous login"
    )
    model_parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Do not attempt to open the browser automatically during Nous login",
    )
    model_parser.add_argument(
        "--timeout",
        type=float,
        default=15.0,
        help="HTTP request timeout in seconds for Nous login (default: 15)",
    )
    model_parser.add_argument(
        "--ca-bundle", help="Path to CA bundle PEM file for Nous TLS verification"
    )
    model_parser.add_argument(
        "--insecure",
        action="store_true",
        help="Disable TLS verification for Nous login (testing only)",
    )
    model_parser.set_defaults(func=cmd_model)

    # Subcommand: hermes model alias (or hermes alias)
    model_subparsers = model_parser.add_subparsers(dest="model_subcommand")
    alias_subparser = model_subparsers.add_parser(
        "alias",
        aliases=["aliases"],
        help="Manage interactive model aliases (dashboard + create)",
    )
    alias_subparser.set_defaults(func=lambda args: _dispatch_alias_dashboard(args))

    # Also register top-level 'alias' for convenience
    top_alias_parser = subparsers.add_parser(
        "alias",
        aliases=["aliases"],
        help="Interactive model alias manager",
    )
    top_alias_parser.set_defaults(func=lambda args: _dispatch_alias_dashboard(args))


def _dispatch_alias_dashboard(args=None):
    from hermes_cli.alias_cmd import interactive_alias_dashboard
    interactive_alias_dashboard(args=args)
