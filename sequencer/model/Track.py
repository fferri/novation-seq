from Pattern import *
from PlayHead import *
import weakref

class Track(object):
    def __init__(self, song, trackIndex):
        self.song = song
        self.trackIndex = trackIndex
        self.patterns = [Pattern(self, patternIndex) for patternIndex in range(64)]
        self.playHead = PlayHead()
        self.playHeadPrev = PlayHead()
        self.observers = weakref.WeakKeyDictionary()
        self.volume = 100
        self.muted = False
        self.lastSelectedPatternIndex = 0

    def addObserver(self, callable_):
        self.observers[callable_] = 1

    def removeObserver(self, callable_):
        if callable_ in self.observers: del self.observers[callable_]

    def notifyPlayHeadChange(self):
        if self.playHead.patternIndex != self.playHeadPrev.patternIndex or self.playHead.patternRow != self.playHeadPrev.patternRow:
            observers = list(self.observers.keys())
            for observer in observers:
                observer.onPlayHeadChange(self.playHeadPrev, self.playHead)

    def notifyTrackStatusChange(self):
        observers = list(self.observers.keys())
        for observer in observers:
            observer.onTrackStatusChange(self.trackIndex, self.volume, self.muted, self.isActive())

    def setVolume(self, volume):
        volume = max(0, min(127, int(volume)))
        if self.volume != volume:
            self.volume = volume
            self.notifyTrackStatusChange()

    def setMute(self, mute):
        mute = bool(mute)
        if mute != self.muted:
            self.muted = bool(mute)
            self.notifyTrackStatusChange()

    def toggleMute(self):
        self.muted = not self.muted
        self.notifyTrackStatusChange()

    def isActive(self):
        return self.song.activeTrack == self

    def activate(self):
        if self.song.activeTrack != self:
            prevActiveTrack = self.song.activeTrack
            self.song.activeTrack = self
            prevActiveTrack.notifyTrackStatusChange()
            self.notifyTrackStatusChange()

