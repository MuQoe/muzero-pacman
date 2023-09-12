class Game:
    """
    The Game manages the control flow, soliciting actions from agents.
    """

    def __init__(self):
        self.rules = None
        self.startingIndex = 0
        self.gameOver = False
        self.moveHistory = []
        self.numMoves = 0
        self.board = None

    def to_play(self):
        # TODO: rewrite this
        return self.startingIndex

    def reset(self):
        # TODO: rewrite this
        pass

    def step(self, action):
        # TODO: rewrite this
        pass

    def get_observation(self):
        # pass
        pass

    def is_game_over(self):
        pass

    def get_result_string(self):
        pass

    def check_win(self):
        pass
