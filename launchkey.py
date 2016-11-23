import pyext
from devices import Launchkey

class LaunchkeyPdImpl(Launchkey):
    def __init__(self, pdobj):
        super(LaunchkeyPdImpl, self).__init__()
        self.pdobj = pdobj
        self.midiBuffer = [[], []]

    def writeMidi(self, port, v1, v2, v3):
        if port == 0:
            self.pdobj._outlet(1, ['midi', v1])
            self.pdobj._outlet(1, ['midi', v2])
            self.pdobj._outlet(1, ['midi', v3])
        elif port == 1:
            self.pdobj._outlet(1, ['cmidi', v1])
            self.pdobj._outlet(1, ['cmidi', v2])
            self.pdobj._outlet(1, ['cmidi', v3])

    def bufferMidi(self, port, f):
        if f & 0x80: # status bit
            self.midiBuffer[port] = [f]
        else:
            self.midiBuffer[port].append(f)
        if len(self.midiBuffer[port]) == 3:
            self.onMidiData(port, self.midiBuffer[port])
            self.midiBuffer[port] = []

    def onNoteEvent(self, note, velocity):
        self.pdobj._outlet(1, ['note', note, velocity])

    def onPadEvent(self, row, col, velocity):
        self.pdobj._outlet(1, ['pad', row, col, velocity])

    def onControlEvent(self, num, value):
        self.pdobj._outlet(1, ['control', num, value])

    def onButtonEvent(self, name, pressed):
        self.pdobj._outlet(1, ['button', name, pressed])

class LaunchkeyPd(pyext._class):
    _inlets = 1
    _outlets = 1

    def __init__(self, *args):
        self.launchkey = LaunchkeyPdImpl(self)

    def midi_1(self, f):
        self.launchkey.bufferMidi(0, int(f))

    def cmidi_1(self, f):
        self.launchkey.bufferMidi(1, int(f))

    def reset_1(self):
        self.launchkey.reset()

    def extendedmode_1(self, enable):
        self.launchkey.setExtendedMode(enable)

    def setled_1(self, row, col, r, g, *args):
        self.launchkey.setLed(row, col, r, g)

