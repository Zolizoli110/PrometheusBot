from _pyrepl.commands import end
from typing import List, Tuple

from .base_bot import BaseBot

EMPTY = -1
BLOCKED = -2


class AttackBot(BaseBot):
    def __init__(self, uid: int):
        super().__init__(uid)
        self.cols = 0
        self.rows = 0
        self.board: List[List[int]] = []
        self.win_length = 0

    def init_board(self, cols: int, rows: int, win_length: int, obstacles: List[Tuple[int, int]], time_given: int) -> None:
        self.cols = cols
        self.rows = rows
        self.win_length = win_length
        self.board = [[EMPTY for _ in range(rows)] for _ in range(cols)]

        for x, y in obstacles:
            if 0 <= x < cols and 0 <= y < rows:
                self.board[x][y] = BLOCKED

    def make_a_move(self, time_left: int) -> Tuple[int, int]:
        for y in range(self.rows-1, 0, -1):
            line = y
            for x in range(line, 0, -1):
                if self.board[x][y] != EMPTY and self.board[x][y] != self.unique_id:
                    break
                if self.board[x][y] == EMPTY:
                    return x, y

        # No EMPTY cell found (board full or corrupted)
        return 0, 0

    #def check(self):
        start = Tuple[0, 0]
        end = Tuple[self.win_length, self.win_length]
        obstacle = Tuple[int, int]
        for y in range(start.index(1), end.index(1)):
            for x in range(start.index(0), end.index(0)):
                if self.board[x][y] != EMPTY:
                    obstacle = x, y
    def notify_move(self, bot_uid: int, move: Tuple[int, int]) -> None:
        x, y = move
        if 0 <= x < self.cols and 0 <= y < self.rows:
            self.board[x][y] = bot_uid
