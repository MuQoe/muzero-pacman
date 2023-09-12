class AgentRules:
  """
  These functions govern how each agent interacts with her environment.
  """

  def getLegalActions(state, agentIndex):
    """
    Returns a list of legal actions (which are both possible & allowed)
    """
    agentState = state.getAgentState(agentIndex)
    conf = agentState.configuration
    possibleActions = Actions.getPossibleActions(conf, state.data.layout.walls)
    return AgentRules.filterForAllowedActions(agentState, possibleActions)

  getLegalActions = staticmethod(getLegalActions)

  def filterForAllowedActions(agentState, possibleActions):
    return possibleActions

  filterForAllowedActions = staticmethod(filterForAllowedActions)

  def applyAction(state, action, agentIndex):
    """
    Edits the state to reflect the results of the action.
    """
    legal = AgentRules.getLegalActions(state, agentIndex)
    if action not in legal:
      raise Exception("Illegal action " + str(action))

    # Update Configuration
    agentState = state.data.agentStates[agentIndex]
    speed = 1.0
    # if agentState.isPacman: speed = 0.5
    vector = Actions.directionToVector(action, speed)
    oldConfig = agentState.configuration
    agentState.configuration = oldConfig.generateSuccessor(vector)

    # Eat
    next = agentState.configuration.getPosition()
    nearest = nearestPoint(next)

    if next == nearest:
      isRed = state.isOnRedTeam(agentIndex)
      # Change agent type
      agentState.isPacman = [isRed, state.isRed(agentState.configuration)].count(True) == 1
      # if he's no longer pacman, he's on his own side, so reset the num carrying timer
      # agentState.numCarrying *= int(agentState.isPacman)
      if agentState.numCarrying > 0 and not agentState.isPacman:
        score = agentState.numCarrying if isRed else -1 * agentState.numCarrying
        state.data.scoreChange += score

        agentState.numReturned += agentState.numCarrying
        agentState.numCarrying = 0

        redCount = 0
        blueCount = 0
        for index in range(state.getNumAgents()):
          agentState = state.data.agentStates[index]
          if index in state.getRedTeamIndices():
            redCount += agentState.numReturned
          else:
            blueCount += agentState.numReturned
        if redCount >= (TOTAL_FOOD / 2) - MIN_FOOD or blueCount >= (TOTAL_FOOD / 2) - MIN_FOOD:
          state.data._win = True

    if agentState.isPacman and manhattanDistance(nearest, next) <= 0.9:
      AgentRules.consume(nearest, state, state.isOnRedTeam(agentIndex))

  applyAction = staticmethod(applyAction)

  def consume(position, state, isRed):
    x, y = position
    # Eat food
    if state.data.food[x][y]:

      # blue case is the default
      teamIndicesFunc = state.getBlueTeamIndices
      score = -1
      if isRed:
        # switch if its red
        score = 1
        teamIndicesFunc = state.getRedTeamIndices

      # go increase the variable for the pacman who ate this
      agents = [state.data.agentStates[agentIndex] for agentIndex in teamIndicesFunc()]
      for agent in agents:
        if agent.getPosition() == position:
          agent.numCarrying += 1
          break  # the above should only be true for one agent...

      # do all the score and food grid maintainenace
      # state.data.scoreChange += score
      state.data.food = state.data.food.copy()
      state.data.food[x][y] = False
      state.data._foodEaten = position
      # if (isRed and state.getBlueFood().count() == MIN_FOOD) or (not isRed and state.getRedFood().count() == MIN_FOOD):
      #  state.data._win = True

    # Eat capsule
    if isRed:
      myCapsules = state.getBlueCapsules()
    else:
      myCapsules = state.getRedCapsules()
    if (position in myCapsules):
      state.data.capsules.remove(position)
      state.data._capsuleEaten = position

      # Reset all ghosts' scared timers
      if isRed:
        otherTeam = state.getBlueTeamIndices()
      else:
        otherTeam = state.getRedTeamIndices()
      for index in otherTeam:
        state.data.agentStates[index].scaredTimer = SCARED_TIME

  consume = staticmethod(consume)

  def decrementTimer(state):
    timer = state.scaredTimer
    if timer == 1:
      state.configuration.pos = nearestPoint(state.configuration.pos)
    state.scaredTimer = max(0, timer - 1)

  decrementTimer = staticmethod(decrementTimer)

  def dumpFoodFromDeath(state, agentState, agentIndex):
    if not (DUMP_FOOD_ON_DEATH):
      # this feature is not turned on
      return

    if not agentState.isPacman:
      raise Exception('something is seriously wrong, this agent isnt a pacman!')

    # ok so agentState is this:
    if (agentState.numCarrying == 0):
      return

    # first, score changes!
    # we HACK pack that ugly bug by just determining if its red based on the first position
    # to die...
    dummyConfig = Configuration(agentState.getPosition(), 'North')
    isRed = state.isRed(dummyConfig)

    # the score increases if red eats dots, so if we are refunding points,
    # the direction should be -1 if the red agent died, which means he dies
    # on the blue side
    scoreDirection = (-1) ** (int(isRed) + 1)

    # state.data.scoreChange += scoreDirection * agentState.numCarrying

    def onRightSide(state, x, y):
      dummyConfig = Configuration((x, y), 'North')
      return state.isRed(dummyConfig) == isRed

    # we have food to dump
    # -- expand out in BFS. Check:
    #   - that it's within the limits
    #   - that it's not a wall
    #   - that no other agents are there
    #   - that no power pellets are there
    #   - that it's on the right side of the grid
    def allGood(state, x, y):
      width, height = state.data.layout.width, state.data.layout.height
      food, walls = state.data.food, state.data.layout.walls

      # bounds check
      if x >= width or y >= height or x <= 0 or y <= 0:
        return False

      if walls[x][y]:
        return False
      if food[x][y]:
        return False

      # dots need to be on the side where this agent will be a pacman :P
      if not onRightSide(state, x, y):
        return False

      if (x, y) in state.data.capsules:
        return False

      # loop through agents
      agentPoses = [state.getAgentPosition(i) for i in range(state.getNumAgents())]
      if (x, y) in agentPoses:
        return False

      return True

    numToDump = agentState.numCarrying
    state.data.food = state.data.food.copy()
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
      if (allGood(state, x, y)):
        state.data.food[x][y] = True
        foodAdded.append((x, y))
        numToDump -= 1

      # generate successors
      positionQueue = positionQueue + genSuccessors(x, y)

    state.data._foodAdded = foodAdded
    # now our agentState is no longer carrying food
    agentState.numCarrying = 0
    pass

  dumpFoodFromDeath = staticmethod(dumpFoodFromDeath)

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

  checkDeath = staticmethod(checkDeath)

  def placeGhost(state, ghostState):
    ghostState.configuration = ghostState.start

  placeGhost = staticmethod(placeGhost)


class GameState:
  """
  A GameState specifies the full game state, including the food, capsules,
  agent configurations and score changes.

  GameStates are used by the Game object to capture the actual state of the game and
  can be used by agents to reason about the game.

  Much of the information in a GameState is stored in a GameStateData object.  We
  strongly suggest that you access that data via the accessor methods below rather
  than referring to the GameStateData object directly.
  """

  ####################################################
  # Accessor methods: use these to access state data #
  ####################################################

  def getLegalActions( self, agentIndex=0 ):
    """
    Returns the legal actions for the agent specified.
    """
    return AgentRules.getLegalActions( self, agentIndex )

  def generateSuccessor( self, agentIndex, action):
    """
    Returns the successor state (a GameState object) after the specified agent takes the action.
    """
    # Copy current state
    state = GameState(self)

    # Find appropriate rules for the agent
    AgentRules.applyAction( state, action, agentIndex )
    AgentRules.checkDeath(state, agentIndex)
    AgentRules.decrementTimer(state.data.agentStates[agentIndex])

    # Book keeping
    state.data._agentMoved = agentIndex
    state.data.score += state.data.scoreChange
    state.data.timeleft = self.data.timeleft - 1
    return state

  def getAgentState(self, index):
    return self.data.agentStates[index]

  def getAgentPosition(self, index):
    """
    Returns a location tuple if the agent with the given index is observable;
    if the agent is unobservable, returns None.
    """
    agentState = self.data.agentStates[index]
    ret = agentState.getPosition()
    if ret:
      return tuple(int(x) for x in ret)
    return ret

  def getNumAgents( self ):
    return len( self.data.agentStates )

  def getScore( self ):
    """
    Returns a number corresponding to the current score.
    """
    return self.data.score

  def getRedFood(self):
    """
    Returns a matrix of food that corresponds to the food on the red team's side.
    For the matrix m, m[x][y]=true if there is food in (x,y) that belongs to
    red (meaning red is protecting it, blue is trying to eat it).
    """
    return halfGrid(self.data.food, red = True)

  def getBlueFood(self):
    """
    Returns a matrix of food that corresponds to the food on the blue team's side.
    For the matrix m, m[x][y]=true if there is food in (x,y) that belongs to
    blue (meaning blue is protecting it, red is trying to eat it).
    """
    return halfGrid(self.data.food, red = False)

  def getRedCapsules(self):
    return halfList(self.data.capsules, self.data.food, red = True)

  def getBlueCapsules(self):
    return halfList(self.data.capsules, self.data.food, red = False)

  def getWalls(self):
    """
    Just like getFood but for walls
    """
    return self.data.layout.walls

  def hasFood(self, x, y):
    """
    Returns true if the location (x,y) has food, regardless of
    whether it's blue team food or red team food.
    """
    return self.data.food[x][y]

  def hasWall(self, x, y):
    """
    Returns true if (x,y) has a wall, false otherwise.
    """
    return self.data.layout.walls[x][y]

  def isOver( self ):
    return self.data._win

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

  def isOnRedTeam(self, agentIndex):
    """
    Returns true if the agent with the given agentIndex is on the red team.
    """
    return self.teams[agentIndex]

  def getAgentDistances(self):
    """
    Returns a noisy distance to each agent.
    """
    if 'agentDistances' in dir(self) :
      return self.agentDistances
    else:
      return None

  def getDistanceProb(self, trueDistance, noisyDistance):
    "Returns the probability of a noisy distance given the true distance"
    if noisyDistance - trueDistance in SONAR_NOISE_VALUES:
      return 1.0/SONAR_NOISE_RANGE
    else:
      return 0

  def getInitialAgentPosition(self, agentIndex):
    "Returns the initial position of an agent."
    return self.data.layout.agentPositions[agentIndex][1]

  def getCapsules(self):
    """
    Returns a list of positions (x,y) of the remaining capsules.
    """
    return self.data.capsules

  #############################################
  #             Helper methods:               #
  # You shouldn't need to call these directly #
  #############################################

  def __init__( self, prevState = None ):
    """
    Generates a new state by copying information from its predecessor.
    """
    if prevState != None: # Initial state
      self.data = GameStateData(prevState.data)
      self.blueTeam = prevState.blueTeam
      self.redTeam = prevState.redTeam
      self.data.timeleft = prevState.data.timeleft

      self.teams = prevState.teams
      self.agentDistances = prevState.agentDistances
    else:
      self.data = GameStateData()
      self.agentDistances = []

  def deepCopy( self ):
    state = GameState( self )
    state.data = self.data.deepCopy()
    state.data.timeleft = self.data.timeleft

    state.blueTeam = self.blueTeam[:]
    state.redTeam = self.redTeam[:]
    state.teams = self.teams[:]
    state.agentDistances = self.agentDistances[:]
    return state

  def makeObservation(self, index):
    state = self.deepCopy()

    # Adds the sonar signal
    pos = state.getAgentPosition(index)
    n = state.getNumAgents()
    distances = [noisyDistance(pos, state.getAgentPosition(i)) for i in range(n)]
    state.agentDistances = distances

    # Remove states of distant opponents
    if index in self.blueTeam:
      team = self.blueTeam
      otherTeam = self.redTeam
    else:
      otherTeam = self.blueTeam
      team = self.redTeam

    for enemy in otherTeam:
      seen = False
      enemyPos = state.getAgentPosition(enemy)
      for teammate in team:
        if util.manhattanDistance(enemyPos, state.getAgentPosition(teammate)) <= SIGHT_RANGE:
          seen = True
      if not seen: state.data.agentStates[enemy].configuration = None
    return state

  def __eq__( self, other ):
    """
    Allows two states to be compared.
    """
    if other == None: return False
    return self.data == other.data

  def __hash__( self ):
    """
    Allows states to be keys of dictionaries.
    """
    return int(hash( self.data ))

  def __str__( self ):

    return str(self.data)

  def initialize( self, layout, numAgents):
    """
    Creates an initial game state from a layout array (see layout.py).
    """
    self.data.initialize(layout, numAgents)
    positions = [a.configuration for a in self.data.agentStates]
    self.blueTeam = [i for i,p in enumerate(positions) if not self.isRed(p)]
    self.redTeam = [i for i,p in enumerate(positions) if self.isRed(p)]
    self.teams = [self.isRed(p) for p in positions]
    #This is usually 60 (always 60 with random maps)
    #However, if layout map is specified otherwise, it could be less
    global TOTAL_FOOD
    TOTAL_FOOD = layout.totalFood

  def isRed(self, configOrPos):
    width = self.data.layout.width
    if type(configOrPos) == type( (0,0) ):
      return configOrPos[0] < width // 2
    else:
      return configOrPos.pos[0] < width // 2
