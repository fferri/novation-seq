#import sequencer
from sequencer.model import *

s = Song()
songRow = 0
trackIndex = 0
s.set(songRow, trackIndex, [0, 1])
print('s.get({:d}, {:d}) = {}'.format(songRow, trackIndex, s.get(songRow, trackIndex)))

t = s.tracks[trackIndex]
t.setNoteColumns([0, 1])

p0 = t.patterns[0]
p0.setLength(8)
p0.setSpeedReduction(1)
p0.noteAdd(0, 60, 1)
p0.noteAdd(1, 62, 2)
p0.noteAdd(3, 63, 1)
p0.noteAdd(4, 65, 4)
p0.noteAdd(1, 74, 2)
p0.noteDelete(1, 62)
p0.noteDelete(1, 74)
p0.noteAdd(1, 74, 2)
p0.noteAdd(6, 84, 2)
p0.set(0, 3, 500)
print(p0.dump())
print(p0.noteGetIntervals())

p1 = t.patterns[1]
p1.setLength(4)
p1.setSpeedReduction(4)
p1.noteAdd(0, 10, 2)
p1.noteAdd(2, 20, 1)
p1.set(0, 3, 275)
p1.set(1, 3, 250)
p1.set(2, 3, 225)
p1.set(3, 3, 200)
print(p1.dump())
print(p1.noteGetIntervals())

for _ in range(16):
    print(t.tick(songRow))
