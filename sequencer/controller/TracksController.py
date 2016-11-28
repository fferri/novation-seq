from LKController import *

class TracksController(LKController):
    def __init__(self, io):
        self.io = io
        for track in self.io.song.tracks:
            track.addObserver(self)
        self.io.transport.addObserver(self)

    def onTrackStatusChange(self, trackIndex, volume, muted, isActive):
        self.update()

    def onPlaybackStatusChange(self, playing):
        self.updatePlaybackStatus()

    def updatePlaybackStatus(self):
        self.io.launchkey.setLed(1, 8, *([3, 0] if self.io.transport.isPlaying() else [0, 1]))

    def update(self):
        activeTrack = self.io.song.activeTrack
        for trackIndex, track in enumerate(self.io.song.tracks):
            m = 3 * int(track.muted)
            a = 2 * int(activeTrack == track)
            self.io.launchkey.setLed(0, trackIndex, a, a)
            self.io.launchkey.setLed(1, trackIndex, m, 1 - m)
        self.updatePlaybackStatus()

    def onPadPress(self, row, col, velocity):
        if row == 0 and col < 8:
            self.io.song.tracks[col].activate()
        elif row == 1 and col < 8:
            self.io.song.tracks[col].toggleMute()
        elif row == 1 and col == 8:
            if self.io.transport.isPlaying(): self.io.transport.stop()
            else: self.io.transport.start()
            self.update()

    def onControlChange(self, num, value):
        self.io.song.tracks[num].setVolume(value)

