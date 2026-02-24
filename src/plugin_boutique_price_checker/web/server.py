"""CLI entrypoint for running the FastAPI server."""

import uvicorn


def main() -> None:
    """Run the API server with sensible local defaults."""
    uvicorn.run(
        "plugin_boutique_price_checker.web.api:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
    )

