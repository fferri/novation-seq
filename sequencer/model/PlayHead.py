class PlayHead(object):
    def __init__(self):
        self.patternIndex = -1
        self.patternRow = 0

    def reset(self):
        self.patternIndex = -1
        self.patternRow = 0

    def copyFrom(self, playHead):
        self.patternIndex = playHead.patternIndex
        self.patternRow = playHead.patternRow

