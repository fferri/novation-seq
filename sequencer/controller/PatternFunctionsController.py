from PatternController import *
from NumberSelectController import *

class PatternFunctionsController(PatternController):
    def __init__(self, parent):
        self.parent = parent
        self.io = parent.io
        self.trackIndex = parent.trackIndex
        self.track = self.io.song.tracks[self.trackIndex]
        self.patternIndex = parent.patternIndex
        self.pattern = self.track.patterns[self.patternIndex]
        self.pattern.addObserver(self)

    def __str__(self):
        return '{}(parent={})'.format(self.__class__.__name__, self.parent)

    def update(self, sync=True):
        self.parent.update(sync=False)
        self.io.launchpad.set('default', 'top', 8, 7, 2, 2)
        self.io.launchpad.set('default', 'right', 0, 8, 0, 3)
        self.io.launchpad.set('default', 'right', 1, 8, 0, 3)
        if sync:
            self.io.launchpad.syncBuffer('default')

    def onLPButtonPress(self, buf, section, row, col):
        super(PatternFunctionsController, self).onLPButtonPress(buf, section, row, col)

    def onLPButtonRelease(self, buf, section, row, col):
        super(PatternFunctionsController, self).onLPButtonRelease(buf, section, row, col)
        buf = str(buf)
        section = str(section)
        if buf != 'default':
            return
        if section == 'top' and row == 8:
            if col == 7:
                self.io.setLPController(self.parent)
                return
        if section == 'right' and col == 8:
            if row == 0: # set pattern length
                cb = lambda n: self.pattern.setLength(n)
                self.io.setLPController(NumberSelectController(self, cb, self.pattern.getLength(), 1, 64))
                return
            elif row == 1: # set pattern speed reduction
                cb = lambda n: self.pattern.setSpeedReduction(n)
                self.io.setLPController(NumberSelectController(self, cb, self.pattern.getSpeedReduction(), 1, 32))
                return

