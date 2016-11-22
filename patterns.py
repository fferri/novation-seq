import pyext
from collections import defaultdict

class patterns(pyext._class):
    _inlets = 1
    _outlets = 2

    def __init__(self):
        self.data = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
        self.length = defaultdict(lambda: 16)
        self.currentPattern = 0
        self.currentRow = 0
        self.nextPattern = None

    def get_1(self, pattern, row, col):
        self._outlet(1, self.data[pattern][row][col])

    def set_1(self, pattern, row, col, value):
        pattern = int(pattern)
        row = int(row)
        col = int(col)
        value = int(value)
        if value == 0:
            del self.data[pattern][row][col]
            if len(self.data[pattern][row]) == 0:
                del self.data[pattern][row]
        else:
            self.data[pattern][row][col] = value

    def getrow_1(self, pattern, row):
        v = list(self.data[pattern][row]) + [0]
        v = [self.data[pattern][row][col] for col in range(1 + max(v))]
        self._outlet(1, v)

    def setrow_1(self, pattern, row, *values):
        for col, value in enumerate(values):
            self.set_1(pattern, row, col, value)

    def clearpattern_1(self, pattern):
        del self.data[pattern]

    def setlength_1(self, pattern, length):
        self.length[pattern] = length

    def getlength_1(self, pattern):
        self._outlet(2, self.length[pattern])

    def tick_1(self):
        self.getrow_1(self.currentPattern, self.currentRow)
        self._outlet(2, self.currentRow)
        self.currentRow += 1
        if self.currentRow >= self.length[self.currentPattern]:
            self.currentRow = 0
            if self.nextPattern is not None:
                self.currentPattern = self.nextPattern
                self.nextPattern = None

    def setcurrentpattern_1(self, pattern):
        self.currentPattern = pattern
        self.currentRow = 0

    def enqueuepattern_1(self, pattern):
        self.nextPattern = pattern
