class Controller(object):
    def update(self):
        pass

    def onPlayHeadChange(self, trackIndex, patternIndex, playHeadRow):
        pass

    def onTrackStatusChange(self, trackIndex, volume, muted, active):
        pass

    def onPatternChange(self, trackIndex, patternIndex):
        pass

    def onCurrentRowChange(self, row):
        pass

    def onSongChange(self):
        pass

