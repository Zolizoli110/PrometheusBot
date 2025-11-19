import random
import time
from typing import List, Tuple

from .base_bot import BaseBot


EMPTY = -1
BLOCKED = -2


class SmartRandomBot(BaseBot):
    def __init__(self, uid: int):
        super().__init__(uid)
        self.rng = random.Random(time.time_ns())
        self.cols = 0
        self.rows = 0
        self.board: List[List[int]] = []
        self.empty_cells: List[Tuple[int, int]] = []

    def init_board(self, cols: int, rows: int, win_length: int, obstacles: List[Tuple[int, int]], time_given: int) -> None:
        self.cols = cols
        self.rows = rows

        self.board = [[EMPTY for _ in range(rows)] for _ in range(cols)]

        obs_set = set(obstacles)
        for x, y in obs_set:
            if 0 <= x < cols and 0 <= y < rows:
                self.board[x][y] = BLOCKED

        self.empty_cells = [
            (x, y)
            for x in range(cols)
            for y in range(rows)
            if self.board[x][y] == EMPTY
        ]

    def make_a_move(self, time_left: int) -> Tuple[int, int]:
        # If no empty cells remain, fall back to something (should not happen)
        if not self.empty_cells:
            x = self.rng.randrange(self.cols)
            y = self.rng.randrange(self.rows)
            return x, y

        x, y = self.rng.choice(self.empty_cells)
        return x, y

    def notify_move(self, bot_uid: int, move: Tuple[int, int]) -> None:
        x, y = move
        if not (0 <= x < self.cols and 0 <= y < self.rows):
            return

        self.board[x][y] = bot_uid

        try:
            self.empty_cells.remove((x, y))
        except ValueError:
            pass
