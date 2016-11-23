import pyext
from collections import defaultdict
from devices import BufferedLaunchpad

class BufferedLaunchpadPdImpl(BufferedLaunchpad):
    def __init__(self, pdobj):
        super(BufferedLaunchpadPdImpl, self).__init__()
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

    def onBufferButtonEvent(self, bufferName, sectionName, row, col, pressed):
        self.pdobj._outlet(1, ['buffer', bufferName, sectionName, 'button', row, col, int(pressed)])

class BufferedLaunchpadPd(pyext._class):
    _inlets = 1
    _outlets = 1

    def __init__(self):
        self.buffer = BufferedLaunchpadPdImpl(self)

    def midi_1(self, f):
        self.buffer.bufferMidi(int(f))

    def select_1(self, bufferName):
        bufferName = str(bufferName)
        self.buffer.selectBuffer(bufferName)
        self.buffer.syncCurrentBuffer()

    def clear_1(self, bufferName):
        bufferName = str(bufferName)
        self.buffer.clearBuffer(bufferName)
        self.buffer.syncCurrentBuffer()

    def clearb_1(self, bufferName):
        bufferName = str(bufferName)
        self.buffer.clearBuffer(bufferName)

    def set_1(self, bufferName, sectionName, row, col, r, g):
        bufferName = str(bufferName)
        sectionName = str(sectionName)
        self.buffer.set(bufferName, sectionName, row, col, r, g)
        self.buffer.syncCurrentBuffer()

    def setb_1(self, bufferName, sectionName, row, col, r, g):
        bufferName = str(bufferName)
        sectionName = str(sectionName)
        self.buffer.set(bufferName, sectionName, row, col, r, g)

    def sync_1(self, bufferName):
        self.buffer.syncCurrentBuffer()

    def scroll_1(self, bufferName, sectionName, row, col):
        bufferName = str(bufferName)
        sectionName = str(sectionName)
        self.buffer.scroll(bufferName, sectionName, row, col)
        self.buffer.syncCurrentBuffer()

    def scrollb_1(self, bufferName, sectionName, row, col):
        bufferName = str(bufferName)
        sectionName = str(sectionName)
        self.buffer.scroll(bufferName, sectionName, row, col)

