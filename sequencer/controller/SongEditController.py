from LPController import *
from PatternSelectController import *
from NumberSelectController import *

class SongEditController(LPController):
    def __init__(self, parent):
        self.parent = parent
        self.io = self.parent.io
        self.io.song.addObserver(self)
        self.vscroll = 0

    def __str__(self):
        return '{}(parent={})'.format(self.__class__.__name__, self.parent)

    def onCurrentRowChange(self, row):
        self.update()

    def onSongChange(self):
        self.update()

    def update(self, sync=True):
        self.sendCommand(['clearb', 'default'])

        for row in range(self.io.song.getLength()):
            curRow = row == self.io.song.currentRow
            for trackIndex, track in enumerate(self.io.song.tracks):
                v = self.io.song.get(row, trackIndex)
                c = [0, 0] if v == -1 else [2, 2] if curRow else [0, 3]
                self.sendCommand(['setb', 'default', 'center', row, trackIndex] + c)
            self.sendCommand(['setb', 'default', 'right', row, 8, 3 * int(curRow), 1])
        self.sendCommand(['setb', 'default', 'top', 8, 4, 2, 2])
        if sync:
            self.sendCommand(['sync', 'default'])

    def onLPButtonPress(self, buf, section, row, col):
        super(SongEditController, self).onLPButtonPress(buf, section, row, col)
        buf = str(buf)
        section = str(section)
        if buf != 'default':
            return
        if section == 'center':
            self.editingRow = row
            self.editingTrack = col
            v = self.io.song.get(row, col)
            cb = lambda trkIdx, patIdx: self.io.song.set(self.editingRow, trkIdx, patIdx)
            self.io.setLPController(PatternSelectController(self, self.editingTrack, cb, v, True, listenToTrackStatusChange=False))
        elif section == 'top' and row == 8:
            if col in range(2):
                self.vscroll += int(col == 1) - int(col == 0)
                self.sendCommand(['scroll', 'default', 'center', vscroll, 0])
                self.sendCommand(['scroll', 'default', 'right', vscroll, 0])
                return
            if col == 4:
                self.io.setLPController(self.parent)
                return
        elif section == 'right': # and col == 8:
            cb = lambda n: self.io.song.setRowDuration(row, n)
            self.io.setLPController(NumberSelectController(self, cb, self.io.song.getRowDuration(row), 1, 64))
            return


