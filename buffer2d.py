import pyext
from collections import defaultdict

class buffer2d(pyext._class):
    _inlets = 2
    _outlets = 2

    def __init__(self):
        self.currentBuffer = 'default'
        self.sections = ('top', 'right', 'center')
        self.sectionCoords = {'top': [(8, i) for i in range(8)], 'right': [(i, 8) for i in range(8)], 'center': [(i, j) for i in range(8) for j in range(8)]}
        self.buffer = {k: {'default': self.emptyBuffer(), '_dev': self.emptyBuffer()} for k in self.sections}

    def emptyBuffer(self):
        return {'rowOffset': 0, 'colOffset': 0, 'data': defaultdict(lambda: [0, 0])}

    def _anything_2(self, *args):
        a = list(args[:])
        if a[0] in (pyext.Symbol('button'), pyext.Symbol('pad')):
            if a[1] == 8: section = 'top'
            elif a[2] == 8: section = 'right'
            else: section = 'center'
            a[1] += self.buffer[section][self.currentBuffer]['rowOffset']
            a[2] += self.buffer[section][self.currentBuffer]['colOffset']
            self._outlet(1, [self.currentBuffer, section] + a)
            #self._outlet(1, ['_cur', section] + a)
        else:
            self._outlet(1, [self.currentBuffer] + list(args))
            #self._outlet(1, ['_cur'] + list(args))

    def sendCommand(self, *l):
        self._outlet(2, l)

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
                    self.sendCommand('setled', dstRow, dstCol, red, green)

    def syncCurrentBuffer(self):
        self.syncBuffer(self.currentBuffer)

    def select_1(self, bufferName):
        bufferName = str(bufferName)
        self.currentBuffer = bufferName
        for section in self.sections:
            if bufferName not in self.buffer[section]:
                self.buffer[section][bufferName] = self.emptyBuffer()
        self.syncCurrentBuffer()

    def clear_1(self, bufferName):
        self.clearb_1(bufferName)
        self.syncCurrentBuffer()

    def clearb_1(self, bufferName):
        bufferName = str(bufferName)
        if bufferName == '_cur': bufferName = self.currentBuffer
        for section in self.sections:
            keys = list(self.buffer[section][bufferName]['data'].keys())
            for key in keys:
                del self.buffer[section][bufferName]['data'][key]

    def set_1(self, bufferName, sectionName, row, col, r, g):
        self.setb_1(bufferName, sectionName, row, col, r, g)
        self.syncCurrentBuffer()

    def setb_1(self, bufferName, sectionName, row, col, r, g):
        bufferName = str(bufferName)
        sectionName = str(sectionName)
        if bufferName == '_cur': bufferName = self.currentBuffer
        if r == 0 and g == 0 and (row, col) in self.buffer[sectionName][bufferName]['data']:
            del self.buffer[sectionName][bufferName]['data'][row, col]
        else:
            self.buffer[sectionName][bufferName]['data'][row, col] = [r, g]

    def sync_1(self, bufferName):
        self.syncCurrentBuffer()

    def scroll_1(self, bufferName, sectionName, row, col):
        bufferName = str(bufferName)
        sectionName = str(sectionName)
        if bufferName == '_cur': bufferName = self.currentBuffer
        row = int(row)
        col = int(col)
        self.buffer[sectionName][bufferName]['rowOffset'] = row
        self.buffer[sectionName][bufferName]['colOffset'] = col
        self.syncCurrentBuffer()

