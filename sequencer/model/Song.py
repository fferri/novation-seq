from Track import *
import weakref

class Song(object):
    def __init__(self, numTracks=8, defaultRowDuration=16):
        self.tracks = [Track(self, trackIndex) for trackIndex in range(numTracks)]
        self.activeTrack = self.tracks[0]
        self.rowDuration = defaultdict(lambda: defaultRowDuration)
        self.currentRow = 0
        self.currentTick = 0
        self.lastOutputRow = None
        self.playHeads = {}
        self.playHeadsPrev = {}
        self.length = 1
        self.data = defaultdict(lambda: defaultdict(lambda: -1))
        self.observers = weakref.WeakKeyDictionary()

    def addObserver(self, callable_):
        self.observers[callable_] = 1

    def removeObserver(self, callable_):
        if callable_ in self.observers: del self.observers[callable_]

    def notifySongChange(self):
        observers = list(self.observers.keys())
        for observer in observers:
            observer.onSongChange()

    def notifyCurrentRowChange(self):
        observers = list(self.observers.keys())
        for observer in observers:
            observer.onCurrentRowChange(self.currentRow)

    def get(self, row, col):
        return self.data[row][col]

    def set(self, row, col, value, notify=True):
        if value == -1:
            del self.data[row][col]
        else:
            self.data[row][col] = value
        if notify: self.notifySongChange()

    def getRow(self, row):
        ncols = max(self.data[row]) if len(self.data[row]) else 0
        return [self.get(row, col) for col in range(1 + ncols)]

    def setRow(self, row, values, notify=True):
        for col, value in enumerate(values):
            self.set(row, col, value, notify=False)
        if notify: self.notifySongChange()

    def clear(self, notify=True):
        rows = tuple(self.data.keys())
        for row in rows:
            del self.data[row]
        if notify: self.notifySongChange()

    def getLength(self):
        return self.length

    def setLength(self, length, notify=True):
        self.length = length
        if notify: self.notifySongChange()

    def getRowDuration(self, row):
        return self.rowDuration[row]

    def setRowDuration(self, row, duration):
        self.rowDuration[row] = duration

    def rewind(self):
        self.currentRow = 0
        self.currentTick = 0
        for track in self.tracks:
            track.playHeadPrev.copyFrom(track.playHead)
            track.playHead.reset()
            track.notifyPlayHeadChange()

    def getRowModulo(self, row):
        from fractions import gcd
        pl = [1] + [t.patterns[pi].getLength() for t, pi in zip(self.tracks, self.getRow(row))]
        return reduce(gcd,pl)

    def incrTick(self):
        self.currentTick += 1
        if self.currentTick >= self.rowDuration[self.currentRow]:
            self.currentTick = 0
            self.currentRow += 1
            if self.currentRow >= self.getLength():
                self.currentRow = 0

    def tick(self):
        output = {}
        for trackIndex, track in enumerate(self.tracks):
            track.playHeadPrev.copyFrom(track.playHead)
            track.playHead.patternIndex = self.get(self.currentRow, trackIndex)
            if track.playHead.patternIndex != -1:
                pattern = track.patterns[track.playHead.patternIndex]
                t = int(self.currentTick / pattern.getSpeedReduction())
                track.playHead.patternRow = t % pattern.getLength()
                if track.playHead.patternRow != track.playHeadPrev.patternRow:
                    output[trackIndex] = pattern.getRow(track.playHead.patternRow)
                    if track.muted:
                        output[trackIndex] = [-1 for _ in output[trackIndex]]
            track.notifyPlayHeadChange()
        if self.lastOutputRow != self.currentRow:
            self.notifyCurrentRowChange()
        ret = (self.currentRow, self.currentTick, output)
        self.lastOutputRow = self.currentRow
        self.incrTick()
        return ret

    def dump(self):
        d = []
        for trackIndex, track in enumerate(self.tracks):
            for patternIndex, pattern in enumerate(track.patterns):
                d.append(pattern.dump())
        return '\n'.join(d)

