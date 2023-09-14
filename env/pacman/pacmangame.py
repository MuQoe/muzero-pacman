import gymnasium as gym
import numpy as np
from gymnasium.spaces import Box, Discrete

from env.pacman.abstractGame import AbstractPacmanGame
from env.pacman.defs import *
from env.pacman.util import *


class PacmanGame(AbstractPacmanGame):
    """
    The Game manages the control flow, soliciting actions from agents.
    """

    def __init__(self, num_stack: int = 6):
        super().__init__(num_stack)
        self.num_stack = num_stack

    def step(self, action, agent_index=0):
        self.reset_data()
        directions = Directions.toDirection(action)

        self.applyAction(directions, agent_index)
        self.checkDeath(agent_index)
        decrementTimer(self.getAgentState(agent_index))

        self._agentMoved = agent_index
        self.score += self.scoreChange
        self.time_left -= 1

        # swap player
        self.current_player = (self.current_player + 1) % 4

        done = self.check_win()

        reward = 0
        # reward = 1 if self.check_win() else 0
        # reward = self.scoreChange
        # # 红色的reward 是负的
        # if self.isOnRedTeam(agent_index):
        #     reward = -reward
        #
        # # 时间惩罚
        # if abs(reward) <= 0.1:
        #     reward -= 0.1
        # if self.check_win():
        max_score = self.total_food / 2
        reward += abs(self.score)
        reward -= float(max_score) / float(1200 - self.time_left)

        return self.observation(), reward, done

    def reset_data(self):
        # self._foodEaten = None
        self._foodAdded = None
        # self._capsuleEaten = None
        self.scoreChange = 0

    def check_win(self):
        return self.game_end or self.time_left <= 0

    def getAgentState(self, index):
        return self.agentStates[index]

    def get_legal_actions(self, agentIndex):
        """
        Returns a list of legal actions (which are both possible & allowed)
        """
        agentState = self.getAgentState(agentIndex)
        conf = agentState.configuration
        possibleActions = Actions.getPossibleActions(conf, self.walls)

        # to actions
        actions = []
        for action in possibleActions:
            actions.append(Directions.toAction(action))
        # print('legal actions: ', actions, agentIndex)
        return actions

    def applyAction(self, action, agent_index):
        """
            Edits the state to reflect the results of the action.
        """
        legal = self.get_legal_actions(agent_index)
        if Directions.toAction(action) not in legal:
            agent = self.getAgentState(agent_index)
            raise Exception("Illegal action " + str(action) + " agent: " + str(agent))
            # raise Exception("Illegal action " + str(action))

        # Update Configuration
        agentState = self.getAgentState(agent_index)
        speed = 1.0
        # if agentState.isPacman: speed = 0.5
        vector = Actions.directionToVector(action, speed)
        oldConfig = agentState.configuration
        agentState.configuration = oldConfig.generateSuccessor(vector)

        # Eat
        next = agentState.configuration.getPosition()
        nearest = nearestPoint(next)

        if next == nearest:
            isRed = self.isOnRedTeam(agent_index)
            # Change agent type
            agentState.isPacman = [isRed, self.isRed(agentState.configuration)].count(True) == 1
            if agentState.numCarrying > 0 and not agentState.isPacman:
                score = agentState.numCarrying if isRed else -1 * agentState.numCarrying
                self.scoreChange += score

                agentState.numReturned += agentState.numCarrying
                agentState.numCarrying = 0

                redCount = 0
                blueCount = 0
                for index in range(4):
                    agentState = self.agentStates[index]
                    if index in self.getRedTeamIndices():
                        redCount += agentState.numReturned
                    else:
                        blueCount += agentState.numReturned
                if redCount >= (self.total_food / 2) - MIN_FOOD or blueCount >= (self.total_food / 2) - MIN_FOOD:
                    self.game_end = True
                # print('red: ', redCount, 'blue: ', blueCount, self.time_left)

        if agentState.isPacman and manhattanDistance(nearest, next) <= 0.9:
            self.consume(nearest, self.isOnRedTeam(agent_index))

    def consume(self, position, isRed):
        x, y = position
        # Eat food
        if self.food[x][y]:

            teamIndicesFunc = self.getBlueTeamIndices
            if isRed:
                teamIndicesFunc = self.getRedTeamIndices

            # go increase the variable for the pacman who ate this
            agents = [self.getAgentState(agentIndex) for agentIndex in teamIndicesFunc()]
            for agent in agents:
                if agent.getPosition() == position:
                    agent.numCarrying += 1
                    break

            self.food = self.food.copy()
            self.food[x][y] = False
            self._foodEaten = position

        # Eat capsule
        if isRed:
            myCapsules = self.getBlueCapsules()
        else:
            myCapsules = self.getRedCapsules()
        if position in myCapsules:
            self.capsules.remove(position)
            self._capsuleEaten = position

            # Reset all ghosts' scared timers
            if isRed:
                otherTeam = self.getBlueTeamIndices()
            else:
                otherTeam = self.getRedTeamIndices()
            for index in otherTeam:
                self.agentStates[index].scaredTimer = SCARED_TIME

    def checkDeath(self, agent_index):
        agentState = self.getAgentState(agent_index)
        if self.isOnRedTeam(agent_index):
            otherTeam = self.getBlueTeamIndices()
        else:
            otherTeam = self.getRedTeamIndices()
        if agentState.isPacman:
            for index in otherTeam:
                otherAgentState = self.agentStates[index]
                if otherAgentState.isPacman:
                    continue
                ghostPosition = otherAgentState.getPosition()
                if ghostPosition is None:
                    continue
                if manhattanDistance(ghostPosition, agentState.getPosition()) <= COLLISION_TOLERANCE:
                    # award points to the other team for killing Pacmen
                    if otherAgentState.scaredTimer <= 0:
                        self.dumpFoodFromDeath(agentState)

                        score = KILL_POINTS
                        if self.isOnRedTeam(agent_index):
                            score = -score
                        self.scoreChange += score
                        agentState.isPacman = False
                        agentState.configuration = agentState.start
                        agentState.scaredTimer = 0
                    else:
                        score = KILL_POINTS
                        if self.isOnRedTeam(agent_index):
                            score = -score
                        self.scoreChange += score
                        otherAgentState.isPacman = False
                        otherAgentState.configuration = otherAgentState.start
                        otherAgentState.scaredTimer = 0
        else:  # Agent is a ghost
            for index in otherTeam:
                otherAgentState = self.getAgentState(index)
                if not otherAgentState.isPacman: continue
                pacPos = otherAgentState.getPosition()
                if pacPos is None:
                    continue
                if manhattanDistance(pacPos, agentState.getPosition()) <= COLLISION_TOLERANCE:
                    # award points to the other team for killing Pacmen
                    if agentState.scaredTimer <= 0:
                        self.dumpFoodFromDeath(otherAgentState)

                        score = KILL_POINTS
                        if not self.isOnRedTeam(agent_index):
                            score = -score
                        self.scoreChange += score
                        otherAgentState.isPacman = False
                        otherAgentState.configuration = otherAgentState.start
                        otherAgentState.scaredTimer = 0
                    else:
                        score = KILL_POINTS
                        if self.isOnRedTeam(agent_index):
                            score = -score
                        self.scoreChange += score
                        agentState.isPacman = False
                        agentState.configuration = agentState.start
                        agentState.scaredTimer = 0

    def dumpFoodFromDeath(self, agentState):
        if not agentState.isPacman:
            raise Exception('something is seriously wrong, this agent isnt a pacman!')

        # ok so agentState is this:
        if agentState.numCarrying == 0:
            return

        # first, score changes!
        # we HACK pack that ugly bug by just determining if its red based on the first position
        # to die...
        dummyConfig = Configuration(agentState.getPosition(), 'North')
        isRed = self.isRed(dummyConfig)

        # the score increases if red eats dots, so if we are refunding points,
        # the direction should be -1 if the red agent died, which means he dies
        # on the blue side
        # scoreDirection = (-1) ** (int(isRed) + 1)

        numToDump = agentState.numCarrying
        self.food = self.food.copy()
        foodAdded = []

        def genSuccessors(x, y):
            DX = [-1, 0, 1]
            DY = [-1, 0, 1]
            return [(x + dx, y + dy) for dx in DX for dy in DY]

        # BFS graph search
        positionQueue = [agentState.getPosition()]
        seen = set()
        while numToDump > 0:
            if not len(positionQueue):
                raise Exception('Exhausted BFS! uh oh')
            # pop one off, graph check
            popped = positionQueue.pop(0)
            if popped in seen:
                continue
            seen.add(popped)

            x, y = popped[0], popped[1]
            x = int(x)
            y = int(y)
            if self.allGood(x, y, isRed):
                self.food[x][y] = True
                foodAdded.append((x, y))
                numToDump -= 1

            # generate successors
            positionQueue = positionQueue + genSuccessors(x, y)

        self._foodAdded = foodAdded
        # now our agentState is no longer carrying food
        agentState.numCarrying = 0
        pass

    def to_play(self):
        return self.current_player

    def onRightSide(self, x, y, is_red):
        dummyConfig = Configuration((x, y), 'North')
        return self.isRed(dummyConfig) == is_red

    def allGood(self, x, y, is_red):
        width, height = self.layout.width, self.layout.height
        food, walls = self.food, self.layout.walls

        # bounds check
        if x >= width or y >= height or x <= 0 or y <= 0:
            return False

        if walls[x][y]:
            return False
        if food[x][y]:
            return False

        # dots need to be on the side where this agent will be a pacman :P
        if not self.onRightSide(x, y, is_red):
            return False

        if (x, y) in self.capsules:
            return False

        # loop through agents
        agentPoses = [self.getAgentPosition(i) for i in range(4)]
        if (x, y) in agentPoses:
            return False

        return True

    def observation(self) -> np.ndarray:
        # 初始化一个21x34x18的全零观测
        observation = np.zeros((21, 34, 18), dtype=np.uint8)

        # current player
        current_player = self.current_player
        current_agent = self.agentStates[current_player]
        current_pos = current_agent.getPosition()
        current_team = self.getBlueTeamIndices()
        other_team = self.getRedTeamIndices()
        foodlist = self.getBlueFood()
        capsulelist = self.getBlueCapsules()

        if self.isOnRedTeam(current_player):
            current_team = self.getRedTeamIndices()
            other_team = self.getBlueTeamIndices()
            foodlist = self.getRedFood()
            capsulelist = self.getRedCapsules()
        distances = [noisyDistance(current_pos, self.getAgentPosition(i)) for i in range(4)]

        # set the current player's pos with the current player's index
        for index in current_team:
            agent_state = self.agentStates[index]
            agent_pos = agent_state.getPosition()
            if agent_pos is not None:
                if agent_state.isPacman:
                    observation[0, agent_pos[0], agent_pos[1]] = index
                else:
                    agent_pos = agent_state.getPosition()
                    if agent_pos is not None:
                        observation[1, agent_pos[0], agent_pos[1]] = index
                        if agent_state.scaredTimer > 0:
                            observation[
                                7, agent_pos[0], agent_pos[1]] = agent_state.scaredTimer

        for index in other_team:
            agent_state = self.agentStates[index]
            agent_pos = agent_state.getPosition()
            if agent_pos is not None:
                distance_to_enemy = manhattanDistance(current_pos, agent_state.configuration.pos)
                if distance_to_enemy <= SIGHT_RANGE:
                    if agent_state.isPacman:
                        observation[2, agent_pos[0], agent_pos[1]] = index
                    else:
                        observation[3, agent_pos[0], agent_pos[1]] = index
                        if agent_state.scaredTimer > 0:
                            observation[8, agent_pos[0], agent_pos[1]] = agent_state.scaredTimer

        # 食物位置
        foods = foodlist.asList()
        if len(foods) > 0:
            food_x, food_y = zip(*foods)
            observation[4, food_x, food_y] = 1

        # 能量点位置（己方为1，敌方为-1）
        if len(capsulelist) > 0:
            capsule_x, capsule_y = zip(*capsulelist)
            observation[5, capsule_x, capsule_y] = 1

        # 墙的位置
        wall_x, wall_y = zip(*self.walls.asList())
        observation[7, wall_x, wall_y] = 1

        # 敌方Pacman的大致距离
        observation[9, :, :] = distances[other_team[0]]
        observation[10, :, :] = distances[other_team[1]]

        # numCarrying
        observation[11, :, :] = self.getAgentState(0).numCarrying
        observation[12, :, :] = self.getAgentState(1).numCarrying
        observation[13, :, :] = self.getAgentState(2).numCarrying
        observation[14, :, :] = self.getAgentState(3).numCarrying

        observation[15, :, :] = self.getAgentState(0).numReturned
        observation[16, :, :] = self.getAgentState(1).numReturned
        observation[17, :, :] = self.getAgentState(2).numReturned
        observation[18, :, :] = self.getAgentState(3).numReturned

        observation[19, :, :] = self.score
        observation[20, :, :] = self.current_player
        return observation

    def _foodWallStr(self, hasFood, hasWall):
        if hasFood:
            return '.'
        elif hasWall:
            return '%'
        else:
            return ' '

    def _pacStr(self, dir):
        if dir == Directions.NORTH:
            return 'v'
        if dir == Directions.SOUTH:
            return '^'
        if dir == Directions.WEST:
            return '>'
        return '<'

    def _ghostStr(self, dir):
        return 'G'
        if dir == Directions.NORTH:
            return 'M'
        if dir == Directions.SOUTH:
            return 'W'
        if dir == Directions.WEST:
            return '3'
        return 'E'

    def __str__(self):
        width, height = self.layout.width, self.layout.height
        map = Grid(width, height)
        if type(self.food) == type((1, 2)):
            self.food = reconstituteGrid(self.food)
        for x in range(width):
            for y in range(height):
                food, walls = self.food, self.layout.walls
                map[x][y] = self._foodWallStr(food[x][y], walls[x][y])

        for agentState in self.agentStates:
            if agentState == None: continue
            if agentState.configuration == None: continue
            x, y = [int(i) for i in nearestPoint(agentState.configuration.pos)]
            agent_dir = agentState.configuration.direction
            if agentState.isPacman:
                map[x][y] = self._pacStr(agent_dir)
            else:
                map[x][y] = self._ghostStr(agent_dir)

        for x, y in self.capsules:
            map[x][y] = 'o'

        return str(map) + ("\nScore: %d\n" % self.score)
