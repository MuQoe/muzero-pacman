import gymnasium as gym
import numpy as np
from gymnasium.spaces import Box, Discrete

from env.pacman.abstractGame import AbstractPacmanGame
from env.pacman.defs import *
from env.pacman.util import *


class Game(AbstractPacmanGame):
    """
    The Game manages the control flow, soliciting actions from agents.
    """

    def __init__(self, num_stack: int = 6):
        self.num_stack = num_stack

    def step(self, action):
        # TODO: rewrite this
        directions = Directions.toDirection(action)

    def get_observation(self):
        # pass
        pass

    def is_game_over(self):
        pass

    def get_result_string(self):
        pass

    def check_win(self):
        pass

    def getAgentState(self, index):
        return self.agentStates[index]

    def getLegalActions(state, agentIndex):
        """
        Returns a list of legal actions (which are both possible & allowed)
        """
        agentState = state.getAgentState(agentIndex)
        conf = agentState.configuration
        possibleActions = Actions.getPossibleActions(conf, state.walls)
        return possibleActions

    def applyAction(self, action):
        """
            Edits the state to reflect the results of the action.
            """
        legal = self.getLegalActions(self.to_play)
        if action not in legal:
            raise Exception("Illegal action " + str(action))

        # Update Configuration
        agentState = self.getAgentState(self.to_play)
        speed = 1.0
        # if agentState.isPacman: speed = 0.5
        vector = Actions.directionToVector(action, speed)
        oldConfig = agentState.configuration
        agentState.configuration = oldConfig.generateSuccessor(vector)

        # Eat
        next = agentState.configuration.getPosition()
        nearest = nearestPoint(next)

        if next == nearest:
            isRed = self.isOnRedTeam(self.to_play)
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
                if redCount >= (TOTAL_FOOD / 2) - MIN_FOOD or blueCount >= (TOTAL_FOOD / 2) - MIN_FOOD:
                    self.isWin = True

        if agentState.isPacman and manhattanDistance(nearest, next) <= 0.9:
            self.consume(nearest, self.isOnRedTeam(self.to_play))

    def consume(self, position, isRed):
        x, y = position
        # Eat food
        if self.food[x][y]:

            teamIndicesFunc = self.getBlueTeamIndices
            score = -1
            if isRed:
                score = 1
                teamIndicesFunc = self.getRedTeamIndices

            # go increase the variable for the pacman who ate this
            agents = [self.agentStates[agentIndex] for agentIndex in teamIndicesFunc()]
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

    def checkDeath(state, agentIndex):
        agentState = state.data.agentStates[agentIndex]
        if state.isOnRedTeam(agentIndex):
            otherTeam = state.getBlueTeamIndices()
        else:
            otherTeam = state.getRedTeamIndices()
        if agentState.isPacman:
            for index in otherTeam:
                otherAgentState = state.data.agentStates[index]
                if otherAgentState.isPacman: continue
                ghostPosition = otherAgentState.getPosition()
                if ghostPosition == None: continue
                if manhattanDistance(ghostPosition, agentState.getPosition()) <= COLLISION_TOLERANCE:
                    # award points to the other team for killing Pacmen
                    if otherAgentState.scaredTimer <= 0:
                        AgentRules.dumpFoodFromDeath(state, agentState, agentIndex)

                        score = KILL_POINTS
                        if state.isOnRedTeam(agentIndex):
                            score = -score
                        state.data.scoreChange += score
                        agentState.isPacman = False
                        agentState.configuration = agentState.start
                        agentState.scaredTimer = 0
                    else:
                        score = KILL_POINTS
                        if state.isOnRedTeam(agentIndex):
                            score = -score
                        state.data.scoreChange += score
                        otherAgentState.isPacman = False
                        otherAgentState.configuration = otherAgentState.start
                        otherAgentState.scaredTimer = 0
        else:  # Agent is a ghost
            for index in otherTeam:
                otherAgentState = state.data.agentStates[index]
                if not otherAgentState.isPacman: continue
                pacPos = otherAgentState.getPosition()
                if pacPos == None: continue
                if manhattanDistance(pacPos, agentState.getPosition()) <= COLLISION_TOLERANCE:
                    # award points to the other team for killing Pacmen
                    if agentState.scaredTimer <= 0:
                        AgentRules.dumpFoodFromDeath(state, otherAgentState, agentIndex)

                        score = KILL_POINTS
                        if not state.isOnRedTeam(agentIndex):
                            score = -score
                        state.data.scoreChange += score
                        otherAgentState.isPacman = False
                        otherAgentState.configuration = otherAgentState.start
                        otherAgentState.scaredTimer = 0
                    else:
                        score = KILL_POINTS
                        if state.isOnRedTeam(agentIndex):
                            score = -score
                        state.data.scoreChange += score
                        agentState.isPacman = False
                        agentState.configuration = agentState.start
                        agentState.scaredTimer = 0