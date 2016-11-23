import pyext
from devices import Launchpad

class LaunchpadPdImpl(Launchpad):
    def __init__(self, pdobj):
        super(LaunchpadPdImpl, self).__init__()
        self.pdobj = pdobj
        self.midiBuffer = []

    def writeMidi(self, v1, v2, v3):
        self.pdobj._outlet(1, ['midi', v1])
        self.pdobj._outlet(1, ['midi', v2])
        self.pdobj._outlet(1, ['midi', v3])

    def bufferMidi(self, f):
        if f & 0x80: # status bit
            self.midiBuffer = [f]
        else:
            self.midiBuffer.append(f)
        if len(self.midiBuffer) == 3:
            self.onMidiData(self.midiBuffer)
            self.midiBuffer = []

    def onButtonEvent(self, row, col, pressed):
        self.pdobj._outlet(1, ['button', row, col, int(pressed)])
    
class LaunchpadPd(pyext._class):
    _inlets = 1
    _outlets = 1

    def __init__(self):
        self.launchpad = LaunchpadPdImpl(self)

    def midi_1(self, f):
        self.launchpad.bufferMidi(int(f))

    def reset_1(self):
        self.launchpad.reset()

    def setled_1(self, row, col, r, g, *args):
        clear = bool(args[0]) if len(args) >= 1 else False
        copy = bool(args[1]) if len(args) >= 2 else False
        self.launchpad.setLed(row, col, r, g, clear, copy)

    def buffers_1(self, displaying, updating, *args):
        flash = int(bool(args[0])) if len(args) >= 1 else False
        copy = int(bool(args[1])) if len(args) >= 2 else False
        self.launchpad.setBuffers(displaying, updating, flash, copy)

    def testleds_1(self, val):
        self.launchpad.testLeds(val)

    def setdutycycle_1(self, num, denom):
        self.launchpad.setDutyCycle(num, denom)

