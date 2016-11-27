from LPController import *
from SongPatternsSelectController import *
from NumberSelectController import *

class SongEditController(LPController):
    def __init__(self, parent):
        self.parent = parent
        self.io = self.parent.io
        self.io.song.addObserver(self)
        self.vscroll = 0

    def __str__(self):
        return '{}(parent={})'.format(self.__class__.__name__, self.parent)

    def setVScroll(self, rowOffset):
        l = self.io.song.getLength()
        self.vscroll = max(0, min(max(0, l - 8), rowOffset))

    def incrVScroll(self, deltaRowOffset):
        self.setVScroll(self.vscroll + deltaRowOffset)

    def rowDown(self):
        self.incrVScroll(1)

    def rowUp(self):
        self.incrVScroll(-1)

    def onCurrentRowChange(self, row):
        if self.io.isActiveController(self):
            self.update()

    def onSongChange(self):
        if self.io.isActiveController(self):
            self.update()

    def update(self, sync=True):
        self.io.launchpad.clearBuffer('default')
        self.io.launchpad.scroll('default', 'center', self.vscroll, 0)
        self.io.launchpad.scroll('default', 'right', self.vscroll, 0)

        for row in range(self.io.song.getLength()):
            curRow = row == self.io.song.currentRow
            for trackIndex, track in enumerate(self.io.song.tracks):
                empty = self.io.song.isEmpty(row, trackIndex)
                c = [0, 0] if empty else [2, 2] if curRow else [0, 3]
                self.io.launchpad.set('default', 'center', row, trackIndex, *c)
            self.io.launchpad.set('default', 'right', row, 8, 3 * int(curRow), 1)
        self.io.launchpad.set('default', 'top', 8, 4, 2, 2)
        self.io.launchpad.set('default', 'top', 8, 0, 0, 1)
        self.io.launchpad.set('default', 'top', 8, 1, 0, 1)
        if sync:
            self.io.launchpad.syncBuffer('default')

    def onLPButtonPress(self, buf, section, row, col):
        super(SongEditController, self).onLPButtonPress(buf, section, row, col)
        buf = str(buf)
        section = str(section)
        if buf != 'default':
            return
        if section == 'center':
            self.io.song.tracks[col].activate()
            self.io.setLPController(SongPatternsSelectController(self, row))
        elif section == 'top' and row == 8:
            if col in range(2):
                if col == 0: self.rowUp()
                if col == 1: self.rowDown()
                self.io.launchpad.scroll('default', 'center', self.vscroll, 0)
                self.io.launchpad.scroll('default', 'right', self.vscroll, 0)
                self.io.launchpad.syncBuffer('default')
                return
            if col == 4:
                self.io.setLPController(self.parent)
                return
        elif section == 'right': # and col == 8:
            if row < self.io.song.getLength():
                cb = lambda n: self.io.song.setRowDuration(row, n)
                self.io.setLPController(NumberSelectController(self, cb, self.io.song.getRowDuration(row), 1, 64))
            return


