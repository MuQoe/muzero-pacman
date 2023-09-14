from env.unit_test.baselineTeam import Agent1, Agent2


class expert_pacman:
    def __init__(self):
        self.agent1 = Agent1(0)
        self.agent2 = Agent1(1)
        self.agent3 = Agent2(2)
        self.agent4 = Agent2(3)
        self.agents = [self.agent1, self.agent2, self.agent3, self.agent4]

    def fit(self, env):
        for agent in self.agents:
            agent.fit(env)

    def getAction(self, env):
        player_index = env.current_player
        player = self.agents[player_index]
        move = player.getAction(env)

        return move
