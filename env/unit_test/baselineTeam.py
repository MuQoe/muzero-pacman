import random

from env.pacman import util
from env.pacman.defs import Directions, Actions
from env.pacman.game import PacmanGame
from env.pacman.util import nearestPoint
from env.unit_test import distanceCalculator

MAX_CAPACITY = 3


class TestTeamDummy:
    def __init__(self, index):
        self.carrying = 0
        self.current_target = None
        self.index = index

        self.red = None

        self.agentsOnTeam = None

        self.distancer = None

        self.observationHistory = []

        self.boundary = None

        self.display = None

    def fit(self, env):
        self.red = env.isOnRedTeam(self.index)

        self.distancer = distanceCalculator.Distancer(env.layout)
        # comment this out to forgo maze distance computation and use manhattan distances
        self.distancer.getMazeDistances()

        import __main__
        if '_display' in dir(__main__):
            self.display = __main__._display

        self.boundary = self.getBoundary(env)

    def getClosestPos(self, gameState:PacmanGame, pos_list):
        min_length = 9999
        min_pos = None
        my_local_state = gameState.getAgentState(self.index)
        my_pos = my_local_state.getPosition()
        for pos in pos_list:
            temp_length = self.getMazeDistance(my_pos, pos)
            if temp_length < min_length:
                min_length = temp_length
                min_pos = pos
        return min_pos

    def getBoundary(self, gameState: PacmanGame):
        boundary_location = []
        height = gameState.layout.height
        width = gameState.layout.width
        for i in range(height):
            if self.red:
                j = int(width / 2) - 1
            else:
                j = int(width / 2)
            if not gameState.hasWall(j, i):
                boundary_location.append((j, i))
        return boundary_location

    def aStarSearch(self, problem):
        """Search the node that has the lowest combined cost and heuristic first."""
        myPQ = util.PriorityQueue()
        startState = problem.getStartState()
        # print(f"start states {startState}")
        startNode = (startState, '', 0, [])
        heuristic = problem._manhattanDistance
        myPQ.push(startNode, heuristic(startState))
        visited = set()
        best_g = dict()
        while not myPQ.isEmpty():
            node = myPQ.pop()
            state, action, cost, path = node
            # print(cost)
            # print(f"visited list is {visited}")
            # print(f"best_g list is {best_g}")
            if (not state in visited) or cost < best_g.get(str(state)):
                visited.add(state)
                best_g[str(state)] = cost
                if problem.isGoalState(state):
                    path = path + [(state, action)]
                    actions = [action[1] for action in path]
                    del actions[0]
                    return actions
                for succ in problem.getSuccessors(state):
                    succState, succAction, succCost = succ
                    newNode = (succState, succAction, cost + succCost, path + [(node, action)])
                    myPQ.push(newNode, heuristic(succState) + cost + succCost)
        return []

    def getAction(self, gameState: PacmanGame):
        action = self.getAction_inner(gameState)
        return Directions.toAction(action)
    def getAction_inner(self, gameState):
        """
        Calls chooseAction on a grid position, but continues on half positions.
        If you subclass CaptureAgent, you shouldn't need to override this method.  It
        takes care of appending the current gameState on to your observation history
        (so you have a record of the game states of the game) and will call your
        choose action method if you're in a state (rather than halfway through your last
        move - this occurs because Pacman agents move half as quickly as ghost agents).

        """
        # self.observationHistory.append(gameState)

        myState = gameState.getAgentState(self.index)
        myPos = myState.getPosition()
        if myPos != nearestPoint(myPos):
            # We're halfway from one position to the next
            return gameState.getLegalActions(self.index)[0]
        else:
            return self.chooseAction(gameState)

    def chooseAction(self, gameState: PacmanGame):
        """
        Picks among actions randomly.
        """
        # if(self.index == 1):
        #     print(self.current_target)


        if not self.current_target == None:
            # if agent already have a goal
            pass
        elif self.carrying == MAX_CAPACITY or len(self.getFood(gameState).asList()) <= 2:
            # if agent got all the food it needed
            # it will reach to the closest boundary with A* search (manhattanDistance as heuristic)
            self.current_target = self.getClosestPos(gameState, self.boundary)
        else:
            # if agent have more capacity to carry
            # it will find the next closest food
            foodGrid = self.getFood(gameState)
            self.current_target = self.getClosestPos(gameState, foodGrid.asList())

        problem = PositionSearchProblem(gameState, self.current_target, self.index)
        path = self.aStarSearch(problem)

        if path == []:
            actions = gameState.get_legal_actions(self.index)
            return random.choice(actions)
        else:
            action = path[0]
            dx, dy = Actions.directionToVector(action)
            x, y = gameState.getAgentState(self.index).getPosition()
            new_x, new_y = int(x + dx), int(y + dy)
            if (new_x, new_y) == self.current_target:
                self.current_target = None
            if self.getFood(gameState)[new_x][new_y]:
                self.carrying += 1
            elif (new_x, new_y) in self.boundary:
                self.carrying = 0
            return path[0]

    def getFood(self, gameState: PacmanGame):
        """
        Returns the food you're meant to eat. This is in the form of a matrix
        where m[x][y]=true if there is food you can eat (based on your team) in that square.
        """
        if self.red:
            return gameState.getBlueFood()
        else:
            return gameState.getRedFood()

    def getFoodYouAreDefending(self, gameState: PacmanGame):
        """
        Returns the food you're meant to protect (i.e., that your opponent is
        supposed to eat). This is in the form of a matrix where m[x][y]=true if
        there is food at (x,y) that your opponent can eat.
        """
        if self.red:
            return gameState.getRedFood()
        else:
            return gameState.getBlueFood()

    def getCapsules(self, gameState: PacmanGame):
        if self.red:
            return gameState.getBlueCapsules()
        else:
            return gameState.getRedCapsules()

    def getCapsulesYouAreDefending(self, gameState: PacmanGame):
        if self.red:
            return gameState.getRedCapsules()
        else:
            return gameState.getBlueCapsules()

    def getOpponents(self, gameState: PacmanGame):
        """
        Returns agent indices of your opponents. This is the list of the numbers
        of the agents (e.g., red might be "1,3,5")
        """
        if self.red:
            return gameState.getBlueTeamIndices()
        else:
            return gameState.getRedTeamIndices()

    def getTeam(self, gameState: PacmanGame):
        """
        Returns agent indices of your team. This is the list of the numbers
        of the agents (e.g., red might be the list of 1,3,5)
        """
        if self.red:
            return gameState.getRedTeamIndices()
        else:
            return gameState.getBlueTeamIndices()

    def getScore(self, gameState: PacmanGame):
        """
        Returns how much you are beating the other team by in the form of a number
        that is the difference between your score and the opponents score.  This number
        is negative if you're losing.
        """
        if self.red:
            return gameState.getScore()
        else:
            return gameState.getScore() * -1

    def getMazeDistance(self, pos1, pos2):
        """
        Returns the distance between two points; These are calculated using the provided
        distancer object.

        If distancer.getMazeDistances() has been called, then maze distances are available.
        Otherwise, this just returns Manhattan distance.
        """
        d = self.distancer.getDistance(pos1, pos2)
        return d

    def getPreviousObservation(self):
        """
        Returns the GameState object corresponding to the last state this agent saw
        (the observed state of the game last time this agent moved - this may not include
        all of your opponent's agent locations exactly).
        """
        if len(self.observationHistory) == 1:
            return None
        else:
            return self.observationHistory[-2]

    def getCurrentObservation(self):
        """
        Returns the GameState object corresponding this agent's current observation
        (the observed state of the game - this may not include
        all of your opponent's agent locations exactly).
        """
        return self.observationHistory[-1]

    def displayDistributionsOverPositions(self, distributions):
        """
        Overlays a distribution over positions onto the pacman board that represents
        an agent's beliefs about the positions of each agent.

        The arg distributions is a tuple or list of util.Counter objects, where the i'th
        Counter has keys that are board positions (x,y) and values that encode the probability
        that agent i is at (x,y).

        If some elements are None, then they will be ignored.  If a Counter is passed to this
        function, it will be displayed. This is helpful for figuring out if your agent is doing
        inference correctly, and does not affect gameplay.
        """
        dists = []
        for dist in distributions:
            if dist != None:
                if not isinstance(dist, util.Counter): raise Exception("Wrong type of distribution")
                dists.append(dist)
            else:
                dists.append(util.Counter())
        else:
            self._distributions = dists  # These can be read by pacclient.py


class PositionSearchProblem:
    """
    It is the ancestor class for all the search problem class.
    A search problem defines the state space, start state, goal test, successor
    function and cost function.  This search problem can be used to find paths
    to a particular point.
    """

    def __init__(self, gameState :PacmanGame, goal, agentIndex=0, costFn=lambda x: 1):
        self.walls = gameState.getWalls()
        self.costFn = costFn
        x, y = gameState.getAgentState(agentIndex).getPosition()
        self.startState = int(x), int(y)
        self.goal_pos = goal

    def getStartState(self):
        return self.startState

    def isGoalState(self, state):

        return state == self.goal_pos

    def getSuccessors(self, state):
        successors = []
        for action in [Directions.NORTH, Directions.SOUTH, Directions.EAST, Directions.WEST]:
            x, y = state
            dx, dy = Actions.directionToVector(action)
            nextx, nexty = int(x + dx), int(y + dy)
            if not self.walls[nextx][nexty]:
                nextState = (nextx, nexty)
                cost = self.costFn(nextState)
                successors.append((nextState, action, cost))
        return successors

    def getCostOfActions(self, actions):
        if actions == None: return 999999
        x, y = self.getStartState()
        cost = 0
        for action in actions:
            # Check figure out the next state and see whether its' legal
            dx, dy = Actions.directionToVector(action)
            x, y = int(x + dx), int(y + dy)
            if self.walls[x][y]: return 999999
            cost += self.costFn((x, y))
        return cost

    def _manhattanDistance(self, pos):
        return util.manhattanDistance(pos, self.goal_pos)


class Agent1(TestTeamDummy):
    pass


class Agent2(TestTeamDummy):

    # this agent will reach to the furthest goal
    def getClosestPos(self, gameState, pos_list):
        return self.getFurthestPos(gameState, pos_list)

    def getFurthestPos(self, gameState, pos_list):
        max_length = -1
        max_pos = None
        my_local_state = gameState.getAgentState(self.index)
        my_pos = my_local_state.getPosition()
        for pos in pos_list:
            temp_length = self.getMazeDistance(my_pos, pos)
            if temp_length > max_length:
                max_length = temp_length
                max_pos = pos
        return max_pos