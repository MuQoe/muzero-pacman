class Game:
    """
    The Game manages the control flow, soliciting actions from agents.
    """

    def __init__(self):
        self.rules = rules
        self.startingIndex = starting_index
        self.gameOver = False
        self.moveHistory = []
        self.numMoves = 0

    def to_play(self):
        # TODO: rewrite this
        return self.startingIndex

    def reset(self):
        # TODO: rewrite this
        pass

