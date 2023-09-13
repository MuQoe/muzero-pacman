import random
import time
import numpy as np
from env.pacman import layout
from env.pacman.game import Game
from env.unit_test import captureGraphicsDisplay
from env.unit_test.baselineTeam import Agent1, Agent2

# seed = random.randint(0, 99999999)
# # layout = 'layouts/random%08dCapture.lay' % seed
# # print 'Generating random layout in %s' % layout
# import mazeGenerator
#
# temp = mazeGenerator.generateMaze(seed)
# l = layout.Layout(temp.split('\n'))
# aaa = 0
# random.seed('cs188')
# captureGraphicsDisplay.FRAME_TIME = 0
# display = captureGraphicsDisplay.PacmanGraphics('./baselineTeam.py',"Red",'./baselineTeam.py',
#                                                         "Blue", 1, 0, capture=True)
# import __main__
# __main__.__dict__['_display'] = display


env = Game(start_index=0)

red_one = Agent1(0)
blue_one = Agent1(1)
red_two = Agent2(2)
blue_two = Agent2(3)

red_one.fit(env)
blue_one.fit(env)
red_two.fit(env)
blue_two.fit(env)
players = [red_one, blue_one, red_two, blue_two]
player_index = 0

start_time = time.time()
# display.initialize(env)
while True:
    player = players[player_index]
    # temp_env = env.copy()
    move = player.getAction(env)
    obs, _, done = env.step(move, player_index)

    # display.update(env.copy())
    if done:
        print(env.getScore())
        break
    # print(env)
    # update the player index
    player_index = (player_index + 1) % 4

end_time = time.time()
print(f"Time elapsed: {end_time - start_time}")
