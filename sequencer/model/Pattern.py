from collections import defaultdict
import weakref

class Pattern(object):
    def __init__(self, track, patternIndex, length=16):
        self.track = track
        self.patternIndex = patternIndex
        self.length = length
        self.speedReduction = 4
        self.data = defaultdict(lambda: defaultdict(lambda: -1))
        self.observers = weakref.WeakKeyDictionary()
        self.playHeadRow = -1
        self.playHeadRowPrev = -1
        self.playHeadTick = 0

    def addObserver(self, callable_):
        self.observers[callable_] = 1

    def removeObserver(self, callable_):
        if callable_ in self.observers: del self.observers[callable_]

    def notifyPatternChange(self):
        observers = list(self.observers.keys())
        for observer in observers:
            observer.onPatternChange(self.track.trackIndex, self.patternIndex)

    def notifyPlayHeadChange(self):
        observers = list(self.observers.keys())
        for observer in observers:
            observer.onPlayHeadChange(self.track.trackIndex, self.patternIndex, self.playHeadRow)

    def tick(self):
        if self.playHeadRow == -1: self.playHeadRow = 0
        ret = None
        playHeadChanged = False
        if self.playHeadTick == 0:
            ret = (self.playHeadRow, self.playHeadTick, self.getRow(self.playHeadRow))
            if self.playHeadRowPrev != self.playHeadRow:
                # Track will call Pattern.notifyPlayHeadChange after tracking active notes
                playHeadChanged = True
        self.playHeadRowPrev = self.playHeadRow
        self.playHeadTick += 1
        if self.playHeadTick >= self.speedReduction:
            self.playHeadTick = 0
            self.playHeadRow += 1
            if self.playHeadRow >= self.getLength():
                self.playHeadRow = 0
        return ret, playHeadChanged

    def resetTick(self):
        self.playHeadRow = -1
        self.playHeadRowPrev = -1
        self.playHeadTick = 0

    def noteAdd(self, row, note, duration, velocity=100):
        if note < 1: return
        startRow = int(row)
        endRow = startRow + max(int(duration), 1)
        col = self.noteFreeColumn(startRow, endRow)
        if col is not None:
            for row in range(startRow, endRow):
                self.set(row, col, note if row == startRow else -2, notify=False)
            self.notifyPatternChange()

    def noteGetColumn(self, row, note):
        if note < 1: return
        for noteCol in self.track.noteCols:
            if self.get(row, noteCol) == note:
                return noteCol

    def noteGetLength(self, row, note, col=None):
        if note < 1: return
        if col is None: col = self.noteGetColumn(row, note)
        if col is None: return
        length = 1
        row += 1
        while self.get(row, col) == -2 and row < self.getLength():
            length += 1
            row += 1
        return length

    def noteDelete(self, row, note):
        if note < 1: return
        col = self.noteGetColumn(row, note)
        if col is None: return
        length = self.noteGetLength(row, note, col)
        for row1 in range(row, row + length):
            self.set(row1, col, -1, notify=False)
        self.notifyPatternChange()

    def noteFreeColumn(self, row, endRow):
        for noteCol in self.track.noteCols:
            if all(self.get(row, noteCol) == -1 for row in range(row, endRow)):
                return noteCol

    def noteGetIntervals(self):
        ret = {}
        for col in self.track.noteCols:
            for row in range(self.getLength()):
                v = self.get(row, col)
                if v > 0:
                    ret[v] = ret.get(v, []) + [(row, row + self.noteGetLength(row, v, col))]
        return ret

    def noteIsPlayingAt(self, row, note):
        intervals = self.noteGetIntervals()
        if note not in intervals: return False
        for interval in intervals[note]:
            if row in range(*interval):
                return True
        return False

    def noteIsPlayingInRange(self, rowStart, rowStop, note):
        if rowStart >= rowStop: return False
        intervals = self.noteGetIntervals()
        if note not in intervals: return False
        def overlap(start1, stop1, start2, stop2):
            return (start2 <= start1 <= stop2) or (start2 <= stop1 <= stop2) or (start1 <= start2 <= stop1) or (start1 <= stop2 <= stop1)
        for interval in intervals[note]:
            if overlap(rowStart, rowStop, interval[0], interval[1]-1):
                return True
        return False

    def isEmptyCell(self, row, col):
        if row not in self.data: return True
        if col not in self.data[row]: return True
        if self.data[row][col] == -1: return True
        return False

    def isEmptyRow(self, row):
        if row not in self.data: return True
        for col in self.data[row]:
            if self.data[row][col] != -1:
                return False
        return True

    def isEmpty(self):
        for row in self.data:
            for col in self.data[row]:
                if self.data[row][col] != -1:
                    return False
        return True

    def get(self, row, col):
        return self.data[row][col]

    def set(self, row, col, value, notify=True):
        if row in self.data and col in self.data[row] and value == -1:
            del self.data[row][col]
            if self.isEmptyRow(row):
                del self.data[row]
        else:
            self.data[row][col] = value
        if notify: self.notifyPatternChange()

    def getRow(self, row):
        numCols = 1 + (max(self.data[row]) if len(self.data[row]) else 0)
        # make sure to always output noteColumns:
        numCols = max(numCols, 1 + max(self.track.noteCols))
        return [self.get(row, col) for col in range(numCols)]

    def setRow(self, row, values, notify=True):
        for col, value in enumerate(values):
            self.set(row, col, value, notify=False)
        if notify: self.notifyPatternChange()

    def clear(self, notify=True):
        self.clearRows(self.data.keys(), notify)

    def clearRowRange(self, startRow, endRow=None, notify=True):
        if endRow is None:
            self.clearRows([row for row in self.data.keys() if row >= startRow], notify)
        else:
            self.clearRows(range(startRow, 1 + endRow), notify)

    def clearRows(self, rows, notify=True):
        for row in rows:
            del self.data[row]
        if notify: self.notifyPatternChange()

    def getLength(self):
        return self.length

    def setLength(self, length, notify=True):
        oldLength = self.length
        self.length = length
        self.clearRowRange(length, None, False)
        if self.length > oldLength:
            # repeat data to fill empty region of pattern:
            for srcRow in range(self.length):
                for dstRow in range(srcRow + oldLength, self.length, oldLength):
                    self.setRow(dstRow, self.getRow(srcRow), False)
        if notify: self.notifyPatternChange()

    def getSpeedReduction(self):
        return self.speedReduction

    def setSpeedReduction(self, speedReduction, notify=True):
        self.speedReduction = speedReduction
        if notify: self.notifyPatternChange()

    def dump(self):
        def valstr(v):
            if v == -2: return '  |'
            if v == -1: return '   '
            if v == 0: return '  ^'
            return '%03d' % v
        lines = []
        for row in range(self.getLength()):
            lines.append('%02d: %s' % (row, ' '.join(map(valstr, self.getRow(row)))))
        return 'Pattern #%d:\n%s' % (self.patternIndex, '\n'.join(lines))

