from time import time
from heapq import *
from pygame import pypm

class Output:
    def __init__(self, application, midiOut):
        self.application = application
        self.midiOut = self.openMidi(midiOut)
        self.scheduledEvents = []

    def openMidi(self, name):
        for i in range(pypm.CountDevices()):
            info = pypm.GetDeviceInfo(i)
            if info[1] == name and info[3]:
                print('opening MIDI output device {} ({})'.format(info[1], info))
                return pypm.Output(i, 0)

    def play(self, channel, notes, trigEvent):
        t = time()
        for note in notes:
            duration = 60./self.application.bpm/4*trigEvent.length
            heappush(self.scheduledEvents, (t, (0x90 + channel, note, trigEvent.velocity)))
            heappush(self.scheduledEvents, (t+duration, (0x80 + channel, note, 0)))

    def tick(self):
        t = time()
        while len(self.scheduledEvents) > 0 and self.scheduledEvents[0][0] <= t:
            t, ev = heappop(self.scheduledEvents)
            if self.midiOut: self.midiOut.WriteShort(*ev)
            else: print('OUTPUT: {:02X} {:02X} {:02X}'.format(*ev))

