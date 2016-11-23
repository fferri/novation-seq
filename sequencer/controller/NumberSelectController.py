from LPController import *

class NumberSelectController(LPController):
    def __init__(self, parent, callback, currentValue=0, minValue=0, maxValue=64):
        self.parent = parent
        self.io = self.parent.io
        self.callback = callback
        self.currentValue = currentValue
        self.minValue = minValue
        self.maxValue = maxValue

    def __str__(self):
        return '{}(parent={}, currentValue={}, minValue={}, maxValue={})'.format(self.__class__.__name__, self.parent, self.currentValue, self.minValue, self.maxValue)

    def update(self, sync=True):
        self.io.launchpad.clearBuffer('default')
        for v in range(max(0, self.minValue), 1 + self.maxValue):
            cur = v == self.currentValue
            color = [2, 0] if cur else [0, 2]
            if v == 0:
                self.io.launchpad.set('default', 'right', row, col, *color)
            else:
                row, col = (v - 1) / 8, (v - 1) % 8
                self.io.launchpad.set('default', 'center', row, col, *color)
        if sync:
            self.io.launchpad.syncBuffer('default')

    def onLPButtonPress(self, buf, section, row, col):
        super(NumberSelectController, self).onLPButtonPress(buf, section, row, col)
        buf = str(buf)
        section = str(section)
        if buf != 'default':
            return
        if section == 'center':
            v = 1 + row * 8 + col
            if self.minValue <= v <= self.maxValue:
                self.selectNumber(v)
            return
        elif section == 'right' and col == 8 and row == 7 and self.minValue <= 0 and self.maxValue >= 0:
            self.selectNumber(0)
            return

    def selectNumber(self, v):
        self.callback(v)
        self.io.setLPController(self.parent)

