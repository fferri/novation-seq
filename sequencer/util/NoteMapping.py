from sequencer.util import scales

class NoteMapping(object):
    def __init__(self, initialMap = None, pageSize = 8):
        self.pageSize = 8
        if initialMap is None:
            initialMap = enumerate(scales.chromatic())
            self.pageSize = 6
        # note on the grid -> midi note:
        self.direct = {}
        # midi note -> note(s) on the grid
        self.inverse = {}
        for gridRow, midiNote in dict(initialMap).items():
            self.direct[gridRow] = midiNote
            self.inverse[midiNote] = self.inverse.get(midiNote, []) + [gridRow]

    def getMidiNote(self, gridRow):
        return self.direct.get(gridRow, -1)

    def getGridRows(self, midiNote):
        return self.inverse.get(midiNote, [])

