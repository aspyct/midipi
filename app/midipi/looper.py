#!/usr/bin/env python3

import asyncio
import rtmidi
import rtmidi.midiconstants
import sys
import time

from rtmidi.midiconstants import (
    NOTE_ON,
    NOTE_OFF,
    POLY_PRESSURE,
    PITCH_BEND,
    CHANNEL_PRESSURE,
    CONTROL_CHANGE,
    ALL_NOTES_OFF
)


INPUT_PORT_NAME = "Looper in"
OUTPUT_PORT_NAME = "Looper out"

START_STOP_RECORDING = 0x01
SELECT_TRACK = 0x02


class Looper:
    def __init__(self):
        self.midi_in = rtmidi.MidiIn()
        self.midi_out = rtmidi.MidiOut()

        self.current_recorder = None
        self.current_player = None

        self.selected_track = 0
        self.tracks = [None] * 10
        self.playback_event_loop = asyncio.new_event_loop()

        self.message_handlers = {
            START_STOP_RECORDING: self.start_stop_recording,
            SELECT_TRACK: self.select_track
        }

    def run_forever(self):
        self.midi_in.set_callback(self.input_callback)
        self.open_midi_ports()
        self.playback_event_loop.run_forever()

    def open_midi_ports(self):
        self.midi_in.open_virtual_port(INPUT_PORT_NAME)
        self.midi_out.open_virtual_port(OUTPUT_PORT_NAME)

    def input_callback(self, midi_input, time_stamp):
        # TODO use the time_stamp and time_delta for better precision?
        now = time.monotonic() # TODO Maybe correct with time delta from message?
        message, time_delta = midi_input

        message_type = message[0] & 0xf0

        # TODO Optimise this?
        if message_type in (
            NOTE_ON,
            NOTE_OFF,
            POLY_PRESSURE,
            PITCH_BEND,
            CHANNEL_PRESSURE
        ):
            # This is a message to send to the recorder
            if self.current_recorder is not None:
                self.current_recorder.on_message(message, now)

        elif message_type == rtmidi.midiconstants.CONTROL_CHANGE:
            handler = self.message_handlers.get(message[1], self.default_handler)
            handler(message)

    def start_stop_recording(self, _):
        # TODO Make sure we're always on the same thread
        if self.current_player is not None:
            self.current_player.stop()
            self.current_player = None

        if self.current_recorder is None:
            self.current_recorder = Recorder()
            self.current_recorder.start()
        else:
            loop = self.current_recorder.finish()
            self.current_recorder = None
            self.tracks[self.selected_track] = loop
            self.play_track(self.selected_track)

    def select_track(self, message):
        selection = message[2]

        if not (0 <= selection < len(self.tracks)):
            print("Not a valid track: {}".format(selection), file=sys.stderr)
            return
        elif self.current_recorder is not None:
            # We're recording. Selecting a track sets the desired slot
            self.selected_track = selection
        else:
            self.play_track(selection)

    def default_handler(self, message):
        print("Can't handle message: {}".format(repr(message)), file=sys.stderr)

    def play_track(self, selection):
        # For now we'll only play one track at a time
        if self.current_player is not None:
            self.current_player.stop()

        self.current_player = Player(
            self.tracks[selection],
            self.midi_out,
            self.playback_event_loop
        )
        self.current_player.play()


class Loop:
    def __init__(self, messages, time_to_end):
        """

        :type messages: list
        """
        self.messages = messages
        self.time_to_end = time_to_end


class Player:
    def __init__(self, loop, midi_out, event_loop):
        self.loop = loop
        self.midi_out = midi_out
        self.event_loop = event_loop

        self.start_time = None
        self.next_call_handle = None

    def play(self):
        self.event_loop.call_soon_threadsafe(self.__schedule_first_message)

    def stop(self):
        self.event_loop.call_soon_threadsafe(self.__cancel)

    def __schedule_first_message(self):
        self.start_time = self.event_loop.time()
        self.__schedule_message(0)

    def __schedule_message(self, i):
        time, message = self.loop.messages[i]

        self.next_call_handle = self.event_loop.call_at(
            self.start_time + time,
            self.__send_message,
            message,
            i
        )

    def __send_message(self, message, i):
        self.midi_out.send_message(message)

        if len(self.loop.messages) - 1 > i:
            self.__schedule_message(i + 1)
        else:
            # Done. Loop around
            self.next_call_handle = self.event_loop.call_at(
                self.start_time + self.loop.time_to_end,
                self.__schedule_first_message
            )

    def __cancel(self):
        if self.next_call_handle is not None:
            self.next_call_handle.cancel()
            self.next_call_handle = None

            self.midi_out.send_message([CONTROL_CHANGE, ALL_NOTES_OFF, 0])


class Recorder:
    def __init__(self):
        self.start_time = None
        self.messages = None

    def start(self):
        self.start_time = time.monotonic()
        self.messages = []

    def finish(self):
        now = time.monotonic()
        return Loop(
            self.messages,
            now - self.start_time
        )

    def on_message(self, message, time):
        self.messages.append(
            (time - self.start_time, message)
        )


def main():
    looper = Looper()
    looper.run_forever()


def multiprocess(stdouterr_file):
    sys.stdout = sys.stderr = open(stdouterr_file, 'w')
    main()


if __name__ == '__main__':
    main()
