try:
    import pyext
except ImportError:
    class pyext:
        class _class:
            pass
from collections import defaultdict
import json
import weakref

def debug(s, *args, **kwargs):
    print('Seq: {}'.format(s.format(*args, **kwargs)))

class Pattern(object):
    def __init__(self, track, patternIndex, length=16):
        self.track = track
        self.patternIndex = patternIndex
        self.length = length
        self.speedReduction = 1
        self.data = defaultdict(lambda: defaultdict(lambda: -1))
        # needed by note* methods. many notes -> polyphonic (voice stealing)
        # e.g.:
        # noteCols = [0]        # (monophonic)
        # noteCols = [0,1,2,3]  # (4-notes poliphony)
        self.noteCols = list(range(8))
        self.observers = weakref.WeakKeyDictionary()

    def addObserver(self, callable_):
        self.observers[callable_] = 1

    def removeObserver(self, callable_):
        if callable_ in self.observers: del self.observers[callable_]

    def notifyPatternChange(self):
        observers = list(self.observers.keys())
        for observer in observers:
            observer.onPatternChange(self.track.trackIndex, self.patternIndex)

    def getNoteColumns(self):
        return self.noteCols[:]

    def setNoteColumns(self, noteCols):
        self.noteCols = noteCols[:]
        self.notifyPatternChange()

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
        for noteCol in self.noteCols:
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
        for noteCol in self.noteCols:
            if all(self.get(row, noteCol) == -1 for row in range(row, endRow)):
                return noteCol

    def noteGetIntervals(self):
        ret = {}
        for col in self.noteCols:
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
        if value == -1:
            del self.data[row][col]
            if self.isEmptyRow(row):
                del self.data[row]
        else:
            self.data[row][col] = value
        if notify: self.notifyPatternChange()

    def getRow(self, row):
        ncols = max(self.data[row]) if len(self.data[row]) else 0
        return [self.get(row, col) for col in range(1 + ncols)]

    def setRow(self, row, values, notify=True):
        for col, value in enumerate(values):
            self.set(row, col, value, notify=False)
        if notify: self.notifyPatternChange()

    def clear(self, notify=True):
        rows = tuple(self.data.keys())
        for row in rows:
            del self.data[row]
        if notify: self.notifyPatternChange()

    def getLength(self):
        return self.length

    def setLength(self, length, notify=True):
        self.length = length
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

class PlayHead(object):
    def __init__(self):
        self.patternIndex = -1
        self.patternRow = 0

    def reset(self):
        self.patternIndex = -1
        self.patternRow = 0

    def copyFrom(self, playHead):
        self.patternIndex = playHead.patternIndex
        self.patternRow = playHead.patternRow

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

class Controller(object):
    def update(self):
        pass

    def onPlayHeadChange(self, old, new):
        pass

    def onTrackStatusChange(self, trackIndex, volume, muted, active):
        pass

    def onPatternChange(self, trackIndex, patternIndex):
        pass

    def onCurrentRowChange(self, row):
        pass

    def onSongChange(self):
        pass

class LPController(Controller):
    def __init__(self, io):
        self.io = io

    def sendCommand(self, cmd):
        self.io.sendLaunchpadCommand(cmd)

    def onLPButtonPress(self, buf, section, row, col):
        debug('LPController.onLPButtonPress({buf}, {section}, {row}, {col})', **locals())

    def onLPButtonRelease(self, buf, section, row, col):
        debug('LPController.onLPButtonRelease({buf}, {section}, {row}, {col})', **locals())

class LKController(Controller):
    def __init__(self, io):
        self.io = io

    def sendCommand(self, cmd):
        self.io.sendLaunchkeyCommand(cmd)

    def onButtonPress(self, buttonName):
        debug('LKController.onButtonPress({buttonName})', **locals())

    def onButtonRelease(self, buttonName):
        debug('LKController.onButtonRelease({buttonName})', **locals())

    def onNoteOn(self, note, velocity):
        debug('LKController.onNoteOn({note}, {velocity})', **locals())

    def onNoteOff(self, note):
        debug('LKController.onNoteOff({note})', **locals())

    def onPadPress(self, row, col, velocity):
        debug('LKController.onPadPress({row}, {col}, {velocity})', **locals())

    def onPadRelease(self, row, col, velocity):
        debug('LKController.onPadRelease({row}, {col}, {velocity})', **locals())

    def onControlChange(self, num, value):
        debug('LKController.onControlChange({num}, {value})', **locals())

class PatternController(LPController):
    def onPatternChange(self, trackIndex, patternIndex):
        debug('PatternController.onPatternChange({trackIndex}, {patternIndex})', **locals())
        if self.io.lpcontroller == self and self.trackIndex == trackIndex and self.patternIndex == patternIndex:
            self.update()

class PatternEditController(PatternController):
    def __init__(self, io, trackIndex, patternIndex):
        self.io = io
        self.trackIndex = trackIndex
        self.track = self.io.song.tracks[self.trackIndex]
        self.patternIndex = patternIndex
        self.pattern = self.track.patterns[self.patternIndex]
        self.scroll = [0, 0]
        self.renderNoteOffs = False
        self.track.addObserver(self)
        self.pattern.addObserver(self)

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
            self.scroll = [0, 0]
        self.pattern.removeObserver(self)
        self.patternIndex = patternIndex
        self.pattern = self.track.patterns[self.patternIndex]
        self.pattern.addObserver(self)
        self.track.lastSelectedPatternIndex = self.patternIndex
        if update:
            self.update()

    def onTrackStatusChange(self, trackIndex, volume, muted, active):
        debug('PatternEditController.onTrackStatusChange({trackIndex}, {volume}, {muted}, {active})', **locals())
        if active == False:
            newTrack = self.io.song.activeTrack
            u = self.io.lpcontroller == self
            self.selectPattern(newTrack.trackIndex, newTrack.lastSelectedPatternIndex, update=u)

    def onPlayHeadChange(self, old, new):
        if self.patternIndex in (old.patternIndex, new.patternIndex):
            self.io.lpcontroller.update()

    def update(self, sync=True):
        debug('PatternEditController.update()')
        self.sendCommand(['clearb', 'default'])

        if self.track.playHead.patternIndex == self.patternIndex:
            for row in range(128):
                self.sendCommand(['setb', 'default', 'center', row, self.track.playHead.patternRow, 1, 0])

        for note, intervals in self.pattern.noteGetIntervals().items():
            for (rowStart, rowStop) in intervals:
                self.sendCommand(['setb', 'default', 'center', note, rowStart, 2, 3])
                for row in range(rowStart + 1, rowStop):
                    self.sendCommand(['setb', 'default', 'center', note, row, 0, 1])
                if self.renderNoteOffs:
                    self.sendCommand(['setb', 'default', 'center', note, rowStop, 1, 0])

        if sync:
            self.sendCommand(['sync', 'default'])

    def onLPButtonPress(self, buf, section, row, col):
        super(PatternEditController, self).onLPButtonPress(buf, section, row, col)
        buf = str(buf)
        section = str(section)
        if buf != 'default':
            return
        if section == 'center':
            patternRow = col
            note = row
            if self.pattern.noteGetLength(patternRow, note) is not None:
                self.io.setLPController(PatternEditNoteController(self, patternRow, note))
            elif not self.pattern.noteIsPlayingAt(patternRow, note):
                self.io.setLPController(PatternAddNoteController(self, patternRow, note))
        elif section == 'top' and row == 8:
            if col in range(4):
                self.scroll[0] += int(col == 1) - int(col == 0)
                self.scroll[1] += int(col == 3) - int(col == 2)
                self.scroll[0] = max(0, min(127, self.scroll[0]))
                self.scroll[1] = max(0, min(max(0, self.pattern.getLength() - 8), self.scroll[1]))
                self.sendCommand(['scroll', 'default', 'center'] + self.scroll)
                return
            if col == 4:
                self.io.setLPController(SongEditController(self))
                return
            if col == 5:
                cb = lambda trkIdx, patIdx: self.selectPattern(trkIdx, patIdx, True)
                v = self.track.lastSelectedPatternIndex
                self.io.setLPController(PatternSelectController(self, self.trackIndex, cb, v, False))
                return
            if col == 7:
                self.io.setLPController(PatternFunctionsController(self))
                return

class PatternAddNoteController(PatternController):
    def __init__(self, parent, patternRow, note):
        self.parent = parent
        self.io = parent.io
        self.trackIndex = parent.trackIndex
        self.track = self.io.song.tracks[self.trackIndex]
        self.patternIndex = parent.patternIndex
        self.pattern = self.track.patterns[self.patternIndex]
        self.patternRow = patternRow
        self.note = note
        self.length = 1
        self.pattern.addObserver(self)

    def __str__(self):
        return '{}(parent={}, trackIndex={}, patternIndex={}, patternRow={}, note={})'.format(self.__class__.__name__, self.parent, self.trackIndex, self.patternIndex, self.patternRow, self.note)

    def update(self, sync=True):
        self.parent.update(sync=False)
        debug('PatternAddNoteController.update()')
        for c in range(self.length):
            self.sendCommand(['setb', 'default', 'center', self.note, self.patternRow + c, 3, 0])
        if sync:
            self.sendCommand(['sync', 'default'])

    def onLPButtonPress(self, buf, section, row, col):
        super(PatternAddNoteController, self).onLPButtonPress(buf, section, row, col)
        buf = str(buf)
        section = str(section)
        if buf != 'default':
            return
        if section == 'center':
            if row == self.note and col > self.patternRow:
                length = 1 + col - self.patternRow
                if not self.pattern.noteIsPlayingInRange(self.patternRow, self.patternRow + length - 1, self.note):
                    self.length = length
                    self.update()
                return

    def onLPButtonRelease(self, buf, section, row, col):
        super(PatternAddNoteController, self).onLPButtonRelease(buf, section, row, col)
        buf = str(buf)
        section = str(section)
        if buf != 'default':
            return
        if section == 'center':
            if row == self.note and col == self.patternRow:
                self.pattern.noteAdd(self.patternRow, self.note, self.length)
                self.io.setLPController(self.parent)
                return
            if row == self.note and col > self.patternRow:
                self.length = 1
                self.update()
                return

class PatternEditNoteController(PatternController):
    def __init__(self, parent, patternRow, note):
        self.parent = parent
        self.io = parent.io
        self.trackIndex = parent.trackIndex
        self.track = self.io.song.tracks[self.trackIndex]
        self.patternIndex = parent.patternIndex
        self.pattern = self.track.patterns[self.patternIndex]
        self.patternRow = patternRow
        self.note = note
        self.deleteOnRelease = True
        self.originalLength = self.pattern.noteGetLength(self.patternRow, self.note)
        self.length = self.originalLength
        self.pattern.addObserver(self)

    def __str__(self):
        return '{}(parent={}, trackIndex={}, patternIndex={}, patternRow={}, note={})'.format(self.__class__.__name__, self.parent, self.trackIndex, self.patternIndex, self.patternRow, self.note)

    def update(self, sync=True):
        self.parent.update(sync=False)
        debug('PatternEditNoteController.update()')
        for c in range(self.length):
            self.sendCommand(['setb', 'default', 'center', self.note, self.patternRow + c, 3, 0])
        if sync:
            self.sendCommand(['sync', 'default'])

    def onLPButtonPress(self, buf, section, row, col):
        super(PatternEditNoteController, self).onLPButtonPress(buf, section, row, col)
        buf = str(buf)
        section = str(section)
        if buf != 'default':
            return
        if section == 'center':
            if row == self.note and col > self.patternRow:
                self.deleteOnRelease = False
                length = 1 + col - self.patternRow
                if not self.pattern.noteIsPlayingInRange(self.patternRow + self.originalLength, self.patternRow + length - 1, self.note):
                    self.length = length
                    self.update()
                return

    def onLPButtonRelease(self, buf, section, row, col):
        super(PatternEditNoteController, self).onLPButtonRelease(buf, section, row, col)
        buf = str(buf)
        section = str(section)
        if buf != 'default':
            return
        if section == 'center':
            if row == self.note and col == self.patternRow:
                if self.deleteOnRelease:
                    debug('delete selected note {} at row {}', self.note, self.patternRow)
                    self.pattern.noteDelete(self.patternRow, self.note)
                else:
                    debug('resize selected note {} at row {} to length {}', self.note, self.patternRow, self.length)
                    self.pattern.noteDelete(self.patternRow, self.note)
                    self.pattern.noteAdd(self.patternRow, self.note, self.length)
                self.io.setLPController(self.parent)
                return
            if row == self.note and col > self.patternRow:
                self.length = 1
                self.deleteOnRelease = False
                self.update()
                return

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
        debug('PatternSelectController.update()')
        self.sendCommand(['clearb', 'default'])
        for patternIndex in range(64):
            row, col = patternIndex / 8, patternIndex % 8
            pattern = self.track.patterns[patternIndex]
            empty = pattern.isEmpty()
            #cur = patternIndex == self.track.lastSelectedPatternIndex
            cur = patternIndex == self.currentPatternIndex
            color = [2, 0] if cur else [0, 1] if empty else [2, 3]
            self.sendCommand(['setb', 'default', 'center', row, col] + color)
        if self.allowNullSelection:
            self.sendCommand(['setb', 'default', 'right', 7, 8, 3, 0])
        if sync:
            self.sendCommand(['sync', 'default'])

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
            if col in range(4):
                #self.scroll[0] += int(col == 1) - int(col == 0)
                #self.scroll[1] += int(col == 3) - int(col == 2)
                #self.scroll[0] = max(0, min(127, self.scroll[0]))
                #self.scroll[1] = max(0, min(max(0, self.pattern.getLength() - 8), self.scroll[1]))
                #self.sendCommand(['scroll', 'default', 'center'] + self.scroll)
                return
            if col == 5:
                self.io.setLPController(self.parent)
                return
        elif section == 'right' and col == 8:
            if row == 7 and self.allowNullSelection:
                self.callback(self.trackIndex, -1)
                self.io.setLPController(self.parent)

class PatternFunctionsController(PatternController):
    def __init__(self, parent):
        self.parent = parent
        self.io = parent.io
        self.trackIndex = parent.trackIndex
        self.track = self.io.song.tracks[self.trackIndex]
        self.patternIndex = parent.patternIndex
        self.pattern = self.track.patterns[self.patternIndex]
        self.pattern.addObserver(self)

    def __str__(self):
        return '{}(parent={})'.format(self.__class__.__name__, self.parent)

    def update(self, sync=True):
        self.parent.update(sync=False)
        debug('PatternFunctionsController.update()')
        self.sendCommand(['setb', 'default', 'top', 8, 7, 2, 2])
        self.sendCommand(['setb', 'default', 'right', 0, 8, 0, 3])
        self.sendCommand(['setb', 'default', 'right', 1, 8, 0, 3])
        if sync:
            self.sendCommand(['sync', 'default'])

    def onLPButtonPress(self, buf, section, row, col):
        super(PatternFunctionsController, self).onLPButtonPress(buf, section, row, col)

    def onLPButtonRelease(self, buf, section, row, col):
        super(PatternFunctionsController, self).onLPButtonRelease(buf, section, row, col)
        buf = str(buf)
        section = str(section)
        if buf != 'default':
            return
        if section == 'top' and row == 8:
            if col == 7:
                self.io.setLPController(self.parent)
                return
        if section == 'right' and col == 8:
            if row == 0: # set pattern length
                cb = lambda n: self.pattern.setLength(n)
                self.io.setLPController(NumberSelectController(self, cb, self.pattern.getLength(), 1, 64))
                return
            elif row == 1: # set pattern speed reduction
                cb = lambda n: self.pattern.setSpeedReduction(n)
                self.io.setLPController(NumberSelectController(self, cb, self.pattern.getSpeedReduction(), 1, 32))
                return

class SongEditController(LPController):
    def __init__(self, parent):
        self.parent = parent
        self.io = self.parent.io
        self.io.song.addObserver(self)
        self.vscroll = 0

    def __str__(self):
        return '{}(parent={})'.format(self.__class__.__name__, self.parent)

    def onCurrentRowChange(self, row):
        self.update()

    def onSongChange(self):
        self.update()

    def update(self, sync=True):
        debug('SongEditController.update()')
        self.sendCommand(['clearb', 'default'])

        for row in range(self.io.song.getLength()):
            curRow = row == self.io.song.currentRow
            for trackIndex, track in enumerate(self.io.song.tracks):
                v = self.io.song.get(row, trackIndex)
                c = [0, 0] if v == -1 else [2, 2] if curRow else [0, 3]
                self.sendCommand(['setb', 'default', 'center', row, trackIndex] + c)
            self.sendCommand(['setb', 'default', 'right', row, 8, 3 * int(curRow), 1])
        self.sendCommand(['setb', 'default', 'top', 8, 4, 2, 2])
        if sync:
            self.sendCommand(['sync', 'default'])

    def onLPButtonPress(self, buf, section, row, col):
        super(SongEditController, self).onLPButtonPress(buf, section, row, col)
        buf = str(buf)
        section = str(section)
        if buf != 'default':
            return
        if section == 'center':
            self.editingRow = row
            self.editingTrack = col
            v = self.io.song.get(row, col)
            cb = lambda trkIdx, patIdx: self.io.song.set(self.editingRow, trkIdx, patIdx)
            self.io.setLPController(PatternSelectController(self, self.editingTrack, cb, v, True, listenToTrackStatusChange=False))
        elif section == 'top' and row == 8:
            if col in range(2):
                self.vscroll += int(col == 1) - int(col == 0)
                self.sendCommand(['scroll', 'default', 'center', vscroll, 0])
                self.sendCommand(['scroll', 'default', 'right', vscroll, 0])
                return
            if col == 4:
                self.io.setLPController(self.parent)
                return
        elif section == 'right': # and col == 8:
            cb = lambda n: self.io.song.setRowDuration(row, n)
            self.io.setLPController(NumberSelectController(self, cb, self.io.song.getRowDuration(row), 1, 64))
            return


class NumberSelectController(LPController):
    def __init__(self, parent, callback, currentValue=0, minValue=0, maxValue=64):
        self.parent = parent
        self.io = self.parent.io
        self.callback = callback
        self.currentValue = currentValue
        self.minValue = minValue
        self.maxValue = maxValue

    def __str__(self):
        return '{}(parent={}, currentValue={}, minValue={}, maxValue={})'.format(self.__class__.__name__, self.parent, self.currentValue, self.minValue, self.maxValue)

    def update(self, sync=True):
        debug('NumberSelectController.update()')
        self.sendCommand(['clearb', 'default'])
        for v in range(max(0, self.minValue), 1 + self.maxValue):
            cur = v == self.currentValue
            color = [2, 0] if cur else [0, 2]
            if v == 0:
                self.sendCommand(['setb', 'default', 'right', row, col] + color)
            else:
                row, col = (v - 1) / 8, (v - 1) % 8
                self.sendCommand(['setb', 'default', 'center', row, col] + color)
        if sync:
            self.sendCommand(['sync', 'default'])

    def onLPButtonPress(self, buf, section, row, col):
        super(NumberSelectController, self).onLPButtonPress(buf, section, row, col)
        buf = str(buf)
        section = str(section)
        if buf != 'default':
            return
        if section == 'center':
            v = 1 + row * 8 + col
            if self.minValue <= v <= self.maxValue:
                self.selectNumber(v)
            return
        elif section == 'right' and col == 8 and row == 7 and self.minValue <= 0 and self.maxValue >= 0:
            self.selectNumber(0)
            return

    def selectNumber(self, v):
        self.callback(v)
        self.io.setLPController(self.parent)

class TracksController(LKController):
    def __init__(self, io):
        self.io = io
        for track in self.io.song.tracks:
            track.addObserver(self)

    def onTrackStatusChange(self, trackIndex, volume, muted, isActive):
        if isActive == True:
            debug('TracksController.onTrackStatusChange: track {trackIndex} is now active', **locals())
        self.update()

    def update(self):
        debug('TracksController.update() called')
        activeTrack = self.io.song.activeTrack
        for trackIndex, track in enumerate(self.io.song.tracks):
            m = 3 * int(track.muted)
            a = 2 * int(activeTrack == track)
            self.sendCommand(['setled', 0, trackIndex, a, a])
            self.sendCommand(['setled', 1, trackIndex, m, 1 - m])

    def onPadPress(self, row, col, velocity):
        if row == 0 and col < 8:
            self.io.song.tracks[col].activate()
        elif row == 1 and col < 8:
            self.io.song.tracks[col].toggleMute()

    def onControlChange(self, num, value):
        self.io.song.tracks[num].setVolume(value)

class IO(pyext._class):
    _inlets = 3
    _outlets = 3

    def __init__(self):
        self.song = Song()
        self.lpcontroller = PatternEditController(self, 0, 0)
        self.lkcontroller = TracksController(self)

    def _init(self):
        self.sendLaunchkeyCommand(['extendedmode', 1])
        self.lpcontroller.update()
        self.lkcontroller.update()

    def setLPController(self, c):
        debug('LPController changes to %s' % c)
        self.lpcontroller = c
        self.lpcontroller.update()

    def setLKController(self, c):
        debug('LKController changes to %s' % c)
        self.lkcontroller = c
        self.lkcontroller.update()

    def onLPButtonPress(self, buf, section, row, col):
        for controller in (self.lpcontroller, self.lkcontroller):
            if isinstance(controller, LPController):
                controller.onLPButtonPress(buf, section, row, col)

    def onLPButtonRelease(self, buf, section, row, col):
        for controller in (self.lpcontroller, self.lkcontroller):
            if isinstance(controller, LPController):
                controller.onLPButtonRelease(buf, section, row, col)

    def onButtonPress(self, buttonName):
        for controller in (self.lpcontroller, self.lkcontroller):
            if isinstance(controller, LKController):
                controller.onButtonPress(buttonName)

    def onButtonRelease(self, buttonName):
        for controller in (self.lpcontroller, self.lkcontroller):
            if isinstance(controller, LKController):
                controller.onButtonRelease(buttonName)

    def onNoteOn(self, note, velocity):
        for controller in (self.lpcontroller, self.lkcontroller):
            if isinstance(controller, LKController):
                controller.onNoteOn(note, velocity)

    def onNoteOff(self, note):
        for controller in (self.lpcontroller, self.lkcontroller):
            if isinstance(controller, LKController):
                controller.onNoteOff(note)

    def onPadPress(self, row, col, velocity):
        for controller in (self.lpcontroller, self.lkcontroller):
            if isinstance(controller, LKController):
                controller.onPadPress(row, col, velocity)

    def onPadRelease(self, row, col, velocity):
        for controller in (self.lpcontroller, self.lkcontroller):
            if isinstance(controller, LKController):
                controller.onPadRelease(row, col, velocity)

    def onControlChange(self, num, value):
        for controller in (self.lpcontroller, self.lkcontroller):
            if isinstance(controller, LKController):
                controller.onControlChange(num, value)

    def getrowduration_1(self, row):
        self._outlet(1, ['rowduration', row, self.song.getRowDuration(row)])

    def setrowduration_1(self, row, duration):
        self.song.setRowDuration(row, duration)

    def rewind_1(self):
        self.song.rewind()

    def tick_1(self):
        currentRow, currentTick, output = self.song.tick()
        self._outlet(1, ['pos', currentRow, currentTick])
        for trackIndex, row in output.items():
            self._outlet(1, ['output', trackIndex] + row)

    def dump_1(self):
        debug(self.song.dump())

    def songget_1(self, row, col):
        self._outlet(1, ['song', 'data', row, col, self.song.get(row, col)])

    def songset_1(self, row, col, value):
        self.song.set(row, col, value)

    def songgetrow_1(self, row):
        self._outlet(1, ['song', 'data-row', row] + self.song.getRow(row))

    def songsetrow_1(self, row, *values):
        self.song.setRow(row, values)

    def songclear_1(self):
        self.song.clear()

    def songgetlength_1(self):
        self._outlet(1, ['song', 'length', self.song.getLength()])

    def songsetlength_1(self, length):
        self.song.setLength(length)

    def get_1(self, trackIndex, patternIndex, row, col):
        pattern = self.song.tracks[trackIndex].patterns[patternIndex]
        self._outlet(1, ['track', trackIndex, 'pattern', patternIndex, 'data', row, col, pattern.get(row, col)])

    def set_1(self, trackIndex, patternIndex, row, col, value):
        pattern = self.song.tracks[trackIndex].patterns[patternIndex]
        pattern.set(row, col, value)

    def getrow_1(self, trackIndex, patternIndex, row):
        pattern = self.song.tracks[trackIndex].patterns[patternIndex]
        self._outlet(1, ['track', trackIndex, 'pattern', patternIndex, 'data-row', row] + pattern.getRow(row))

    def setrow_1(self, trackIndex, patternIndex, row, *values):
        pattern = self.song.tracks[trackIndex].patterns[patternIndex]
        pattern.setRow(row, values)

    def clear_1(self, trackIndex, patternIndex):
        pattern = self.song.tracks[trackIndex].patterns[patternIndex]
        pattern.clear()

    def getlength_1(self, trackIndex, patternIndex):
        pattern = self.song.tracks[trackIndex].patterns[patternIndex]
        self._outlet(1, ['track', trackIndex, 'pattern', patternIndex, 'length', pattern.getLength()])

    def setlength_1(self, trackIndex, patternIndex, length):
        pattern = self.song.tracks[trackIndex].patterns[patternIndex]
        pattern.setLength(length)

    def getspeedreduction_1(self, trackIndex, patternIndex):
        pattern = self.song.tracks[trackIndex].patterns[patternIndex]
        self._outlet(1, ['track', trackIndex, 'pattern', patternIndex, 'speedreduction', pattern.getSpeedReduction()])

    def setspeedreduction_1(self, trackIndex, patternIndex, speedReduction):
        pattern = self.song.tracks[trackIndex].patterns[patternIndex]
        pattern.setSpeedReduction(speedReduction)

    def buffer_2(self, buf, section, btnCmd, row, col, pressed):
        if pressed: self.onLPButtonPress(buf, section, row, col)
        else: self.onLPButtonRelease(buf, section, row, col)

    def note_3(self, note, velocity):
        if velocity > 0: self.onNoteOn(note, velocity)
        else: self.onNoteOff(note)

    def control_3(self, num, value):
        self.onControlChange(num, value)

    def pad_3(self, row, col, velocity):
        if velocity > 0: self.onPadPress(row, col, velocity)
        else: self.onPadRelease(row, col, velocity)

    def button_3(self, name, pressed):
        if pressed: self.onButtonPress(name)
        else: self.onButtonRelease(name)

    def sendLaunchpadCommand(self, l):
        self._outlet(2, l)

    def sendLaunchkeyCommand(self, l):
        self._outlet(3, l)

