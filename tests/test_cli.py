"""Unit tests for CLI argument and watchlist handling."""

import json
import sys

import pytest

from plugin_boutique_price_checker import cli


def test_parse_args_single_url_mode(monkeypatch) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "prog",
            "--url",
            "https://example.com/p",
            "--threshold",
            "50",
            "--to",
            "alerts@example.com",
        ],
    )

    args = cli.parse_args()
    assert args.url == "https://example.com/p"
    assert args.threshold == 50.0
    assert args.watchlist_file is None


def test_parse_args_requires_threshold_with_url(monkeypatch) -> None:
    monkeypatch.setattr(sys, "argv", ["prog", "--url", "https://example.com/p"])
    with pytest.raises(SystemExit):
        cli.parse_args()


def test_parse_args_disallows_threshold_with_watchlist(monkeypatch, tmp_path) -> None:
    watchlist = tmp_path / "watchlist.json"
    watchlist.write_text("[]", encoding="utf-8")
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "prog",
            "--watchlist-file",
            str(watchlist),
            "--threshold",
            "25",
        ],
    )
    with pytest.raises(SystemExit):
        cli.parse_args()


def test_load_watchlist_valid_file(tmp_path) -> None:
    watchlist = tmp_path / "watchlist.json"
    watchlist.write_text(
        json.dumps(
            [
                {
                    "url": "https://example.com/a",
                    "threshold": 99,
                    "to": "a@example.com",
                },
                {
                    "url": "https://example.com/b",
                    "threshold": "49.95",
                },
            ]
        ),
        encoding="utf-8",
    )

    items = cli.load_watchlist(str(watchlist))
    assert len(items) == 2
    assert items[0]["threshold"] == 99.0
    assert items[1]["threshold"] == 49.95
    assert items[1]["to"] is None


def test_load_watchlist_rejects_invalid_item(tmp_path) -> None:
    watchlist = tmp_path / "watchlist.json"
    watchlist.write_text(
        json.dumps([{"url": "https://example.com/a", "threshold": "not-a-number"}]),
        encoding="utf-8",
    )

    with pytest.raises(RuntimeError, match="invalid 'threshold'"):
        cli.load_watchlist(str(watchlist))
