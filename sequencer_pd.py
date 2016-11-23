import pyext
from sequencer.model import *
from sequencer.controller import *
from device import *

class LaunchpadImpl(BufferedLaunchpad):
    def __init__(self, pdobj):
        super(LaunchpadImpl, self).__init__()
        self.pdobj = pdobj

    def writeMidi(self, v1, v2, v3):
        for v in (v1, v2, v3):
            self.pdobj._outlet(1, ['midi', self.pdobj.launchpadPort, v])

    def onBufferButtonEvent(self, buf, section, row, col, pressed):
        for controller in (self.pdobj.lpcontroller, self.pdobj.lkcontroller):
            if isinstance(controller, LPController):
                if pressed: controller.onLPButtonPress(buf, section, row, col)
                else: controller.onLPButtonRelease(buf, section, row, col)

class LaunchkeyImpl(Launchkey):
    def __init__(self, pdobj):
        super(LaunchkeyImpl, self).__init__()
        self.pdobj = pdobj

    def writeMidi(self, port, v1, v2, v3):
        for v in (v1, v2, v3):
            self.pdobj._outlet(1, ['midi', self.pdobj.launchkeyPorts[port], v])

    def onNoteEvent(self, note, velocity):
        for controller in (self.pdobj.lpcontroller, self.pdobj.lkcontroller):
            if isinstance(controller, LKController):
                if velocity > 0: controller.onNoteOn(note, velocity)
                else: controller.onNoteOff(note)

    def onPadEvent(self, row, col, velocity):
        for controller in (self.pdobj.lpcontroller, self.pdobj.lkcontroller):
            if isinstance(controller, LKController):
                if velocity > 0: controller.onPadPress(row, col, velocity)
                else: controller.onPadRelease(row, col, velocity)

    def onControlEvent(self, num, value):
        for controller in (self.pdobj.lpcontroller, self.pdobj.lkcontroller):
            if isinstance(controller, LKController):
                controller.onControlChange(num, value)

    def onButtonEvent(self, buttonName, pressed):
        for controller in (self.pdobj.lpcontroller, self.pdobj.lkcontroller):
            if isinstance(controller, LKController):
                if pressed: controller.onButtonPress(buttonName)
                else: controller.onButtonPress(buttonName)

class IO(pyext._class):
    _inlets = 1
    _outlets = 1

    def __init__(self, launchpadPort, launchkeyPort, launchkeyCtrlPort, midiOutPort):
        self.launchpadPort = launchpadPort
        self.launchkeyPorts = (launchkeyPort, launchkeyCtrlPort)
        self.midiOutPort = midiOutPort
        self.song = Song()
        self.launchpad = LaunchpadImpl(self)
        self.launchkey = LaunchkeyImpl(self)
        self.lpcontroller = PatternEditController(self, 0, 0)
        self.lkcontroller = TracksController(self)
        self.midiBuffer = {}

    def _init(self):
        self.launchpad.reset()
        self.launchkey.reset()
        self.launchkey.setExtendedMode(True)
        self.lpcontroller.update()
        self.lkcontroller.update()

    def init_1(self):
        self._init()

    def setLPController(self, c):
        self.lpcontroller = c
        self.lpcontroller.update()

    def setLKController(self, c):
        self.lkcontroller = c
        self.lkcontroller.update()

    def midi_1(self, pdport, f):
        if pdport not in self.midiBuffer or f & 0x80:
            self.midiBuffer[pdport] = []
        self.midiBuffer[pdport].append(f)
        if len(self.midiBuffer[pdport]) == 3:
            if pdport == self.launchpadPort:
                self.launchpad.onMidiData(self.midiBuffer[pdport])
            elif pdport == self.launchkeyPorts[0]:
                self.launchkey.onMidiData(0, self.midiBuffer[pdport])
            elif pdport == self.launchkeyPorts[1]:
                self.launchkey.onMidiData(1, self.midiBuffer[pdport])

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

