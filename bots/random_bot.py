import random
import time
from typing import List, Tuple

from .base_bot import BaseBot


class RandomBot(BaseBot):
    def __init__(self, uid: int):
        super().__init__(uid)
        self.rng = random.Random(time.time_ns())
        self.cols = 0
        self.rows = 0

    def init_board(self, cols, rows, win_length, obstacles, time_given):
        self.cols = cols
        self.rows = rows

    def make_a_move(self, time_left) -> Tuple[int, int]:
        return (self.rng.randrange(self.cols),
                self.rng.randrange(self.rows))

    def notify_move(self, bot_uid: int, move: Tuple[int, int]):
        pass
