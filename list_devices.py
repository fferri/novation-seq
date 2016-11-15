from device import *

print('LAUNCHKEY:')
din,dout=Launchkey.listDevices()
for i,x in enumerate(zip(din,dout)):
    print('#{:d} IN: {}'.format(i,x[0].name))
    print('#{:d} OUT: {}'.format(i,x[1].name))

print('LAUNCHPAD:')
din,dout=Launchpad.listDevices()
for i,x in enumerate(zip(din,dout)):
    print('#{:d} IN: {}'.format(i,x[0].name))
    print('#{:d} OUT: {}'.format(i,x[1].name))

print('ALL DEVICES:')
for i in range(pypm.CountDevices()):
    info = pypm.GetDeviceInfo(i)
    print('#{:d} {}: {}'.format(i, 'IN' if info[2] else 'OUT' if info[3] else '?', info[:2]))

