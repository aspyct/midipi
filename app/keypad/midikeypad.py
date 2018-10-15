#!/usr/bin/env python3

import curses
import rtmidi
from rtmidi.midiconstants import CONTROL_CHANGE


MIDI_NAME = "MidiPad"
MIDI_CHANNEL = 0
ENTER = 0x01
TRACK_SELECTED = 0x02


class MidiPad:
    def __init__(self, stdscr, midi_out, midi_channel=0):
        """
        :type midi_out: rtmidi.MidiOut
        """
        self.stdscr = stdscr
        self.midi_out = midi_out
        self.midi_channel = midi_channel & 0x0f
        self.handlers = {
            0x0a: self.handle_enter
        }

        for digit in range(0x30, 0x40):
            self.handlers[digit] = self.handle_digit

    def run(self):
        self.stdscr.clear()

        try:
            while 1:
                key = self.stdscr.getch()
                self.handle_input(key)
        except KeyboardInterrupt:
            print("Thanks for playing with me! Bye :)")

    def show_error(self, message):
        self.clear_error()
        self.stdscr.addstr(0, 0, message)

    def clear_error(self):
        # TODO
        pass

    def handle_input(self, key):
        try:
            self.handlers[key](key)
            self.clear_error()
        except KeyError:
            self.show_error("Unhandled key: 0x{0:02X}".format(key))

    def handle_digit(self, digit):
        int_value = digit - 0x30

        message = [
            CONTROL_CHANGE | self.midi_channel,
            TRACK_SELECTED,
            int_value
        ]

        self.midi_out.send_message(message)

    def handle_enter(self, _):
        message = [
            CONTROL_CHANGE | self.midi_channel,
            ENTER,
            0
        ]

        self.midi_out.send_message(message)


def main(stdscr):
    midi_out = rtmidi.MidiOut()
    midi_out.open_virtual_port(MIDI_NAME)

    pad = MidiPad(stdscr, midi_out, MIDI_CHANNEL)
    pad.run()


if __name__ == '__main__':
    curses.wrapper(main)
