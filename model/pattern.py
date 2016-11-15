class Pattern:
    def __init__(self, track):
        self.track = track
        self._data = {}
        self._length = 8
        self.tickPos = 0

    def tick(self):
        self.tickPos = (self.tickPos + 1) % self._length
        return self.tickPos

    def rows(self):
        return len(self.track.outputRow)

    def length(self):
        return self._length

    def getRow(self, row):
        return {c: v for (r,c), v in self._data.items() if r == row}

    def getCol(self, col):
        return {r: v for (r,c), v in self._data.items() if c == col}

    def get(self, row, col):
        return self._data[row,col] if (row,col) in self._data else None

    def set(self, row, col, value):
        self._data[row,col] = value

    def clear(self, row, col):
        del self._data[row,col]

    def addColBlock(self):
        if self._length + 8 <= 64:
            self._length += 8

    def delColBlock(self):
        if self._length >= 16:
            self._length -= 8

