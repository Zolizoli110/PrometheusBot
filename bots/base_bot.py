from typing import List, Tuple

class BaseBot:
    """
    All bots must inherit from BaseBot.
    Bots must define:
        - init_board()
        - make_a_move()
        - notify_move()
    """

    def __init__(self, uid: int):
        self.unique_id = uid
        # Always use the actual class name as the bot name
        self.name = self.__class__.__name__

    def init_board(self, cols: int, rows: int, win_length: int, obstacles: List[Tuple[int, int]], time_given: int) -> None:
        raise NotImplementedError

    def make_a_move(self, time_left: int) -> Tuple[int, int]:
        raise NotImplementedError

    def notify_move(self, bot_uid: int, move: Tuple[int, int]) -> None:
        raise NotImplementedError
