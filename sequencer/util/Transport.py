import weakref

class Transport(object):
    def __init__(self, io):
        self.io = io
        self.playing = False
        self.observers = weakref.WeakKeyDictionary()

    def addObserver(self, callable_):
        self.observers[callable_] = 1

    def removeObserver(self, callable_):
        if callable_ in self.observers: del self.observers[callable_]

    def notifyPlaybackStatusChange(self):
        observers = [self.io] + list(self.observers.keys())
        for observer in observers:
            observer.onPlaybackStatusChange(self.playing)

    def isPlaying(self):
        return self.playing

    def start(self):
        if not self.playing:
            self.playing = True
            self.notifyPlaybackStatusChange()

    def stop(self):
        if self.playing:
            self.playing = False
            self.notifyPlaybackStatusChange()

