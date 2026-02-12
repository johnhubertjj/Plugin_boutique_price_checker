"""Create a macOS launchd plist for plugin-boutique-alert."""

from __future__ import annotations

import argparse
import plistlib
from pathlib import Path


def parse_args() -> argparse.Namespace:
    """Parse CLI inputs for plist generation."""
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
    parser.add_argument(
        "--url",
        default="https://www.pluginboutique.com/product/...",
        help="Plugin Boutique product URL",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=100.0,
        help="Send alert when price is below this threshold",
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
    """Validate scheduling values for launchd."""
    if hour < 0 or hour > 23:
        raise ValueError("--hour must be between 0 and 23")
    if minute < 0 or minute > 59:
        raise ValueError("--minute must be between 0 and 59")


def build_plist(args: argparse.Namespace) -> dict:
    """Build the launchd plist dictionary."""
    recipient = args.to or args.email_address
    return {
        "Label": args.label,
        "ProgramArguments": [
            str(Path(args.command_path).expanduser()),
            "--url",
            args.url,
            "--threshold",
            str(args.threshold),
            "--to",
            recipient,
        ],
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


def main() -> None:
    """Generate and write the plist file."""
    args = parse_args()
    validate_time(args.hour, args.minute)

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
