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
    pass#print('Seq: {}'.format(s.format(*args, **kwargs)))

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
        for observer in self.observers:
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

    def get(self, row, col):
        return self.data[row][col]

    def set(self, row, col, value, notify=True):
        if value == -1:
            del self.data[row][col]
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
    def __init__(self, trackIndex):
        self.trackIndex = trackIndex
        self.patterns = [Pattern(self, patternIndex) for patternIndex in range(64)]
        self.playHead = PlayHead()
        self.playHeadPrev = PlayHead()
        self.observers = weakref.WeakKeyDictionary()

    def addObserver(self, callable_):
        self.observers[callable_] = 1

    def removeObserver(self, callable_):
        if callable_ in self.observers: del self.observers[callable_]

    def notifyPlayHeadChange(self):
        if self.playHead.patternIndex != self.playHeadPrev.patternIndex or self.playHead.patternRow != self.playHeadPrev.patternRow:
            for observer in self.observers:
                observer.onPlayHeadChange(self.playHeadPrev, self.playHead)

class Song(object):
    def __init__(self, numTracks=8, defaultRowDuration=16):
        self.tracks = [Track(trackIndex) for trackIndex in range(numTracks)]
        self.rowDuration = defaultdict(lambda: defaultRowDuration)
        self.currentRow = 0
        self.currentTick = 0
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
        for observer in self.observers:
            observer.onSongChange()

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
        ret = (self.currentRow, self.currentTick, output)
        self.incrTick()
        return ret

    def dump(self):
        d = []
        for trackIndex, track in enumerate(self.tracks):
            for patternIndex, pattern in enumerate(track.patterns):
                d.append(pattern.dump())
        return '\n'.join(d)

class Controller(object):
    def __init__(self, io):
        self.io = io

    def update(self):
        pass

    def onPatternChange(self, trackIndex, patternIndex):
        debug('Controller.onPatternChange({trackIndex}, {patternIndex})', **locals())

    def onLaunchpadButtonPress(self, buf, section, row, col):
        debug('Controller.onLaunchpadButtonPress({buf}, {section}, {row}, {col})', **locals())

    def onLaunchpadButtonRelease(self, buf, section, row, col):
        debug('Controller.onLaunchpadButtonRelease({buf}, {section}, {row}, {col})', **locals())

    def onLaunchkeyButtonPress(self, buttonName):
        debug('Controller.onLaunchkeyButtonPress({buttonName})', **locals())

    def onLaunchkeyButtonRelease(self, buttonName):
        debug('Controller.onLaunchkeyButtonRelease({buttonName})', **locals())

    def onLaunchkeyNoteOn(self, note, velocity):
        debug('Controller.onLaunchkeyNoteOn({note}, {velocity})', **locals())

    def onLaunchkeyNoteOff(self, note):
        debug('Controller.onLaunchkeyNoteOff({note})', **locals())

    def onLaunchkeyPadPress(self, row, col, velocity):
        debug('Controller.onLaunchkeyPadPress({row}, {col}, {velocity})', **locals())

    def onLaunchkeyPadRelease(self, row, col, velocity):
        debug('Controller.onLaunchkeyPadRelease({row}, {col}, {velocity})', **locals())

    def onLaunchkeyControlChange(self, num, value):
        debug('Controller.onLaunchkeyControlChange({num}, {value})', **locals())

class PatternController(Controller):
    def onPatternChange(self, trackIndex, patternIndex):
        debug('PatternController.onPatternChange({trackIndex}, {patternIndex})', **locals())
        if self.io.controller == self and self.trackIndex == trackIndex and self.patternIndex == patternIndex:
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

    def onPlayHeadChange(self, old, new):
        if self.patternIndex in (old.patternIndex, new.patternIndex):
            self.update()

    def update(self):
        debug('PatternEditController.update()')
        self.io.sendLaunchpadCommand(['clearb', 'default'])

        if self.track.playHead.patternIndex == self.patternIndex:
            for row in range(128):
                self.io.sendLaunchpadCommand(['setb', 'default', 'center', row, self.track.playHead.patternRow, 1, 0])

        for note, intervals in self.pattern.noteGetIntervals().items():
            for (rowStart, rowStop) in intervals:
                self.io.sendLaunchpadCommand(['setb', 'default', 'center', note, rowStart, 2, 3])
                for row in range(rowStart + 1, rowStop):
                    self.io.sendLaunchpadCommand(['setb', 'default', 'center', note, row, 0, 1])
                if self.renderNoteOffs:
                    self.io.sendLaunchpadCommand(['setb', 'default', 'center', note, rowStop, 1, 0])

        self.io.sendLaunchpadCommand(['sync', 'default'])

    def onLaunchpadButtonPress(self, buf, section, row, col):
        super(PatternEditController, self).onLaunchpadButtonPress(buf, section, row, col)
        buf = str(buf)
        section = str(section)
        if buf != 'default':
            return
        if section == 'center':
            patternRow = col
            note = row
            if self.pattern.noteGetLength(patternRow, note) is not None:
                self.io.setController(PatternEditNoteController(self, patternRow, note))
            elif not self.pattern.noteIsPlayingAt(patternRow, note):
                self.io.setController(PatternAddNoteController(self, patternRow, note))
        elif section == 'top':
            self.scroll[0] += int(col == 1) - int(col == 0)
            self.scroll[1] += int(col == 3) - int(col == 2)
            self.scroll[0] = max(0, min(127, self.scroll[0]))
            self.scroll[1] = max(0, min(max(0, self.pattern.getLength() - 8), self.scroll[1]))
            self.io.sendLaunchpadCommand(['scroll', 'default', 'center'] + self.scroll)

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
        return '{}(trackIndex={}, patternIndex={}, patternRow={}, note={})'.format(self.__class__.__name__, self.trackIndex, self.patternIndex, self.patternRow, self.note)

    def update(self):
        self.parent.update()
        debug('PatternAddNoteController.update()')
        for c in range(self.length):
            self.io.sendLaunchpadCommand(['setb', 'default', 'center', self.note, self.patternRow + c, 3, 0])
        self.io.sendLaunchpadCommand(['sync', 'default'])

    def onLaunchpadButtonPress(self, buf, section, row, col):
        super(PatternAddNoteController, self).onLaunchpadButtonPress(buf, section, row, col)
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

    def onLaunchpadButtonRelease(self, buf, section, row, col):
        super(PatternAddNoteController, self).onLaunchpadButtonRelease(buf, section, row, col)
        buf = str(buf)
        section = str(section)
        if buf != 'default':
            return
        if section == 'center':
            if row == self.note and col == self.patternRow:
                self.pattern.noteAdd(self.patternRow, self.note, self.length)
                self.io.setController(self.parent)
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
        return '{}(trackIndex={}, patternIndex={}, patternRow={}, note={})'.format(self.__class__.__name__, self.trackIndex, self.patternIndex, self.patternRow, self.note)

    def update(self):
        self.parent.update()
        debug('PatternEditNoteController.update()')
        for c in range(self.length):
            self.io.sendLaunchpadCommand(['setb', 'default', 'center', self.note, self.patternRow + c, 3, 0])
        self.io.sendLaunchpadCommand(['sync', 'default'])

    def onLaunchpadButtonPress(self, buf, section, row, col):
        super(PatternEditNoteController, self).onLaunchpadButtonPress(buf, section, row, col)
        buf = str(buf)
        section = str(section)
        if buf != 'default':
            return
        if section == 'center':
            if row == self.note and col > self.patternRow:
                self.deleteOnRelease = False
                length = 1 + col - self.patternRow
                if not self.pattern.noteIsPlayingInRange(self.patternRow + self.originalLength, self.patternRow + length, self.note):
                    self.length = length
                    self.update()
                return

    def onLaunchpadButtonRelease(self, buf, section, row, col):
        super(PatternEditNoteController, self).onLaunchpadButtonRelease(buf, section, row, col)
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
                self.io.setController(self.parent)
                return
            if row == self.note and col > self.patternRow:
                self.length = 1
                self.deleteOnRelease = False
                self.update()
                return

class IO(pyext._class):
    _inlets = 3
    _outlets = 3

    def __init__(self):
        self.song = Song()
        self.controller = PatternEditController(self, 0, 0)

    def _init(self):
        self.controller.update()

    def setController(self, c):
        debug('Controller changes to %s' % c)
        self.controller = c
        self.controller.update()

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
        if pressed:
            self.controller.onLaunchpadButtonPress(buf, section, row, col)
        else:
            self.controller.onLaunchpadButtonRelease(buf, section, row, col)

    def note_3(self, note, velocity):
        if velocity > 0:
            self.controller.onLaunchkeyNoteOn(note, velocity)
        else:
            self.controller.onLaunchkeyNoteOff(note)

    def control_3(self, num, value):
        self.controller.onLaunchkeyControlChange(num, value)

    def pad_3(self, row, col, velocity):
        if velocity > 0:
            self.controller.onLaunchkeyPadPress(row, col, velocity)
        else:
            self.controller.onLaunchkeyPadRelease(row, col, velocity)

    def button_3(self, name, pressed):
        if pressed:
            self.controller.onLaunchkeyButtonPress(name)
        else:
            self.controller.onLaunchkeyButtonRelease(name)

    def sendLaunchpadCommand(self, l):
        self._outlet(2, l)

    def sendLaunchkeyCommand(self, l):
        self._outlet(3, l)

