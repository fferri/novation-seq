from LPController import *

class PatternSelectController(LPController):
    def __init__(self, parent, trackIndex, callback, currentPatternIndex, allowNullSelection, listenToTrackStatusChange=True):
        self.parent = parent
        self.io = self.parent.io
        self.trackIndex = trackIndex
        self.track = self.io.song.tracks[self.trackIndex]
        self.callback = callback
        self.currentPatternIndex = currentPatternIndex
        self.allowNullSelection = allowNullSelection
        if listenToTrackStatusChange:
            for track in self.io.song.tracks:
                track.addObserver(self)
        for pattern in self.track.patterns:
            pattern.addObserver(self)

    def __str__(self):
        return '{}(parent={})'.format(self.__class__.__name__, self.parent)

    def selectTrack(self, trackIndex):
        self.trackIndex = trackIndex
        self.track = self.io.song.tracks[self.trackIndex]
        self.update()

    def onPatternChange(self, trackIndex, patternIndex):
        if trackIndex == self.trackIndex:
            self.update()

    def onTrackStatusChange(self, trackIndex, volume, muted, active):
        if active:
            self.selectTrack(trackIndex)

    def update(self, sync=True):
        self.io.launchpad.clearBuffer('default')
        self.io.launchpad.scroll('default', 'center', 0, 0)
        self.io.launchpad.scroll('default', 'right', 0, 0)
        for patternIndex in range(64):
            row, col = patternIndex / 8, patternIndex % 8
            pattern = self.track.patterns[patternIndex]
            empty = pattern.isEmpty()
            #cur = patternIndex == self.track.lastSelectedPatternIndex
            cur = patternIndex == self.currentPatternIndex
            color = [2, 0] if cur else [0, 1] if empty else [2, 3]
            self.io.launchpad.set('default', 'center', row, col, *color)
        if self.allowNullSelection:
            self.io.launchpad.set('default', 'right', 7, 8, 3, 0)
        if sync:
            self.io.launchpad.syncBuffer('default')

    def onLPButtonPress(self, buf, section, row, col):
        super(PatternSelectController, self).onLPButtonPress(buf, section, row, col)
        buf = str(buf)
        section = str(section)
        if buf != 'default':
            return
        if section == 'center':
            patternIndex = row * 8 + col
            #self.parent.selectPattern(self.trackIndex, patternIndex, update=False)
            self.callback(self.trackIndex, patternIndex)
            self.io.setLPController(self.parent)
            pass
        elif section == 'top' and row == 8:
            if col == 5:
                self.io.setLPController(self.parent)
                return
        elif section == 'right' and col == 8:
            if row == 7 and self.allowNullSelection:
                self.callback(self.trackIndex, -1)
                self.io.setLPController(self.parent)

