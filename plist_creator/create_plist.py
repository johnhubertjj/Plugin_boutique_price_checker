"""Create a macOS launchd plist for plugin-boutique-alert."""

from __future__ import annotations

import argparse
import json
import plistlib
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    """Parse CLI inputs for plist generation.

    Args:
        None.

    Returns:
        argparse.Namespace: Parsed arguments for plist creation.
    """
    parser = argparse.ArgumentParser(
        description="Generate a launchd plist for plugin-boutique-alert."
    )
    parser.add_argument(
        "--command-path",
        required=True,
        help="Absolute path to plugin-boutique-alert executable",
    )
    parser.add_argument("--email-address", required=True, help="EMAIL_ADDRESS value")
    parser.add_argument("--email-password", required=True, help="EMAIL_PASSWORD value")
    parser.add_argument("--smtp-address", required=True, help="SMTP_ADDRESS value")
    parser.add_argument(
        "--output",
        default="~/Library/LaunchAgents/com.example.pluginboutique.alert.plist",
        help="Output plist path",
    )
    parser.add_argument(
        "--label",
        default="com.example.pluginboutique.alert",
        help="LaunchAgent label",
    )
    parser.add_argument(
        "--working-directory",
        default=str(Path.cwd()),
        help="Working directory for the job",
    )
    parser.add_argument("--hour", type=int, default=9, help="Run hour (0-23)")
    parser.add_argument("--minute", type=int, default=0, help="Run minute (0-59)")
    target_group = parser.add_mutually_exclusive_group()
    target_group.add_argument(
        "--watchlist-file",
        default=None,
        help="Path to watchlist JSON file for multiple URL/threshold entries",
    )
    target_group.add_argument(
        "--url",
        default="https://www.pluginboutique.com/product/...",
        help="Plugin Boutique product URL",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=100.0,
        help="Send alert when price is below this threshold (single URL mode)",
    )
    parser.add_argument(
        "--to",
        default=None,
        help="Recipient email for alert (defaults to --email-address)",
    )
    parser.add_argument(
        "--stdout-path",
        default="/tmp/pluginboutique-alert.out",
        help="stdout log file path",
    )
    parser.add_argument(
        "--stderr-path",
        default="/tmp/pluginboutique-alert.err",
        help="stderr log file path",
    )
    return parser.parse_args()


def validate_time(hour: int, minute: int) -> None:
    """Validate scheduling values for launchd.

    Args:
        hour: Launch hour in 24-hour format.
        minute: Launch minute.

    Returns:
        None: Raises ``ValueError`` when values are out of range.
    """
    if hour < 0 or hour > 23:
        raise ValueError("--hour must be between 0 and 23")
    if minute < 0 or minute > 59:
        raise ValueError("--minute must be between 0 and 59")


def build_plist(args: argparse.Namespace) -> dict:
    """Build the launchd plist dictionary.

    Args:
        args: Parsed CLI arguments used to construct plist fields.

    Returns:
        dict: Dictionary ready for serialization with ``plistlib``.
    """
    recipient = args.to or args.email_address
    program_arguments = [str(Path(args.command_path).expanduser())]
    if args.watchlist_file:
        program_arguments.extend(["--watchlist-file", str(Path(args.watchlist_file).expanduser())])
        program_arguments.extend(["--to", recipient])
    else:
        program_arguments.extend(
            [
                "--url",
                args.url,
                "--threshold",
                str(args.threshold),
                "--to",
                recipient,
            ]
        )

    return {
        "Label": args.label,
        "ProgramArguments": program_arguments,
        "EnvironmentVariables": {
            "EMAIL_ADDRESS": args.email_address,
            "EMAIL_PASSWORD": args.email_password,
            "SMTP_ADDRESS": args.smtp_address,
        },
        "WorkingDirectory": str(Path(args.working_directory).expanduser()),
        "StartCalendarInterval": {
            "Hour": args.hour,
            "Minute": args.minute,
        },
        "StandardOutPath": args.stdout_path,
        "StandardErrorPath": args.stderr_path,
    }


def validate_watchlist_file(watchlist_file: str) -> str:
    """Validate watchlist JSON file path and basic structure.

    Args:
        watchlist_file: Path to a JSON file containing watchlist entries.

    Returns:
        str: Expanded absolute-compatible watchlist file path for CLI usage.
    """
    path = Path(watchlist_file).expanduser()
    if not path.exists():
        raise ValueError(f"Watchlist file does not exist: {path}")
    if path.suffix.lower() != ".json":
        raise ValueError("Watchlist file must be a .json file")

    with path.open("r", encoding="utf-8") as f:
        data: Any = json.load(f)

    if not isinstance(data, list) or not data:
        raise ValueError("Watchlist file must contain a non-empty JSON array")

    for index, item in enumerate(data):
        if not isinstance(item, dict):
            raise ValueError(f"Watchlist item at index {index} must be an object")
        if not isinstance(item.get("url"), str) or not item["url"].strip():
            raise ValueError(f"Watchlist item at index {index} is missing a valid 'url'")
        try:
            float(item.get("threshold"))
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Watchlist item at index {index} has invalid 'threshold'") from exc

    return str(path)


def main() -> None:
    """Generate and write the plist file.

    Args:
        None.

    Returns:
        None: Writes plist output and prints usage instructions.
    """
    args = parse_args()
    validate_time(args.hour, args.minute)
    if args.watchlist_file:
        args.watchlist_file = validate_watchlist_file(args.watchlist_file)

    plist_data = build_plist(args)
    output_path = Path(args.output).expanduser()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("wb") as f:
        plistlib.dump(plist_data, f, fmt=plistlib.FMT_XML, sort_keys=False)

    print(f"Created plist: {output_path}")
    print(f"Label: {args.label}")
    print("Load with: launchctl load " + str(output_path))


if __name__ == "__main__":
    main()
