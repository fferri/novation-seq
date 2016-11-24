#import sequencer
from sequencer.model import *

s = Song()
t = Track(s, 0)
p = t.patterns[0]
p.setLength(8)
t.setNoteColumns([0,1,2])
p.noteAdd(0,10,1)
p.noteAdd(1,10,1)
p.noteAdd(2,10,1)
p.noteAdd(2,20,2)
p.noteAdd(1,30,1)
p.noteAdd(4,10,2)
p.noteAdd(7,20,1)
p.setLength(8)
p.noteDelete(4,10)
p.noteDelete(1,10)
print(p.dump())
print(p.noteGetIntervals())
