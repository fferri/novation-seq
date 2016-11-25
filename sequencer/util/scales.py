def makeScale(rootNote, intervals):
    f = lambda o, m: rootNote + o * 12 + m
    return [f(o, m) for o in range(128) for m in intervals if f(o, m) < 128]

def scale(f):
    def wrapper(rootNote = 0):
        return makeScale(rootNote, f())
    return wrapper

@scale
def chromatic():
    return range(12)

@scale
def major():
    return (0, 2, 4, 5, 7, 9, 11, 12)

@scale
def minor():
    return (0, 2, 3, 5, 7, 8, 10, 12)

def drum8():
    return list(range(36)) + [36, 38, 39, 40, 42, 44, 46, 49] + [37, 41, 43, 45, 47, 48, 50, 51] + list(range(52, 128))

