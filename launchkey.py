import pyext

class launchkey(pyext._class):
    _inlets = 1
    _outlets = 3

    def __init__(self, *args):
        self.midiBuffer = [[], []]
        self.buttonMidiMap = {0x68: 'track-up', 0x69: 'track-down',
                              0x6A: 'track-left', 0x6B: 'track-right'}
        self.controlMidiMap = {0x15 + i: i for i in range(8)}

    def __del__(self):
        pass

    def writeMidi(self, v1, v2, v3):
        self._outlet(2, v1)
        self._outlet(2, v2)
        self._outlet(2, v3)

    def writeOutput(self, *l):
        self._outlet(3, l)

    def midi_1(self, f):
        self.bufferMidi(0, int(f))

    def cmidi_1(self, f):
        self.bufferMidi(1, int(f))

    def clip(self, x, xmin, xmax):
        return max(xmin, min(xmax, x))

    def reset_1(self):
        self.writeMidi(0xB0, 0x00, 0x00)

    def extendedmode_1(self, enable):
        self.writeMidi(0x90, 0x0C, 0x7F * int(enable))

    def makeValue(self, r, g, clear=False, copy=False):
        r = int(self.clip(r, 0, 3))
        g = int(self.clip(g, 0, 3))
        clear = int(clear)
        copy = int(copy)
        return r | (g << 4) | (clear << 3) | (copy << 2)

    def setled_1(self, row, col, r, g, *args):
        row = int(self.clip(row, 0, 1))
        col = int(self.clip(col, 0, 8))
        r = int(self.clip(r, 0, 3))
        g = int(self.clip(g, 0, 3))
        status, addr = 0x90, 0x60 + row * 0x10 + col
        val = (r & 3) | ((g & 3) << 4)
        self.writeMidi(status, addr, val)

    def bufferMidi(self, i, f):
        if f & 0x80: # status bit
            self.midiBuffer[i] = [f]
        else:
            self.midiBuffer[i].append(f)
        if len(self.midiBuffer[i]) == 3:
            self.onMidiData(i, self.midiBuffer[i])
            self.midiBuffer[i] = []

    def onMidiData(self, i, data):
        if i == 0:
            if data[0] & 0xF0 in (0x90, 0x80):
                self.writeOutput('note', data[1], data[2])
            else:
                print('launchkey: unrecognized midi on note iface: %02X %02X %02X' % tuple(data))
        elif i == 1:
	    if data[0] in (0xB0, ):
		if data[1] >= 0x15 and data[1] <= 0x1C:
		    self.writeOutput('control', self.controlMidiMap[data[1]], data[2])
		if data[1] >= 0x68 and data[1] <= 0x6D:
		    self.writeOutput('button', self.buttonMidiMap[data[1]], data[2] > 0)
	    elif data[0] in (0x90, 0x80) and data[1] & 0xF0 in (0x60, 0x70) and data[1] & 0x0F <= 8:
		row = int(data[1] & 0xF0 == 0x70)
		col = data[1] & 0x0F
		self.writeOutput('pad', row, col, data[2])
	    else:
		print('launchkey: unrecognized midi on control iface: %02X %02X %02X' % tuple(data))
