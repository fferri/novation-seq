import pyext
from sequencer.model import *
from sequencer.controller import *

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
        self.lpcontroller = c
        self.lpcontroller.update()

    def setLKController(self, c):
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
        pass

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

