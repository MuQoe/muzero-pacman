import random

from env.pacman import layout
from env.pacman.game import Game
from env.unit_test.baselineTeam import TestTeam

# seed = random.randint(0, 99999999)
# # layout = 'layouts/random%08dCapture.lay' % seed
# # print 'Generating random layout in %s' % layout
# import mazeGenerator
#
# temp = mazeGenerator.generateMaze(seed)
# l = layout.Layout(temp.split('\n'))
# aaa = 0

env = Game()
red_one = TestTeam(0)
blue_one = TestTeam(1)
red_two = TestTeam(2)
blue_two = TestTeam(3)

red_one.fit(env)
blue_one.fit(env)
red_two.fit(env)
blue_two.fit(env)
players = [red_one, blue_one, red_two, blue_two]
player_index = 0
while True:
    player = players[player_index]
    move = player.getAction(env)
    _, _, done = env.step(move)

    if done:
        print(env.getScore())
        break


    # update the player index
    player_index = (player_index + 1) % 4




