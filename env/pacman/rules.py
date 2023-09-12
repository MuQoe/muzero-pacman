import defs
class CaptureRules:
    """
    These game rules manage the control flow of a game, deciding when
    and how the game starts and ends.
    """

    def __init__(self, quiet = False):
        self.quiet = quiet

    def newGame(self, layout, agents, display, length, muteAgents, catchExceptions):
        initState = GameState()
        initState.initialize(layout, len(agents))
        starter = random.randint(0, 1)
        print('%s team starts' % ['Red', 'Blue'][starter])
        game = Game(agents, display, self, startingIndex=starter, muteAgents=muteAgents,
                    catchExceptions=catchExceptions)
        game.state = initState
        # game.length = length
        # game.state.data.timeleft = length
        if 'drawCenterLine' in dir(display):
            display.drawCenterLine()
        self._initBlueFood = initState.getBlueFood().count()
        self._initRedFood = initState.getRedFood().count()
        return game

    def process(self, state, game):
        """
        Checks to see whether it is time to end the game.
        """
        if 'moveHistory' in dir(game):
            if len(game.moveHistory) == game.length:
                state.data._win = True

        if state.isOver():
            game.gameOver = True
            if not game.rules.quiet:
                redCount = 0
                blueCount = 0
                foodToWin = (defs.TOTAL_FOOD / 2) - defs.MIN_FOOD
                for index in range(state.getNumAgents()):
                    agentState = state.data.agentStates[index]
                    if index in state.getRedTeamIndices():
                        redCount += agentState.numReturned
                    else:
                        blueCount += agentState.numReturned

                if blueCount >= foodToWin:  # state.getRedFood().count() == MIN_FOOD:
                    print('The Blue team has returned at least %d of the opponents\' dots.' % foodToWin)
                elif redCount >= foodToWin:  # state.getBlueFood().count() == MIN_FOOD:
                    print('The Red team has returned at least %d of the opponents\' dots.' % foodToWin)
                else:  # if state.getBlueFood().count() > MIN_FOOD and state.getRedFood().count() > MIN_FOOD:
                    print('Time is up.')
                    if state.data.score == 0:
                        print('Tie game!')
                    else:
                        winner = 'Red'
                        if state.data.score < 0: winner = 'Blue'
                        print('The %s team wins by %d points.' % (winner, abs(state.data.score)))

    def getProgress(self, game):
        blue = 1.0 - (game.state.getBlueFood().count() / float(self._initBlueFood))
        red = 1.0 - (game.state.getRedFood().count() / float(self._initRedFood))
        moves = len(self.moveHistory) / float(game.length)

        # return the most likely progress indicator, clamped to [0, 1]
        return min(max(0.75 * max(red, blue) + 0.25 * moves, 0.0), 1.0)

    def agentCrash(self, game, agentIndex):
        if agentIndex % 2 == 0:
            print("Red agent crashed", file=sys.stderr)
            game.state.data.score = -1
        else:
            print("Blue agent crashed", file=sys.stderr)
            game.state.data.score = 1



