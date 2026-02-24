"""Tests for module entrypoint execution."""

import runpy


def test_module_entrypoint_calls_cli_main(monkeypatch) -> None:
    import plugin_boutique_price_checker.cli as cli_module

    called = {"count": 0}

    def fake_main() -> None:
        called["count"] += 1

    monkeypatch.setattr(cli_module, "main", fake_main)

    runpy.run_module("plugin_boutique_price_checker.__main__", run_name="__main__")

    assert called["count"] == 1
