import sys, gen, render as R
W, C = gen.build()
R.render(W.a, W.names, 'q_overall.png', view=sys.argv[1] if len(sys.argv)>1 else 'ne', scale=1, floor_y=gen.G-6)
# 剖切：只留 x<=QX
import numpy as np
a = W.a.copy(); a[gen.QX+1:, :, :] = 0
R.render(a, W.names, 'q_cut.png', view='se', scale=2, crop=(gen.PX-20, gen.QX+1, 20, 262), floor_y=gen.G-40)
