from PatternController import *
from PatternAddNoteController import *
from PatternEditNoteController import *
from SongEditController import *
from PatternSelectController import *
from PatternFunctionsController import *

class PatternEditController(PatternController):
    def __init__(self, io, trackIndex, patternIndex):
        self.io = io
        self.trackIndex = trackIndex
        self.track = self.io.song.tracks[self.trackIndex]
        self.patternIndex = patternIndex
        self.pattern = self.track.patterns[self.patternIndex]
        self.scroll = [0, 0]
        self.renderNoteOffs = False
        self.track.addObserver(self)
        self.pattern.addObserver(self)

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
            self.scroll = [0, 0]
        self.pattern.removeObserver(self)
        self.patternIndex = patternIndex
        self.pattern = self.track.patterns[self.patternIndex]
        self.pattern.addObserver(self)
        self.track.lastSelectedPatternIndex = self.patternIndex
        if update:
            self.update()

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

        if self.track.playHead.patternIndex == self.patternIndex:
            for row in range(128):
                self.io.launchpad.set('default', 'center', row, self.track.playHead.patternRow, 1, 0)

        for note, intervals in self.pattern.noteGetIntervals().items():
            for (rowStart, rowStop) in intervals:
                self.io.launchpad.set('default', 'center', note, rowStart, 2, 3)
                for row in range(rowStart + 1, rowStop):
                    self.io.launchpad.set('default', 'center', note, row, 0, 1)
                if self.renderNoteOffs:
                    self.io.launchpad.set('default', 'center', note, rowStop, 1, 0)

        if sync:
            self.io.launchpad.syncBuffer('default')

    def onLPButtonPress(self, buf, section, row, col):
        super(PatternEditController, self).onLPButtonPress(buf, section, row, col)
        buf = str(buf)
        section = str(section)
        if buf != 'default':
            return
        if section == 'center':
            patternRow = col
            note = row
            if self.pattern.noteGetLength(patternRow, note) is not None:
                self.io.setLPController(PatternEditNoteController(self, patternRow, note))
            elif not self.pattern.noteIsPlayingAt(patternRow, note):
                self.io.setLPController(PatternAddNoteController(self, patternRow, note))
        elif section == 'top' and row == 8:
            if col in range(4):
                self.scroll[0] += int(col == 1) - int(col == 0)
                self.scroll[1] += int(col == 3) - int(col == 2)
                self.scroll[0] = max(0, min(127, self.scroll[0]))
                self.scroll[1] = max(0, min(max(0, self.pattern.getLength() - 8), self.scroll[1]))
                self.io.launchpad.scroll('default', 'center', *self.scroll)
                self.io.launchpad.syncBuffer('default')
                return
            if col == 4:
                self.io.setLPController(SongEditController(self))
                return
            if col == 5:
                cb = lambda trkIdx, patIdx: self.selectPattern(trkIdx, patIdx, True)
                v = self.track.lastSelectedPatternIndex
                self.io.setLPController(PatternSelectController(self, self.trackIndex, cb, v, False))
                return
            if col == 7:
                self.io.setLPController(PatternFunctionsController(self))
                return

