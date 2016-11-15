from .outputrow import *
from .pattern import *

class Track:
    def __init__(self, output, channel):
        self.output = output
        self.channel = channel
        self.outputRow = [OutputRow(self, set([36+i])) for i in range(64)]
        self.transpose = 0
        self.pattern = [Pattern(self) for _ in range(16)]
        self.playPattern = self.pattern[0]
        self.editPattern = self.pattern[0]
        self.slow = 0
        self.slowBuf = 0

    def tick(self):
        self.slowBuf += 1
        if self.slowBuf >= 2**self.slow:
            self.slowBuf = 0
            for pattern in self.pattern:
                p = pattern.tick()
                if pattern == self.playPattern:
                    col = pattern.getCol(p)
                    for row, evt in col.items():
                        notes = self.outputRow[row].notes
                        self.output.play(self.channel, notes, evt)

