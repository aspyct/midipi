#!/usr/bin/env python3

import rtmidi
import time
import sys

class AllChannels:
    def __eq__(self, channel):
        return True


class ExactMatch:
    def __init__(self, name):
        self.name = name

    def __eq__(self, other):
        return self.name == other

    def __str__(self):
        return "exact({})".format(repr(self.name))


class MidiDevice:
    def __init__(self, full_name, port):
        self.full_name = full_name
        self.port = port
        self.input = None
        self.output = None
        self.forwards = []

    def matches(self, user_spec):
        if type(user_spec) is str:
            return user_spec.lower() in self.full_name.lower()
        else:
            return user_spec == self.full_name

    def prepare_for_output(self):
        if self.output is None:
            self.output = rtmidi.MidiOut()
            self.output.open_port(self.port)

    def send_message(self, message):
        self.output.send_message(message)

    def forward_messages(self, output, channel):
        output.prepare_for_output()

        self.input = rtmidi.MidiIn()
        self.input.open_port(self.port)
        self.input.set_callback(self.callback)

        self.forwards.append((output, channel))

    def callback(self, midi_data, _):
        message, delta = midi_data
        midi_channel = message[0] & 0x0f

        for (output, channel) in self.forwards: 
            # +1 because it's zero indexed, yet numbered 1-16
            if channel == midi_channel + 1:
                output.send_message(message)


class Station:
    def __init__(self):
        self.input_devices = None
        self.output_devices = None

    def wire(self, wiring):
        input_device_list = self.__discover_input_devices()
        output_device_list = self.__discover_output_devices()

        wire_list = []
        for (input_spec, channel, output_spec) in wiring:
            input_device = self.__find_matching_device(input_spec, input_device_list)
            output_device = self.__find_matching_device(output_spec, output_device_list)
            
            if input_device is None:
                print(
                    "Can't find an input device matching: " + str(input_spec),
                    file=sys.stderr
                )

            if output_device is None:
                print(
                    "Can't find an output device matching output: " + str(output_spec),
                    file=sys.stderr
                )

            if input_device is None or output_device is None:
                print("Skipping", file=sys.stderr)
                continue

            wire_list.append((input_device, output_device, channel))

        for (in_d, out_d, chan) in wire_list:
            in_d.forward_messages(out_d, chan)

    def wire_and_run(self, wiring):
        self.wire(wiring)

        try:
            while 1:
                time.sleep(10)
        except KeyboardInterrupt:
            # TODO Send a midi panic command to all devices
            print("Interrupted. Goodbye")
    
    def __discover_input_devices(self):
        return self.__discover_devices(rtmidi.MidiIn())
    
    def __discover_output_devices(self):
        return self.__discover_devices(rtmidi.MidiOut())

    def __discover_devices(self, midi):
        return list(
            MidiDevice(name, port) for port, name in enumerate(midi.get_ports())
        )

    def __find_matching_device(self, spec, device_list):
        device = None

        for potential_device in device_list:
            if potential_device.matches(spec):
                if device is None:
                    device = potential_device
                else:
                    raise Exception("More than one devices match " + str(spec))

        return device


#################
# Configuration #
#################

# TODO Default configuration should just be to wire every input to every output
# TODO Also it should watch usb ports for new inputs

exact = lambda x: ExactMatch(x)
all_channels = AllChannels()

wiring = [
    ('lpk25', all_channels, 'model d'),
    ('Arturia BeatStep Pro MIDI 1', 1, 'model d'),
    ('unknown input', all_channels, 'model d')
]

station = Station()
station.wire_and_run(wiring)

