import numpy as np

class Song:
    def __init__(self, application):
        self.application = application
        self.data = -1 * np.ones((8,8), dtype=np.int16)
        self.curRow = 0

    def selectRow(self, row):
        self.curRow = row
        for i in range(self.data.shape[1]):
            p = self.data[row,i]
            if p == -1: p = None
            else: p = self.application.track[i].pattern[p]
            self.application.track[i].playPattern = p
        print('selected song row #%d (%s)' % (row, self.data[row,:]))

