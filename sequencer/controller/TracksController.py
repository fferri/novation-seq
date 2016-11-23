from LKController import *

class TracksController(LKController):
    def __init__(self, io):
        self.io = io
        for track in self.io.song.tracks:
            track.addObserver(self)

    def onTrackStatusChange(self, trackIndex, volume, muted, isActive):
        self.update()

    def update(self):
        activeTrack = self.io.song.activeTrack
        for trackIndex, track in enumerate(self.io.song.tracks):
            m = 3 * int(track.muted)
            a = 2 * int(activeTrack == track)
            self.io.launchkey.setLed(0, trackIndex, a, a)
            self.io.launchkey.setLed(1, trackIndex, m, 1 - m)

    def onPadPress(self, row, col, velocity):
        if row == 0 and col < 8:
            self.io.song.tracks[col].activate()
        elif row == 1 and col < 8:
            self.io.song.tracks[col].toggleMute()

    def onControlChange(self, num, value):
        self.io.song.tracks[num].setVolume(value)

