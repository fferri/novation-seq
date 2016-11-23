from PatternController import *

class PatternAddNoteController(PatternController):
    def __init__(self, parent, patternRow, note):
        self.parent = parent
        self.io = parent.io
        self.trackIndex = parent.trackIndex
        self.track = self.io.song.tracks[self.trackIndex]
        self.patternIndex = parent.patternIndex
        self.pattern = self.track.patterns[self.patternIndex]
        self.patternRow = patternRow
        self.note = note
        self.length = 1
        self.pattern.addObserver(self)

    def __str__(self):
        return '{}(parent={}, trackIndex={}, patternIndex={}, patternRow={}, note={})'.format(self.__class__.__name__, self.parent, self.trackIndex, self.patternIndex, self.patternRow, self.note)

    def update(self, sync=True):
        self.parent.update(sync=False)
        for c in range(self.length):
            self.io.launchpad.set('default', 'center', self.note, self.patternRow + c, 3, 0)
        if sync:
            self.io.launchpad.syncBuffer('default')

    def onLPButtonPress(self, buf, section, row, col):
        super(PatternAddNoteController, self).onLPButtonPress(buf, section, row, col)
        buf = str(buf)
        section = str(section)
        if buf != 'default':
            return
        if section == 'center':
            if row == self.note and col > self.patternRow:
                length = 1 + col - self.patternRow
                if not self.pattern.noteIsPlayingInRange(self.patternRow, self.patternRow + length - 1, self.note):
                    self.length = length
                    self.update()
                return

    def onLPButtonRelease(self, buf, section, row, col):
        super(PatternAddNoteController, self).onLPButtonRelease(buf, section, row, col)
        buf = str(buf)
        section = str(section)
        if buf != 'default':
            return
        if section == 'center':
            if row == self.note and col == self.patternRow:
                self.pattern.noteAdd(self.patternRow, self.note, self.length)
                self.io.setLPController(self.parent)
                return
            if row == self.note and col > self.patternRow:
                self.length = 1
                self.update()
                return

