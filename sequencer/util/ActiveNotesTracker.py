from collections import defaultdict
import weakref

class ActiveNotesTracker(object):
    def __init__(self):
        self.notes = defaultdict(lambda: -1)
        self.observers = weakref.WeakKeyDictionary()

    def addObserver(self, callable_):
        self.observers[callable_] = 1

    def removeObserver(self, callable_):
        if callable_ in self.observers: del self.observers[callable_]

    def notifyActiveNotes(self):
        observers = list(self.observers.keys())
        for observer in observers:
            observer.onActiveNotes(self.notes)

    def track(self, outputArray):
        oldNotes = {k: v for k, v in self.notes.items()}
        for col, val in enumerate(outputArray):
            if val == -2: continue
            else: self.notes[col] = val
        if oldNotes != self.notes:
            self.notifyActiveNotes()

    def get(self):
        return [note for note in self.notes.values() if note > 0]

    def reset(self):
        for key in keys:
            self.notes[key] = -1

