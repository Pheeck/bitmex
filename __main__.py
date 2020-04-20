#! /usr/bin/env python3

import sys

from multithreaded.multithreaded import Bot

import frontend.windows as windows
import newfrontend.landing as landing


def main(argv):
    if len(argv) > 1 and argv[1].lower() == "onlybot":
        Bot.main()
    else:
        if len(argv) > 1 and argv[1].lower() == "newfrontend":
            window = landing.Landing()
        else:
            window = windows.Main()
        while window.isAlive:
            window.update()


if __name__ == "__main__":
    main(sys.argv)
