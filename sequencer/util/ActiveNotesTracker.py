from collections import defaultdict

class ActiveNotesTracker(object):
    def __init__(self):
        self.notes = defaultdict(lambda: -1)

    def track(self, outputArray):
        for col, val in enumerate(outputArray):
            if val == -2: continue
            else: self.notes[col] = val

    def get(self):
        return [note for note in self.notes.values() if note > 0]

    def reset(self):
        for key in keys:
            self.notes[key] = -1

