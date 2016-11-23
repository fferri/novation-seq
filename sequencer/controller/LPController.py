from Controller import *

class LPController(Controller):
    def __init__(self, io):
        self.io = io

    def sendCommand(self, cmd):
        self.io.sendLaunchpadCommand(cmd)

    def onLPButtonPress(self, buf, section, row, col):
        pass

    def onLPButtonRelease(self, buf, section, row, col):
        pass

