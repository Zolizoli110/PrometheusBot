import argparse
import logging
from pathlib import Path

from game.runner import run_tournament


def main() -> None:
    logger = logging.getLogger("game")
    logger.setLevel(logging.INFO)
    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(ch)

    root = Path(__file__).parent.resolve()

    parser = argparse.ArgumentParser(description="X-in-a-Line Tournament Runner")

    parser.add_argument("--boards", default=str(root / "boards"),
                        help="Directory with board modules (default: boards/)")

    parser.add_argument("--bots", default=str(root / "bots"),
                        help="Directory with bot modules (default: bots/)")

    parser.add_argument("--logs", default=str(root / "logs"),
                        help="Directory for log files (default: logs/)")

    parser.add_argument("--verbose", default="info",
                        choices=["debug", "info", "warning", "error"],
                        help="Logging level (default: info)")

    args = parser.parse_args()

    run_tournament(
        boards_dir=args.boards,
        bots_dir=args.bots,
        logs_dir=args.logs,
        verbose_level=args.verbose,
    )


if __name__ == "__main__":
    main()
