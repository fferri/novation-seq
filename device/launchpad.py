from pygame import pypm
from collections import namedtuple
from .base import Base
import re

# https://d19ulaff0trnck.cloudfront.net/sites/default/files/novation/downloads/4080/launchpad-programmers-reference.pdf
class Launchpad(Base):
	deviceMatcher = lambda s: re.match('^Launchpad.*', s)

	button = namedtuple('button', ('row', 'col', 'pressed', 'data'))

	def __init__(self, inputDevId=None, outputDevId=None):
		if None in (inputDevId, outputDevId):
			inputDevs, outputDevs = self.listDevices()
		if inputDevId is None: inputDevId = inputDevs[0].id
		if outputDevId is None: outputDevId = outputDevs[0].id
		self.midiIn = pypm.Input(inputDevId, 0)
		self.midiOut = pypm.Output(outputDevId, 0)

	def reset(self):
		self.midiOut.WriteShort(0xB0, 0x00, 0x00)

	@staticmethod
	def makeValue(rgb, clear=False, copy=False):
		red, green = rgb[0:2]
		Base.checkBounds(red, 0, 3, 'red value')
		Base.checkBounds(green, 0, 3, 'green value')
		return red | (green << 4) | (int(clear) << 3) | (int(copy) << 2)

	def setLed(self, row, col, rgb, clear=False, copy=False):
		Base.checkBounds(row, 0, 8, 'row')
		Base.checkBounds(col, 0, 8, 'col')
		if row == 8: status, addr = 0xB0, 0x68 + col # top row
		else: status, addr = 0x90, (row & 0x0F) << 4 | 0x0F & col
		self.midiOut.WriteShort(status, addr, Launchpad.makeValue(rgb, clear, copy))

	def setBuffers(self, displaying=0, updating=0, flash=False, copy=False):
		Base.checkBounds(displaying, 0, 1, 'displaying')
		Base.checkBounds(updating, 0, 1, 'updating')
		val = 1 << 5
		val |= displaying
		val |= updating << 2
		val |= int(flash) << 3
		val |= int(copy) << 4
		self.midiOut.WriteShort(0xB0, 0x00, val)

	def testLeds(self, val):
		Base.checkBounds(val, 0, 2, 'val')
		self.midiOut.WriteShort(0xB0, 0x00, 0x7D + val)

	def setDutyCycle(self, num, denom):
		Base.checkBounds(num, 1, 16, 'num')
		Base.checkBounds(denom, 3, 18, 'denom')
		h = int(num >= 9)
		self.midiOut.WriteShort(0xB0, 0x1E + h, 16 * (num - 1 - 8 * h) + denom - 3)

	def setLeds(self, a, rightcol=[], toprow=[]):
		Base.checkDomain(len(a), (64,), 'a\'s length')
		Base.checkDomain(len(rightcol), (0, 8), 'rightcol\'s length')
		Base.checkDomain(len(toprow), (0, 8), 'toprow\'s length')
		v = a + rightcol + (toprow if rightcol else [])
		for v1, v2 in zip(v[::2],v[1::2]):
			v1, v2 = Launchpad.makeValue(v1), Launchpad.makeValue(v2)
			self.midiOut.WriteShort(0x92, v1, v2)
	
	def poll(self):
		if not self.midiIn.Poll(): return
		d, tstamp = self.midiIn.Read(1)[0]
		if d[0] == 0xB0:
			row = 8
			col = d[1] - 104
		else:
			row = d[1] // 16
			col = d[1] % 16
		s = Launchpad.button(row, col, d[2] > 0, d)
		return s

