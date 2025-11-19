from typing import List, Tuple

from .base_bot import BaseBot

EMPTY = -1
BLOCKED = -2


class SmartWalkingBot(BaseBot):
    def __init__(self, uid: int):
        super().__init__(uid)
        self.cols = 0
        self.rows = 0
        self.board: List[List[int]] = []

    def init_board(self, cols: int, rows: int, win_length: int, obstacles: List[Tuple[int, int]], time_given: int) -> None:
        self.cols = cols
        self.rows = rows
        self.board = [[EMPTY for _ in range(rows)] for _ in range(cols)]

        for x, y in obstacles:
            if 0 <= x < cols and 0 <= y < rows:
                self.board[x][y] = BLOCKED

    def make_a_move(self, time_left: int) -> Tuple[int, int]:
        for y in range(self.rows):
            for x in range(self.cols):
                if self.board[x][y] == EMPTY:
                    return x, y

        # No EMPTY cell found (board full or corrupted)
        return 0, 0

    def attack() :
        raise NotImplementedError
    
    def defense():
        raise NotImplementedError

    def notify_move(self, bot_uid: int, move: Tuple[int, int]) -> None:
        x, y = move
        if 0 <= x < self.cols and 0 <= y < self.rows:
            self.board[x][y] = bot_uid
