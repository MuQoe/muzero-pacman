import random

from env.pacman import layout

seed = random.randint(0, 99999999)
# layout = 'layouts/random%08dCapture.lay' % seed
# print 'Generating random layout in %s' % layout
import mazeGenerator

temp = mazeGenerator.generateMaze(seed)
l = layout.Layout(temp.split('\n'))
aaa = 0