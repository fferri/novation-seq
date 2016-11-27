from Track import *
import weakref

class Song(object):
    def __init__(self, numTracks=8, defaultRowDuration=16):
        self.tracks = [Track(self, trackIndex) for trackIndex in range(numTracks)]
        self.activeTrack = self.tracks[0]
        self.rowDuration = defaultdict(lambda: defaultRowDuration)
        self.currentRow = 0
        self.currentTick = 0
        self.currentRowPrev = -1
        self.length = 1
        self.data = defaultdict(lambda: defaultdict(lambda: set()))
        self.observers = weakref.WeakKeyDictionary()
        self.maxPatternPolyphony = 8

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
        flatSet = [-1] * self.maxPatternPolyphony
        for i, el in enumerate(self.data[row][col]):
            flatSet[i] = el
        return flatSet

    def contains(self, row, col, item):
        return item in self.data[row][col]

    def isEmpty(self, row, col):
        return len(self.data[row][col]) == 0

    def set(self, row, col, items, notify=True):
        items = set(list(set(item for item in items if item != -1))[:self.maxPatternPolyphony])
        if items != self.data[row][col]:
            self.data[row][col] = set(items)
            if notify: self.notifySongChange()

    def add(self, row, col, item, notify=True):
        if len(self.data[row][col]) < self.maxPatternPolyphony and item not in self.data[row][col]:
            self.data[row][col].add(item)
            if notify: self.notifySongChange()

    def remove(self, row, col, item, notify=True):
        if item in self.data[row][col]:
            self.data[row][col].remove(item)
            if notify: self.notifySongChange()

    def toggle(self, row, col, item, notify=True):
        if item in self.data[row][col]:
            self.remove(row, col, item, notify)
        else:
            self.add(row, col, item, notify)

    def getRow(self, row):
        ret = []
        for trackIndex, track in enumerate(self.tracks):
            ret.extend(self.get(row, trackIndex))
        return ret

    def setRow(self, row, values, notify=True):
        l = len(self.tracks) * self.maxPatternPolyphony
        if len(values) != l:
            raise ValueError('values must have %d elements' % l)
        for trackIndex, track in enumerate(self.tracks):
            start = trackIndex * self.maxPatternPolyphony
            end = (trackIndex + 1) * self.maxPatternPolyphony
            self.set(row, trackIndex, values[start:end], notify=False)
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
        self.currentRowPrev = -1
        self.currentTick = 0
        for track in self.tracks:
            track.resetTick()

    def getRowModulo(self, row):
        from fractions import gcd
        # get patterns playing in every track:
        pats = []
        for trackIndex, track in enumerate(self.tracks):
            for patternIndex in self.get(row, trackIndex):
                pats.append(track.patterns[patternIndex])
        return reduce(gcd, [1] + [pat.getLength() for pat in pats])

    def tick(self):
        output = {}
        for trackIndex, track in enumerate(self.tracks):
            if self.currentRowPrev != self.currentRow:
                track.resetTick(self.currentRowPrev)
                if self.currentRow >= self.getLength():
                    self.currentRow = 0
                self.notifyCurrentRowChange()
            self.currentRowPrev = self.currentRow
            r = track.tick(self.currentRow)
            if not track.muted:
                output[trackIndex] = r
                track.activeNotes.track(r)
            self.currentTick += 1
            if self.currentTick >= self.rowDuration[self.currentRow]:
                self.currentTick = 0
                self.currentRow += 1
        ret = (self.currentRow, self.currentTick, output)
        return ret

    def resetTick(self):
        self.currentRow = 0
        self.currentTick = 0
        self.currentRowPrev = -1
        for track in self.tracks:
            track.resetTick()

    def dump(self):
        d = []
        for trackIndex, track in enumerate(self.tracks):
            for patternIndex, pattern in enumerate(track.patterns):
                d.append(pattern.dump())
        return '\n'.join(d)

