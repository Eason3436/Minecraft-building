"""組裝：塔身＋地景。"""
import time
from core import *
import tower as TW, land as LD


def main():
    t0 = time.time()
    W = World()
    info = {}
    LD.build_land(W, info)
    TW.build_tower(W, info)
    print('built', round(time.time() - t0, 1), {k: v for k, v in info.items() if k != 'furniture'})
    return W, info


if __name__ == '__main__':
    W, info = main()
    import render as R
    R.render(W.a, W.names, 'quick.png', view='sw', scale=1, title='quick')
    print(W.stats())
