#!/usr/bin/env python3
import os
import signal
from multiprocessing import Process

import keypad
import looper
import wires


def main():
    looper_proc = Process(target=looper.main)
    wires_proc = Process(target=wires.main)

    looper_proc.start()
    wires_proc.start()  # Looks like cherrypy hates to run without stdin...

    def rewire():
        os.kill(wires_proc.pid, signal.SIGHUP)

    try:
        keypad.main(rewire)
    except KeyboardInterrupt:
        wires_proc.terminate()
        looper_proc.terminate()
    finally:
        wires_proc.kill()
        looper_proc.kill()


if __name__ == '__main__':
    main()
