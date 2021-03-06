from PatternController import *

class PatternEditNoteController(PatternController):
    def __init__(self, parent, patternRow, note):
        self.parent = parent
        self.io = parent.io
        self.trackIndex = parent.trackIndex
        self.track = self.io.song.tracks[self.trackIndex]
        self.patternIndex = parent.patternIndex
        self.pattern = self.track.patterns[self.patternIndex]
        self.patternRow = patternRow
        self.note = note
        self.deleteOnRelease = True
        self.originalLength = self.pattern.noteGetLength(self.patternRow, self.note)
        self.length = self.originalLength
        self.pattern.addObserver(self)

    def __str__(self):
        return '{}(parent={}, trackIndex={}, patternIndex={}, patternRow={}, note={})'.format(self.__class__.__name__, self.parent, self.trackIndex, self.patternIndex, self.patternRow, self.note)

    def update(self, sync=True):
        self.parent.update(sync=False)
        for c in range(self.length):
            for row in self.parent.note2rows(self.note):
                col = self.patternRow + c
                self.io.launchpad.set('default', 'center', row, col, 3, 0)
        if sync:
            self.io.launchpad.syncBuffer('default')

    def onLPButtonPress(self, buf, section, row, col):
        super(PatternEditNoteController, self).onLPButtonPress(buf, section, row, col)
        buf = str(buf)
        section = str(section)
        if buf != 'default':
            return
        if section == 'center':
            note = self.parent.row2note(row)
            if note == self.note and col > self.patternRow:
                self.deleteOnRelease = False
                length = 1 + col - self.patternRow
                if not self.pattern.noteIsPlayingInRange(self.patternRow + self.originalLength, self.patternRow + length - 1, self.note):
                    self.length = length
                    self.update()
                return

    def onLPButtonRelease(self, buf, section, row, col):
        super(PatternEditNoteController, self).onLPButtonRelease(buf, section, row, col)
        buf = str(buf)
        section = str(section)
        if buf != 'default':
            return
        if section == 'center':
            note = self.parent.row2note(row)
            if note == self.note and col == self.patternRow:
                if self.deleteOnRelease:
                    self.pattern.noteDelete(self.patternRow, self.note)
                else:
                    self.pattern.noteDelete(self.patternRow, self.note)
                    self.pattern.noteAdd(self.patternRow, self.note, self.length)
                self.io.setLPController(self.parent)
                return
            if note == self.note and col > self.patternRow:
                self.length = 1
                self.deleteOnRelease = False
                self.update()
                return

