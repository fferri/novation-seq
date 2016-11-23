from LPController import *

class PatternController(LPController):
    def onPatternChange(self, trackIndex, patternIndex):
        if self.io.lpcontroller == self and self.trackIndex == trackIndex and self.patternIndex == patternIndex:
            self.update()

