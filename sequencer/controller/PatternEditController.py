from PatternController import *
from PatternAddNoteController import *
from PatternEditNoteController import *
from SongEditController import *
from PatternSelectController import *
from NumberSelectController import *
from sequencer.util import NoteMapping, scales
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
        self.trackScale = defaultdict(int)
        self.scales = [NoteMapping()]
        self.scaleColor = [[1,0]]
        for root in range(12):
            for scale, color in (('major', [1,1]), ('minor', [0,1])):
                self.scales.append(NoteMapping(enumerate(getattr(scales, scale)(root))))
                self.scaleColor.append(color)
        self.scales.append(NoteMapping(enumerate(scales.drum8())))
        self.scaleColor.append([3, 1])

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

    def setScale(self, i):
        # try to maintain scroll (i.e. see the same note) after changing scale:
        # (if the scale is very nonlinear this isn't going to work very well)
        getVisibleNotes = lambda row0: [self.row2note(row0 + r) for r in range(8)]
        visibleNotes = getVisibleNotes(self.scroll[self.trackIndex][0])
        # change scale
        self.trackScale[self.trackIndex] = i
        # look up note row in new scale:
        for j in (0, -1, 1, -2, 2, -3, 3, -4, 4, -5, 5, -6, 6, -7, 7):
            rows = self.note2rows(visibleNotes[0])
            if len(rows) == 1:
                self.setVScroll(rows[0])
                break
            elif len(rows) > 1:
                # if multiple rows contain the first note, pick the row which shows
                # the maximum number of notes visible with the previous scale:
                vn0 = set(visibleNotes)
                scoredRows = map(lambda r: (len(vn0 & set(getVisibleNotes(r))), r), rows)
                bestRow, bestScore = max(scoredRows)
                self.setVScroll(bestRow)
                break
        self.update()

    def getScaleColor(self, i):
        return self.scaleColor[i]

    def row2note(self, row):
        mapping = self.scales[self.trackScale[self.trackIndex]]
        note = mapping.getMidiNote(row)
        return note

    def note2rows(self, note):
        mapping = self.scales[self.trackScale[self.trackIndex]]
        rows = mapping.getGridRows(note)
        return rows

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
            for row in self.note2rows(note):
                self.io.launchpad.set('default', 'right', row, 8, 1, 0)

        # draw notes
        for note, intervals in self.pattern.noteGetIntervals().items():
            for (patternRowStart, patternRowStop) in intervals:
                for row in self.note2rows(note):
                    self.io.launchpad.set('default', 'center', row, patternRowStart, 2, 3)
                    for patternRow in range(patternRowStart + 1, patternRowStop):
                        self.io.launchpad.set('default', 'center', row, patternRow, 0, 1)
                    if self.renderNoteOffs:
                        self.io.launchpad.set('default', 'center', row, patternRowStop, 1, 0)

        # turn on buttons with a function
        for col in range(4):
            self.io.launchpad.set('default', 'top', 8, col, 2 * int(self.shift), 1)
        self.io.launchpad.set('default', 'top', 8, 7, 2, 1)
        if self.shift:
            self.io.launchpad.set('default', 'top', 8, 4, 2, 1)
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
            note = self.row2note(row)
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
        if section == 'top' and row == 8 and col == 4 and self.shift:
            self.shift = False # otherwise shift gets stuck
            cb = lambda n: self.setScale(n)
            self.io.setLPController(NumberSelectController(self, cb, self.trackScale[self.trackIndex], 0, len(self.scales) - 1, colorFunc=self.getScaleColor))
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

