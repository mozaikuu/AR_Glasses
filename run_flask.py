from __future__ import annotations

import argparse

from config.settings import settings
from flask_app import app


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Flask interface")
    parser.add_argument("--reload", action="store_true", default=settings.auto_reload)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    use_reload = bool(args.reload)
    app.run(
        host=settings.flask_host,
        port=settings.flask_port,
        debug=use_reload,
        use_reloader=use_reload,
    )


if __name__ == "__main__":
    main()
