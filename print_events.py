from device import *
from time import sleep
import sys

def printEvent(prefix,e):
    if e is not None:
        print('{}: {}'.format(prefix,e))

def main():
    launchkey = Launchkey()
    launchpad = Launchpad()
    launchkey.reset()
    launchpad.reset()
    launchkey.extendedMode(True)
    while True:
        printEvent('Launchkey',launchkey.poll())
        printEvent('Launchpad',launchpad.poll())

if __name__ == '__main__': main(*sys.argv[1:])
