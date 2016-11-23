from collections import defaultdict
from device import Launchpad

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

