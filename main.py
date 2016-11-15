from device import *
from model import *
from time import sleep, time, clock
import sys
import numpy as np
from enum import Enum
import math

class State(Enum):
    viewPattern = 0
    editNote = 10
    editRow = 30
    resizePattern = 50
    editSong = 100
    selectPattern = 101

class Application:
    def __init__(self):
        self.launchpad = Launchpad()
        self.launchpad.reset()
        self.launchpad.setBuffers(0, 1)
        self.launchkey = Launchkey()
        self.launchkey.reset()
        self.launchkey.extendedMode(True)
        self.state = State.viewPattern
        self.offset = 0
        self.rowOffset = 0
        self.lpBuf = np.zeros((9,9,2), dtype=np.uint8)
        self.lpBak = np.zeros((9,9,2), dtype=np.uint8)
        self.lkBuf = np.zeros((2,9,2), dtype=np.uint8)
        self.lkBak = np.zeros((2,9,2), dtype=np.uint8)
        self.output = Output(self, b'IAC Driver Bus 1')
        self.track = [Track(self.output, i) for i in range(8)]
        self.curTrack = self.track[0]
        self.song = Song(self)
        self.tpqn = 96
        self.bpm = 120
        self.lastTickTime = 0.
        self.ticks = 0

    def cleanup(self):
        self.launchpad.reset()
        self.launchkey.reset()
        self.launchkey.extendedMode(False)

    def getTickInterval(self):
        return 60./self.bpm/self.tpqn

    def updateLKScreen(self):
        diff = self.lkBuf != self.lkBak
        for i in range(diff.shape[0]):
            for j in range(diff.shape[1]):
                if diff[i,j].any():
                    launchkey.setLed(i, j, self.lkBuf[i,j,:])
        self.lkBak = np.copy(self.lkBuf)

    def updateLPScreen(self):
        diff = self.lpBuf != self.lpBak
        self.launchpad.setBuffers(0, 1)
        for i in range(self.lpBuf.shape[0]):
            for j in range(self.lpBuf.shape[1]):
                if diff[i,j].any():
                    self.launchpad.setLed(i, j, self.lpBuf[i,j,:])
        self.launchpad.setBuffers(1, 0, copy=True)
        self.lpBak = np.copy(self.lpBuf)

    def drawPattern(self):
        self.lpBuf *= 0

        # draw playhead:
        if self.curTrack.editPattern == self.curTrack.playPattern:
            _, tickPos = self.pat2scr(0, self.curTrack.playPattern.tickPos)
            if 0 <= tickPos < 8:
                self.lpBuf[0:8,tickPos,:] = [1,0]

        self.lpBuf[8,7,:] = [1,1]
        self.lpBuf[8,6,:] = [1,0]
        self.lpBuf[8,0:4,:] = [1,1]
        for (row, col), v in self.curTrack.editPattern._data.items():
            r, c = self.pat2scr(row, col)
            if r < 0 or c < 0 or r >= 8 or c >= 8: continue
            #self.lpBuf[r,8] = [0,1] # output indicator
            self.lpBuf[r,c] = [1,3]
            for c1 in range(c+1,c+v.length):
                if c1 < 8:
                    self.lpBuf[r,c1] = [0,1]

        self.launchkey.reset()
        if self.state == State.editRow:
            notes = self.curTrack.outputRow[self.editingRow].notes
            for note in notes:
                note = note % 12
                r,c=[(1,0),(0,0),(1,1),(0,1),(1,2),(1,3),(0,3),(1,4),(0,4),(1,5),(0,5),(1,6)][note]
                self.launchkey.setLed(r,c,[0,3])
            self.launchkey.setLed(1,8,[3,0])

    def drawPatternResize(self):
        self.lpBuf *= 0
        r = math.ceil(self.curTrack.editPattern.rows() / 8)
        c = math.ceil(self.curTrack.editPattern.length() / 8)
        self.lpBuf[:r,:c,:] = [0,1]
        for i in range(r):
            for j in range(c):
                if len([(r,c) for (r,c) in self.curTrack.editPattern._data if r>=i*8 and r<(i+1)*8 and c>=j*8 and c<(j+1)*8]) > 0:
                    self.lpBuf[i,j,:] = [1,3]
        self.lpBuf[8,2,:] = [3,0]
        self.lpBuf[8,3,:] = [0,3]
        self.lpBuf[8,7,:] = [3,3]
        if self.offset % 8 == 0 and self.rowOffset % 8 == 0:
            self.lpBuf[self.rowOffset//8,self.offset//8] = [3,1]

    def drawEditSong(self):
        self.lpBuf *= 0
        self.lpBuf[8,6,:] = [3,3]
        self.lpBuf[self.song.curRow,8,:] = [0,3]
        for i in range(self.song.data.shape[0]):
            for j in range(self.song.data.shape[1]):
                if self.song.data[i,j] == -1: continue
                self.lpBuf[i,j] = [0,3]

        self.launchkey.reset()
        if self.state == State.selectPattern:
            for row in range(2):
                for col in range(8):
                    self.launchkey.setLed(row, col, [0,3])
            self.launchkey.setLed(1, 8, [3,0])

    def updateScreen(self):
        self.updateLKScreen()
        self.updateLPScreen()

    def refresh(self):
        if self.state in (State.resizePattern,):
            self.drawPatternResize()
        elif self.state in (State.editSong, State.selectPattern):
            self.drawEditSong()
        else:
            self.drawPattern()
        self.updateScreen()

    def pollEvents(self):
        e = self.launchpad.poll()
        if e is not None: return e
        e = self.launchkey.poll()
        if e is not None: return e

    def moveOffset(self, deltaRowOffset, deltaOffset):
        self.offset = max(0, min(self.curTrack.editPattern.length() - 8, self.offset + deltaOffset))
        self.rowOffset = max(0, min(self.curTrack.editPattern.rows() - 8, self.rowOffset + deltaRowOffset))

    def scr2pat(self, r, c):
        return r + self.rowOffset, c + self.offset

    def pat2scr(self, r, c):
        return r - self.rowOffset, c - self.offset

    def runTick(self):
        self.output.tick()
        ti = self.getTickInterval()
        t = time()
        if t - self.lastTickTime > ti:
            oldp = int(self.ticks * 4 / self.tpqn)
            self.ticks += 1
            self.lastTickTime = t
            newp = int(self.ticks * 4 / self.tpqn)
            if newp > oldp:
                for track in self.track:
                    track.tick()
                return self.state in (State.viewPattern, State.editRow)

    def run(self):
        self.refresh()
        while True:
            refresh = self.runTick()
            e = self.pollEvents()
            oldState = self.state
            if e is not None:
                refresh = refresh or self.processEvent(e)
            if refresh:
                self.refresh()

    def processEvent(self, e):
        if self.state == State.viewPattern:
            if isinstance(e, Launchpad.button) and e.pressed:
                if e.col == 8:
                    self.state = State.editRow
                    self.editingRow = e.row
                    return True
                if e.row < 8 and e.col < 8:
                    r, c = self.scr2pat(e.row, e.col)
                    v = self.curTrack.editPattern.get(r, c)
                    self.editingRow = r
                    self.editingCol = c
                    self.deleteNoteOnRelease = True
                    if v is None:
                        self.deleteNoteOnRelease = False
                        self.curTrack.editPattern.set(r, c, Trig())
                    self.state = State.editNote
                    return True
                if e.row == 8:
                    if e.col == 7:
                        self.state = State.resizePattern
                        self.originalPatternLength = self.curTrack.editPattern.length()
                        #self.lpBuf *= 0
                        return True
                    if e.col == 6:
                        self.state = State.editSong
                        return True
                    if e.col in (0, 1, 2, 3):
                        self.moveOffset([-8,8,0,0][e.col], [0,0,-8,8][e.col])
                        return True
            if isinstance(e, Launchkey.button) and e.pressed:
                deltaOffset = int(e.name == 'track-right') - int(e.name == 'track-left')
                deltaRowOffset = int(e.name == 'track-down') - int(e.name == 'track-up')
                self.moveOffset(deltaRowOffset, deltaOffset)
                return True
            if isinstance(e, Launchkey.pad) and e.velocity > 0 and e.row == 0:
                self.curTrack = self.track[e.col]
                return True
            if isinstance(e, Launchkey.note):
                self.output.midiOut.WriteShort((0x90 if e.velocity > 0 else 0x80) + self.curTrack.channel, e.note, e.velocity)
                return False
        if self.state == State.editSong:
            if isinstance(e, Launchpad.button) and e.pressed:
                if e.col == 8:
                    self.song.selectRow(e.row)
                    return True
                if e.row == 8 and e.col == 6:
                    self.state = State.viewPattern
                    return True
                if e.row < 8 and e.col < 8 and e.pressed:
                    self.state = State.selectPattern
                    self.songRow = e.row
                    self.songCol = e.col
                    return True
        if self.state == State.selectPattern:
            if isinstance(e, Launchpad.button) and not e.pressed:
                if e.row == self.songRow and e.col == self.songCol:
                    self.state = State.editSong
                    return True
            if isinstance(e, Launchkey.pad) and e.velocity > 0:
                if e.col == 8 and e.row == 1:
                    self.song.data[self.songRow,self.songCol] = -1
                elif e.col < 8:
                    self.song.data[self.songRow,self.songCol] = e.col + 8 * e.row
                return True
        if self.state == State.resizePattern:
            if isinstance(e, Launchpad.button) and e.pressed:
                if e.row == 8 and e.col == 7:
                    oldLen, newLen = self.originalPatternLength, self.curTrack.editPattern.length()
                    cp = {}
                    for (r,c), v in self.curTrack.editPattern._data.items():
                        if c < oldLen:
                            for i in range(1,900):
                                if c+i*oldLen >= newLen: break
                                cp[r,c+i*oldLen] = v
                    for (r,c), v in cp.items():
                        self.curTrack.editPattern._data[r,c] = v
                    self.state = State.viewPattern
                    return True
                if e.row == 8 and e.col == 2:
                    self.curTrack.editPattern.delColBlock()
                    if self.offset >= self.curTrack.editPattern.length():
                        self.offset -= 8
                    return True
                if e.row == 8 and e.col == 3:
                    self.curTrack.editPattern.addColBlock()
                    return True
                if e.row < math.ceil(self.curTrack.editPattern.rows() / 8) and e.col < math.ceil(self.curTrack.editPattern.length() / 8):
                    self.offset = e.col * 8
                    self.rowOffset = e.row * 8
                    self.state = State.viewPattern
                    return True
            if isinstance(e, Launchkey.button) and e.pressed:
                deltaOffset = int(e.name == 'track-right') - int(e.name == 'track-left')
                deltaRowOffset = int(e.name == 'track-down') - int(e.name == 'track-up')
                self.moveOffset(8 * deltaRowOffset, 8 * deltaOffset)
                return True
        if self.state == State.editNote:
            if isinstance(e, Launchpad.button):
                r, c = self.scr2pat(e.row, e.col)
                if r == self.editingRow and c == self.editingCol and not e.pressed:
                    if self.deleteNoteOnRelease:
                        self.curTrack.editPattern.clear(self.editingRow, self.editingCol)
                    self.state = State.viewPattern
                    self.editingRow = None
                    self.editingCol = None
                    return True
                if r == self.editingRow and c > self.editingCol:
                    self.deleteNoteOnRelease = False
                    n = self.curTrack.editPattern.get(self.editingRow, self.editingCol)
                    n.length = c - self.editingCol + 1 if e.pressed else 1
                    self.curTrack.editPattern.set(self.editingRow, self.editingCol, n)
                    return True
        if self.state == State.editRow:
            if isinstance(e, Launchpad.button) and e.col == 8 and not e.pressed:
                self.state = State.viewPattern
                self.editingRow = None
                return True
            if isinstance(e, Launchkey.note) and e.velocity > 0:
                if e.note in self.curTrack.outputRow[self.editingRow].notes:
                    self.curTrack.outputRow[self.editingRow].notes.remove(e.note)
                else:
                    self.curTrack.outputRow[self.editingRow].notes.add(e.note)
                return True
            if isinstance(e, Launchkey.pad) and e.velocity > 0 and e.row == 1 and e.col == 8:
                self.curTrack.outputRow[self.editingRow].notes.clear()
                return True
        #print('unhandled input: {}'.format(e))

if __name__ == '__main__':
    application = Application()
    try:
        application.run()
    except KeyboardInterrupt:
        application.cleanup()

