from LPController import *

class SongPatternsSelectController(LPController):
    def __init__(self, parent, songRow):
        self.parent = parent
        self.io = self.parent.io
        self.songRow = songRow
        self.track = self.io.song.activeTrack
        self.trackIndex = self.track.trackIndex
        self.io.song.addObserver(self)
        for track in self.io.song.tracks:
            track.addObserver(self)
        for pattern in self.track.patterns:
            pattern.addObserver(self)

    def __str__(self):
        return '{}(parent={}, songRow={})'.format(self.__class__.__name__, self.parent, self.songRow)

    def selectTrack(self, trackIndex):
        self.trackIndex = trackIndex
        self.track = self.io.song.tracks[self.trackIndex]
        self.update()

    def onSongChange(self):
        self.update()

    def onPatternChange(self, trackIndex, patternIndex):
        if trackIndex == self.trackIndex:
            self.update()

    def onTrackStatusChange(self, trackIndex, volume, muted, active):
        if active:
            self.selectTrack(trackIndex)

    def update(self, sync=True):
        self.io.launchpad.clearBuffer('default')
        self.io.launchpad.set('default', 'right', 7, 8, 0, 1)
        for patternIndex in range(64):
            row, col = patternIndex / 8, patternIndex % 8
            pattern = self.track.patterns[patternIndex]
            empty = pattern.isEmpty()
            selected = self.io.song.contains(self.songRow, self.trackIndex, patternIndex)
            color = [2, 0] if selected else [0, 1] if empty else [2, 3]
            self.io.launchpad.set('default', 'center', row, col, *color)
        if sync:
            self.io.launchpad.syncBuffer('default')

    def onLPButtonPress(self, buf, section, row, col):
        super(SongPatternsSelectController, self).onLPButtonPress(buf, section, row, col)
        buf = str(buf)
        section = str(section)
        if buf != 'default':
            return
        if section == 'center':
            patternIndex = row * 8 + col
            self.io.song.toggle(self.songRow, self.trackIndex, patternIndex)
            pass
        elif section == 'right' and col == 8 and row ==7:
            self.io.setLPController(self.parent)
            return

