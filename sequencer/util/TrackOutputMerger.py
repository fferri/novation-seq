from collections import defaultdict

class TrackOutputMerger(object):
    def __init__(self, track):
        self.track = track
        self.song = self.track.song
        self.trackIndex = self.track.trackIndex
        self.columnDest = {} # (pat, column) -> outputColumn or -1 if inactive

    def nextFreeColumn(self):
        v = set(self.columnDest.values())
        for col in self.track.getNoteColumns():
            if col not in v:
                return col

    def merge(self, songRow, playingPatterns, trackOutput):
        '''
        Merge the output of several patterns playing at once in the same track.

        `trackOutput` is a dictionary whose key is the patternIndex and whose value
        is the pattern row
        '''
        noteCols = self.track.getNoteColumns()

        output = {col: -1 for col in noteCols}
        # for each pattern that is playing in the current song row...
        for patternIndex in playingPatterns:
            if patternIndex in trackOutput:
                rowIndex, tickIndex, outputRow = trackOutput[patternIndex]
                hasOutput = True
            else:
                hasOutput = False
            # for each note column...
            for col in noteCols:
                if hasOutput:
                    # track the active notes in each pattern
                    z = outputRow[col]
                    if z > 0:
                        dest = self.nextFreeColumn()
                        if dest is not None:
                            self.columnDest[patternIndex, col] = dest
                else:
                    if (patternIndex, col) in self.columnDest:
                        z = -2
                    else:
                        z = -1

                if (patternIndex, col) in self.columnDest:
                    output[self.columnDest[patternIndex, col]] = z
                    if z == -1:
                        del self.columnDest[patternIndex, col]

        maxlen = 0
        for patternIndex, outputTuple in trackOutput.items():
            rowIndex, tickIndex, outputRow = outputTuple
            maxlen = max(maxlen, len(outputRow))
            for col, value in enumerate(outputRow):
                if col in noteCols: continue
                if col in output and output[col] != -1: continue
                output[col] = value

        outputVec = [-1] * maxlen
        for i, v in output.items():
            if i < maxlen:
                outputVec[i] = v

        return outputVec

