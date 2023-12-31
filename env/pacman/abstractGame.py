import collections
import copy
import random
from collections import deque

import gymnasium as gym
import numpy as np
from gymnasium.spaces import Box, Discrete

from defaultlayout import test_layout
from env.pacman import mazeGenerator, layout
from env.pacman.defs import Directions, AgentState, Configuration
from env.pacman.util import halfList, nearestPoint, halfGrid
import expandmap

class AbstractPacmanGame(gym.Env):

    def __init__(
            self,
            num_stack: int = 6,
            seeds : int = 0,
    ) -> None:
        """
        :param num_stack: stack last N history frames as input, default is 6.
        """
        self.layout_seed = seeds
        self.num_stack = num_stack
        self.world = np.zeros((18, 34), dtype=np.int8)

        seed = random.randint(0, 99999999)
        temp = mazeGenerator.generateMazeWithSize(seed).split('\n')
        temp = expandmap.expand_board_with_percent(temp,34,18)

        # layout_str = "\n".join(temp) + "\n"
        # # save to file
        # with open('layout.txt','w') as f:
        #     f.write(layout_str)

        world = layout.Layout(temp)


        self.walls = world.walls
        self.food = world.food
        self.capsules = world.capsules
        self.agentStates = []
        self.layout = world
        numGhosts = 0
        numGhostAgents = 4
        for isPacman, pos in world.agentPositions:
            if not isPacman:
                if numGhosts == numGhostAgents:
                    continue  # Max ghosts reached already
                else:
                    numGhosts += 1
            self.agentStates.append(AgentState(Configuration(pos, Directions.STOP), isPacman))
        self._eaten = [False for a in self.agentStates]

        positions = [a.configuration for a in self.agentStates]
        self.blueTeam = [i for i, p in enumerate(positions) if not self.isRed(p)]
        self.redTeam = [i for i, p in enumerate(positions) if self.isRed(p)]
        self.teams = [self.isRed(p) for p in positions]
        self.total_food = self.layout.totalFood

        self.TIME_LIMIT = 400
        self.time_left = self.TIME_LIMIT
        self.score = 0
        self.scoreChange = 0
        self._foodEaten = None
        self._foodAdded = None
        self._capsuleEaten = None

        # red and blue player
        """
        red -> [0, 2]
        blue -> [1 ,3]
        """
        self.red_one = 0
        self.red_two = 2
        self.blue_one = 1
        self.blue_two = 3

        self.red_team = 0
        self.blue_team = 1

        self.player_dict = {
            0: self.red_one,
            1: self.blue_one,
            2: self.red_two,
            3: self.blue_two,
        }

        self.action_dim = Directions.len()
        # self.legal_actions = np.ones(self.action_dim, dtype=np.int8).flatten()

        self.current_player = random.randint(0, 1)

        self.steps = 0
        self.game_end = False
        self._agentMoved = None
        self.last_move = None

        self.history = []
        self.trace = collections.Counter()

        self.reset()

    def reset(self, **kwargs) -> np.ndarray:
        """Reset game to initial state."""
        super().reset(**kwargs)

        self.world = np.zeros((18, 34), dtype=np.int8)

        seed = random.randint(0, 99999999)
        temp = mazeGenerator.generateMazeWithSize(seed).split('\n')
        temp = expandmap.expand_board_with_percent(temp, 34, 18)
        world = layout.Layout(temp)
        #world = layout.Layout(mazeGenerator.generateMaze(self.layout_seed))
        self.walls = world.walls
        self.food = world.food
        self.capsules = world.capsules
        self.agentStates = []
        self.layout = world
        numGhosts = 0
        numGhostAgents = 4
        for isPacman, pos in world.agentPositions:
            if not isPacman:
                if numGhosts == numGhostAgents:
                    continue  # Max ghosts reached already
                else:
                    numGhosts += 1
            self.agentStates.append(AgentState(Configuration(pos, Directions.STOP), isPacman))
        self._eaten = [False for a in self.agentStates]

        positions = [a.configuration for a in self.agentStates]
        self.blueTeam = [i for i, p in enumerate(positions) if not self.isRed(p)]
        self.redTeam = [i for i, p in enumerate(positions) if self.isRed(p)]
        self.teams = [self.isRed(p) for p in positions]
        self.total_food = self.layout.totalFood

        self.time_left = self.TIME_LIMIT
        self.score = 0
        self.scoreChange = 0
        self._foodEaten = None
        self._foodAdded = None
        self._capsuleEaten = None

        # red and blue player
        """
        red -> [0, 2]
        blue -> [1 ,3]
        """
        self.red_one = 0
        self.red_two = 2
        self.blue_one = 1
        self.blue_two = 3

        self.red_team = 0
        self.blue_team = 1

        self.player_dict = {
            0: self.red_one,
            1: self.blue_one,
            2: self.red_two,
            3: self.blue_two,
        }

        self.action_dim = Directions.len()
        # self.legal_actions = np.ones(self.action_dim, dtype=np.int8).flatten()

        self.current_player = random.randint(0, 1)

        self.steps = 0
        self.game_end = False
        self._agentMoved = None
        self.last_move = None

        self.history = []
        self.trace = collections.Counter()

        return self.observation()

    def observation(self) -> np.ndarray:
        return np.zeros((21, 18, 34), dtype=np.int8)

    # implement a copy function that returns a copy of the game
    def copy(self):
        return copy.deepcopy(self)
    @property
    def opponent_team(self) -> int:
        if self.current_player == self.red_one or self.current_player == self.red_two:
            return self.blue_team
        return self.red_team

    def isRed(self, config_or_pos):
        width = self.layout.width
        if isinstance(config_or_pos, tuple):
            return config_or_pos[0] < width // 2
        else:
            return config_or_pos.pos[0] < width // 2

    def isOnRedTeam(self, agent_index):
        """
        Returns true if the agent with the given agentIndex is on the red team.
        """
        return self.teams[agent_index]

    def getRedTeamIndices(self):
        """
        Returns a list of agent index numbers for the agents on the red team.
        """
        return self.redTeam[:]

    def getBlueTeamIndices(self):
        """
        Returns a list of the agent index numbers for the agents on the blue team.
        """
        return self.blueTeam[:]

    def getRedCapsules(self):
        return halfList(self.capsules, self.food, red=True)

    def getBlueCapsules(self):
        return halfList(self.capsules, self.food, red=False)

    def getAgentPosition(self, index):
        """
        Returns a location tuple if the agent with the given index is observable;
        if the agent is unobservable, returns None.
        """
        agentState = self.agentStates[index]
        ret = agentState.getPosition()
        if ret:
            return tuple(int(x) for x in ret)
        return ret

    def getScore(self):
        """
        Returns a number corresponding to the current score.
        """
        return self.score

    def getRedFood(self):
        """
        Returns a matrix of food that corresponds to the food on the red team's side.
        For the matrix m, m[x][y]=true if there is food in (x,y) that belongs to
        red (meaning red is protecting it, blue is trying to eat it).
        """
        return halfGrid(self.food, red=True)

    def getBlueFood(self):
        """
        Returns a matrix of food that corresponds to the food on the blue team's side.
        For the matrix m, m[x][y]=true if there is food in (x,y) that belongs to
        blue (meaning blue is protecting it, red is trying to eat it).
        """
        return halfGrid(self.food, red=False)
    def getWalls(self):
        """
        Just like getFood but for walls
        """
        return self.walls

    def hasWall(self, x, y):
        """
        Returns true if (x,y) has a wall, false otherwise.
        """
        return self.walls[x][y]
