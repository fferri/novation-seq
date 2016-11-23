import pyext
from collections import defaultdict
from launchpad import Launchpad, LaunchpadPdImpl

class BufferedLaunchpad(Launchpad):
    def __init__(self):
        super(BufferedLaunchpad, self).__init__()
        self.currentBuffer = 'default'
        self.sections = ('top', 'right', 'center')
        self.sectionCoords = {'top': [(8, i) for i in range(8)], 'right': [(i, 8) for i in range(8)], 'center': [(i, j) for i in range(8) for j in range(8)]}
        self.buffer = {k: {'default': self.emptyBuffer(), '_dev': self.emptyBuffer()} for k in self.sections}

    def onButtonEvent(self, row, col, pressed):
        if row == 8: section = 'top'
        elif col == 8: section = 'right'
        else: section = 'center'
        row += self.buffer[section][self.currentBuffer]['rowOffset']
        col += self.buffer[section][self.currentBuffer]['colOffset']
        self.onBufferButtonEvent(self.currentBuffer, section, row, col, pressed)

    def onBufferButtonEvent(self, bufferName, sectionName, row, col, pressed):
        raise RuntimeError('method BufferedLaunchpad.onBufferButtonEvent not implemented')

    def emptyBuffer(self):
        return {'rowOffset': 0, 'colOffset': 0, 'data': defaultdict(lambda: [0, 0])}

    def syncBuffer(self, name):
        for section in self.sections:
            for (dstRow, dstCol) in self.sectionCoords[section]:
                srcRow = self.buffer[section][name]['rowOffset'] + dstRow
                srcCol = self.buffer[section][name]['colOffset'] + dstCol
                if self.buffer[section]['_dev']['data'][dstRow, dstCol] != self.buffer[section][name]['data'][srcRow, srcCol]:
                    if self.buffer[section][name]['data'][srcRow, srcCol] == [0, 0]:
                        del self.buffer[section]['_dev']['data'][dstRow, dstCol]
                    else:
                        self.buffer[section]['_dev']['data'][dstRow, dstCol] = self.buffer[section][name]['data'][srcRow, srcCol]
                    red, green = self.buffer[section]['_dev']['data'][dstRow, dstCol]
                    self.setLed(dstRow, dstCol, red, green)

    def syncCurrentBuffer(self):
        self.syncBuffer(self.currentBuffer)

    def selectBuffer(self, bufferName):
        self.currentBuffer = bufferName
        for section in self.sections:
            if bufferName not in self.buffer[section]:
                self.buffer[section][bufferName] = self.emptyBuffer()

    def clearBuffer(self, bufferName):
        if bufferName == '_cur': bufferName = self.currentBuffer
        for section in self.sections:
            keys = list(self.buffer[section][bufferName]['data'].keys())
            for key in keys:
                del self.buffer[section][bufferName]['data'][key]

    def set(self, bufferName, sectionName, row, col, r, g):
        if bufferName == '_cur': bufferName = self.currentBuffer
        if r == 0 and g == 0 and (row, col) in self.buffer[sectionName][bufferName]['data']:
            del self.buffer[sectionName][bufferName]['data'][row, col]
        else:
            self.buffer[sectionName][bufferName]['data'][row, col] = [r, g]

    def scroll(self, bufferName, sectionName, row, col):
        if bufferName == '_cur': bufferName = self.currentBuffer
        row = int(row)
        col = int(col)
        self.buffer[sectionName][bufferName]['rowOffset'] = row
        self.buffer[sectionName][bufferName]['colOffset'] = col

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

