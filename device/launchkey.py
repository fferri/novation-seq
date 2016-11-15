from pygame import pypm
from collections import namedtuple
from .base import Base
import re

class Launchkey(Base):
	'''
	Launchkey MK1 device.
	This class is not suitable for MK2 devices.
	The protocol for MK2 devices is documented at https://d19ulaff0trnck.cloudfront.net/sites/default/files/novation/downloads/10535/launchkey-mk2-programmers-reference-guide.pdf
	The protocol for MK1 devices has been reverse engineered.
	'''

	deviceMatcher = lambda s: re.match('^Launchkey.*', s)

	note = namedtuple('note', ('note', 'velocity', 'data'))
	pad = namedtuple('pad', ('row', 'col', 'velocity', 'data'))
	control = namedtuple('control', ('num', 'value', 'data'))
	button = namedtuple('button', ('name', 'pressed', 'data'))

	buttonMidiMap = {0x68: 'track-up', 0x69: 'track-down',
			0x6A: 'track-left', 0x6B: 'track-right'}
	controlMidiMap = {0x15 + i: i for i in range(8)}

	def __init__(self, inputDevId=None, inputCDevId=None, outputDevId=None, outputCDevId=None):
		if None in (inputDevId, inputCDevId, outputDevId, outputCDevId):
			inputDevs, outputDevs = self.listDevices()
			isCtrl = lambda s: s.name.decode('ascii').endswith( 'InControl')
			inputCDevs = [dev for dev in inputDevs if isCtrl(dev)]
			inputDevs = [dev for dev in inputDevs if not isCtrl(dev)]
			outputCDevs = [dev for dev in outputDevs if isCtrl(dev)]
			outputDevs = [dev for dev in outputDevs if not isCtrl(dev)]
		if inputDevId is None: inputDevId = inputDevs[0].id
		if inputCDevId is None: inputCDevId = inputCDevs[0].id
		if outputDevId is None: outputDevId = outputDevs[0].id
		if outputCDevId is None: outputCDevId = outputCDevs[0].id
		self.midiIn = pypm.Input(inputDevId, 0)
		self.midiCIn = pypm.Input(inputCDevId, 0)
		self.midiOut = pypm.Output(outputDevId, 0)
		self.midiCOut = pypm.Output(outputCDevId, 0)

	def reset(self):
		self.midiCOut.WriteShort(0xB0, 0x00, 0x00)

	def extendedMode(self, enable):
		self.midiCOut.WriteShort(0x90, 0x0C, 0x7F if enable else 0x00)
	
	def poll(self):
		if self.midiCIn.Poll():
			d, tstamp = self.midiCIn.Read(1)[0]
			if d[0] in (0xB0, ):
				if d[1] >= 0x15 and d[1] <= 0x1C:
					return Launchkey.control(Launchkey.controlMidiMap[d[1]], d[2], d)
				if d[1] >= 0x68 and d[1] <= 0x6D:
					return Launchkey.button(Launchkey.buttonMidiMap[d[1]], d[2] > 0, d)
			elif d[0] in (0x90, 0x80) and d[1] & 0xF0 in (0x60, 0x70) and d[1] & 0x0F <= 8:
				row = int(d[1] & 0xF0 == 0x70)
				col = d[1] & 0x0F
				return Launchkey.pad(row, col, d[2], d)
			else:
				print('Launchkey: unrecognized midi on control iface: %02X %02X %02X' % tuple(d[:3]))
		if self.midiIn.Poll():
			d, tstamp = self.midiIn.Read(1)[0]
			if d[0] & 0xF0 in (0x90, 0x80):
				return Launchkey.note(d[1], d[2], d)
			else:
				print('Launchkey: unrecognized midi on note iface: %02X %02X %02X' % tuple(d[:3]))
	
	def setLed(self, row, col, val, blink = False):
		status, addr = 0x90,0x60 + row * 0x10 + col
		val = (val[0]&3) | ((val[1]&3)<<4)
		self.midiCOut.WriteShort(status, addr, val)

