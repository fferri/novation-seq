import pyext

class Launchkey(object):
    def __init__(self):
        self.portName = {0: 'MIDI', 1: 'InControl'}
        self.reportUnrecognizedMessages = False
        self.buttonMidiMap = {0x68: 'track-up', 0x69: 'track-down',
                              0x6A: 'track-left', 0x6B: 'track-right'}
        self.controlMidiMap = {0x15 + i: i for i in range(8)}

    def onNoteEvent(self, note, velocity):
        raise RuntimeError('method Launchkey.onXyzEvent not implemented')

    def onPadEvent(self, row, col, velocity):
        raise RuntimeError('method Launchkey.onXyzEvent not implemented')

    def onControlEvent(self, num, value):
        raise RuntimeError('method Launchkey.onXyzEvent not implemented')

    def onButtonEvent(self, name, pressed):
        raise RuntimeError('method Launchkey.onXyzEvent not implemented')

    def writeMidi(self, v1, v2, v3):
        raise RuntimeError('method Launchkey.writeMidi not implemented')

    def onMidiData(self, port, data):
        if port == 0:
            if data[0] & 0xF0 in (0x90, 0x80):
                self.onNoteEvent(data[1], data[2])
                return
        elif port == 1:
	    if data[0] in (0xB0, ):
		if data[1] >= 0x15 and data[1] <= 0x1C:
		    self.onControlEvent(self.controlMidiMap[data[1]], data[2])
                    return
		if data[1] >= 0x68 and data[1] <= 0x6D:
		    self.onButtonEvent(self.buttonMidiMap[data[1]], data[2] > 0)
                    return
	    elif data[0] in (0x90, 0x80) and data[1] & 0xF0 in (0x60, 0x70) and data[1] & 0x0F <= 8:
		row = int(data[1] & 0xF0 == 0x70)
		col = data[1] & 0x0F
		self.onPadEvent(row, col, data[2])
                return
        if self.reportUnrecognizedMessages:
            fmt = 'Launchkey: unrecognized midi data on %s iface: %02X %02X %02X'
            print(fmt % (self.portName[port]) + tuple(data))

    def clip(self, x, xmin, xmax):
        return max(xmin, min(xmax, x))

    def reset(self):
        self.writeMidi(0xB0, 0x00, 0x00)

    def setExtendedMode(self, enable):
        self.writeMidi(0x90, 0x0C, 0x7F * int(enable))

    def makeValue(self, r, g, clear=False, copy=False):
        r = int(self.clip(r, 0, 3))
        g = int(self.clip(g, 0, 3))
        clear = int(clear)
        copy = int(copy)
        return r | (g << 4) | (clear << 3) | (copy << 2)

    def setLed(self, row, col, r, g):
        row = int(self.clip(row, 0, 1))
        col = int(self.clip(col, 0, 8))
        r = int(self.clip(r, 0, 3))
        g = int(self.clip(g, 0, 3))
        status, addr = 0x90, 0x60 + row * 0x10 + col
        val = (r & 3) | ((g & 3) << 4)
        self.writeMidi(status, addr, val)

class LaunchkeyPdImpl(Launchkey):
    def __init__(self, pdobj):
        super(LaunchkeyPdImpl, self).__init__()
        self.pdobj = pdobj
        self.midiBuffer = [[], []]

    def writeMidi(self, v1, v2, v3):
        self.pdobj._outlet(2, v1)
        self.pdobj._outlet(2, v2)
        self.pdobj._outlet(2, v3)

    def bufferMidi(self, port, f):
        if f & 0x80: # status bit
            self.midiBuffer[port] = [f]
        else:
            self.midiBuffer[port].append(f)
        if len(self.midiBuffer[port]) == 3:
            self.onMidiData(port, self.midiBuffer[port])
            self.midiBuffer[port] = []

    def onNoteEvent(self, note, velocity):
        self.pdobj._outlet(3, ['note', note, velocity])

    def onPadEvent(self, row, col, velocity):
        self.pdobj._outlet(3, ['pad', row, col, velocity])

    def onControlEvent(self, num, value):
        self.pdobj._outlet(3, ['control', num, value])

    def onButtonEvent(self, name, pressed):
        self.pdobj._outlet(3, ['button', name, pressed])

class LaunchkeyPd(pyext._class):
    _inlets = 1
    _outlets = 3

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

