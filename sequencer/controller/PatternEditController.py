from PatternController import *
from PatternAddNoteController import *
from PatternEditNoteController import *
from SongEditController import *
from PatternSelectController import *
from NumberSelectController import *
from collections import defaultdict

class PatternEditController(PatternController):
    def __init__(self, io, trackIndex, patternIndex):
        self.io = io
        self.trackIndex = trackIndex
        self.track = self.io.song.tracks[self.trackIndex]
        self.patternIndex = patternIndex
        self.pattern = self.track.patterns[self.patternIndex]
        self.scroll = defaultdict(lambda: [36, 0])
        self.renderNoteOffs = False
        self.track.addObserver(self)
        self.pattern.addObserver(self)
        self.shift = False

    def __str__(self):
        return '{}(trackIndex={}, patternIndex={})'.format(self.__class__.__name__, self.trackIndex, self.patternIndex)

    def selectPattern(self, trackIndex, patternIndex, update=True):
        if self.trackIndex == trackIndex and self.patternIndex == patternIndex:
            return
        if self.trackIndex != trackIndex:
            self.track.removeObserver(self)
            self.trackIndex = self.io.song.activeTrack.trackIndex
            self.track = self.io.song.tracks[self.trackIndex]
            self.track.addObserver(self)
        self.pattern.removeObserver(self)
        self.patternIndex = patternIndex
        self.pattern = self.track.patterns[self.patternIndex]
        self.pattern.addObserver(self)
        self.track.lastSelectedPatternIndex = self.patternIndex
        self.setHScroll(0)
        if update:
            self.update()

    def setVScroll(self, rowOffset):
        self.scroll[self.trackIndex][0] = max(1, min(127, rowOffset))

    def setHScroll(self, colOffset):
        l = self.pattern.getLength()
        self.scroll[self.trackIndex][1] = max(0, min(max(0, l - 8), colOffset))

    def setScroll(self, rowOffset, colOffset):
        self.setVScroll(rowOffset)
        self.setHScroll(colOffset)

    def incrVScroll(self, deltaRowOffset):
        self.setVScroll(self.scroll[self.trackIndex][0] + deltaRowOffset)

    def incrHScroll(self, deltaColOffset):
        self.setHScroll(self.scroll[self.trackIndex][1] + deltaColOffset)

    def incrScroll(self, deltaRowOffset, deltaColOffset):
        self.incrVScroll(deltaRowOffset)
        self.incrHScroll(deltaColOffset)

    def onTrackStatusChange(self, trackIndex, volume, muted, active):
        if active == False:
            newTrack = self.io.song.activeTrack
            u = self.io.lpcontroller == self
            self.selectPattern(newTrack.trackIndex, newTrack.lastSelectedPatternIndex, update=u)

    def onPlayHeadChange(self, old, new):
        if self.patternIndex in (old.patternIndex, new.patternIndex):
            self.io.lpcontroller.update()

    def update(self, sync=True):
        self.io.launchpad.clearBuffer('default')
        self.io.launchpad.invertRows('default','center')
        self.io.launchpad.invertRows('default','right')
        self.io.launchpad.scroll('default','center', *self.scroll[self.trackIndex])
        self.io.launchpad.scroll('default','right', self.scroll[self.trackIndex][0], 0)

        # draw playhead
        if self.track.playHead.patternIndex == self.patternIndex:
            for row in range(128):
                self.io.launchpad.set('default', 'center', row, self.track.playHead.patternRow, 1, 0)

        # draw active notes
        for note in self.track.activeNotes.get():
            self.io.launchpad.set('default', 'right', note, 8, 1, 0)

        # draw notes
        for note, intervals in self.pattern.noteGetIntervals().items():
            for (rowStart, rowStop) in intervals:
                self.io.launchpad.set('default', 'center', note, rowStart, 2, 3)
                for row in range(rowStart + 1, rowStop):
                    self.io.launchpad.set('default', 'center', note, row, 0, 1)
                if self.renderNoteOffs:
                    self.io.launchpad.set('default', 'center', note, rowStop, 1, 0)

        # turn on buttons with a function
        for col in range(4):
            self.io.launchpad.set('default', 'top', 8, col, 2 * int(self.shift), 1)
        self.io.launchpad.set('default', 'top', 8, 7, 2, 1)
        if self.shift:
            self.io.launchpad.set('default', 'top', 8, 5, 2, 1)
            self.io.launchpad.set('default', 'top', 8, 6, 2, 1)
        else:
            self.io.launchpad.set('default', 'top', 8, 4, 0, 1)
            self.io.launchpad.set('default', 'top', 8, 5, 0, 1)

        if sync:
            self.io.launchpad.syncBuffer('default')

    def onLPButtonPress(self, buf, section, row, col):
        super(PatternEditController, self).onLPButtonPress(buf, section, row, col)
        if buf != 'default': return
        if section == 'center':
            patternRow = col
            note = row
            if self.pattern.noteGetLength(patternRow, note) is not None:
                self.io.setLPController(PatternEditNoteController(self, patternRow, note))
            elif not self.pattern.noteIsPlayingAt(patternRow, note):
                self.io.setLPController(PatternAddNoteController(self, patternRow, note))
            return
        if section == 'top' and row == 8 and col in range(4):
            rowStep, colStep = (1, 1) if self.shift else (8, 8)
            self.incrVScroll(rowStep * (int(col == 0) - int(col == 1))) # flipped
            self.incrHScroll(colStep * (int(col == 3) - int(col == 2)))
            self.io.launchpad.scroll('default', 'center', *self.scroll[self.trackIndex])
            self.io.launchpad.syncBuffer('default')
            return
        if section == 'top' and row == 8 and col == 4 and not self.shift:
            self.io.setLPController(SongEditController(self))
            return
        if section == 'top' and row == 8 and col == 5 and not self.shift:
            cb = lambda trkIdx, patIdx: self.selectPattern(trkIdx, patIdx, True)
            v = self.track.lastSelectedPatternIndex
            self.io.setLPController(PatternSelectController(self, self.trackIndex, cb, v, False))
            return
        if section == 'top' and row == 8 and col == 5 and self.shift:
            self.shift = False # otherwise shift gets stuck
            cb = lambda n: self.pattern.setLength(n)
            self.io.setLPController(NumberSelectController(self, cb, self.pattern.getLength(), 1, 64))
            return
        if section == 'top' and row == 8 and col == 6 and self.shift:
            self.shift = False # otherwise shift gets stuck
            cb = lambda n: self.pattern.setSpeedReduction(n)
            self.io.setLPController(NumberSelectController(self, cb, self.pattern.getSpeedReduction(), 1, 32))
            return
        if section == 'top' and row == 8 and col == 7:
            self.shift = True
            self.update()
            return

    def onLPButtonRelease(self, buf, section, row, col):
        if buf != 'default': return
        if section == 'top' and row == 8 and col == 7:
            self.shift = False
            self.update()
            return

