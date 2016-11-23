import pyext

class Launchpad(object):
    def onButtonEvent(self, row, col, pressed):
        raise RuntimeError('method Launchpad.onButtonEvent not implemented')

    def writeMidi(self, v1, v2, v3):
        raise RuntimeError('method Launchpad.writeMidi not implemented')

    def onMidiData(self, data):
        if data[0] == 0xB0:
            row = 8
            col = data[1] - 104
        else:
            row = data[1] // 16
            col = data[1] % 16
        self.onButtonEvent(row, col, data[2] > 0)

    def clip(self, x, xmin, xmax):
        return max(xmin, min(xmax, x))

    def reset(self):
        self.writeMidi(0xB0, 0x00, 0x00)

    def makeValue(self, r, g, clear=False, copy=False):
        r = int(self.clip(r, 0, 3))
        g = int(self.clip(g, 0, 3))
        clear = int(clear)
        copy = int(copy)
        return r | (g << 4) | (clear << 3) | (copy << 2)

    def setLed(self, row, col, r, g, clear=False, copy=False):
        row = int(self.clip(row, 0, 8))
        col = int(self.clip(col, 0, 8))
        r = int(self.clip(r, 0, 3))
        g = int(self.clip(g, 0, 3))
        if row == 8: status, addr = 0xB0, 0x68 + col # top row
        else: status, addr = 0x90, (row & 0x0F) << 4 | 0x0F & col
        self.writeMidi(status, addr, self.makeValue(r, g, clear, copy))

    def setBuffers(self, displaying, updating, flash=False, copy=False):
        displaying = int(self.clip(displaying, 0, 1))
        updating = int(self.clip(updating, 0, 1))
        val = 1 << 5
        val |= displaying
        val |= updating << 2
        val |= flash << 3
        val |= copy << 4
        self.writeMidi(0xB0, 0x00, val)

    def testLeds(self, val):
        self.writeMidi(0xB0, 0x00, 0x7D + self.clip(val, 0, 2))

    def setDutyCycle(self, num, denom):
        num = int(self.clip(num, 1, 16))
        denom = int(self.clip(denom, 3, 18))
        h = int(num >= 9)
        self.writeMidi(0xB0, 0x1E + h, 16 * (num - 1 - 8 * h) + denom - 3)

    def setLeds(self, *args):
        if len(args) not in (128, 144, 160):
            raise ValueError('setleds must have either 128, 144 or 160 arguments')
        for i in range(0, len(args), 4):
            r1, g1, r2, g2 = map(int, args[i:i+4])
            v1 = self.makeValue(r1, g1)
            v2 = self.makeValue(r2, g2)
            self.writeMidi(0x92, v1, v2)

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

