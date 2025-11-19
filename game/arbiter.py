from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from enum import IntEnum
from typing import List, Tuple, Optional

logger = logging.getLogger("game")


class BoardCell(IntEnum):
    BLOCKED = -2
    EMPTY = -1
    # players are 0..N-1


@dataclass
class BoardConfig:
    name: str
    width: int
    height: int
    win_length: int
    num_players: int
    obstacles: List[Tuple[int, int]]
    time_ms: int


@dataclass
class GameResult:
    winner_index: Optional[int]          # None => draw / no winner
    board_name: str
    player_names: List[str]              # class names of participating bots
    eliminated: List[int]                # indices of eliminated players


class Arbiter:
    def __init__(self, config: BoardConfig, bot_classes: List[type]) -> None:
        self.config = config
        self.W = config.width
        self.H = config.height

        if len(bot_classes) != config.num_players:
            raise ValueError(
                f"Board '{config.name}' expects {config.num_players} players, "
                f"but got {len(bot_classes)} bot classes."
            )

        self.board: List[List[int]] = [
            [BoardCell.EMPTY for _ in range(self.H)]
            for _ in range(self.W)
        ]

        for (x, y) in config.obstacles:
            self._check_inside_board(x, y)
            self.board[x][y] = BoardCell.BLOCKED

        self.bots = [cls(uid=i) for i, cls in enumerate(bot_classes)]

        self.time_left_ms: List[int] = [config.time_ms for _ in range(config.num_players)]

        self.eliminated: List[bool] = [False] * config.num_players

        self.current_player = 0
        self.winner: Optional[int] = None

    def _check_inside_board(self, x: int, y: int) -> None:
        if not (0 <= x < self.W and 0 <= y < self.H):
            raise ValueError(f"Cell ({x}, {y}) is outside of the board")

    def _is_cell_empty(self, x: int, y: int) -> bool:
        return self.board[x][y] == BoardCell.EMPTY

    def _board_full(self) -> bool:
        return all(cell != BoardCell.EMPTY for row in self.board for cell in row)

    def _active_players(self) -> List[int]:
        return [i for i, eliminated in enumerate(self.eliminated) if not eliminated]

    def _next_active_player(self, current: int) -> int:
        n = self.config.num_players
        for offset in range(1, n + 1):
            idx = (current + offset) % n
            if not self.eliminated[idx]:
                return idx
        return current  # fallback; should not be used if at least one active player exists

    def _eliminate_player(self, pid: int, reason: str) -> bool:
        if self.eliminated[pid]:
            return False  # already eliminated

        bot = self.bots[pid]
        logger.info(f"  Bot P{pid} ({bot.name}) is ELIMINATED: {reason}")
        self.eliminated[pid] = True

        active = self._active_players()
        if not active:
            # Everyone eliminated: no winner
            self.winner = None
            return True
        if len(active) == 1:
            # Exactly one player left: that player wins
            self.winner = active[0]
            return True

        return False

    def _check_winner_from_last_move(self, x: int, y: int, pid: int) -> bool:
        def count_dir(dx: int, dy: int) -> int:
            c = 1  # include (x, y)
            # forward
            cx, cy = x + dx, y + dy
            while 0 <= cx < self.W and 0 <= cy < self.H and self.board[cx][cy] == pid:
                c += 1
                cx += dx
                cy += dy
            # backward
            cx, cy = x - dx, y - dy
            while 0 <= cx < self.W and 0 <= cy < self.H and self.board[cx][cy] == pid:
                c += 1
                cx -= dx
                cy -= dy
            return c

        for dx, dy in [(1, 0), (0, 1), (1, 1), (1, -1)]:
            if count_dir(dx, dy) >= self.config.win_length:
                return True
        return False

    def run(self, verbose: bool = True) -> GameResult:
        if verbose:
            logger.info(f"\n=== Game on board '{self.config.name}' ===")
            logger.info(
                f"Board: {self.W}x{self.H}, win length: {self.config.win_length}, "
                f"players: {self.config.num_players}"
            )
            logger.info("Players (in order):")
            for i, bot in enumerate(self.bots):
                logger.info(f"  P{i}: {bot.name}")
            logger.info("")

        for pid, bot in enumerate(self.bots):
            try:
                bot.init_board(
                    cols=self.W,
                    rows=self.H,
                    win_length=self.config.win_length,
                    obstacles=self.config.obstacles,
                    time_given=self.config.time_ms,
                )
            except Exception as exc:
                logger.info(f"  Bot P{pid} ({bot.name}) failed in init_board: {exc}")
                game_over = self._eliminate_player(pid, "init_board failure")
                if game_over:
                    if verbose:
                        logger.info("=== Game over (during initialization) ===\n")
                    eliminated_indices = [i for i, e in enumerate(self.eliminated) if e]
                    return GameResult(
                        winner_index=self.winner,
                        board_name=self.config.name,
                        player_names=[bot.name for bot in self.bots],
                        eliminated=eliminated_indices,
                    )

        while True:
            if self.eliminated[self.current_player]:
                active = self._active_players()
                if len(active) <= 1:
                    break
                self.current_player = self._next_active_player(self.current_player)
                continue

            pid = self.current_player
            bot = self.bots[pid]

            if verbose:
                self._print_board()
                logger.info(
                    f"P{pid} ({bot.name}) to move. "
                    f"Time left: {self.time_left_ms[pid]} ms"
                )

            start_ns = time.perf_counter_ns()
            try:
                x, y = bot.make_a_move(self.time_left_ms[pid])
            except Exception as exc:
                logger.info(f"  Bot P{pid} ({bot.name}) crashed with exception: {exc}")
                game_over = self._eliminate_player(pid, "crash")
                if game_over:
                    break
                self.current_player = self._next_active_player(pid)
                if verbose:
                    logger.info("")
                continue
            end_ns = time.perf_counter_ns()

            spent_ms = (end_ns - start_ns) // 1_000_000
            self.time_left_ms[pid] -= spent_ms
            if self.time_left_ms[pid] < 0:
                logger.info(f"  Bot P{pid} ({bot.name}) exceeded its time budget.")
                game_over = self._eliminate_player(pid, "timeout")
                if game_over:
                    break
                self.current_player = self._next_active_player(pid)
                if verbose:
                    logger.info("")
                continue

            if verbose:
                logger.info(f"  Bot P{pid} -> move ({x}, {y})")

            if not (0 <= x < self.W and 0 <= y < self.H):
                logger.info("  Illegal move: outside of board.")
                game_over = self._eliminate_player(pid, "illegal move (outside board)")
                if game_over:
                    break
                self.current_player = self._next_active_player(pid)
                if verbose:
                    logger.info("")
                continue

            if self.board[x][y] == BoardCell.BLOCKED:
                logger.info("  Illegal move: blocked cell.")
                game_over = self._eliminate_player(pid, "illegal move (blocked cell)")
                if game_over:
                    break
                self.current_player = self._next_active_player(pid)
                if verbose:
                    logger.info("")
                continue

            if not self._is_cell_empty(x, y):
                logger.info("  Illegal move: occupied cell.")
                game_over = self._eliminate_player(pid, "illegal move (occupied cell)")
                if game_over:
                    break
                self.current_player = self._next_active_player(pid)
                if verbose:
                    logger.info("")
                continue

            self.board[x][y] = pid

            for other_id, other in enumerate(self.bots):
                if self.eliminated[other_id]:
                    continue
                try:
                    other.notify_move(pid, (x, y))
                except Exception as exc:
                    logger.info(f"  notify_move raised for {other.name}: {exc}")

            if self._check_winner_from_last_move(x, y, pid):
                self.winner = pid
                if verbose:
                    logger.info("")
                    self._print_board()
                    logger.info(f"Winner: P{pid} ({bot.name})")
                break

            if self._board_full():
                if verbose:
                    logger.info("")
                    self._print_board()
                    logger.info("Board full: draw among remaining players.")
                self.winner = None
                break

            self.current_player = self._next_active_player(pid)
            if verbose:
                logger.info("")

        if verbose:
            logger.info("=== Game over ===")

        eliminated_indices = [i for i, e in enumerate(self.eliminated) if e]

        return GameResult(
            winner_index=self.winner,
            board_name=self.config.name,
            player_names=[bot.name for bot in self.bots],
            eliminated=eliminated_indices,
        )

    def _print_board(self) -> None:
        logger.info("   " + " ".join(str(x // 10) for x in range(self.W)))
        logger.info("   " + " ".join(str(x % 10) for x in range(self.W)))
        for y in range(self.H):
            row = []
            for x in range(self.W):
                c = self.board[x][y]
                if c == BoardCell.EMPTY:
                    row.append(".")
                elif c == BoardCell.BLOCKED:
                    row.append("#")
                else:
                    row.append(str(c))
            logger.info(f"{y:02} " + " ".join(row))
        logger.info("")
