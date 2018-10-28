#!/usr/bin/env python3
import os
import os.path
import signal
from multiprocessing import Process

import midipi.pad
import midipi.looper
import midipi.wires


def main():
    midipi.pad.main(start_other_processes)

def start_other_processes():
    Process(
        target=midipi.looper.multiprocess,
        args=('looper.log', )
    ).start()

    Process(
        target=midipi.wires.multiprocess,
        args=('wires.log', )
    ).start()
    

if __name__ == '__main__':
    main()
