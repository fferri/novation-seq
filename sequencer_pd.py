import pyext
from sequencer.model import *
from sequencer.controller import *
from sequencer.util import Transport
from device import *

class LaunchpadImpl(BufferedLaunchpad):
    def __init__(self, pdobj):
        super(LaunchpadImpl, self).__init__()
        self.pdobj = pdobj

    def writeMidi(self, v1, v2, v3):
        for v in (v1, v2, v3):
            self.pdobj._outlet(1, ['midi', self.pdobj.launchpadPort, v])

    def onBufferButtonEvent(self, buf, section, row, col, pressed):
        for controller in (self.pdobj.app.lpcontroller, self.pdobj.app.lkcontroller):
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
        for controller in (self.pdobj.app.lpcontroller, self.pdobj.app.lkcontroller):
            if isinstance(controller, LKController):
                if velocity > 0: controller.onNoteOn(note, velocity)
                else: controller.onNoteOff(note)

    def onPadEvent(self, row, col, velocity):
        for controller in (self.pdobj.app.lpcontroller, self.pdobj.app.lkcontroller):
            if isinstance(controller, LKController):
                if velocity > 0: controller.onPadPress(row, col, velocity)
                else: controller.onPadRelease(row, col, velocity)

    def onControlEvent(self, num, value):
        for controller in (self.pdobj.app.lpcontroller, self.pdobj.app.lkcontroller):
            if isinstance(controller, LKController):
                controller.onControlChange(num, value)

    def onButtonEvent(self, buttonName, pressed):
        for controller in (self.pdobj.app.lpcontroller, self.pdobj.app.lkcontroller):
            if isinstance(controller, LKController):
                if pressed: controller.onButtonPress(buttonName)
                else: controller.onButtonRelease(buttonName)

class Application(object):
    def __init__(self, pdobj):
        self.pdobj = pdobj
        self.song = Song()
        self.transport = Transport()
        self.launchpad = LaunchpadImpl(pdobj)
        self.launchkey = LaunchkeyImpl(pdobj)
        self.lpcontroller = PatternEditController(self, 0, 0)
        self.lkcontroller = TracksController(self)
        for track in self.song.tracks:
            track.addObserver(self)
        self.transport.addObserver(self)

    def initDevices(self):
        self.launchpad.reset()
        self.launchkey.reset()
        self.launchkey.setExtendedMode(True)
        self.lpcontroller.update()
        self.lkcontroller.update()

    def writeMidi(self, v1, v2, v3):
        self.pdobj.writeMidi(v1, v2, v3)

    def setLPController(self, c):
        self.lpcontroller = c
        self.lpcontroller.update()

    def setLKController(self, c):
        self.lkcontroller = c
        self.lkcontroller.update()

    def isActiveController(self, controller):
        return controller in (self.lpcontroller, self.lkcontroller)

    def onTrackStatusChange(self, trackIndex, volume, muted, isActive):
        self.pdobj._outlet(1, ['volume', trackIndex, 0 if muted else volume])

    def onPlaybackStatusChange(self, playing):
        if playing:
            self.pdobj._outlet(1, ['delaytick', self.tickPeriod()])
        else:
            self.song.resetTick()

    def tickPeriod(self):
        return 60000. / self.song.getTicksPerBeat() / self.song.getBeatsPerMinute() / 4.

class IO(pyext._class):
    _inlets = 1
    _outlets = 1

    def __init__(self, launchpadPort, launchkeyPort, launchkeyCtrlPort, midiOutPort):
        self.launchpadPort = launchpadPort
        self.launchkeyPorts = (launchkeyPort, launchkeyCtrlPort)
        self.midiOutPort = midiOutPort
        self.midiBuffer = {}
        self.app = Application(self)
        self.song = self.app.song
        self.transport = self.app.transport
        self.launchkey = self.app.launchkey
        self.launchpad = self.app.launchpad

    def init_1(self):
        self.app.initDevices()

    def setLPController(self, c):
        self.app.setLPController(c)

    def setLKController(self, c):
        self.app.setLKController(c)

    def isActiveController(self, controller):
        return self.app.isActiveController(controller)

    def writeMidi(self, v1, v2, v3):
        for v in (v1, v2, v3):
            self._outlet(1, ['midi', self.midiOutPort, v])

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

    def setticksperbeat_1(self, tpb):
        self.song.setTicksPerBeat(tpb)

    def setbeatsperminute_1(self, bpm):
        self.song.setBeatsPerMinute(bpm)

    def start_1(self):
        self.transport.start()

    def stop_1(self):
        self.transport.stop()

    def delayedtick_1(self):
        if self.transport.isPlaying():
            self.tick_1()
            self._outlet(1, ['delaytick', self.app.tickPeriod()])

    def songgetrowduration_1(self, row):
        self._outlet(1, ['rowduration', row, self.song.getRowDuration(row)])

    def songsetrowduration_1(self, row, duration):
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

    def songset_1(self, row, col, *values):
        self.song.set(row, col, values)

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

