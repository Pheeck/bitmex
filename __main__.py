#! /usr/bin/env python3

import sys

import frontend.windows as windows


def main(argv):
    window = windows.Main()
    while window.isAlive:
        window.update()


if __name__ == "__main__":
    main(sys.argv)
