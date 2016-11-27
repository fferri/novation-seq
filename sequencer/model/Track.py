from Pattern import *
from sequencer.util import ActiveNotesTracker, TrackOutputMerger
from collections import defaultdict
import weakref

class Track(object):
    def __init__(self, song, trackIndex):
        self.song = song
        self.trackIndex = trackIndex
        self.patterns = [Pattern(self, patternIndex) for patternIndex in range(64)]
        self.noteCols = list(range(8)) # default: 8-note polyphony, using the first 8 columns
        self.observers = weakref.WeakKeyDictionary()
        self.volume = 100
        self.muted = False
        self.lastSelectedPatternIndex = 0
        self.activeNotes = ActiveNotesTracker()
        self.liveNotes = defaultdict(bool)
        self.outputMerger = TrackOutputMerger(self)
        self.playingPatterns = []

    def addObserver(self, callable_):
        self.observers[callable_] = 1

    def removeObserver(self, callable_):
        if callable_ in self.observers: del self.observers[callable_]

    def notifyTrackStatusChange(self):
        observers = list(self.observers.keys())
        for observer in observers:
            observer.onTrackStatusChange(self.trackIndex, self.volume, self.muted, self.isActive())

    def setPlayingPatterns(self, patterns):
        self.playingPatterns = [p for p in patterns if p != -1]

    def tick(self, songRow):
        trackOutput = {}
        playHeadChanged = {}
        for patternIndex in self.playingPatterns:
            pattern = self.patterns[patternIndex]
            ret1, playHeadChanged[patternIndex] = pattern.tick()
            if ret1 is not None:
                trackOutput[patternIndex] = ret1
        ret = self.outputMerger.merge(songRow, self.playingPatterns, trackOutput)
        self.activeNotes.track(ret)
        for patternIndex, changed in playHeadChanged.items():
            if changed:
                self.patterns[patternIndex].notifyPlayHeadChange()
        return ret

    def resetTick(self, songRow=None):
        if songRow is None:
            for pattern in self.patterns:
                pattern.resetTick()
        else:
            for patternIndex in self.song.get(songRow, self.trackIndex):
                if patternIndex != -1:
                    pattern = self.patterns[patternIndex]
                    pattern.resetTick()

    def getNoteColumns(self):
        return self.noteCols[:]

    def setNoteColumns(self, noteCols):
        self.noteCols = noteCols[:]
        # TODO: self.notifyTrackChange()

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

