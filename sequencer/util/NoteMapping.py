from sequencer.util import scales

class NoteMapping(object):
    def __init__(self, initialMap=None):
        if initialMap is None:
            initialMap = enumerate(scales.chromatic())
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

