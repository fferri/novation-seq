from device import *
from time import sleep
import sys

def printEvent(prefix,e):
    if e is not None:
        print('{}: {}'.format(prefix,e))

def main():
    launchpad = Launchpad()
    launchpad.reset()
    launchpad.setLed(8,0,[3,0])
    launchpad.setLed(8,1,[3,3])
    launchpad.setLed(8,2,[0,3])
    launchpad.setLed(8,3,[3,3])

if __name__ == '__main__': main(*sys.argv[1:])
