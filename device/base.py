from pygame import pypm
from collections import namedtuple
import re

class Base:
	@staticmethod
	def checkBounds(value, valueMin, valueMax, name='value'):
		if value < valueMin or value > valueMax:
			msg = '{name} must be between {valueMin} and {valueMax} ({value})'
			raise ValueError(msg.format(**locals()))

	@staticmethod
	def checkDomain(value, dom, name='value'):
		if value not in dom:
			values = ', '.join(str(x) for x in dom)
			msg = '{name} must be '
			msg += 'one of: {values}' if len(dom) > 1 else '{dom[0]}'
			raise ValueError(msg.format(**locals()))

	@classmethod
	def listDevices(cls, includeAlreadyOpen = True):
		device = namedtuple('device',
				('id', 'iface', 'name', 'inPorts', 'outPorts', 'opened'))
		inputDevs, outputDevs = [], []
		for i in range(pypm.CountDevices()):
			d = device(i, *pypm.GetDeviceInfo(i))
			if d.opened and not includeAlreadyOpen: continue
			if cls.deviceMatcher(d.name.decode('ascii')):
				if d.inPorts: inputDevs.append(d)
				if d.outPorts: outputDevs.append(d)
		return inputDevs, outputDevs

