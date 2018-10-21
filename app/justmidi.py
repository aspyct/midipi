#!/usr/bin/env python3

from multiprocessing import Process

import keypad
import looper
import wires


def main():
    looper_proc = Process(target=looper.main)
    wires_proc = Process(target=wires.main)

    looper_proc.start()
    wires_proc.start()

    try:
        keypad.main()
    except KeyboardInterrupt:
        wires_proc.terminate()
        looper_proc.terminate()
    finally:
        wires_proc.kill()
        looper_proc.kill()


if __name__ == '__main__':
    main()
