from __future__ import annotations

import itertools
import logging
from collections import defaultdict
from pathlib import Path
from typing import Dict

from .arbiter import Arbiter
from .discovery import (
    load_package,
    discover_board_modules,
    discover_bot_classes,
    board_module_to_config,
)

logger = logging.getLogger("game")


def _safe(s: str) -> str:
    """Make a string safe for filenames (letters, digits, -, _)."""
    return "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in s)


def run_tournament(boards_dir: str, bots_dir: str, logs_dir: str, verbose_level: str,) -> Dict[str, int]:
    logger.setLevel(logging.INFO)
    game_verbose = verbose_level.lower() in ("debug", "info")

    log_dir = Path(logs_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    for p in log_dir.iterdir():
        try:
            if p.is_file():
                p.unlink()
        except Exception as e:
            logger.error(f"Could not delete '{p}': {e}")

    boards_pkg = load_package(boards_dir, "dynamic_boards")
    bots_pkg = load_package(bots_dir, "dynamic_bots")

    board_modules = discover_board_modules(boards_pkg)
    bot_classes = discover_bot_classes(bots_pkg)

    if not board_modules:
        logger.info("No boards found in boards directory.")
        return {}
    if not bot_classes:
        logger.info("No bots found in bots directory.")
        return {}

    logger.info("Discovered boards:")
    for bm in board_modules:
        logger.info(f"  - {bm.BOARD_NAME}")
    logger.info("\nDiscovered bots:")
    for bc in bot_classes:
        logger.info(f"  - {bc.__name__}")
    logger.info("")

    points = defaultdict(int)      # bot_name -> total points
    bot_games = defaultdict(int)   # bot_name -> games played
    draws = 0
    game_id = 0

    for mod in board_modules:
        cfg = board_module_to_config(mod)
        num = cfg.num_players
        logger.info(f"\n=== Board: {cfg.name} ({num} players) ===")

        if len(bot_classes) < num:
            msg = (
                f"ERROR: Board '{cfg.name}' requires {num} players, "
                f"but only {len(bot_classes)} bots are available."
            )
            logger.error(msg)
            error_log = log_dir / f"ERROR__{_safe(cfg.name)}.log"
            with error_log.open("w", encoding="utf-8") as f:
                f.write(msg + "\n")
            raise RuntimeError(msg)

        for perm in itertools.permutations(bot_classes, num):
            game_id += 1
            logger.info(f"\n--- Game {game_id} ---")

            for i, bot_cls in enumerate(perm):
                bot_name = bot_cls.__name__
                logger.info(f"  P{i}: {bot_name}")
                bot_games[bot_name] += 1

            board_part = _safe(cfg.name)
            bots_part = "__".join(_safe(cls.__name__) for cls in perm)
            game_log = log_dir / f"game_{game_id:03d}__{board_part}__{bots_part}.log"

            file_handler = logging.FileHandler(game_log, mode="w", encoding="utf-8")
            file_handler.setFormatter(logging.Formatter("%(message)s"))
            logger.addHandler(file_handler)
            logger.info(f"[LOG] Writing this game to: {game_log}")

            arb = Arbiter(cfg, list(perm))
            # Verbose moves only for info-or-lower log level
            result = arb.run(verbose=game_verbose)

            if result.winner_index is None:
                logger.info("Result: draw.")
                draws += 1

                eliminated_set = set(result.eliminated)
                for idx, bot_cls in enumerate(perm):
                    if idx in eliminated_set:
                        continue
                    points[bot_cls.__name__] += 1
            else:
                winner_cls = perm[result.winner_index]
                winner_name = winner_cls.__name__
                logger.info(f"\nResult: {winner_name} wins.")
                points[winner_name] += 2

            logger.removeHandler(file_handler)
            file_handler.close()

    logger.info("\n=== Tournament summary ===")

    total_games = game_id
    total_points = sum(points.values())

    logger.info(f"Total games played: {total_games}")
    logger.info(f"Total points awarded: {total_points}")
    logger.info(f"Draw games: {draws}")

    if bot_games:
        logger.info("\nPer-bot statistics:")
        ordered_names = sorted(
            bot_games.keys(),
            key=lambda n: (-points.get(n, 0), n),
        )
        for name in ordered_names:
            g = bot_games[name]
            p = points.get(name, 0)
            logger.info(f"  {name}: {p} points in {g} games")

    return dict(points)
