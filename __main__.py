#! /usr/bin/env python3

import sys

import bot.bot as bot

import frontend.windows as windows
import newfrontend.landing as landing


def main(argv):
    if len(argv) > 1 and argv[1].lower() == "onlybot":
        bot.main()
    else:
        if len(argv) > 1 and argv[1].lower() == "newfrontend":
            window = landing.Landing()
        else:
            window = windows.Main()
        while window.isAlive:
            window.update()


if __name__ == "__main__":
    main(sys.argv)
